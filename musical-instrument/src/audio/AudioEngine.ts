/*
  AudioEngine
  High-level Web Audio polyphonic synthesizer with:
  - Multiple waveforms (sine, square, sawtooth, triangle)
  - ADSR envelope per voice
  - Master low-pass filter (cutoff/Q)
  - Simple convolution reverb with procedurally generated impulse
  - Dynamics compressor
  - Master gain and analyser for visualization

  The engine is designed for real-time interaction from UI components.
  All time scheduling uses AudioContext.currentTime for click/pop-free changes.
*/

export type Waveform = "sine" | "square" | "sawtooth" | "triangle";

export interface EnvelopeSettings {
  attackSeconds: number; // Time to reach 100% from 0
  decaySeconds: number;  // Time to decay from 100% to sustain level
  sustainLevel: number;  // 0..1 level while key is held
  releaseSeconds: number;// Time to go from sustain to 0 after key up
}

export interface FilterSettings {
  cutoffHz: number;  // 50..20000
  resonanceQ: number;// 0.0001..40
}

export interface ReverbSettings {
  wet: number;       // 0..1
  seconds: number;   // length of generated impulse response
  decay: number;     // exponential decay factor
}

export interface AudioEngineState {
  waveform: Waveform;
  envelope: EnvelopeSettings;
  filter: FilterSettings;
  reverb: ReverbSettings;
  masterVolume: number; // 0..1
  octaveOffset: number; // integer octave shift
}

interface Voice {
  oscillator: OscillatorNode;
  gain: GainNode;
  noteName: string;
}

export class AudioEngine {
  private audioContext: AudioContext | null = null;
  private masterGain!: GainNode;
  private analyser!: AnalyserNode;
  private filter!: BiquadFilterNode;
  private reverb!: ConvolverNode;
  private reverbGain!: GainNode;
  private compressor!: DynamicsCompressorNode;
  private voices: Map<string, Voice> = new Map(); // key: noteName

  public state: AudioEngineState = {
    waveform: "sine",
    envelope: {
      attackSeconds: 0.01,
      decaySeconds: 0.2,
      sustainLevel: 0.7,
      releaseSeconds: 0.3,
    },
    filter: {
      cutoffHz: 16000,
      resonanceQ: 0.0001,
    },
    reverb: {
      wet: 0.15,
      seconds: 2.2,
      decay: 2.0,
    },
    masterVolume: 0.7,
    octaveOffset: 0,
  };

  // Lazily create the audio graph on first user interaction due to browser policies
  public ensureStarted = async (): Promise<void> => {
    if (this.audioContext) {
      if (this.audioContext.state === "suspended") {
        await this.audioContext.resume();
      }
      return;
    }

    const ctx = new (window.AudioContext || (window as any).webkitAudioContext)();
    this.audioContext = ctx;

    // Core nodes
    this.masterGain = ctx.createGain();
    this.masterGain.gain.value = this.state.masterVolume;

    this.filter = ctx.createBiquadFilter();
    this.filter.type = "lowpass";
    this.filter.frequency.value = this.state.filter.cutoffHz;
    this.filter.Q.value = this.state.filter.resonanceQ;

    this.reverb = ctx.createConvolver();
    this.reverb.buffer = this.createImpulseResponse(ctx, this.state.reverb.seconds, this.state.reverb.decay);

    this.reverbGain = ctx.createGain();
    this.reverbGain.gain.value = this.state.reverb.wet;

    this.compressor = ctx.createDynamicsCompressor();
    this.compressor.threshold.value = -18;
    this.compressor.knee.value = 30;
    this.compressor.ratio.value = 6;
    this.compressor.attack.value = 0.003;
    this.compressor.release.value = 0.25;

    this.analyser = ctx.createAnalyser();
    this.analyser.fftSize = 2048;

    // Routing: voices -> filter -> [split dry/reverb] -> compressor -> analyser -> destination
    const dryGain = ctx.createGain();
    dryGain.gain.value = 1 - this.state.reverb.wet;

    this.filter.connect(dryGain);
    this.filter.connect(this.reverb);

    dryGain.connect(this.compressor);
    this.reverb.connect(this.reverbGain);
    this.reverbGain.connect(this.compressor);

    this.compressor.connect(this.masterGain);
    this.masterGain.connect(this.analyser);
    this.analyser.connect(ctx.destination);
  };

  // Public nodes for visualization
  public getAnalyser = (): AnalyserNode | null => this.analyser ?? null;

  // Voice handling
  public noteOn = async (noteName: string, velocity: number = 1): Promise<void> => {
    await this.ensureStarted();
    if (!this.audioContext) return;
    const ctx = this.audioContext;
    const now = ctx.currentTime;

    // If voice already exists, restart its envelope to avoid duplicates
    if (this.voices.has(noteName)) {
      this.noteOff(noteName);
    }

    const oscillator = ctx.createOscillator();
    oscillator.type = this.state.waveform;
    oscillator.frequency.value = this.noteToFrequency(noteName, this.state.octaveOffset);

    const voiceGain = ctx.createGain();
    voiceGain.gain.cancelScheduledValues(now);
    voiceGain.gain.setValueAtTime(0.0001, now);

    // Connect voice into filter input
    oscillator.connect(voiceGain);
    voiceGain.connect(this.filter);

    oscillator.start(now);

    // ADSR envelope
    const env = this.state.envelope;
    const peak = Math.max(0.0001, Math.min(1, velocity));
    const sustain = Math.max(0.0001, Math.min(1, env.sustainLevel)) * peak;

    // Attack: ramp up quickly for responsiveness
    voiceGain.gain.exponentialRampToValueAtTime(peak, now + Math.max(0.001, env.attackSeconds));
    // Decay: down to sustain
    voiceGain.gain.exponentialRampToValueAtTime(Math.max(0.0001, sustain), now + Math.max(0.001, env.attackSeconds + env.decaySeconds));

    this.voices.set(noteName, { oscillator, gain: voiceGain, noteName });
  };

