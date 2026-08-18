/**
 * Enhanced WebSocket Hook for Audio
 * File: frontend/src/hooks/useAudioWebSocket.ts
 * 
 * Manages WebSocket connection for real-time audio streaming
 */

import { useEffect, useRef, useState, useCallback } from "react";
import { createAssistantSocket } from "../services/websocket";

export interface AudioWebSocketState {
  connected: boolean;
  audioReady: boolean;
  error: string | null;
  lastTranscript: string | null;
  status: string | null;
}

export interface AudioWebSocketHandlers {
  onAudioResponse?: (data: string, mimeType: string) => void;
  onTranscript?: (text: string) => void;
  onAssistantResponse?: (message: Record<string, any>) => void;
  onError?: (error: string) => void;
  onEscalation?: (message: Record<string, any>) => void;
  onStatus?: (message: Record<string, any>) => void;
  onReady?: () => void;
  onStreamClosed?: () => void;
}

export function useAudioWebSocket(
  sessionId: string,
  handlers: AudioWebSocketHandlers = {}
) {
  const [state, setState] = useState<AudioWebSocketState>({
    connected: false,
    audioReady: false,
    error: null,
    lastTranscript: null,
    status: null,
  });

  const socketRef = useRef<WebSocket | null>(null);
  const handlersRef = useRef(handlers);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    handlersRef.current = handlers;
  }, [handlers]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    try {
      const socket = createAssistantSocket(sessionId);
      socketRef.current = socket;

      socket.addEventListener("open", () => {
        setState((prev) => ({
          ...prev,
          connected: true,
          error: null,
        }));
      });

      socket.addEventListener("message", (event) => {
        try {
          const data = JSON.parse(event.data);
          handleMessage(data);
        } catch (error) {
          console.error("Failed to parse WebSocket message:", error);
        }
      });

      socket.addEventListener("error", (event) => {
        console.error("WebSocket error:", event);
        setState((prev) => ({
          ...prev,
          error: "Connection error",
        }));
      });

      socket.addEventListener("close", () => {
        setState((prev) => ({
          ...prev,
          connected: false,
          audioReady: false,
        }));

        if (socketRef.current === socket) {
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, 3000);
        }
      });
    } catch (error) {
      setState((prev) => ({
        ...prev,
        error: String(error),
      }));
    }
  }, [sessionId]);

  // Handle incoming messages
  const handleMessage = useCallback(
    (data: Record<string, any>) => {
      const messageType = data.type;

      switch (messageType) {
        case "audio_stream_ready":
          setState((prev) => ({
            ...prev,
            audioReady: true,
          }));
          handlersRef.current.onReady?.();
          break;

        case "audio_response":
          handlersRef.current.onAudioResponse?.(
            data.data,
            data.mime_type || "audio/wav"
          );
          break;

        case "audio_transcript":
        case "transcript":
          setState((prev) => ({
            ...prev,
            lastTranscript: data.content,
          }));
          handlersRef.current.onTranscript?.(data.content);
          break;

        case "assistant_response":
          handlersRef.current.onAssistantResponse?.(data);
          break;

        case "escalation_notice":
          handlersRef.current.onEscalation?.(data);
          break;

        case "status":
          setState((prev) => ({
            ...prev,
            status: data.status || data.message || null,
          }));
          handlersRef.current.onStatus?.(data);
          break;

        case "audio_stream_closed":
          handlersRef.current.onStreamClosed?.();
          break;

        case "error":
          setState((prev) => ({
            ...prev,
            error: data.error,
          }));
          handlersRef.current.onError?.(data.error);
          break;

        default:
          break;
      }
    },
    []
  );

  // Send audio chunk
  const sendAudioChunk = useCallback(
    (arrayBuffer: ArrayBuffer, mimeType = "audio/wav") => {
      if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
        console.error("WebSocket not connected");
        return;
      }

      // Convert ArrayBuffer to base64
      const bytes = new Uint8Array(arrayBuffer);
      let binary = "";
      for (let i = 0; i < bytes.length; i++) {
        binary += String.fromCharCode(bytes[i]);
      }
      const base64 = btoa(binary);

      socketRef.current.send(
        JSON.stringify({
          type: "audio_chunk",
          session_id: sessionId,
          data: base64,
          mime_type: mimeType,
        })
      );
    },
    [sessionId]
  );

  // Start audio stream
  const startAudioStream = useCallback(
    (language = "en", customerId?: string) => {
      if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
        console.error("WebSocket not connected");
        return;
      }

      socketRef.current.send(
        JSON.stringify({
          type: "audio_start",
          session_id: sessionId,
          language: language,
          customer_id: customerId,
        })
      );
    },
    [sessionId]
  );

  // End audio stream
  const endAudioStream = useCallback(() => {
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      console.error("WebSocket not connected");
      return;
    }

    socketRef.current.send(
      JSON.stringify({
        type: "audio_end",
        session_id: sessionId,
      })
    );
  }, [sessionId]);

  const startCall = useCallback(
    (language = "en", customerId?: string) => {
      if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
        console.error("WebSocket not connected");
        return;
      }

      socketRef.current.send(
        JSON.stringify({
          type: "start_call",
          session_id: sessionId,
          language,
          customer_id: customerId,
        })
      );
    },
    [sessionId]
  );

  const sendUserMessage = useCallback(
    (content: string, language = "en", customerId?: string) => {
      if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
        console.error("WebSocket not connected");
        return;
      }

      socketRef.current.send(
        JSON.stringify({
          type: "user_message",
          session_id: sessionId,
          content,
          language,
          customer_id: customerId,
        })
      );
    },
    [sessionId]
  );

  // Disconnect
  const disconnect = useCallback(() => {
    if (socketRef.current) {
      const socket = socketRef.current;
      socketRef.current = null;
      socket.close();
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    ...state,
    connect,
    disconnect,
    sendAudioChunk,
    startAudioStream,
    endAudioStream,
    startCall,
    sendUserMessage,
  };
}
