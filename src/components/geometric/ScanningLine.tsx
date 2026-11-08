import React, { useEffect, useRef } from 'react';
import { cn } from '../../utils/cn';

export interface ScanningLineProps extends React.HTMLAttributes<HTMLDivElement> {
  orientation?: 'horizontal' | 'vertical'; // Beam orientation
  direction?: 'forward' | 'reverse' | 'alternate';
  speedMs?: number; // Time for one sweep (default: 2400)
  active?: boolean;
  color?: string; // Hex (default: #F5F5F5)
  showTrailParticles?: boolean;
}

export const ScanningLine: React.FC<ScanningLineProps> = ({
  orientation = 'horizontal',
  direction = 'alternate',
  speedMs = 2400,
  active = true,
  color = '#F5F5F5',
  showTrailParticles = true,
  className,
  children,
  ...props
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!active) return;

    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = container.clientWidth || 300);
    let height = (canvas.height = container.clientHeight || 150);

    const handleResize = () => {
      if (!canvas || !container) return;
      width = canvas.width = container.clientWidth || 300;
      height = canvas.height = container.clientHeight || 150;
    };

    window.addEventListener('resize', handleResize);

    const startTime = performance.now();

    // Particle trail pool
    const particles: Array<{ x: number; y: number; opacity: number; size: number }> = [];

    const isHorizontal = orientation === 'horizontal';
    const maxDistance = isHorizontal ? height : width;

    const render = (now: number) => {
      ctx.clearRect(0, 0, width, height);

      const elapsed = (now - startTime) % speedMs;
      const progress = elapsed / speedMs;

      let posNorm = progress;
      if (direction === 'alternate') {
        const doubleProgress = (elapsed % (speedMs * 2)) / (speedMs * 2);
        posNorm = doubleProgress < 0.5 ? doubleProgress * 2 : (1 - doubleProgress) * 2;
      } else if (direction === 'reverse') {
        posNorm = 1 - progress;
      }

      const beamPosition = posNorm * maxDistance;

      // Draw thin scanning line
      ctx.strokeStyle = color;
      ctx.lineWidth = 1;
      ctx.globalAlpha = 0.85;

      ctx.beginPath();
      if (isHorizontal) {
        ctx.moveTo(0, beamPosition);
        ctx.lineTo(width, beamPosition);
      } else {
        ctx.moveTo(beamPosition, 0);
        ctx.lineTo(beamPosition, height);
      }
      ctx.stroke();

      // Spawn trail particles along the beam
      if (showTrailParticles && Math.random() > 0.4) {
        const count = Math.floor(Math.random() * 3) + 1;
        for (let i = 0; i < count; i++) {
          particles.push({
            x: isHorizontal ? Math.random() * width : beamPosition,
            y: isHorizontal ? beamPosition : Math.random() * height,
            opacity: 0.9,
            size: Math.random() > 0.5 ? 3 : 2,
          });
        }
      }

      // Render and fade particles
      ctx.fillStyle = color;
      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        p.opacity -= 0.035;

        if (p.opacity <= 0) {
          particles.splice(i, 1);
          continue;
        }

        ctx.globalAlpha = p.opacity;
        ctx.fillRect(p.x, p.y, p.size, p.size);
      }

      animationFrameId = requestAnimationFrame(render);
    };

    animationFrameId = requestAnimationFrame(render);

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, [active, orientation, direction, speedMs, color, showTrailParticles]);

  return (
    <div
      ref={containerRef}
      className={cn('relative overflow-hidden w-full h-full min-h-[80px]', className)}
      {...props}
    >
      <canvas
        ref={canvasRef}
        className="absolute inset-0 block w-full h-full pointer-events-none z-10"
      />
      {children && <div className="relative z-0 h-full">{children}</div>}
    </div>
  );
};

