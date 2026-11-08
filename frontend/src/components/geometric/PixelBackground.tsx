import React, { useEffect, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { cn } from '../../utils/cn';

export interface PixelBackgroundProps {
  pixelSize?: number;
  gap?: number;
  interactionRadius?: number;
  displacementStrength?: number;
  baseOpacity?: number;
  activeOpacity?: number;
  disabledRoutes?: string[];
  className?: string;
}

interface PixelNode {
  baseX: number;
  baseY: number;
  currentX: number;
  currentY: number;
  opacity: number;
}

/**
 * Global Cursor-Reactive Geometric Pixel Background
 *
 * Implements Prompt 04's geometric pixel motion engine globally across application routes.
 * Operates on a fixed non-blocking canvas with window-level pointer tracking, smooth spring
 * physics, reduced-motion compliance, and mobile-optimized wave modulation.
 *
 * Route Awareness:
 * Automatically skips rendering on routes specified in `disabledRoutes` (defaults to ['/'])
 * to preserve the dedicated hero InteractivePixelGrid on the homepage and prevent double-rendering.
 */
export const PixelBackground: React.FC<PixelBackgroundProps> = ({
  pixelSize = 3,
  gap = 24,
  interactionRadius = 110,
  displacementStrength = 5,
  baseOpacity = 0.045,
  activeOpacity = 0.28,
  disabledRoutes = ['/'],
  className,
}) => {
  const location = useLocation();
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const mouseRef = useRef<{ x: number; y: number; active: boolean; lastMove: number }>({
    x: -9999,
    y: -9999,
    active: false,
    lastMove: 0,
  });

  const [reducedMotion, setReducedMotion] = useState(false);
  const isHomeRoute = disabledRoutes.includes(location.pathname);

  // 1. Accessibility: Detect prefers-reduced-motion media query
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReducedMotion(mediaQuery.matches);

    const handleMediaChange = (e: MediaQueryListEvent) => {
      setReducedMotion(e.matches);
    };

    mediaQuery.addEventListener('change', handleMediaChange);
    return () => mediaQuery.removeEventListener('change', handleMediaChange);
  }, []);

  // 2. Window-Level Pointer Tracking (passive, non-blocking)
  useEffect(() => {
    if (isHomeRoute) return;

    const handlePointerMove = (e: PointerEvent) => {
      mouseRef.current = {
        x: e.clientX,
        y: e.clientY,
        active: true,
        lastMove: performance.now(),
      };
    };

    const handlePointerLeave = () => {
      mouseRef.current.active = false;
      mouseRef.current.x = -9999;
      mouseRef.current.y = -9999;
    };

    const handleTouchMove = (e: TouchEvent) => {
      if (e.touches.length > 0) {
        const touch = e.touches[0];
        mouseRef.current = {
          x: touch.clientX,
          y: touch.clientY,
          active: true,
          lastMove: performance.now(),
        };
      }
    };

    const handleTouchEnd = () => {
      mouseRef.current.active = false;
    };

    window.addEventListener('pointermove', handlePointerMove, { passive: true });
    window.addEventListener('pointerleave', handlePointerLeave);
    window.addEventListener('touchmove', handleTouchMove, { passive: true });
    window.addEventListener('touchend', handleTouchEnd);

    return () => {
      window.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('pointerleave', handlePointerLeave);
      window.removeEventListener('touchmove', handleTouchMove);
      window.removeEventListener('touchend', handleTouchEnd);
    };
  }, [isHomeRoute]);

  // 3. Canvas Simulation & Rendering Engine
  useEffect(() => {
    if (isHomeRoute) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    // Mobile / touch screen detection
    const isCoarsePointer =
      window.matchMedia('(pointer: coarse)').matches || window.innerWidth < 768;

    // Adapt spacing: on mobile, widen gap to decrease node count by ~45% for high performance
    const effectiveGap = isCoarsePointer ? Math.max(gap, 32) : gap;
    const pitch = pixelSize + effectiveGap;

    let nodes: PixelNode[] = [];

    const initializeNodes = () => {
      nodes = [];
      const cols = Math.ceil(width / pitch);
      const rows = Math.ceil(height / pitch);

      const startX = (width - cols * pitch) / 2 + pitch / 2;
      const startY = (height - rows * pitch) / 2 + pitch / 2;

      for (let c = 0; c <= cols; c++) {
        const x = startX + c * pitch;
        if (x < 0 || x > width) continue;

        for (let r = 0; r <= rows; r++) {
          const y = startY + r * pitch;
          if (y < 0 || y > height) continue;

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

    // Resize handler
    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
      initializeNodes();

      if (reducedMotion) {
        drawStaticFrame();
      }
    };

    window.addEventListener('resize', handleResize);

    // Static frame for prefers-reduced-motion (no continuous rAF loop to save power)
    const drawStaticFrame = () => {
      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = '#F5F5F5';
      for (let i = 0; i < nodes.length; i++) {
        const node = nodes[i];
        ctx.globalAlpha = baseOpacity;
        ctx.fillRect(
          node.baseX - pixelSize / 2,
          node.baseY - pixelSize / 2,
          pixelSize,
          pixelSize
        );
      }
    };

    if (reducedMotion) {
      drawStaticFrame();
      return () => {
        window.removeEventListener('resize', handleResize);
      };
    }

    let time = 0;

    // 60 FPS Render Loop
    const render = () => {
      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = '#F5F5F5';

      time += 0.015;
      const mouse = mouseRef.current;

      // Inactivity timeout: if mouse has not moved for 2.5s, gently fade interaction
      const now = performance.now();
      const isMouseRecentlyActive = mouse.active && now - mouse.lastMove < 2500;

      for (let i = 0; i < nodes.length; i++) {
        const node = nodes[i];

        // Mobile Ambient Wave: subtle mathematical undulating luminance
        let ambientModulation = 0;
        if (isCoarsePointer) {
          ambientModulation =
            Math.sin(node.baseX * 0.008 + time) *
            Math.cos(node.baseY * 0.008 + time) *
            0.025;
        }

        if (isMouseRecentlyActive) {
          const dx = node.baseX - mouse.x;
          const dy = node.baseY - mouse.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < interactionRadius) {
            // Linear falloff: 1 at cursor center, 0 at outer threshold
            const factor = 1 - dist / interactionRadius;
            const angle = Math.atan2(dy, dx);

            // Target displacement & opacity
            const targetX = node.baseX + Math.cos(angle) * (displacementStrength * factor);
            const targetY = node.baseY + Math.sin(angle) * (displacementStrength * factor);
            const targetOpacity = baseOpacity + factor * (activeOpacity - baseOpacity);

            // Smooth spring easing
            node.currentX += (targetX - node.currentX) * 0.18;
            node.currentY += (targetY - node.currentY) * 0.18;
            node.opacity += (targetOpacity - node.opacity) * 0.18;
          } else {
            // Return to resting coordinate
            node.currentX += (node.baseX - node.currentX) * 0.08;
            node.currentY += (node.baseY - node.currentY) * 0.08;
            node.opacity += (baseOpacity + ambientModulation - node.opacity) * 0.08;
          }
        } else {
          // Resting state
          node.currentX += (node.baseX - node.currentX) * 0.08;
          node.currentY += (node.baseY - node.currentY) * 0.08;
          node.opacity += (baseOpacity + ambientModulation - node.opacity) * 0.08;
        }

        ctx.globalAlpha = Math.max(0.015, Math.min(0.7, node.opacity));
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
      cancelAnimationFrame(animationFrameId);
    };
  }, [
    isHomeRoute,
    pixelSize,
    gap,
    interactionRadius,
    displacementStrength,
    baseOpacity,
    activeOpacity,
    reducedMotion,
  ]);

  // If on homepage, do not render to preserve existing hero animation and avoid double-rendering
  if (isHomeRoute) {
    return null;
  }

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className={cn(
        'fixed inset-0 pointer-events-none z-0 block w-full h-full select-none',
        className
      )}
    />
  );
};

export default PixelBackground;
