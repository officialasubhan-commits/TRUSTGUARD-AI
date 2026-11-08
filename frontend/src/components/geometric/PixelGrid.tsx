import React from 'react';
import { cn } from '../../utils/cn';

export interface PixelGridProps extends React.HTMLAttributes<HTMLDivElement> {
  gridSize?: number; // Size of grid cell in pixels (default: 24)
  crosshairInterval?: number; // Place crosshair every N cells (default: 4)
  opacity?: number; // Overall grid opacity (default: 0.15)
  showCoordinates?: boolean;
}

export const PixelGrid: React.FC<PixelGridProps> = ({
  gridSize = 24,
  crosshairInterval = 4,
  opacity = 0.15,
  showCoordinates = false,
  className,
  children,
  ...props
}) => {
  return (
    <div
      className={cn('relative overflow-hidden border border-[#292929]', className)}
      style={{ opacity }}
      {...props}
    >
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <pattern
            id={`pixel-grid-pattern-${gridSize}`}
            width={gridSize}
            height={gridSize}
            patternUnits="userSpaceOnUse"
          >
            {/* 1px grid dot at intersection */}
            <rect x="0" y="0" width="1.5" height="1.5" fill="#F5F5F5" fillOpacity="0.4" />
          </pattern>
          <pattern
            id={`pixel-crosshair-pattern-${gridSize * crosshairInterval}`}
            width={gridSize * crosshairInterval}
            height={gridSize * crosshairInterval}
            patternUnits="userSpaceOnUse"
          >
            {/* Minimal plus crosshair marker */}
            <path
              d="M -3 0 L 3 0 M 0 -3 L 0 3"
              stroke="#F5F5F5"
              strokeWidth="1"
              strokeOpacity="0.5"
            />
          </pattern>
        </defs>

        <rect width="100%" height="100%" fill={`url(#pixel-grid-pattern-${gridSize})`} />
        <rect
          width="100%"
          height="100%"
          fill={`url(#pixel-crosshair-pattern-${gridSize * crosshairInterval})`}
        />
      </svg>

      {showCoordinates && (
        <div className="absolute bottom-2 right-2 text-[9px] font-mono text-[#666666] tracking-widest pointer-events-none select-none">
          GRID: {gridSize}PX // COORD: [0,0]
        </div>
      )}

      {children && <div className="relative z-10">{children}</div>}
    </div>
  );
};

