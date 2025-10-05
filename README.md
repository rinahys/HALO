🧤 HALO — Hand-Assisted Learning Operator

A low-cost, sensor-based dataglove and 3D simulation for visualising hand motion in real time.

👋 Overview

HALO is a prototype dataglove that tracks hand motion using embedded sensors and visualises it in a 3D environment.
It was designed as a proof-of-concept to explore accessible motion tracking without relying on cameras or expensive commercial gloves.

🧩 How It Works

HALO has three main layers:

Hardware — A glove fitted with multiple IMUs (motion sensors) and an ESP32 microcontroller.

Transmission — Sensor data is streamed via I²C and serial to a computer.

Simulation — A 3D model (built in VPython) mirrors the hand’s motion in real time.

It started as a web-based Three.js visualiser, then pivoted to VPython for faster debugging and calibration.

⚙️ Hardware Summary

11 IMUs total

2× MPU6050 (6-axis) per finger

1× BNO055 (9-axis) on the wrist

ESP32 microcontroller

2× TCA9548A I²C multiplexers (to handle address conflicts)

3D-printed sensor mounts designed in SolidWorks

⚠️ Reproducing the glove requires soldering, power management, and calibration — it’s more of a hardware experiment than a DIY kit.

🧠 Software Stack
Purpose	Tools / Libraries
Microcontroller	Arduino IDE, Wire, MPU6050, Adafruit_BNO055
Simulation	Python, VPython
Modeling	Blender (hand model), SolidWorks (sensor mounts)
IDEs	Visual Studio Code, Arduino IDE
🧰 Data Processing

To make IMU data usable:

Raw sensor data → Low-pass + Complementary filtering

Orientation represented as quaternions (for stable 3D rotation)

Real-time updates rendered in VPython

🔋 Power Notes

Powering 11 sensors on one glove isn’t trivial.
We tested 9 V and Li-ion batteries with LM2596 buck converters, but ultimately powered the prototype via USB for reliability.
A proper power management PCB is recommended for future versions.

🚀 Future Ideas

Gesture recognition with machine learning

Haptic feedback integration

Modular PCB design

Additional sensors (tactile, ultrasonic, IR)

🧑‍💻 Team

HALO was developed by
Alistair Joubert, Hanna Semnani, Jai Kaza Venkata, Londrina Hyseni, Nicole Oliveira Costa, and Sarah Mahmoud
with mentorship from Suraj Nair.

💬 Notes
The repo and documentation are here for learning, inspiration, and reference — if you build on it, let us know!
