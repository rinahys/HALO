# HALO

## Introduction

HALO (Hand Assisted Learning Operator) is a dataglove-controlled 3D simulation, which can mimic user movement as well as classify some gestures using machine learning.
<br></br>

## Simulation
The simulation was created using three.js, with the rigged hand model being made using Blender.

## Hardware 
The hardware of the data glove can be categorized into three sections: IMUs, Power, and MCU
### IMUs
Our design uses ten 6-axis MPU6050 IMUs (2 IMUs on each finger) and one 9-axis BNO055 IMU on the back of the hand for wrist movement.
### Power
A 9 volt battery? is used to power the dataglove. The voltage is dropped to the desired 3.3 volts using an lm2596 dc-dc buck converter.
<img width="300" height="300" alt="image" src="https://github.com/user-attachments/assets/ca45b96a-a3da-4af4-9517-191788b638ed" />
### MCU
The microcontroller unit used is an esp32. 
yet to include
- comms protocol+MUX


## Glove Design
tbc
## Web Interface
tbc
