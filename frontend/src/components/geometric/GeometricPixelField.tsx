import React, { useEffect, useRef, useState } from 'react';
import { cn } from '../../utils/cn';

export interface GeometricPixelFieldProps extends React.HTMLAttributes<HTMLDivElement> {
  pixelSize?: number; // Size of each square (default: 3)
  gap?: number; // Distance between squares (default: 21)
  baseOpacity?: number; // Base minimum opacity (default: 0.03)
  peakOpacity?: number; // Maximum wave opacity (default: 0.18)
  speed?: number; // Speed of mathematical wave (default: 0.008)
  variance?: number; // Spatial frequency variance (default: 0.015)
}

export const GeometricPixelField: React.FC<GeometricPixelFieldProps> = ({
  pixelSize = 3,
  gap = 21,
  baseOpacity = 0.03,
  peakOpacity = 0.18,
  speed = 0.008,
  variance = 0.015,
  className,
  ...props
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReducedMotion(mediaQuery.matches);

    const handleMediaChange = (e: MediaQueryListEvent) => setReducedMotion(e.matches);
    mediaQuery.addEventListener('change', handleMediaChange);

    return () => mediaQuery.removeEventListener('change', handleMediaChange);
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = container.clientWidth || 300);
    let height = (canvas.height = container.clientHeight || 200);

    const handleResize = () => {
      if (!canvas || !container) return;
      width = canvas.width = container.clientWidth || 300;
      height = canvas.height = container.clientHeight || 200;
      if (reducedMotion) renderStatic();
    };

    window.addEventListener('resize', handleResize);

    // Responsive adaptation: Increase gap on smaller screens to reduce square count
    const effectiveGap = width < 640 ? gap * 1.5 : gap;
    const pitch = pixelSize + effectiveGap;

    const renderStatic = () => {
      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = '#F5F5F5';

      for (let x = 0; x < width; x += pitch) {
        for (let y = 0; y < height; y += pitch) {
          const isSelected = (x * 7 + y * 13) % 29 === 0;
          ctx.globalAlpha = isSelected ? baseOpacity * 2 : baseOpacity;
          ctx.fillRect(x, y, pixelSize, pixelSize);
        }
      }
    };

    if (reducedMotion) {
      renderStatic();
      return () => window.removeEventListener('resize', handleResize);
    }

    let time = 0;

    const render = () => {
      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = '#F5F5F5';
      time += speed;

      for (let x = 0; x < width; x += pitch) {
        for (let y = 0; y < height; y += pitch) {
          // Double sine wave with cross-axis interference
          const wave1 = Math.sin(x * variance + time);
          const wave2 = Math.cos(y * variance + time * 0.8);
          const combined = (wave1 + wave2) / 2;

          // Normalized opacity between baseOpacity and peakOpacity
          const normalized = (combined + 1) / 2; // 0.0 to 1.0
          const opacity = baseOpacity + normalized * (peakOpacity - baseOpacity);

          ctx.globalAlpha = Math.max(0.01, Math.min(1.0, opacity));
          ctx.fillRect(x, y, pixelSize, pixelSize);
        }
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, [pixelSize, gap, baseOpacity, peakOpacity, speed, variance, reducedMotion]);

  return (
    <div
      ref={containerRef}
      className={cn('relative w-full h-full overflow-hidden bg-[#080808]', className)}
      {...props}
    >
      <canvas ref={canvasRef} className="block w-full h-full" />
    </div>
  );
};

