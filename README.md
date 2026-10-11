---
title: SafeCross AI
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# SafeCross AI

**AI-Powered Road Safety and Emergency Management Prototype for Pakistan**

SafeCross AI is an AI-based road safety prototype designed to demonstrate accident severity prediction, traffic analytics, computer-vision-based detection, and emergency-response decision support.

The project explores how artificial intelligence can help analyze road accident risks and support better-informed emergency decisions in Pakistan.

## Key Features

- **Accident Severity Prediction:** Estimates accident severity using supported weather, road, traffic, and accident-related inputs.
- **Fatality Risk Prediction:** Provides a separate fatality-risk prediction capability.
- **Pakistan Traffic Dashboard:** Displays historical traffic accident statistics for analysis.
- **Accident Hotspot Map:** Visualizes accident-related location data for exploratory analysis.
- **Live Accident Detection:** Uses YOLOv8 and OpenCV for computer-vision-based detection.
- **Emergency Priority System:** Demonstrates risk-based emergency prioritization.
- **Emergency Response Support:** Provides recommendations to support emergency decision-making.
- **Prediction History:** Supports reviewing prediction records through the backend.

## Technology Stack

- Python
- Streamlit
- FastAPI
- Machine Learning
- XGBoost components
- YOLOv8
- OpenCV
- Pandas and NumPy
- SQLAlchemy and SQLite

## How It Works

1. The user provides accident-related information through the application.
2. Supported inputs are sent to the backend for processing.
3. The prediction component estimates accident severity.
4. The application displays the prediction and associated risk information.
5. Relevant recommendations are provided to support decision-making.
6. Prediction records can be stored and retrieved through the backend.

## Deployment Stability — Live Detection

Live Detection uses YOLOv8 and OpenCV. The deployment configuration pins `opencv-python-headless` and declares the Linux runtime libraries required by OpenCV in `packages.txt`. The Docker image uses the Python runtime specified by the project configuration.

## Data and Limitations

- The machine-learning training dataset and historical Pakistan traffic statistics are separate data sources.
- Historical statistics are intended for analysis and do not represent real-time accident reports.
- Hotspot visualizations should not be interpreted as verified accident locations unless supported by validated location data.
- Model predictions are estimates and may not always be correct.
- Emergency recommendations and smart-barrier behavior are prototype demonstrations, not certified traffic-control commands.
- SafeCross AI is a decision-support prototype and does not replace emergency services or authorized traffic-management systems.

## Project Goal

SafeCross AI demonstrates how machine learning, computer vision, traffic analytics, and emergency decision support can be combined in a road-safety application focused on Pakistan.
