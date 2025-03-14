
# Autonomous Car Project
g      hp_zSVAxeUBFvsQ17Ai_____JVOWkFFltCff1n2pE4Kv
Overview

This repository contains the code and documentation for an autonomous car project using Raspberry Pi and Arduino. The project focuses on serial communication between Raspberry Pi and Arduino to control the car's movement and sensors.

# Features

Serial communication between Raspberry Pi and Arduino

Motor control using Arduino

Sensor data acquisition (e.g., ultrasonic, IR, or LiDAR)

Basic autonomous navigation

Remote control capabilities

# Hardware Requirements

Raspberry Pi 5 (or any model with serial communication capability)

Arduino (Uno, Mega, or any compatible board)

Motor driver module (L298N or similar)

Ultrasonic sensor (HC-SR04 or similar)

IR sensors for line following

Power supply (batteries or adapter)

# Software Requirements

Raspberry Pi OS (or any Linux-based OS for Raspberry Pi)

Python (for Raspberry Pi)

Arduino IDE (for Arduino programming)

pyserial library for serial communication

# Installation

1. Clone the Repository
2. Install Dependencies
3. Upload Arduino Code
   Open arduino_code.ino in Arduino IDE

   Select the correct board and port

   Upload the code to the Arduino
Run the Python Script

# Communication Protocol

Raspberry Pi sends movement commands (F, B, L, R, S) via serial

Arduino reads commands and controls motors accordingly

Arduino sends sensor data back to Raspberry Pi

# Future Improvements

Implement obstacle avoidance

Integrate a camera for visual navigation

Develop a mobile app for remote control

# Resources

https://robofoundry.medium.com/programming-arduino-from-raspberry-pi-remotely-dc71cf17d84e

https://www.youtube.com/watch?v=mfIacE-SPvg

https://www.youtube.com/watch?v=jU_b8WBTUew

# License

This project is open-source and available under the MIT License.

# Contributors

Dan Chen (@dc8156046)
