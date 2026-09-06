---
title: SafeCross AI
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# SafeCross AI

AI-powered road safety and accident severity prediction system for Pakistan.


## Deployment stability — Live Detection

Live Detection uses YOLOv8 + OpenCV. The deployment configuration pins
`opencv-python-headless` and declares the Linux runtime libraries required
by OpenCV in `packages.txt`. The Docker image uses the same Python 3.12
runtime declared by `runtime.txt`.
