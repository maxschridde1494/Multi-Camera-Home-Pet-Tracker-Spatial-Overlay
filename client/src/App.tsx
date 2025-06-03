import { useEffect, useState } from 'react'
import './App.css'
import { useRealTime, type RealTimeUpdate, RealTimeMessage } from './hooks/useRealTime'
import type { Detection, Snapshot, WebsocketConnectionInit } from './types'

function App() {
  const [last10Detections, setLast10Detections] = useState<Detection[]>([])
  const [last5Snapshots, setLast5Snapshots] = useState<string[]>([])
  const [currentSnapshotIndex, setCurrentSnapshotIndex] = useState(0)
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

  const nextSnapshot = () => {
    setCurrentSnapshotIndex(prev => 
      prev === last5Snapshots.length - 1 ? 0 : prev + 1
    )
  }

  const previousSnapshot = () => {
    setCurrentSnapshotIndex(prev => 
      prev === 0 ? last5Snapshots.length - 1 : prev - 1
    )
  }

  useEffect(() => {
    if (realTimeUpdate) handleRealTimeUpdate(realTimeUpdate)
  }, [realTimeUpdate])

  return (
    <div className="detection-container">
      <h1>Pet Detection Log</h1>
      
      {highConfidenceDetection && (
        <div className="high-confidence-log">
          <h2>High Confidence Detection</h2>
          <div className="log-entry highlight">
            <div className="entry-header">
              {new Date(highConfidenceDetection.timestamp).toLocaleString()} | Camera {highConfidenceDetection.camera_id}
            </div>
            <div className="entry-message">
              {(highConfidenceDetection.confidence * 100).toFixed(1)}% confidence {highConfidenceDetection.class_name} seen
            </div>
          </div>
        </div>
      )}

      {last5Snapshots.length > 0 && (
        <div className="carousel">
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
      )}
      
      <div className="activity-log">
        <h2>Recent Detections</h2>
        <div className="log-entries">
          {last10Detections.map(detection => (
            <div key={detection.detection_id} className="log-entry">
              <div className="entry-header">
                {new Date(detection.timestamp).toLocaleString()} | Camera {detection.camera_id}
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
  )
}

export default App
