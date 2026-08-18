/**
 * Audio Recorder Hook
 * File: frontend/src/hooks/useAudioRecorder.ts
 * 
 * Captures audio from user's microphone and provides:
 * - Real-time audio recording
 * - Audio chunk streaming
 * - Recording state management
 * - Audio processing and encoding
 */

import { useEffect, useRef, useState, useCallback } from "react";

export interface AudioRecorderState {
  isRecording: boolean;
  isPaused: boolean;
  recordedChunks: Blob[];
  audioLevel: number;
}

export interface UseAudioRecorderOptions {
  onAudioChunk?: (chunk: ArrayBuffer) => void;
  onError?: (error: Error) => void;
  mimeType?: string;
  sampleRate?: number;
}

export function useAudioRecorder(options: UseAudioRecorderOptions = {}) {
  const {
    onAudioChunk,
    onError,
    mimeType = "audio/wav",
    sampleRate = 16000,
  } = options;

  const [state, setState] = useState<AudioRecorderState>({
    isRecording: false,
    isPaused: false,
    recordedChunks: [],
    audioLevel: 0,
  });

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyzerRef = useRef<AnalyserNode | null>(null);
  const volumeCheckIntervalRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Request microphone access
  const startRecording = useCallback(async () => {
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("Your browser does not support audio recording");
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: sampleRate,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      streamRef.current = stream;

      // Create audio context for volume monitoring
      const audioContext = new (window.AudioContext ||
        (window as any).webkitAudioContext)();
      audioContextRef.current = audioContext;

      const analyzer = audioContext.createAnalyser();
      analyzer.fftSize = 256;
      const source = audioContext.createMediaStreamSource(stream);
      source.connect(analyzer);
      analyzerRef.current = analyzer;

      // Create media recorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: mimeType,
      });

      mediaRecorderRef.current = mediaRecorder;

      const chunks: Blob[] = [];

      mediaRecorder.ondataavailable = (event: BlobEvent) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
          
          // Convert to ArrayBuffer for streaming
          const reader = new FileReader();
          reader.onload = (e) => {
            const arrayBuffer = e.target?.result as ArrayBuffer;
            if (onAudioChunk && arrayBuffer.byteLength > 0) {
              onAudioChunk(arrayBuffer);
            }
          };
          reader.readAsArrayBuffer(event.data);
        }
      };

      mediaRecorder.start(100); // Emit data every 100ms for streaming

      setState((prev) => ({
        ...prev,
        isRecording: true,
        isPaused: false,
        recordedChunks: chunks,
      }));

      // Monitor audio volume
      const monitorVolume = () => {
        const dataArray = new Uint8Array(analyzer.frequencyBinCount);
        analyzer.getByteFrequencyData(dataArray);
        const average =
          dataArray.reduce((a, b) => a + b) / dataArray.length;
        const level = (average / 255) * 100;

        setState((prev) => ({
          ...prev,
          audioLevel: level,
        }));
      };

      volumeCheckIntervalRef.current = setInterval(monitorVolume, 50);
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      if (onError) onError(err);
      console.error("Failed to start recording:", err);
    }
  }, [mimeType, sampleRate, onAudioChunk, onError]);

  // Stop recording
  const stopRecording = useCallback(async () => {
    if (mediaRecorderRef.current && state.isRecording) {
      mediaRecorderRef.current.stop();

      // Clean up
      if (volumeCheckIntervalRef.current) {
        clearInterval(volumeCheckIntervalRef.current);
      }

      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }

      if (audioContextRef.current) {
        audioContextRef.current.close();
      }

      setState((prev) => ({
        ...prev,
        isRecording: false,
        isPaused: false,
        audioLevel: 0,
      }));
    }
  }, [state.isRecording]);

  // Pause recording
  const pauseRecording = useCallback(() => {
    if (mediaRecorderRef.current && state.isRecording) {
      mediaRecorderRef.current.pause();
      setState((prev) => ({
        ...prev,
        isPaused: true,
      }));
    }
  }, [state.isRecording]);

  // Resume recording
  const resumeRecording = useCallback(() => {
    if (mediaRecorderRef.current && state.isPaused) {
      mediaRecorderRef.current.resume();
      setState((prev) => ({
        ...prev,
        isPaused: false,
      }));
    }
  }, [state.isPaused]);

  // Get recorded audio as blob
  const getRecordedAudio = useCallback(() => {
    if (state.recordedChunks.length === 0) return null;

    return new Blob(state.recordedChunks, { type: mimeType });
  }, [state.recordedChunks, mimeType]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (state.isRecording) {
        stopRecording();
      }
    };
  }, [state.isRecording, stopRecording]);

  return {
    ...state,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    getRecordedAudio,
  };
}
