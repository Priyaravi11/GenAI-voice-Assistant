/**
 * Audio Recorder Hook
 * File: frontend/src/hooks/useAudioRecorder.ts
 *
 * Captures microphone audio as 16 kHz mono PCM for Gemini Live.
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
  onAudioChunk?: (chunk: ArrayBuffer, mimeType: string) => void;
  onError?: (error: Error) => void;
  sampleRate?: number;
}

const PCM_MIME_TYPE = "audio/pcm;rate=16000";

function downsampleBuffer(buffer: Float32Array, inputSampleRate: number, outputSampleRate: number) {
  if (outputSampleRate === inputSampleRate) return buffer;
  if (outputSampleRate > inputSampleRate) {
    throw new Error("Output sample rate must be lower than input sample rate");
  }

  const ratio = inputSampleRate / outputSampleRate;
  const newLength = Math.round(buffer.length / ratio);
  const result = new Float32Array(newLength);

  let offsetResult = 0;
  let offsetBuffer = 0;

  while (offsetResult < result.length) {
    const nextOffsetBuffer = Math.round((offsetResult + 1) * ratio);
    let accumulator = 0;
    let count = 0;

    for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i += 1) {
      accumulator += buffer[i];
      count += 1;
    }

    result[offsetResult] = accumulator / Math.max(count, 1);
    offsetResult += 1;
    offsetBuffer = nextOffsetBuffer;
  }

  return result;
}

function floatTo16BitPcm(buffer: Float32Array) {
  const output = new ArrayBuffer(buffer.length * 2);
  const view = new DataView(output);

  for (let i = 0; i < buffer.length; i += 1) {
    const sample = Math.max(-1, Math.min(1, buffer[i]));
    view.setInt16(i * 2, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true);
  }

  return output;
}

export function useAudioRecorder(options: UseAudioRecorderOptions = {}) {
  const { onAudioChunk, onError, sampleRate = 16000 } = options;

  const [state, setState] = useState<AudioRecorderState>({
    isRecording: false,
    isPaused: false,
    recordedChunks: [],
    audioLevel: 0,
    mimeType: PCM_MIME_TYPE,
  });

  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const isPausedRef = useRef(false);
  const isRecordingRef = useRef(false);

  const cleanup = useCallback(() => {
    processorRef.current?.disconnect();
    sourceRef.current?.disconnect();
    streamRef.current?.getTracks().forEach((track) => track.stop());
    audioContextRef.current?.close();

    processorRef.current = null;
    sourceRef.current = null;
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

      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      const audioContext = new AudioContextClass();
      await audioContext.resume();

      const source = audioContext.createMediaStreamSource(stream);
      const processor = audioContext.createScriptProcessor(4096, 1, 1);

      processor.onaudioprocess = (event) => {
        if (!isRecordingRef.current || isPausedRef.current) return;

        const input = event.inputBuffer.getChannelData(0);
        const downsampled = downsampleBuffer(input, audioContext.sampleRate, sampleRate);
        const pcm = floatTo16BitPcm(downsampled);

        let sum = 0;
        for (let i = 0; i < input.length; i += 1) {
          sum += input[i] * input[i];
        }
        const level = Math.min(100, Math.sqrt(sum / input.length) * 180);

        setState((prev) => ({
          ...prev,
          audioLevel: level,
        }));

        if (pcm.byteLength > 0) {
          onAudioChunk?.(pcm, PCM_MIME_TYPE);
        }
      };

      source.connect(processor);
      processor.connect(audioContext.destination);

      streamRef.current = stream;
      audioContextRef.current = audioContext;
      sourceRef.current = source;
      processorRef.current = processor;
      isRecordingRef.current = true;
      isPausedRef.current = false;

      setState((prev) => ({
        ...prev,
        isRecording: true,
        isPaused: false,
        recordedChunks: [],
        audioLevel: 0,
      }));
    } catch (error) {
      cleanup();
      const err = error instanceof Error ? error : new Error(String(error));
      onError?.(err);
    }
  }, [cleanup, onAudioChunk, onError, sampleRate]);

  const stopRecording = useCallback(async () => {
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
    isPausedRef.current = true;
    setState((prev) => ({
      ...prev,
      isPaused: true,
      audioLevel: 0,
    }));
  }, []);

  const resumeRecording = useCallback(() => {
    if (!isRecordingRef.current) return;
    isPausedRef.current = false;
    setState((prev) => ({
      ...prev,
      isPaused: false,
    }));
  }, []);

  const getRecordedAudio = useCallback(() => null, []);

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
