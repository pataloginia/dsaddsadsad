import React, { useEffect, useRef } from "react";

export const Visualizer: React.FC<{ analyser: AnalyserNode | null }> = ({ analyser }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    let raf = 0;
    if (!canvasRef.current) return;
    const canvasEl = canvasRef.current as HTMLCanvasElement;
    const ctxMaybe = canvasEl.getContext("2d");
    if (!ctxMaybe) return;
    const ctx = ctxMaybe as CanvasRenderingContext2D;

    const bufferLength = analyser ? analyser.frequencyBinCount : 2048;
    const dataArray = new Uint8Array(bufferLength);

    function draw() {
      // Resize handling for crisp drawing
      const dpr = window.devicePixelRatio || 1;
      if (canvasEl.width !== canvasEl.clientWidth * dpr || canvasEl.height !== canvasEl.clientHeight * dpr) {
        canvasEl.width = canvasEl.clientWidth * dpr;
        canvasEl.height = canvasEl.clientHeight * dpr;
      }
      const w = canvasEl.width; const h = canvasEl.height;

      // Background gradient
      const gradient = ctx.createLinearGradient(0, 0, 0, h);
      gradient.addColorStop(0, "rgba(255,255,255,0.06)");
      gradient.addColorStop(1, "rgba(255,255,255,0.02)");
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, w, h);

      // If analyser available, draw bars and waveform
      if (analyser) {
        analyser.getByteFrequencyData(dataArray);
        const barWidth = (w / bufferLength) * 2.2;
        for (let i = 0, x = 0; i < bufferLength; i++, x += barWidth + 1) {
          const v = dataArray[i] / 255; // 0..1
          const barHeight = v * h * 0.6;
          // Neon style
          ctx.fillStyle = `rgba(${120 + Math.floor(120*v)}, ${100 + Math.floor(120*v)}, 255, ${0.35 + 0.45*v})`;
          ctx.fillRect(x, h - barHeight, barWidth, barHeight);
        }
      }

      // Add a flowing aurora curve for ambience
      const t = performance.now() * 0.001;
      ctx.beginPath();
      for (let x = 0; x <= w; x += 8) {
        const y = h*0.5 + Math.sin(x * 0.01 + t) * 12 + Math.cos(x * 0.005 - t*1.2) * 8;
        if (x === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      }
      ctx.strokeStyle = "rgba(170, 140, 255, 0.6)";
      ctx.lineWidth = 2;
      ctx.shadowColor = "rgba(170, 140, 255, 0.5)";
      ctx.shadowBlur = 8;
      ctx.stroke();
      ctx.shadowBlur = 0;

      raf = requestAnimationFrame(draw);
    }
    raf = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(raf);
  }, [analyser]);

  return <canvas ref={canvasRef} style={{ width: "100%", height: "100%" }} />;
};

