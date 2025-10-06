import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

//setting scene
const scene = new THREE.Scene();
const container = document.getElementById("sim-container");
const w = container?.clientWidth || window.innerWidth;
const h = container?.clientHeight || window.innerHeight;

//setting camera
const camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 1000);
camera.position.set(-10, 30, 30);

//setting renderer
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(w, h);
renderer.shadowMap.enabled = false;
renderer.setClearColor(0xa7d196);
(container || document.body).appendChild(renderer.domElement);

//allowing mouse movement in sim
const orbit = new OrbitControls(camera, renderer.domElement);

//lighting
scene.add(new THREE.AmbientLight(0xffffff, 1));
scene.fog = new THREE.FogExp2(0xffffff, 0.01);

//loading hand model:
let handModel = null;
const boneMap = {};
const axesHelpers = [];

const loader = new GLTFLoader();
loader.load(
  "hand.glb",
  (gltf) => {
    handModel = gltf.scene;

    handModel.traverse((o) => {
      if (o.isMesh) {
        o.material = new THREE.MeshBasicMaterial({
          color: o.material.color || 0xffffff,
        });
      }
    });

    handModel.position.set(0, 0, 0);
    handModel.scale.set(1, 1, 1);
    scene.add(handModel);

    // Cache all bones and add optional debug axes
    handModel.traverse((o) => {
      if (o.isBone) {
        o.rotation.order = "XYZ";
        boneMap[o.name] = o;

        const axes = new THREE.AxesHelper(0.5);
        axes.visible = false; 
        o.add(axes);
        axesHelpers.push(axes);
      }
    });

    console.log("All bones in hand model:", Object.keys(boneMap));
  },
  undefined,
  (err) => console.error("Failed to load hand.glb:", err)
);

//calibrating and orientation:
const calibration = {};
let latestData = null;

// finds average of the quaternions
function averageQuaternions(quaternions) {
  const qSum = new THREE.Vector4(0, 0, 0, 0);

  quaternions.forEach((q) => {
    const nq = q.clone().normalize();
    qSum.x += nq.x;
    qSum.y += nq.y;
    qSum.z += nq.z;
    qSum.w += nq.w;
  });

  const n = quaternions.length;
  const mean = new THREE.Quaternion(
    qSum.x / n,
    qSum.y / n,
    qSum.z / n,
    qSum.w / n
  );
  return mean.normalize();
}

let wristAxisFix = new THREE.Quaternion();   // correction for wrist
let fingerAxisFix = new THREE.Quaternion();  // correction for all fingers

// axis fixers for calibrating the sim:
function applyOrientation(bone, qIMU, name) {
  const q = new THREE.Quaternion(qIMU.x, qIMU.y, qIMU.z, qIMU.w).normalize();

  if (calibration[name]) {
    const qOffset = calibration[name].clone().invert();
    q.multiply(qOffset);
  }

  // Apply axis fix depending on bone
  if (name === "handy") {
    q.multiply(wristAxisFix);
  } else {
    q.multiply(fingerAxisFix);
  }

  bone.quaternion.copy(q);
}

// find the mean values,take it as reference to calibrate
function calibrateOverTime(duration = 1500) {
  if (!latestData) return;

  const statusEl = document.getElementById("calibration-status");
  if (statusEl) statusEl.textContent = "Calibrating...";

  const samples = { handy: [], fingers: [] };
  const fingerNames = [
    "pointer001","pointer002",
    "middle001","middle002",
    "ring001","ring002",
    "pinky001","pinky002",
    "thumb001","thumb002"
  ];

  const start = performance.now();

  function sample() {
    if (!latestData) {
      requestAnimationFrame(sample);
      return;
    }

    //storing Wrist imu values for the mean
    if (latestData.wrist) {
      samples.handy.push(new THREE.Quaternion(
        latestData.wrist.x,
        latestData.wrist.y,
        latestData.wrist.z,
        latestData.wrist.w
      ));
    }

    //storing the finger data for the mean
    latestData.fingers?.forEach((f, i) => {
      if (!samples.fingers[i]) samples.fingers[i] = [];
      samples.fingers[i].push(new THREE.Quaternion(f.x, f.y, f.z, f.w));
    });

    if (performance.now() - start < duration) {
      requestAnimationFrame(sample);
    } else {
      // Mean for wrist
      if (samples.handy.length > 0) {
        calibration["handy"] = averageQuaternions(samples.handy);
      }

      // Mean for fingers
      samples.fingers.forEach((arr, i) => {
        if (arr && arr.length > 0) {
          calibration[fingerNames[i]] = averageQuaternions(arr);
        }
      });

      if (statusEl) statusEl.textContent = "Calibration complete ";
      console.log("Calibration complete (averaged):", calibration);
    }
  }

  sample();
}

