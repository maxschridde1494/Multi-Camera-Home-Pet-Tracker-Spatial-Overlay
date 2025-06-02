import { useEffect, useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import { simpleFetch } from './clients/fetch'
import { useRealTime } from './hooks/useRealTime'

interface Detection {
  id: number;
  detection_id: string;  // UUID
  timestamp: string;     // datetime
  model_id: string;
  camera_id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  confidence: number;
  class_name: string;
  class_id: number;
}

function App() {
  const [count, setCount] = useState(0)
  const [detections, setDetections] = useState<Detection[]>([])
  const realTimeUpdate = useRealTime('/ws')

  useEffect(() => {
    const fetchDetections = () => {
      simpleFetch({
        url: '/api/detections',
        onSuccess: (data) => {
          setDetections(data)
        },
        onError: (error) => {
          console.error('Error fetching detections:', error)
        }
      })
    }

    fetchDetections()

    const intervalId = setInterval(fetchDetections, 5000)

    return () => clearInterval(intervalId)
  }, []) 

  useEffect(() => {
    console.log(detections)
  }, [detections])

  useEffect(() => {
    console.log({realTimeUpdate})
  }, [realTimeUpdate])

  return (
    <>
      <div>
        <a href="https://vite.dev" target="_blank">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>Vite + React</h1>
      <div className="card">
        <button onClick={() => setCount((count) => count + 1)}>
          count is {count}
        </button>
        <p>
          Edit <code>src/App.tsx</code> and save to test HMR
        </p>
      </div>
      <p className="read-the-docs">
        Click on the Vite and React logos to learn more
      </p>
    </>
  )
}

export default App
