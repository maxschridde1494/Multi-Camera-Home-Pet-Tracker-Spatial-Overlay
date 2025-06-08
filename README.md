# Project Piper: Multi-Camera Home Dog Tracker

## Project Overview

Track the real-time movements of Piper (my dog) across multiple rooms and outdoor areas using low-cost RTSP cameras and [Roboflow Inference](https://inference.roboflow.com/) object detection.

## Key Inputs

| Source | Format | Notes |
|--------|--------|-------|
| RTSP camera feeds (Tapo C100) | rtsp://... | 4 total, each fixed in a room |
| Object detector | Roboflow model | Custom dog detector (fine-tuned) |
| Room metadata | JSON config | Maps camera ID → room |

## Core MVP Features

### Live Video Ingestion
- Connect to 4 RTSP streams simultaneously
- Sample frames in near real-time

### Dog Detection
- Run inference using Roboflow-hosted fine-tuned model
- Extract bounding box center + confidence
- Map detections to a room based on camera source
- Snapshot Piper's location for strong confidence predictions

### Web App (Real Time Display)
- Display current location of Piper
- Carousel of 5 most recent snapshots
- Activy stream of last 10 predictions

## Phase 2: Spatial Analytics & Visualization

### Overview
Transform raw detection data into meaningful spatial insights by overlaying movement patterns on a house blueprint. This phase focuses on advanced visualization, spatial analysis, and automated insights generation.

### Core Features

#### 1. Spatial Mapping Infrastructure
- **House Layout Integration**
  - Support for PNG/SVG floorplans or JSON layout definitions
  - Manual or automated room boundary scanning
  - Coordinate system mapping for each room
- **Position Triangulation**
  - Multi-camera detection reconciliation
  - Advanced position interpolation for coverage gaps
  - Confidence-weighted position estimation

#### 2. Movement Visualization
- **Real-time Overlay**
  - Live position indicator on floorplan
  - Smooth motion trails with time decay
  - Interactive timeline scrubber
- **Historical Analysis**
  - Heat map generation for activity density
  - Time-lapse playback of movement patterns
  - Customizable time window selection

#### 3. Automated Insights
- **Smart Alerts**
  - Configurable zone-based notifications via Slack
  - Intelligent event detection (e.g., outdoor stays > 60s)
  - Anomaly detection for unusual patterns
- **Analytics Dashboard**
  - Daily/weekly activity summaries
  - Room occupancy statistics
  - Pattern analysis and trends

### Future Extensibility
- Multi-pet tracking support
- API endpoints for external integrations
- Custom event definition framework

### Implementation Priorities
1. Basic floorplan overlay with real-time position
2. Historical path visualization
3. Analytics dashboard
4. Smart alerts and notifications
5. Advanced features (multi-pet, API, etc.)

## Configuration

Before running the application, you need to set up two configuration files:

### 1. [MediaMTX](https://github.com/bluenviron/mediamtx) Proxy Configuration
Copy `mediamtx.sample.yml` to `mediamtx.yml` and configure your RTSP stream settings:
```bash
cp mediamtx.sample.yml mediamtx.yml
```

### 2. Environment Variables
Copy `.env.sample` to `.env` and configure your camera streams:
```bash
cp .env.sample .env
```
Edit `.env` to include your RTSP camera configuration. Example format:
```
CAM_PROXY_CONFIG=[
  {
    "name":"office",
    "stream_url":"rtsp://host.docker.internal:8554/office"
  },
  ...
]
```

## Setup & Running

### Start the Application
```bash
docker-compose up --build
```
Open the React web app at `http://localhost:5173`.

### Tear Down
```bash
docker-compose down
```