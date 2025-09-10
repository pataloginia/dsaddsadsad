import React from "react";
import { useAudioEngine } from "../../context/AudioEngineContext";
import "./controls.css";

export const Controls: React.FC = () => {
  const {
    waveform, setWaveform,
    envelope, setEnvelope,
    filter, setFilter,
    reverb, setReverb,
    masterVolume, setMasterVolume,
    octaveOffset, setOctaveOffset,
  } = useAudioEngine();

  return (
    <div className="controls-root">
      <div className="group">
        <h3>Звук</h3>
        <div className="row">
          <label>Волна</label>
          <select value={waveform} onChange={(e) => setWaveform(e.target.value as any)}>
            <option value="sine">Sine</option>
            <option value="square">Square</option>
            <option value="sawtooth">Saw</option>
            <option value="triangle">Triangle</option>
          </select>
        </div>
        <div className="row">
          <label>Громкость</label>
          <input type="range" min={0} max={1} step={0.01} value={masterVolume}
                 onChange={(e) => setMasterVolume(parseFloat(e.target.value))} />
        </div>
        <div className="row">
          <label>Октава</label>
          <input type="range" min={-2} max={2} step={1} value={octaveOffset}
                 onChange={(e) => setOctaveOffset(parseInt(e.target.value))} />
        </div>
      </div>

      <div className="group">
        <h3>ADSR</h3>
        <div className="row"><label>Attack</label>
          <input type="range" min={0.001} max={2} step={0.001} value={envelope.attackSeconds}
                 onChange={(e) => setEnvelope({ attackSeconds: parseFloat(e.target.value) })} /></div>
        <div className="row"><label>Decay</label>
          <input type="range" min={0.001} max={2} step={0.001} value={envelope.decaySeconds}
                 onChange={(e) => setEnvelope({ decaySeconds: parseFloat(e.target.value) })} /></div>
        <div className="row"><label>Sustain</label>
          <input type="range" min={0} max={1} step={0.01} value={envelope.sustainLevel}
                 onChange={(e) => setEnvelope({ sustainLevel: parseFloat(e.target.value) })} /></div>
        <div className="row"><label>Release</label>
          <input type="range" min={0.001} max={3} step={0.001} value={envelope.releaseSeconds}
                 onChange={(e) => setEnvelope({ releaseSeconds: parseFloat(e.target.value) })} /></div>
      </div>

      <div className="group">
        <h3>Фильтр</h3>
        <div className="row"><label>Cutoff</label>
          <input type="range" min={50} max={20000} step={1} value={filter.cutoffHz}
                 onChange={(e) => setFilter({ cutoffHz: parseFloat(e.target.value) })} /></div>
        <div className="row"><label>Q</label>
          <input type="range" min={0.0001} max={20} step={0.0001} value={filter.resonanceQ}
                 onChange={(e) => setFilter({ resonanceQ: parseFloat(e.target.value) })} /></div>
      </div>

      <div className="group">
        <h3>Реверберация</h3>
        <div className="row"><label>Wet</label>
          <input type="range" min={0} max={1} step={0.01} value={reverb.wet}
                 onChange={(e) => setReverb({ wet: parseFloat(e.target.value) })} /></div>
        <div className="row"><label>Длина</label>
          <input type="range" min={0.2} max={4} step={0.1} value={reverb.seconds}
                 onChange={(e) => setReverb({ seconds: parseFloat(e.target.value) })} /></div>
        <div className="row"><label>Спад</label>
          <input type="range" min={0.5} max={5} step={0.1} value={reverb.decay}
                 onChange={(e) => setReverb({ decay: parseFloat(e.target.value) })} /></div>
      </div>
    </div>
  );
};

