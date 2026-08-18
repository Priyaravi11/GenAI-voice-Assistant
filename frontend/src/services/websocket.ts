const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL ?? "ws://127.0.0.1:8000";

export function createAssistantSocket(sessionId: string) {
  return new WebSocket(`${WS_BASE_URL}/ws/voice/${sessionId}`);
}

export function getWebSocketBaseUrl() {
  return WS_BASE_URL;
}
