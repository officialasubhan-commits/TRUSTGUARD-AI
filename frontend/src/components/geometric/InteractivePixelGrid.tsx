import React, { useEffect, useRef, useState, useCallback } from 'react';
import { cn } from '../../utils/cn';

export interface InteractivePixelGridProps extends React.HTMLAttributes<HTMLDivElement> {
  pixelSize?: number; // Square dimension (default: 3px)
  gap?: number; // Space between grid dots (default: 24px)
  interactionRadius?: number; // Proximity threshold in pixels (default: 100px)
  displacementStrength?: number; // Max push distance away from cursor (default: 6px)
  baseOpacity?: number; // Default square opacity (default: 0.05)
  activeOpacity?: number; // Opacity when cursor is nearby (default: 0.5)
}

interface PixelNode {
  baseX: number;
  baseY: number;
  currentX: number;
  currentY: number;
  opacity: number;
}

export const InteractivePixelGrid: React.FC<InteractivePixelGridProps> = ({
  pixelSize = 3,
  gap = 24,
  interactionRadius = 100,
  displacementStrength = 6,
  baseOpacity = 0.05,
  activeOpacity = 0.5,
  className,
  children,
  ...props
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const mouseRef = useRef<{ x: number; y: number; active: boolean }>({
    x: -9999,
    y: -9999,
    active: false,
  });
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReducedMotion(mediaQuery.matches);
    const handleMedia = (e: MediaQueryListEvent) => setReducedMotion(e.matches);
    mediaQuery.addEventListener('change', handleMedia);
    return () => mediaQuery.removeEventListener('change', handleMedia);
  }, []);

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    mouseRef.current = {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
      active: true,
    };
  }, []);

  const handleMouseLeave = useCallback(() => {
    mouseRef.current.active = false;
    mouseRef.current.x = -9999;
    mouseRef.current.y = -9999;
  }, []);

  const handleTouchMove = useCallback((e: React.TouchEvent<HTMLDivElement>) => {
    if (!containerRef.current || e.touches.length === 0) return;
    const touch = e.touches[0];
    const rect = containerRef.current.getBoundingClientRect();
    mouseRef.current = {
      x: touch.clientX - rect.left,
      y: touch.clientY - rect.top,
      active: true,
    };
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

    let nodes: PixelNode[] = [];

    const initializeNodes = () => {
      nodes = [];
      const pitch = pixelSize + gap;
      for (let x = pitch / 2; x < width; x += pitch) {
        for (let y = pitch / 2; y < height; y += pitch) {
          nodes.push({
            baseX: x,
            baseY: y,
            currentX: x,
            currentY: y,
            opacity: baseOpacity,
          });
        }
      }
    };

    initializeNodes();

    const handleResize = () => {
      if (!canvas || !container) return;
      width = canvas.width = container.clientWidth || 300;
      height = canvas.height = container.clientHeight || 200;
      initializeNodes();
    };

    window.addEventListener('resize', handleResize);

    const resizeObserver = new ResizeObserver(() => {
      handleResize();
    });
    resizeObserver.observe(container);

    const render = () => {
      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = '#F5F5F5';

      const mouse = mouseRef.current;

      for (let i = 0; i < nodes.length; i++) {
        const node = nodes[i];

        if (!reducedMotion && mouse.active) {
          const dx = node.baseX - mouse.x;
          const dy = node.baseY - mouse.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < interactionRadius) {
            // Proximity influence: 1 at center, 0 at edge
            const factor = 1 - dist / interactionRadius;
            const angle = Math.atan2(dy, dx);

            // Target displacement away from cursor
            const targetX = node.baseX + Math.cos(angle) * (displacementStrength * factor);
            const targetY = node.baseY + Math.sin(angle) * (displacementStrength * factor);
            const targetOpacity = baseOpacity + factor * (activeOpacity - baseOpacity);

            // Smooth interpolation
            node.currentX += (targetX - node.currentX) * 0.2;
            node.currentY += (targetY - node.currentY) * 0.2;
            node.opacity += (targetOpacity - node.opacity) * 0.2;
          } else {
            // Smoothly return to base coordinate
            node.currentX += (node.baseX - node.currentX) * 0.1;
            node.currentY += (node.baseY - node.currentY) * 0.1;
            node.opacity += (baseOpacity - node.opacity) * 0.1;
          }
        } else {
          // Stationary state
          node.currentX += (node.baseX - node.currentX) * 0.1;
          node.currentY += (node.baseY - node.currentY) * 0.1;
          node.opacity += (baseOpacity - node.opacity) * 0.1;
        }

        ctx.globalAlpha = node.opacity;
        ctx.fillRect(
          node.currentX - pixelSize / 2,
          node.currentY - pixelSize / 2,
          pixelSize,
          pixelSize
        );
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      resizeObserver.disconnect();
      cancelAnimationFrame(animationFrameId);
    };
  }, [
    pixelSize,
    gap,
    interactionRadius,
    displacementStrength,
    baseOpacity,
    activeOpacity,
    reducedMotion,
  ]);

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleMouseLeave}
      className={cn('relative w-full h-full overflow-hidden bg-[#080808]', className)}
      {...props}
    >
      <canvas ref={canvasRef} className="absolute inset-0 block w-full h-full pointer-events-none" />
      {children && <div className="relative z-10">{children}</div>}
    </div>
  );
};

