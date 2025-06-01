# Multi-Camera Home Pet Tracker & Spatial Overlay

## Project Overview
Track the real-time and historical movements of a dog across multiple rooms (and outdoor areas) using low-cost RTSP cameras, object detection, and a floorplan overlay.

## Demo Goal
Run a few minutes of footage across 4 camera feeds and produce a visual, time-based tracking overlay on a house blueprint, optionally including Slack alerts or heatmap summaries.

## Key Inputs

| Source | Format | Notes |
|--------|--------|-------|
| RTSP camera feeds (Tapo C100) | rtsp://... | 4 total, each fixed in a room |
| House layout | PNG/SVG or JSON | Can be drawn manually or scanned |
| Object detector | Roboflow model | Custom dog detector (fine-tuned) |
| Room metadata | JSON config | Maps camera ID → room → coordinates |

## Core Features

### Live Video Ingestion
- Connect to 4 RTSP streams simultaneously
- Sample or stream frames in near real-time

### Dog Detection
- Run inference using Roboflow-hosted or local model
- Extract bounding box center + confidence

### Camera-to-Room Mapping
- Map detections to a room based on camera source
- Optionally triangulate or interpolate position if multiple detections overlap

### Blueprint Position Mapping
- Convert room ID + detection to (x, y) coordinate on floorplan
- Overlay movement path on blueprint

### Visualization
Render floorplan with:
- 🟢 Live dog position
- 🟡 Motion trails over time
- 🔴 Heatmap of activity density (optional)
- 🕒 Time-based animation / fast-forward

## Stretch Features (Nice to Have)

### Alerts & Logging
- Send Slack alert when dog enters or leaves certain areas (e.g. backyard)
- Log all detections with timestamp + room + position

### Additional Features
- Bathroom trip detector (dog exits house → stays outside > 60s)
- Daily summary report ("Dog spent 72% of time in Living Room")
- Multi-animal support (if another pet is added)
- Simple web dashboard or replay viewer

## Configuration

Before running the application, you need to set up two configuration files:

### 1. MediaMTX Configuration
Copy `mediamtx.sample.yml` to `mediamtx.yml` and configure your RTSP stream settings:
```bash
cp mediamtx.sample.yml mediamtx.yml
```

### 2. Environment Variables
Copy `.env.sample` to `.env` and configure your camera streams:
```bash
cp .env.sample .env
```
Edit `.env` to include your RTSP camera configuration in the following format:
```
CAM_PROXY_CONFIG=[{"name":"office","stream_url":"rtsp://host.docker.internal:8554/office"},...]
```

## Setup & Running

### Start the Application
```bash
docker-compose up --build
```

### Tear Down
```bash
docker-compose down
```