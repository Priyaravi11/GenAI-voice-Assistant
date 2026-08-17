/**
 * Audio Player Hook
 * File: frontend/src/hooks/useAudioPlayer.ts
 * 
 * Plays audio responses from Gemini Live:
 * - Decodes base64 audio
 * - Streams to audio context
 * - Provides playback controls
 */

import { useEffect, useRef, useState, useCallback } from "react";

export interface AudioPlayerState {
  isPlaying: boolean;
  isPaused: boolean;
  currentTime: number;
  duration: number;
}

export function useAudioPlayer() {
  const [state, setState] = useState<AudioPlayerState>({
    isPlaying: false,
    isPaused: false,
    currentTime: 0,
    duration: 0,
  });

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const sourceRef = useRef<MediaElementAudioSourceNode | null>(null);

  // Initialize audio element on mount
  useEffect(() => {
    if (!audioRef.current) {
      audioRef.current = new Audio();

      audioRef.current.addEventListener("play", () => {
        setState((prev) => ({
          ...prev,
          isPlaying: true,
          isPaused: false,
        }));
      });

      audioRef.current.addEventListener("pause", () => {
        setState((prev) => ({
          ...prev,
          isPlaying: false,
          isPaused: true,
        }));
      });

      audioRef.current.addEventListener("ended", () => {
        setState((prev) => ({
          ...prev,
          isPlaying: false,
          isPaused: false,
          currentTime: 0,
        }));
      });

      audioRef.current.addEventListener("timeupdate", () => {
        if (audioRef.current) {
          setState((prev) => ({
            ...prev,
            currentTime: audioRef.current?.currentTime || 0,
          }));
        }
      });

      audioRef.current.addEventListener("loadedmetadata", () => {
        if (audioRef.current) {
          setState((prev) => ({
            ...prev,
            duration: audioRef.current?.duration || 0,
          }));
        }
      });
    }

    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
      }
    };
  }, []);

  // Play audio from base64 data
  const playAudioData = useCallback((base64Data: string, mimeType = "audio/wav") => {
    try {
      if (!audioRef.current) return;

      // Decode base64
      const binaryString = atob(base64Data);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      const blob = new Blob([bytes], { type: mimeType });

      // Create blob URL
      const url = URL.createObjectURL(blob);
      audioRef.current.src = url;
      audioRef.current.play();

      // Cleanup on end
      const cleanup = () => {
        URL.revokeObjectURL(url);
      };
      audioRef.current.addEventListener("ended", cleanup, { once: true });
    } catch (error) {
      console.error("Failed to play audio:", error);
    }
  }, []);

  // Queue audio chunks for continuous playback
  const queueAudioChunk = useCallback(
    (base64Data: string, mimeType = "audio/wav") => {
      playAudioData(base64Data, mimeType);
    },
    [playAudioData]
  );

  // Control methods
  const play = useCallback(() => {
    audioRef.current?.play();
  }, []);

  const pause = useCallback(() => {
    audioRef.current?.pause();
  }, []);

  const stop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
  }, []);

  const seek = useCallback((time: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = time;
    }
  }, []);

  const setVolume = useCallback((volume: number) => {
    if (audioRef.current) {
      audioRef.current.volume = Math.max(0, Math.min(1, volume));
    }
  }, []);

  return {
    ...state,
    play,
    pause,
    stop,
    seek,
    setVolume,
    playAudioData,
    queueAudioChunk,
    audioElement: audioRef.current,
  };
}
