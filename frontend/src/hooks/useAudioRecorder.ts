/**
 * Audio Recorder Hook
 * File: frontend/src/hooks/useAudioRecorder.ts
 *
 * Captures microphone audio as a browser-supported recording blob.
 */

import { useEffect, useRef, useState, useCallback } from "react";

export interface AudioRecorderState {
  isRecording: boolean;
  isPaused: boolean;
  recordedChunks: Blob[];
  audioLevel: number;
  mimeType: string;
}

export interface UseAudioRecorderOptions {
  onRecordingComplete?: (audio: Blob, mimeType: string) => void;
  onError?: (error: Error) => void;
}

const DEFAULT_MIME_TYPE = "audio/webm";

function getSupportedMimeType() {
  const candidates = [
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/mp4",
    "audio/ogg;codecs=opus",
  ];

  return candidates.find((type) => MediaRecorder.isTypeSupported(type)) || "";
}

export function useAudioRecorder(options: UseAudioRecorderOptions = {}) {
  const { onRecordingComplete, onError } = options;

  const [state, setState] = useState<AudioRecorderState>({
    isRecording: false,
    isPaused: false,
    recordedChunks: [],
    audioLevel: 0,
    mimeType: DEFAULT_MIME_TYPE,
  });

  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationRef = useRef<number | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const isPausedRef = useRef(false);
  const isRecordingRef = useRef(false);

  const cleanup = useCallback(() => {
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }

    analyserRef.current?.disconnect();
    streamRef.current?.getTracks().forEach((track) => track.stop());
    audioContextRef.current?.close();

    recorderRef.current = null;
    analyserRef.current = null;
    animationRef.current = null;
    streamRef.current = null;
    audioContextRef.current = null;
    isRecordingRef.current = false;
    isPausedRef.current = false;
  }, []);

  const startRecording = useCallback(async () => {
    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error("Your browser does not support microphone capture.");
      }

      if (isRecordingRef.current) return;

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      const mimeType = getSupportedMimeType();
      const recorder = new MediaRecorder(
        stream,
        mimeType ? { mimeType } : undefined
      );
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      const audioContext = new AudioContextClass();
      await audioContext.resume();

      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 1024;
      source.connect(analyser);

      const samples = new Uint8Array(analyser.fftSize);
      const updateLevel = () => {
        if (!isRecordingRef.current) return;
        analyser.getByteTimeDomainData(samples);
        let sum = 0;
        for (let i = 0; i < samples.length; i += 1) {
          const centered = (samples[i] - 128) / 128;
          sum += centered * centered;
        }
        const level = isPausedRef.current ? 0 : Math.min(100, Math.sqrt(sum / samples.length) * 180);

        setState((prev) => ({
          ...prev,
          audioLevel: level,
        }));

        animationRef.current = requestAnimationFrame(updateLevel);
      };

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        const finalMimeType = recorder.mimeType || mimeType || DEFAULT_MIME_TYPE;
        const audio = new Blob(chunksRef.current, { type: finalMimeType });
        setState((prev) => ({
          ...prev,
          recordedChunks: chunksRef.current,
          mimeType: finalMimeType,
        }));
        chunksRef.current = [];
        if (audio.size > 0) {
          onRecordingComplete?.(audio, finalMimeType);
        }
      };

      streamRef.current = stream;
      recorderRef.current = recorder;
      audioContextRef.current = audioContext;
      analyserRef.current = analyser;
      chunksRef.current = [];
      isRecordingRef.current = true;
      isPausedRef.current = false;
      recorder.start();
      updateLevel();

      setState((prev) => ({
        ...prev,
        isRecording: true,
        isPaused: false,
        recordedChunks: [],
        audioLevel: 0,
        mimeType: recorder.mimeType || mimeType || DEFAULT_MIME_TYPE,
      }));
    } catch (error) {
      cleanup();
      const err = error instanceof Error ? error : new Error(String(error));
      onError?.(err);
    }
  }, [cleanup, onError, onRecordingComplete]);

  const stopRecording = useCallback(async () => {
    if (recorderRef.current && recorderRef.current.state !== "inactive") {
      recorderRef.current.stop();
    }
    cleanup();
    setState((prev) => ({
      ...prev,
      isRecording: false,
      isPaused: false,
      audioLevel: 0,
    }));
  }, [cleanup]);

  const pauseRecording = useCallback(() => {
    if (!isRecordingRef.current) return;
    if (recorderRef.current?.state === "recording") {
      recorderRef.current.pause();
    }
    isPausedRef.current = true;
    setState((prev) => ({
      ...prev,
      isPaused: true,
      audioLevel: 0,
    }));
  }, []);

  const resumeRecording = useCallback(() => {
    if (!isRecordingRef.current) return;
    if (recorderRef.current?.state === "paused") {
      recorderRef.current.resume();
    }
    isPausedRef.current = false;
    setState((prev) => ({
      ...prev,
      isPaused: false,
    }));
  }, []);

  const getRecordedAudio = useCallback(() => {
    if (!chunksRef.current.length) return null;
    return new Blob(chunksRef.current, { type: state.mimeType });
  }, [state.mimeType]);

  useEffect(() => {
    return () => {
      void stopRecording();
    };
  }, [stopRecording]);

  return {
    ...state,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    getRecordedAudio,
  };
}
