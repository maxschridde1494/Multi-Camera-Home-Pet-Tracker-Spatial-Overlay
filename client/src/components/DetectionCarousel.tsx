import { useState, useCallback, useEffect } from 'react'

interface DetectionCarouselProps {
  snapshots: string[]
}

export const DetectionCarousel = ({ snapshots }: DetectionCarouselProps) => {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isPaused, setIsPaused] = useState(false)

  // Reset to first image when new snapshots arrive
  useEffect(() => {
    setCurrentIndex(0)
  }, [snapshots])

  const nextSnapshot = useCallback(() => {
    if (snapshots.length <= 1) return
    setCurrentIndex(prev => 
      prev === snapshots.length - 1 ? 0 : prev + 1
    )
  }, [snapshots.length])

  const previousSnapshot = () => {
    if (snapshots.length <= 1) return
    setCurrentIndex(prev => 
      prev === 0 ? snapshots.length - 1 : prev - 1
    )
  }

  // Auto-scroll effect
  useEffect(() => {
    if (snapshots.length <= 1 || isPaused) return

    const intervalId = setInterval(() => {
      nextSnapshot()
    }, 3000) // Change image every 3 seconds

    return () => clearInterval(intervalId)
  }, [snapshots.length, isPaused, nextSnapshot])

  if (snapshots.length === 0) return null

  return (
    <>
      <h2>Recent Detections</h2>
      <div 
        className="carousel"
        onMouseEnter={() => setIsPaused(true)}
        onMouseLeave={() => setIsPaused(false)}
      >
        <button 
          className="carousel-button prev" 
          onClick={previousSnapshot}
          disabled={snapshots.length <= 1}
        >
          ←
        </button>
        
        <div className="carousel-container">
          <img 
            src={`http://localhost:8000/api/assets/${snapshots[currentIndex]}`} 
            alt={`Detection ${currentIndex + 1} of ${snapshots.length}`} 
            className="detection-image"
          />
          <div className="carousel-indicator">
            {snapshots.map((_, index) => (
              <button
                key={index}
                className={`indicator ${index === currentIndex ? 'active' : ''}`}
                onClick={() => setCurrentIndex(index)}
              />
            ))}
          </div>
        </div>

        <button 
          className="carousel-button next" 
          onClick={nextSnapshot}
          disabled={snapshots.length <= 1}
        >
          →
        </button>
      </div>
    </>
  )
} 