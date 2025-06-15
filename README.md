# 🌟 Poser  
*Interactive AI-Powered Pose Detection on the Web*

Poser is a real-time web application that lets you use your webcam to detect, analyze, and gamify human poses. Poser gives instant feedback on alignment and form—making movement fun, engaging, and accessible. Built with MediaPipe, OpenCV, Flask, and React, Poser delivers a smooth, low-latency experience right in your browser.

---

## 🌱 Introduction

Poser bridges the gap between AI research and everyday movement. By leveraging Google’s MediaPipe Pose model and OpenCV, it tracks your joint landmarks, calculates key angles, and instantly tells you if you’ve nailed the form. A playful UI and scoring system turn mundane exercises into interactive challenges—perfect for home workouts, physical therapy, or just goofing around with friends.

---

## 🌟 Key Features

- **Real-Time Pose Estimation**  
  Utilizes MediaPipe’s efficient landmark detector to process 30+ FPS on modern hardware.

- **Gamified Feedback & Scoring**  
  Hit a 70% alignment threshold to score points; track successes and fails in each session.

- **Multi-Pose Support**  
  Easily extendable: add new poses by defining landmark angles and weights in `server/poses.json`.

- **Live Camera Preview**  
  Mirror, pause, and snapshot your session directly in the browser.

---

## 🧠 Technology Stack

- ⚛️ **React (Create React App)** – Frontend UI & camera integration  
- 🐍 **Flask & Flask-SocketIO** – Backend API & real-time WebSocket channel  
- 📷 **OpenCV** – Frame capture & preprocessing  
- ⛓️ **MediaPipe Pose** – Pose landmark detection  
- 🐳 **Docker & Docker Compose** – Containerization for easy deployment  
- 🔧 **Python (3.9+)** – Backend runtime  
- 🛠️ **Node.js (16+)** – Frontend runtime  

---

## 📝 Project Details

- **Project Title:** Poser  
- **Team Name:** Nakama Dev  
- **Team Members:** Izzul, Adli, Meru, Zaim  
- **Institution:** Universiti Tenaga Nasional (UNITEN)  
- **Event:** LoopHole Hackathon 2025  
