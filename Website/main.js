// main.js
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import * as dat from 'dat.gui';

// ----- Scene / Camera / Renderer -----
const scene = new THREE.Scene();

const container = document.getElementById('sim-container');
const w = container?.clientWidth || window.innerWidth;
const h = container?.clientHeight || window.innerHeight;

const camera = new THREE.PerspectiveCamera(45, w / h, 0.1, 1000);
camera.position.set(-10, 30, 30);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(w, h);
renderer.shadowMap.enabled = true;
renderer.setClearColor(0xFFEA00); // keep your background color
(container || document.body).appendChild(renderer.domElement);

// ----- Controls -----
const orbit = new OrbitControls(camera, renderer.domElement);

// ----- Helpers / Ground -----
scene.add(new THREE.AxesHelper(5));
scene.add(new THREE.GridHelper(30));

const planeGeometry = new THREE.PlaneGeometry(30, 30);
const planeMaterial = new THREE.MeshStandardMaterial({ color: 0xFFFFFF, side: THREE.DoubleSide });
const plane = new THREE.Mesh(planeGeometry, planeMaterial);
plane.rotation.x = -0.5 * Math.PI;
plane.receiveShadow = true;
scene.add(plane);

// ----- Lights -----
scene.add(new THREE.AmbientLight(0x333333));
const spotLight = new THREE.SpotLight(0xFFFFFF);
spotLight.position.set(-100, 100, 0);
spotLight.castShadow = true;
spotLight.angle = 0.2;
scene.add(spotLight);
const sLightHelper = new THREE.SpotLightHelper(spotLight);
scene.add(sLightHelper);

// ----- Fog (as in your original) -----
scene.fog = new THREE.FogExp2(0xFFFFFF, 0.01);

// ----- GUI (only keep light controls that make sense now) -----
const gui = new dat.GUI();
const options = { angle: 0.2, penumbra: 0, intensity: 1 };
gui.add(options, 'angle', 0, 1);
gui.add(options, 'penumbra', 0, 1);
gui.add(options, 'intensity', 0, 2);

// ===================================================================
//                  LOAD YOUR HAND MODEL (hand.glb)
// ===================================================================
let handModel = null;
const boneMap = {}; // name -> Bone

const loader = new GLTFLoader();
loader.load(
  'hand.glb', // Make sure hand.glb is in the same folder as index.html/main.js
  (gltf) => {
    handModel = gltf.scene;
    handModel.traverse((o) => {
      if (o.isMesh) {
        o.castShadow = true;
        o.receiveShadow = true;
      }
    });

    // Adjust if needed to look good in your scene
    handModel.position.set(0, 0, 0);
    handModel.scale.set(1, 1, 1);
    scene.add(handModel);

    // Cache bones by the names you use in Blender
    const names = [
      "handy",
      "pointer.001", "pointer.002",
      "middle.001",  "middle.002",
      "ring.001",    "ring.002",
      "pinky.001",   "pinky.002"
    ];
    names.forEach((n) => {
      const b = handModel.getObjectByName(n);
      if (b) {
        b.rotation.order = 'XYZ'; // match your Blender script
        boneMap[n] = b;
      }
    });

    console.log('Bones found:', Object.keys(boneMap));
  },
  undefined,
  (err) => console.error('Failed to load hand.glb:', err)
);

// ===================================================================
//           MINIMAL HOOK: drive the hand from incoming angles
// ===================================================================
// Accepts either:
//  - 27 values (roll,pitch,yaw for 9 IMUs) → maps to bones 1:1 (your Blender order)
//  - 3–5 values → uses first 3 for wrist (handy) rotation
window.updateHand = function (angles) {
  if (!handModel || !angles) return;

  // Full data path: 27 angles = 9 * (r,p,y)
  if (angles.length === 27) {
    const order = [
      "handy",
      "pointer.001", "pointer.002",
      "middle.001",  "middle.002",
      "ring.001",    "ring.002",
      "pinky.001",   "pinky.002"
    ];
    for (let i = 0; i < order.length; i++) {
      const b = boneMap[order[i]];
      if (!b) continue;
      const rDeg = angles[i * 3 + 0] || 0;
      const pDeg = angles[i * 3 + 1] || 0;
      const yDeg = angles[i * 3 + 2] || 0;
      b.rotation.set(
        THREE.MathUtils.degToRad(rDeg),
        THREE.MathUtils.degToRad(pDeg),
        THREE.MathUtils.degToRad(yDeg)
      );
    }
    return;
  }

  // Fallback: 3–5 angles → rotate wrist only (first 3)
  if (angles.length >= 3 && boneMap["handy"]) {
    const rx = THREE.MathUtils.degToRad(angles[0] || 0);
    const ry = THREE.MathUtils.degToRad(angles[1] || 0);
    const rz = THREE.MathUtils.degToRad(angles[2] || 0);
    boneMap["handy"].rotation.set(rx, ry, rz);
  }
};

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
  // keep light controls live
  spotLight.angle = options.angle;
  spotLight.penumbra = options.penumbra;
  spotLight.intensity = options.intensity;
  sLightHelper.update();

  renderer.render(scene, camera);
}
renderer.setAnimationLoop(animate);