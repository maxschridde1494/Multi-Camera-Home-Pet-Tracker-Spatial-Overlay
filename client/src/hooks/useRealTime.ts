import { useEffect, useState } from "react";
import type { Detection, Snapshot } from '../types'

export enum RealTimeMessage {
  DetectionMade = 'detection_made',
  HighConfidenceDetectionMade = 'high_confidence_detection_made',
  SnapshotMade = 'snapshot_made',
}

export interface RealTimeUpdate {
  timestamp: string;
  status: string;
  message: RealTimeMessage;
  data?: Detection | Snapshot;
}

export function useRealTime(uri: string) {
  const [realTimeUpdate, setRealTimeUpdate] = useState<RealTimeUpdate | null>(null);

  useEffect(() => {
    const ws  = new WebSocket(uri);
    ws.onmessage = (ev) => {
      setRealTimeUpdate(JSON.parse(ev.data));
    }
    return () => ws.close();
  }, []);

  return realTimeUpdate;
}