  public noteOff = (noteName: string): void => {
    if (!this.audioContext) return;
    const ctx = this.audioContext;
    const now = ctx.currentTime;
    const voice = this.voices.get(noteName);
    if (!voice) return;

    const env = this.state.envelope;
    voice.gain.gain.cancelScheduledValues(now);
    const current = Math.max(voice.gain.gain.value, 0.0001);
    voice.gain.gain.setValueAtTime(current, now);
    voice.gain.gain.exponentialRampToValueAtTime(0.0001, now + Math.max(0.001, env.releaseSeconds));

    // Stop oscillator slightly after release to ensure the envelope reaches silence
    voice.oscillator.stop(now + Math.max(0.05, env.releaseSeconds + 0.02));
    // Disconnect later to avoid glitches
    setTimeout(() => {
      try {
        voice.oscillator.disconnect();
        voice.gain.disconnect();
      } catch {}
    }, (Math.max(0.1, env.releaseSeconds + 0.05)) * 1000);

    this.voices.delete(noteName);
  };

  public allNotesOff = (): void => {
    Array.from(this.voices.keys()).forEach((n) => this.noteOff(n));
  };

  // Settings setters
  public setWaveform = (waveform: Waveform): void => {
    this.state.waveform = waveform;
  };

  public setEnvelope = (settings: Partial<EnvelopeSettings>): void => {
    this.state.envelope = { ...this.state.envelope, ...settings };
  };

  public setFilter = (settings: Partial<FilterSettings>): void => {
    if (!this.audioContext) {
      this.state.filter = { ...this.state.filter, ...settings };
      return;
    }
    this.state.filter = { ...this.state.filter, ...settings };
    const { cutoffHz, resonanceQ } = this.state.filter;
    const now = this.audioContext.currentTime;
    if (cutoffHz !== undefined) {
      this.filter.frequency.cancelScheduledValues(now);
      this.filter.frequency.exponentialRampToValueAtTime(Math.max(50, cutoffHz), now + 0.03);
    }
    if (resonanceQ !== undefined) {
      this.filter.Q.cancelScheduledValues(now);
      this.filter.Q.linearRampToValueAtTime(Math.max(0.0001, resonanceQ), now + 0.03);
    }
  };

  public setReverb = (settings: Partial<ReverbSettings>): void => {
    if (!this.audioContext) {
      this.state.reverb = { ...this.state.reverb, ...settings };
      return;
    }
    this.state.reverb = { ...this.state.reverb, ...settings };
    const now = this.audioContext.currentTime;
    if (settings.wet !== undefined) {
      this.reverbGain.gain.cancelScheduledValues(now);
      this.reverbGain.gain.linearRampToValueAtTime(Math.max(0, Math.min(1, settings.wet)), now + 0.05);
    }
    if (settings.seconds !== undefined || settings.decay !== undefined) {
      const { seconds, decay } = this.state.reverb;
      this.reverb.buffer = this.createImpulseResponse(this.audioContext, seconds, decay);
    }
  };

  public setMasterVolume = (volume: number): void => {
    this.state.masterVolume = Math.max(0, Math.min(1, volume));
    if (!this.audioContext) return;
    const now = this.audioContext.currentTime;
    this.masterGain.gain.cancelScheduledValues(now);
    this.masterGain.gain.linearRampToValueAtTime(this.state.masterVolume, now + 0.03);
  };

  public setOctaveOffset = (octaves: number): void => {
    this.state.octaveOffset = Math.max(-3, Math.min(3, Math.round(octaves)));
  };

  // Utilities
  private createImpulseResponse(ctx: AudioContext, seconds: number, decay: number): AudioBuffer {
    const rate = ctx.sampleRate;
    const length = Math.max(1, Math.floor(seconds * rate));
    const impulse = ctx.createBuffer(2, length, rate);
    for (let channel = 0; channel < impulse.numberOfChannels; channel++) {
      const data = impulse.getChannelData(channel);
      for (let i = 0; i < length; i++) {
        // White noise with exponential decay
        data[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / length, decay);
      }
    }
    return impulse;
  }

  private noteToFrequency(noteName: string, octaveShift: number): number {
    // Accept formats like C4, C#4, Db4
    const match = noteName.match(/^([A-Ga-g])(#|b)?(\d)$/);
    if (!match) return 440;
    const note = match[1].toUpperCase();
    const accidental = match[2] || "";
    const octave = parseInt(match[3], 10) + octaveShift;

    const semitoneMap: Record<string, number> = {
      C: 0, "C#": 1, Db: 1, D: 2, "D#": 3, Eb: 3, E: 4, F: 5, "F#": 6, Gb: 6,
      G: 7, "G#": 8, Ab: 8, A: 9, "A#": 10, Bb: 10, B: 11,
    };
    const key = note + accidental;
    const semitone = semitoneMap[key] ?? 9; // default A
    const midi = (octave + 1) * 12 + semitone; // C-1 = 0
    const a4 = 69;
    const freq = 440 * Math.pow(2, (midi - a4) / 12);
    return freq;
  }
}

// Singleton instance convenient for UI
export const audioEngine = new AudioEngine();

