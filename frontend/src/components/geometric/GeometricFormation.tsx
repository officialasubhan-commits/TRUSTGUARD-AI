import React, { useEffect, useRef, useState } from 'react';
import { cn } from '../../utils/cn';

export type FormationPattern = 'shield' | 'matrix' | 'crosshair' | 'horizon' | 'cycle';

export interface GeometricFormationProps extends React.HTMLAttributes<HTMLDivElement> {
  pattern?: FormationPattern;
  pixelCount?: number; // Total morphing elements (default: 64)
  size?: number; // Element square size (default: 4px)
  cycleInterval?: number; // Auto morph cycle ms if pattern === 'cycle' (default: 4000)
}

interface Particle {
  x: number;
  y: number;
  targetX: number;
  targetY: number;
  opacity: number;
  targetOpacity: number;
  scale: number;
}

export const GeometricFormation: React.FC<GeometricFormationProps> = ({
  pattern = 'cycle',
  pixelCount = 64,
  size = 4,
  cycleInterval = 4000,
  className,
  ...props
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [currentPatternIndex, setCurrentPatternIndex] = useState(0);

  const patterns: Array<'shield' | 'matrix' | 'crosshair' | 'horizon'> = [
    'shield',
    'matrix',
    'crosshair',
    'horizon',
  ];

  // Auto cycle patterns if requested
  useEffect(() => {
    if (pattern !== 'cycle') return;
    const interval = setInterval(() => {
      setCurrentPatternIndex((prev) => (prev + 1) % patterns.length);
    }, cycleInterval);
    return () => clearInterval(interval);
  }, [pattern, cycleInterval, patterns.length]);

  const activePattern = pattern === 'cycle' ? patterns[currentPatternIndex] : pattern;

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = container.clientWidth || 320);
    let height = (canvas.height = container.clientHeight || 320);

    const handleResize = () => {
      if (!canvas || !container) return;
      width = canvas.width = container.clientWidth || 320;
      height = canvas.height = container.clientHeight || 320;
    };

    window.addEventListener('resize', handleResize);

    const centerX = width / 2;
    const centerY = height / 2;

    // Generate mathematical target coordinates based on active pattern
    const computeTargets = (pat: 'shield' | 'matrix' | 'crosshair' | 'horizon') => {
      const targets: Array<{ x: number; y: number; opacity: number }> = [];
      const side = Math.ceil(Math.sqrt(pixelCount));

      if (pat === 'shield') {
        // Concentric geometric square boundary (TrustGuard Shield Motif)
        const radius = Math.min(width, height) * 0.32;
        for (let i = 0; i < pixelCount; i++) {
          const angle = (i / pixelCount) * Math.PI * 2;
          const squareFactor = Math.abs(Math.cos(angle)) + Math.abs(Math.sin(angle));
          const r = radius / squareFactor;
          targets.push({
            x: centerX + Math.cos(angle) * r,
            y: centerY + Math.sin(angle) * r,
            opacity: 0.8,
          });
        }
      } else if (pat === 'matrix') {
        // High-density centered cryptographic data matrix
        const cellGap = 16;
        const totalW = (side - 1) * cellGap;
        const startX = centerX - totalW / 2;
        const startY = centerY - totalW / 2;

        for (let i = 0; i < pixelCount; i++) {
          const col = i % side;
          const row = Math.floor(i / side);
          targets.push({
            x: startX + col * cellGap,
            y: startY + row * cellGap,
            opacity: (col + row) % 2 === 0 ? 0.9 : 0.3,
          });
        }
      } else if (pat === 'crosshair') {
        // Precision axis reticle
        const armLength = Math.min(width, height) * 0.38;
        const perArm = Math.floor(pixelCount / 4);

        for (let i = 0; i < pixelCount; i++) {
          const arm = Math.floor(i / perArm);
          const pos = ((i % perArm) / perArm) * armLength;

          let tx = centerX;
          let ty = centerY;

          if (arm === 0) tx += pos; // Right
          else if (arm === 1) tx -= pos; // Left
          else if (arm === 2) ty += pos; // Down
          else ty -= pos; // Up

          targets.push({
            x: tx,
            y: ty,
            opacity: 0.7,
          });
        }
      } else {
        // 'horizon': Dual scanning bars
        const half = Math.floor(pixelCount / 2);
        const span = Math.min(width, height) * 0.75;
        const startX = centerX - span / 2;

        for (let i = 0; i < pixelCount; i++) {
          const isTop = i < half;
          const idx = isTop ? i : i - half;
          const x = startX + (idx / half) * span;
          const y = centerY + (isTop ? -18 : 18);
          targets.push({
            x,
            y,
            opacity: 0.85,
          });
        }
      }

      return targets;
    };

    const targetCoords = computeTargets(activePattern);

    // Initialize particles once
    const particles: Particle[] = [];
    for (let i = 0; i < pixelCount; i++) {
      const target = targetCoords[i] || { x: centerX, y: centerY, opacity: 0.5 };
      particles.push({
        x: centerX + (Math.random() - 0.5) * 80,
        y: centerY + (Math.random() - 0.5) * 80,
        targetX: target.x,
        targetY: target.y,
        opacity: target.opacity,
        targetOpacity: target.opacity,
        scale: 1,
      });
    }

    const render = () => {
      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = '#F5F5F5';

      const updatedTargets = computeTargets(activePattern);

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        const t = updatedTargets[i] || { x: centerX, y: centerY, opacity: 0.5 };

        // Ease towards target coordinate (fluid mathematical reassembly)
        p.x += (t.x - p.x) * 0.08;
        p.y += (t.y - p.y) * 0.08;
        p.opacity += (t.opacity - p.opacity) * 0.08;

        ctx.globalAlpha = Math.max(0, Math.min(1, p.opacity));
        ctx.fillRect(p.x - size / 2, p.y - size / 2, size, size);
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, [activePattern, pixelCount, size]);

  return (
    <div
      ref={containerRef}
      className={cn('relative w-full h-full min-h-[260px] bg-[#080808]', className)}
      {...props}
    >
      <canvas ref={canvasRef} className="block w-full h-full" />
    </div>
  );
};

