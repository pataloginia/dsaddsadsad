/*
  usePianoInput
  Keyboard mappings to musical notes and helpers for piano ranges.
*/
import { useEffect, useRef, useState } from "react";

export type PianoKey = {
  note: string;       // e.g., "C4"
  isSharp: boolean;   // black key
  label?: string;     // optional label for UI
};

// Typical QWERTY mapping for two and a half octaves starting at C4
const KEY_TO_NOTE: Record<string, string> = {
  // Row Z X C V ... for white keys
  z: "C3", s: "C#3", x: "D3", d: "D#3", c: "E3",
  v: "F3", g: "F#3", b: "G3", h: "G#3", n: "A3", j: "A#3", m: "B3",
  ",": "C4", l: "C#4", ".": "D4", ";": "D#4", "/": "E4",
  q: "C4", 2: "C#4", w: "D4", 3: "D#4", e: "E4",
  r: "F4", 5: "F#4", t: "G4", 6: "G#4", y: "A4", 7: "A#4", u: "B4",
  i: "C5", 9: "C#5", o: "D5", 0: "D#5", p: "E5",
};

export function buildPianoRange(startNote: string, numKeys: number): PianoKey[] {
  const order = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
  const match = startNote.match(/^([A-Ga-g])(#|b)?(\d)$/);
  if (!match) throw new Error("Invalid start note");
  const noteLetter = match[1].toUpperCase();
  const accidental = match[2] || "";
  let octave = parseInt(match[3], 10);
  let index = order.indexOf(noteLetter + accidental);
  if (index < 0) index = order.indexOf(noteLetter);

  const keys: PianoKey[] = [];
  for (let i = 0; i < numKeys; i++) {
    const name = order[index];
    const isSharp = name.includes("#");
    keys.push({ note: `${name}${octave}`, isSharp });
    index++;
    if (index >= order.length) {
      index = 0;
      octave++;
    }
  }
  return keys;
}

export function usePianoKeyboard(onDown: (note: string) => void, onUp: (note: string) => void) {
  const pressed = useRef<Set<string>>(new Set());
  const [activeNotes, setActiveNotes] = useState<Set<string>>(new Set());

  useEffect(() => {
    const handleDown = (e: KeyboardEvent) => {
      if (e.repeat) return;
      const key = e.key.toLowerCase();
      const note = KEY_TO_NOTE[key];
      if (!note) return;
      pressed.current.add(key);
      onDown(note);
      setActiveNotes((prev) => new Set(prev).add(note));
    };

    const handleUp = (e: KeyboardEvent) => {
      const key = e.key.toLowerCase();
      const note = KEY_TO_NOTE[key];
      if (!note) return;
      pressed.current.delete(key);
      onUp(note);
      setActiveNotes((prev) => {
        const next = new Set(prev);
        next.delete(note);
        return next;
      });
    };

    window.addEventListener("keydown", handleDown);
    window.addEventListener("keyup", handleUp);
    return () => {
      window.removeEventListener("keydown", handleDown);
      window.removeEventListener("keyup", handleUp);
    };
  }, [onDown, onUp]);

  return activeNotes;
}

