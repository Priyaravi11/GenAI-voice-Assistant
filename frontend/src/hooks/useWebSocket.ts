import { useEffect, useRef, useState } from "react";
import { createAssistantSocket } from "../services/websocket";

export function useWebSocket(sessionId: string) {
  const socketRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<string | null>(null);

  useEffect(() => {
    const socket = createAssistantSocket(sessionId);
    socketRef.current = socket;

    socket.addEventListener("open", () => setConnected(true));
    socket.addEventListener("close", () => setConnected(false));
    socket.addEventListener("message", (event) => setLastMessage(String(event.data)));

    return () => socket.close();
  }, [sessionId]);

  function send(message: unknown) {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(message));
    }
  }

  return { connected, lastMessage, send };
}
