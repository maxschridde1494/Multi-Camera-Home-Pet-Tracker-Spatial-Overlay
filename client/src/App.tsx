import { useEffect, useState, useCallback } from 'react'
import './App.css'
import { useRealTime, type RealTimeUpdate, RealTimeMessage } from './hooks/useRealTime'
import type { Detection, Snapshot, WebsocketConnectionInit } from './types'

function App() {
  const [last10Detections, setLast10Detections] = useState<Detection[]>([])
  const [last5Snapshots, setLast5Snapshots] = useState<string[]>([])
  const [currentSnapshotIndex, setCurrentSnapshotIndex] = useState(0)
  const [isCarouselPaused, setIsCarouselPaused] = useState(false)
  const [highConfidenceDetection, setHighConfidenceDetection] = useState<Detection>()
  const realTimeUpdate = useRealTime('ws://localhost:8000/ws')

  const handleRealTimeUpdate = (realTimeUpdate: RealTimeUpdate) => {
    if (!realTimeUpdate) return

    const { data, message } = realTimeUpdate
    if (!data) return

    switch (message) {
      case RealTimeMessage.ConnectionMade:
        const initData = data as WebsocketConnectionInit
        setLast10Detections(initData.last_10_detections)
        setLast5Snapshots(initData.last_5_snapshots)
        setCurrentSnapshotIndex(0)
        setHighConfidenceDetection(initData.last_10_detections[0])
        break
      case RealTimeMessage.DetectionMade:
        setLast10Detections(prev => [(data as Detection), ...prev].slice(0, 10))
        break
      case RealTimeMessage.HighConfidenceDetectionMade:
        setHighConfidenceDetection(data as Detection)
        break
      case RealTimeMessage.SnapshotMade:
        setLast5Snapshots(prev => [(data as Snapshot).asset_path, ...prev].slice(0, 5))
        setCurrentSnapshotIndex(0) // Reset to latest image
        break
    }
  } 

  const nextSnapshot = useCallback(() => {
    if (last5Snapshots.length <= 1) return
    setCurrentSnapshotIndex(prev => 
      prev === last5Snapshots.length - 1 ? 0 : prev + 1
    )
  }, [last5Snapshots.length])

  const previousSnapshot = () => {
    if (last5Snapshots.length <= 1) return
    setCurrentSnapshotIndex(prev => 
      prev === 0 ? last5Snapshots.length - 1 : prev - 1
    )
  }

  // Auto-scroll effect
  useEffect(() => {
    if (last5Snapshots.length <= 1 || isCarouselPaused) return

    const intervalId = setInterval(() => {
      nextSnapshot()
    }, 3000) // Change image every 3 seconds

    return () => clearInterval(intervalId)
  }, [last5Snapshots.length, isCarouselPaused, nextSnapshot])

  useEffect(() => {
    if (realTimeUpdate) handleRealTimeUpdate(realTimeUpdate)
  }, [realTimeUpdate])

  return (
    <>
      <div className="title-container">
        <div className="title-content">
          <h1 className="project-title">Project Piper</h1>
          <p className="project-subtitle">Multi-Camera Home Pet Tracking System</p>
        </div>
      </div>

      <div className="detection-container">
        {highConfidenceDetection && last5Snapshots[0] && (
          <div className="high-confidence-log">
            <h2>Currently in the {highConfidenceDetection.camera_id}</h2>
            <div className="timestamp-header">
              {new Date(highConfidenceDetection.timestamp).toLocaleString()} | {(highConfidenceDetection.confidence * 100).toFixed(1)}% Confidence
            </div>
            <div className="current-detection">
              <div className="current-image">
                <img 
                  src={`http://localhost:8000/api/assets/${last5Snapshots[0]}`} 
                  alt="Current Detection" 
                  className="detection-image"
                />
              </div>
            </div>
          </div>
        )}

        {last5Snapshots.length > 0 && (
          <>
            <h2>Recent Detections</h2>
            <div 
              className="carousel"
              onMouseEnter={() => setIsCarouselPaused(true)}
              onMouseLeave={() => setIsCarouselPaused(false)}
            >
              <button 
                className="carousel-button prev" 
                onClick={previousSnapshot}
                disabled={last5Snapshots.length <= 1}
              >
                ←
              </button>
              
              <div className="carousel-container">
                <img 
                  src={`http://localhost:8000/api/assets/${last5Snapshots[currentSnapshotIndex]}`} 
                  alt={`Detection ${currentSnapshotIndex + 1} of ${last5Snapshots.length}`} 
                  className="detection-image"
                />
                <div className="carousel-indicator">
                  {last5Snapshots.map((_, index) => (
                    <button
                      key={index}
                      className={`indicator ${index === currentSnapshotIndex ? 'active' : ''}`}
                      onClick={() => setCurrentSnapshotIndex(index)}
                    />
                  ))}
                </div>
              </div>

              <button 
                className="carousel-button next" 
                onClick={nextSnapshot}
                disabled={last5Snapshots.length <= 1}
              >
                →
              </button>
            </div>
          </>
        )}
        
        <div className="activity-log">
          <h2>Pet Detection Log (Last 10)</h2>
          <div className="log-entries">
            {last10Detections.map(detection => (
              <div key={detection.detection_id} className="log-entry">
                <div className="entry-header">
                  {new Date(detection.timestamp).toLocaleString()} | {detection.camera_id}
                </div>
                <div className="entry-message">
                  {(detection.confidence * 100).toFixed(1)}% confidence {detection.class_name} seen
                </div>
              </div>
            ))}
            {Array.from({ length: Math.max(0, 10 - last10Detections.length) }).map((_, i) => (
              <div key={`empty-${i}`} className="log-entry empty">
                <div className="entry-header">
                  -- | --
                </div>
                <div className="entry-message">
                  Waiting for detection...
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  )
}

export default App
