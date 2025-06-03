import type { Detection } from '../types'
import { formatLocalTime } from '../utils/dateUtils'

interface DetectionLogProps {
  detections: Detection[]
}

export const DetectionLog = ({ detections }: DetectionLogProps) => {
  return (
    <div className="activity-log">
      <h2>Pet Detection Log (Last 10)</h2>
      <div className="log-entries">
        {detections.map(detection => (
          <div key={detection.detection_id} className="log-entry">
            <div className="entry-header">
              {formatLocalTime(detection.timestamp)} | {detection.camera_id}
            </div>
            <div className="entry-message">
              {(detection.confidence * 100).toFixed(1)}% confidence {detection.class_name} seen
            </div>
          </div>
        ))}
        {Array.from({ length: Math.max(0, 10 - detections.length) }).map((_, i) => (
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
  )
} 