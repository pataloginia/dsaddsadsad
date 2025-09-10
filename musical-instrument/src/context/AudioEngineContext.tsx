import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { audioEngine, AudioEngine } from "../audio/AudioEngine";
import type { EnvelopeSettings, FilterSettings, ReverbSettings, Waveform } from "../audio/AudioEngine";

interface AudioContextValue {
  engine: AudioEngine;
  // Mirror of engine public state to trigger UI updates on change
  waveform: Waveform;
  envelope: EnvelopeSettings;
  filter: FilterSettings;
  reverb: ReverbSettings;
  masterVolume: number;
  octaveOffset: number;
  setWaveform: (w: Waveform) => void;
  setEnvelope: (p: Partial<EnvelopeSettings>) => void;
  setFilter: (p: Partial<FilterSettings>) => void;
  setReverb: (p: Partial<ReverbSettings>) => void;
  setMasterVolume: (v: number) => void;
  setOctaveOffset: (o: number) => void;
  startAudio: () => Promise<void>;
}

const Ctx = createContext<AudioContextValue | null>(null);

export const AudioEngineProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [waveform, setWaveformState] = useState(audioEngine.state.waveform);
  const [envelope, setEnvelopeState] = useState(audioEngine.state.envelope);
  const [filter, setFilterState] = useState(audioEngine.state.filter);
  const [reverb, setReverbState] = useState(audioEngine.state.reverb);
  const [masterVolume, setMasterVolumeState] = useState(audioEngine.state.masterVolume);
  const [octaveOffset, setOctaveOffsetState] = useState(audioEngine.state.octaveOffset);

  const startAudio = async () => {
    await audioEngine.ensureStarted();
  };

  const value = useMemo<AudioContextValue>(() => ({
    engine: audioEngine,
    waveform,
    envelope,
    filter,
    reverb,
    masterVolume,
    octaveOffset,
    setWaveform: (w) => {
      audioEngine.setWaveform(w);
      setWaveformState(w);
    },
    setEnvelope: (p) => {
      audioEngine.setEnvelope(p);
      setEnvelopeState({ ...audioEngine.state.envelope });
    },
    setFilter: (p) => {
      audioEngine.setFilter(p);
      setFilterState({ ...audioEngine.state.filter });
    },
    setReverb: (p) => {
      audioEngine.setReverb(p);
      setReverbState({ ...audioEngine.state.reverb });
    },
    setMasterVolume: (v) => {
      audioEngine.setMasterVolume(v);
      setMasterVolumeState(v);
    },
    setOctaveOffset: (o) => {
      audioEngine.setOctaveOffset(o);
      setOctaveOffsetState(o);
    },
    startAudio,
  }), [waveform, envelope, filter, reverb, masterVolume, octaveOffset]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      try { audioEngine.allNotesOff(); } catch {}
    };
  }, []);

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
};

export const useAudioEngine = (): AudioContextValue => {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAudioEngine must be used within AudioEngineProvider");
  return ctx;
};

