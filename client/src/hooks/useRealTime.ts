import { useEffect, useState } from "react";

export function useRealTime(uri: string) {
  const [realTimeUpdate, setRealTimeUpdate] = useState<string | null>(null);

  useEffect(() => {
    const ws  = new WebSocket(uri);
    ws.onmessage = (ev) => {
      setRealTimeUpdate(JSON.parse(ev.data));
    }
    return () => ws.close();
  }, []);

  return realTimeUpdate;
}