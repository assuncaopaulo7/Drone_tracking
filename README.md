# Drone Tracking in Simulation with YOLO11 and MAVSDK

## 🧠 Introduction
This project implements a multi-drone tracking system using real-time object detection with YOLOv11 in a Gazebo simulation environment. One drone, equipped with a simulated camera, detects and tracks another moving drone, changing its yaw angle to match the detected drone position. The system integrates computer vision with autonomous flight control using PX4 Autopilot and MAVSDK-Python, and enables coordination via UDP communication.

## 🎥 Results
A demonstration of the drone tracking behavior can be seen in the following GIF:

![Tracking Demo](IMG_0239.gif)

## 🛠 Requirements
- **Gazebo Sim (Harmonic)**
- **PX4-Autopilot v1.14**
- **Python 3.10+**
- **PyTorch** (with CUDA support recommended)
- **Ultralytics YOLO11** (`pip install ultralytics`)
- **MAVSDK-Python**
- **OpenCV** (`opencv-python`)
- **Ubuntu 22.04+** (recommended)

## ▶️ How to Run

1. Clone this repository.

2. Open the `script.sh` file and update all the file paths to match your local environment:
   - YOLO model path (e.g., `best.pt`)
   - CSV trajectory files
   - Any hardcoded absolute paths

3. In the terminal, simply run:
   ```bash
   ./script.sh
