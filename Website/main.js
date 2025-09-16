import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

// ----- Scene / Camera / Renderer -----
const scene = new THREE.Scene();

const container = document.getElementById('sim-container');
const w = container?.clientWidth || window.innerWidth;
const h = container?.clientHeight || window.innerHeight;

const camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 1000);
camera.position.set(-10, 30, 30);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(w, h);
renderer.shadowMap.enabled = false; // not needed with MeshBasicMaterial
renderer.setClearColor(0xA7D196);
(container || document.body).appendChild(renderer.domElement);

// ----- Controls -----
const orbit = new OrbitControls(camera, renderer.domElement);

// ----- Lights -----
const ambientLight = new THREE.AmbientLight(0xffffff, 1);
scene.add(ambientLight);

// ----- Fog -----
scene.fog = new THREE.FogExp2(0xFFFFFF, 0.01);

// ----- Raycaster for clicking bones -----
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();

// ----- Currently highlighted bone -----
let highlightedSphere = null;

// ===================================================================
//                  LOAD HAND MODEL
// ===================================================================
let handModel = null;
const boneMap = {}; // name -> Bone

const loader = new GLTFLoader();
loader.load(
  'hand.glb',
  (gltf) => {
    handModel = gltf.scene;

    handModel.traverse((o) => {
      if (o.isMesh) {
        o.material = new THREE.MeshBasicMaterial({
          color: o.material.color || 0xffffff
        });
      }
    });

    handModel.position.set(0, 0, 0);
    handModel.scale.set(1, 1, 1);
    scene.add(handModel);

    // Traverse all bones and cache them
    handModel.traverse((o) => {
      if (o.isBone) {
        o.rotation.order = 'XYZ';
        boneMap[o.name] = o;

        // Add small helper sphere for easier clicking
        const sphere = new THREE.Mesh(
          new THREE.SphereGeometry(0.15),
          new THREE.MeshBasicMaterial({ color: 0xEFC3CA })
        );
        o.add(sphere);
      }
    });

    console.log('All bones in hand model:', Object.keys(boneMap));
  },
  undefined,
  (err) => console.error('Failed to load hand.glb:', err)
);

// ===================================================================
//           HOOK: update hand from JSON packet
// ===================================================================
window.updateHand = function (data) {
  if (!handModel || !data) return;

  // --- Wrist ---
  if (data.wrist && boneMap["handy"]) {
    const { roll = 0, pitch = 0, yaw = 0 } = data.wrist;
    boneMap["handy"].rotation.set(
      THREE.MathUtils.degToRad(roll),
      THREE.MathUtils.degToRad(pitch),
      THREE.MathUtils.degToRad(yaw)
    );
  }

  // --- Fingers ---
  if (Array.isArray(data.fingers)) {
    const fingerNames = [
      "pointer001", "pointer002",
      "middle001",  "middle002",
      "ring001",    "ring002",
      "pinky001",   "pinky002",
      "thumb001", "thumb002"

    ];

    data.fingers.forEach((f, i) => {
      const name = fingerNames[i];
      const b = boneMap[name];
      if (b && f) {
        b.rotation.set(
          THREE.MathUtils.degToRad(f.roll || 0),
          THREE.MathUtils.degToRad(f.pitch || 0),
          THREE.MathUtils.degToRad(f.yaw || 0)
        );
      }
    });
  }

};

// ===================================================================
//           WebSocket: receive ESP32 data
// ===================================================================
const ESP32_IP = "192.168.50.253"; // replace with your ESP32 IP
const ws = new WebSocket(`ws://${ESP32_IP}:81`);

ws.onopen = () => {
  console.log("Connected to ESP32 WebSocket!");
};

ws.onmessage = (event) => {
  try {
    const data = JSON.parse(event.data);
    window.updateHand(data);
  } catch(e) {
    console.error("JSON parse error:", e);
  }
};

ws.onclose = () => console.log("WebSocket disconnected!");
ws.onerror = (err) => console.error("WebSocket error:", err);

// ===================================================================
//           CLICK TO GET & HIGHLIGHT BONE
// ===================================================================
window.addEventListener('click', (event) => {
  const rect = renderer.domElement.getBoundingClientRect();
  mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

  raycaster.setFromCamera(mouse, camera);

  const bones = Object.values(boneMap);
  const intersects = raycaster.intersectObjects(bones, true);

  if (intersects.length > 0) {
    // Traverse up to the nearest bone
    let obj = intersects[0].object;
    while (obj && !obj.isBone) {
      obj = obj.parent;
    }

    if (obj && obj.isBone) {
      console.log('Clicked bone:', obj.name);

      // Remove previous highlight
      if (highlightedSphere) {
        scene.remove(highlightedSphere);
      }

      // Add highlight at bone position
      highlightedSphere = new THREE.Mesh(
        new THREE.SphereGeometry(0.2),
        new THREE.MeshBasicMaterial({ color: 0xD33B53})
      );
      highlightedSphere.position.copy(obj.getWorldPosition(new THREE.Vector3()));
      scene.add(highlightedSphere);
    }
  }
});

// ----- Resize handling -----
window.addEventListener('resize', () => {
  const w2 = container?.clientWidth || window.innerWidth;
  const h2 = container?.clientHeight || window.innerHeight;
  camera.aspect = w2 / h2;
  camera.updateProjectionMatrix();
  renderer.setSize(w2, h2);
});

// ----- Render loop -----
function animate() {
  renderer.render(scene, camera);
}
renderer.setAnimationLoop(animate);


