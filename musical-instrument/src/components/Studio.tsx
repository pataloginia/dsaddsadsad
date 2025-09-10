import React, { useCallback, useMemo } from "react";
import { useAudioEngine } from "../context/AudioEngineContext";
import { Visualizer } from "./Visualizer";
import { Piano } from "./piano/Piano";
import { Controls } from "./ui/Controls";
import "./studio.css";

export const Studio: React.FC = () => {
  const { engine, startAudio } = useAudioEngine();

  const handleNoteDown = useCallback((note: string) => {
    engine.noteOn(note, 1);
  }, [engine]);

  const handleNoteUp = useCallback((note: string) => {
    engine.noteOff(note);
  }, [engine]);

  const analyser = useMemo(() => engine.getAnalyser(), [engine]);

  return (
    <div className="studio-root">
      <header className="studio-header">
        <div className="brand">
          <span className="brand-accent">Aurora</span> Piano
        </div>
        <button className="primary" onClick={startAudio}>Включить звук</button>
      </header>

      <section className="visualizer-wrap">
        <Visualizer analyser={analyser} />
      </section>

      <section className="controls-wrap">
        <Controls />
      </section>

      <section className="piano-wrap">
        <Piano onDown={handleNoteDown} onUp={handleNoteUp} />
      </section>

      <footer className="studio-footer">
        Играйте мышью, клавиатурой (QWERTY) или касанием. Наушники рекомендуются.
      </footer>
    </div>
  );
};