//updating hand data:
window.updateHand = function (data) {
  if (!handModel || !data) return;
  latestData = data;

  // Wrist
  if (data.wrist && boneMap["handy"]) {
    const { x = 0, y = 0, z = 0, w = 1 } = data.wrist;
    applyOrientation(boneMap["handy"], { x, y, z, w }, "handy");
  }

  // Fingers
  if (Array.isArray(data.fingers)) {
    const fingerNames = [
      "pointer001","pointer002",
      "middle001","middle002",
      "ring001","ring002",
      "pinky001","pinky002",
      "thumb001","thumb002"
    ];

    data.fingers.forEach((f, i) => {
      const name = fingerNames[i];
      const b = boneMap[name];
      if (b && f) {
        applyOrientation(b, f, name);
      }
    });
  }
};

// adds the calibrate function to pressing the button
document.getElementById("calibrate-btn")?.addEventListener("click", () => {
  calibrateOverTime(1500); // average over 1.5s
});

//adding function to the button to allow the axes to show
document.getElementById("axes-toggle")?.addEventListener("change", (e) => {
  const visible = e.target.checked;
  axesHelpers.forEach((a) => (a.visible = visible));
});

// resizing the animation window
window.addEventListener("resize", () => {
  const w2 = container?.clientWidth || window.innerWidth;
  const h2 = container?.clientHeight || window.innerHeight;
  camera.aspect = w2 / h2;
  camera.updateProjectionMatrix();
  renderer.setSize(w2, h2);
});


//for calibration, helps correct axises:
window.addEventListener("keydown", (e) => {
  const step = Math.PI / 2;

  // Wrist corrections (keys 1–3)
  if (e.key === "1") {
    wristAxisFix = new THREE.Quaternion().setFromEuler(new THREE.Euler(step, 0, 0));
    console.log("Wrist axis fix: rotate X 90°");
  } else if (e.key === "2") {
    wristAxisFix = new THREE.Quaternion().setFromEuler(new THREE.Euler(0, step, 0));
    console.log("Wrist axis fix: rotate Y 90°");
  } else if (e.key === "3") {
    wristAxisFix = new THREE.Quaternion().setFromEuler(new THREE.Euler(0, 0, step));
    console.log("Wrist axis fix: rotate Z 90°");
  }

  // Finger corrections (keys 7–9)
  else if (e.key === "7") {
    fingerAxisFix = new THREE.Quaternion().setFromEuler(new THREE.Euler(step, 0, 0));
    console.log("Finger axis fix: rotate X 90°");
  } else if (e.key === "8") {
    fingerAxisFix = new THREE.Quaternion().setFromEuler(new THREE.Euler(0, step, 0));
    console.log("Finger axis fix: rotate Y 90°");
  } else if (e.key === "9") {
    fingerAxisFix = new THREE.Quaternion().setFromEuler(new THREE.Euler(0, 0, step));
    console.log("Finger axis fix: rotate Z 90°");
  }

  // Reset both
  else if (e.key === "0") {
    wristAxisFix = new THREE.Quaternion();
    fingerAxisFix = new THREE.Quaternion();
    console.log("Axis fix: reset (identity)");
  }
});


//looping for updating scene
function animate() {
  renderer.render(scene, camera);
}
renderer.setAnimationLoop(animate);

//connecting to websocket
const debugLog = document.getElementById("debug-log");
function logDebug(msg) {
  debugLog.textContent += "\n" + msg;
  debugLog.scrollTop = debugLog.scrollHeight;
}

let ws;
function connectWS() {
  ws = new WebSocket(`ws://${window.location.hostname}:3000/browser`);

  ws.onopen = () => {
    document.getElementById("connection-status").textContent = "Connected";
    logDebug(" Connected to Node.js server");
  };

  // Latency tracking
  let lastSeq = null;
  let lastEspTs = null;
  let lastBrowserTs = null;

ws.onmessage = (evt) => {
  try {
    const data = JSON.parse(evt.data);

    if (data.type === "esp_status" && data.status === "disconnected") {
      logDebug("ESP32 disconnected");
      document.getElementById("connection-status").textContent = "ESP32 disconnected";
      return;
    }

    if (data.gesture) {
      document.getElementById("gesture-output").textContent = data.gesture;
    }

    if (typeof window.updateHand === "function") {
      window.updateHand(data);
    }

    logDebug(evt.data);
  } catch (err) {
    logDebug("JSON parse error: " + err.message);
  }
};


  ws.onclose = () => {
    document.getElementById("connection-status").textContent = "Disconnected";
    logDebug("WebSocket closed. Reconnecting in 3s...");
    setTimeout(connectWS, 3000);
  };

  ws.onerror = (err) => {
    logDebug("WebSocket error: " + err.message);
  };
}

connectWS();
