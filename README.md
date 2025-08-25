# HALO

## Introduction

HALO (Hand Assisted Learning Operator) is a dataglove-controlled 3D simulation, which can mimic user movement as well as classify some gestures using machine learning. Our design prioritizes accessibility and modularity, being one of the few data glove products on the market built from affordable, widely available components. HALO is tailored for hobbyists and researchers; alongside the product, we provide a detailed guide and explanations to support setup and use, while also encouraging customization and extensions for users who want to build upon our foundation.
<br></br>
<!--here we need to also talk about what we are pitching it as. Cheaper alternative for hobbyists, flexible and modular design, etc-->

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
The microcontroller unit used is an ESP32. The IMUs use the I2C protocol to communicate with the ESP32. To allow the use of more than two IMUs with one ESP32, we used two TCA9548A I2C Multiplexers, which allow communication with up to 8 I2C devices each.


## Glove Design
The components are assembled onto a sports glove and fitted using 3D-printed shields and surfaces to improve stability. Each finger houses two MPU6050 IMUs, one placed above the MCP joint and the other placed above the PIP joint. The BNO055 is placed on the back of the glove, beside the ESP32 and multiplexers, which are stacked on top. The ESP32 and MUXs are fitted into female header pins that are soldered onto a protoboard.
The power module and battery are placed on the forearm, right below the wrist. The module is connected to a protoboard that includes circuitry for a switch, fuse, and an LED that turns on when the battery is connected.include schematic of power cct
## Web Interface
tbc


<!-- lets add a section either in the README or another file where we have all the sources we used like other github repos, articles etc and write what we took inspiration from exactly. would be useful for ourselves later -->
