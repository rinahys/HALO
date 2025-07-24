import * as THREE from 'three';

console.log(THREE)

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera( 25, window.innerWidth / window.innerHeight, 0.1, 1000 );

const canvas = document.querySelector("canvas.threejs");
console.log(canvas);
const renderer = new THREE.WebGLRenderer({canvas});
renderer.setSize( window.innerWidth, window.innerHeight );
document.body.appendChild( renderer.domElement );

const geometry = new THREE.BoxGeometry( 1, 1, 1 );
const material = new THREE.MeshBasicMaterial( { color: 0xff00ff } );
const cube = new THREE.Mesh( geometry, material );
const edges = new THREE.EdgesGeometry(cube.geometry);
const lineMaterial = new THREE.LineBasicMaterial({ color: 0xffffffff});
const wireframe = new THREE.LineSegments(edges, lineMaterial);
cube.add(wireframe);
scene.add( cube );

camera.position.z = 5;

function animate() {
  cube.rotation.x += 0.01;
  cube.rotation.y += 0.01;
  renderer.render( scene, camera );
}
renderer.setAnimationLoop( animate );