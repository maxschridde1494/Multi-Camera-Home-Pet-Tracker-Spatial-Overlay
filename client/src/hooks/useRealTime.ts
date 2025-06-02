import { useEffect, useState } from "react";

export function useRealTime(path: string) {
  const [realTimeUpdate, setRealTimeUpdate] = useState<string | null>(null);

  useEffect(() => {
    const loc = window.location.origin.replace(/^http/, "ws");
    const ws  = new WebSocket(`${loc}/api${path}`);
    ws.onmessage = (ev) => {
      setRealTimeUpdate(JSON.parse(ev.data));
    }
    return () => ws.close();
  }, []);

  return realTimeUpdate;
}