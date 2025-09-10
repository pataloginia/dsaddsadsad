import React, { useMemo } from "react";
import { buildPianoRange, usePianoKeyboard } from "../../hooks/usePianoInput";
import { useAudioEngine } from "../../context/AudioEngineContext";
import "./piano.css";

type Props = { onDown: (note: string) => void; onUp: (note: string) => void };

export const Piano: React.FC<Props> = ({ onDown, onUp }) => {
  const { octaveOffset } = useAudioEngine();
  const keys = useMemo(() => buildPianoRange("C3", 24), []);
  const active = usePianoKeyboard(onDown, onUp);

  const handlePointerDown = (note: string) => (e: React.PointerEvent) => {
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
    onDown(note);
  };
  const handlePointerUp = (note: string) => () => onUp(note);

  return (
    <div className="piano-root" role="group" aria-label="piano">
      {/* White keys layer */}
      <div className="white-layer">
        {keys.filter(k => !k.isSharp).map((k) => (
          <button key={k.note}
                  className={`white ${active.has(k.note) ? 'active' : ''}`}
                  onPointerDown={handlePointerDown(shiftOct(k.note, octaveOffset))}
                  onPointerUp={handlePointerUp(shiftOct(k.note, octaveOffset))}
                  onPointerCancel={handlePointerUp(shiftOct(k.note, octaveOffset))}
                  onPointerLeave={handlePointerUp(shiftOct(k.note, octaveOffset))}
                  aria-pressed={active.has(k.note)}
          >
            <span className="label">{k.note}</span>
          </button>
        ))}
      </div>

      {/* Black keys layer */}
      <div className="black-layer">
        {keys.map((k, idx) => {
          if (!k.isSharp) return null;
          // position over the gap between white keys using CSS grid
          return (
            <button key={k.note}
                    className={`black pos-${idx} ${active.has(k.note) ? 'active' : ''}`}
                    onPointerDown={handlePointerDown(shiftOct(k.note, octaveOffset))}
                    onPointerUp={handlePointerUp(shiftOct(k.note, octaveOffset))}
                    onPointerCancel={handlePointerUp(shiftOct(k.note, octaveOffset))}
                    onPointerLeave={handlePointerUp(shiftOct(k.note, octaveOffset))}
                    aria-pressed={active.has(k.note)}
            />
          );
        })}
      </div>
    </div>
  );
};

function shiftOct(note: string, offset: number): string {
  const m = note.match(/^([A-G]#?)(\d)$/);
  if (!m) return note;
  const name = m[1];
  const oct = parseInt(m[2], 10) + offset;
  return `${name}${oct}`;
}

