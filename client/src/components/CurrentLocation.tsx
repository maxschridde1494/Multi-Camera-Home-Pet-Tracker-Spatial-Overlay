import type { Detection } from '../types'

interface CurrentLocationProps {
  detection?: Detection
  snapshotPath?: string
}

export const CurrentLocation = ({ detection, snapshotPath }: CurrentLocationProps) => {
  if (!detection) return null
  
  return (
    <div className="high-confidence-log">
      <h2>Currently in the {detection.camera_id}</h2>
      <div className="timestamp-header">
        {new Date(detection.timestamp).toLocaleString()} | {(detection.confidence * 100).toFixed(1)}% Confidence
      </div>
      {snapshotPath && (
        <div className="current-detection">
          <div className="current-image">
            <img 
              src={`http://localhost:8000/api/assets/${snapshotPath}`} 
              alt="Current Detection" 
              className="detection-image"
            />
          </div>
        </div>
      )}
    </div>
  )
} 