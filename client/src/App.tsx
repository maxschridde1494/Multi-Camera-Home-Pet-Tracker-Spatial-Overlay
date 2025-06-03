import { useRealTime } from './hooks/useRealTime'
import { ProjectTitle } from './components/ProjectTitle'
import { CurrentLocation } from './components/CurrentLocation'
import { DetectionCarousel } from './components/DetectionCarousel'
import { DetectionLog } from './components/DetectionLog'
import './App.css'

function App() {
  const { 
    last10Detections, 
    last5Snapshots, 
    highConfidenceDetection,
    isLoading 
  } = useRealTime('ws://localhost:8000/ws')

  return (
    <>
      <ProjectTitle />
      <div className="detection-container">
        {isLoading ? (
          <div className="loading">Connecting to pet detection system...</div>
        ): (
          <>
            <CurrentLocation 
              detection={highConfidenceDetection}
              snapshotPath={last5Snapshots?.[0]}
            />
            <DetectionCarousel snapshots={last5Snapshots} />
            <DetectionLog detections={last10Detections} />
          </>
        )}
      </div>
    </>
  )
}

export default App
