import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../../utils/cn';

export interface PixelRevealProps {
  children: React.ReactNode;
  delay?: number;
  duration?: number;
  className?: string;
  showBorderFlash?: boolean;
}

export const PixelReveal: React.FC<PixelRevealProps> = ({
  children,
  delay = 0,
  duration = 0.45,
  className,
  showBorderFlash = true,
}) => {
  return (
    <div className={cn('relative', className)}>
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        transition={{
          duration,
          delay,
          ease: [0.16, 1, 0.3, 1], // Editorial easing
        }}
      >
        {children}
      </motion.div>

      {/* Ephemeral Corner Pixel Flash on Entrance */}
      {showBorderFlash && (
        <AnimatePresence>
          <motion.div
            initial={{ opacity: 1 }}
            animate={{ opacity: 0 }}
            transition={{ duration: 0.6, delay: delay + 0.2 }}
            className="pointer-events-none absolute inset-0 border border-[#F5F5F5]/40"
          >
            <span className="absolute top-0 left-0 w-1 h-1 bg-[#F5F5F5]" />
            <span className="absolute top-0 right-0 w-1 h-1 bg-[#F5F5F5]" />
            <span className="absolute bottom-0 left-0 w-1 h-1 bg-[#F5F5F5]" />
            <span className="absolute bottom-0 right-0 w-1 h-1 bg-[#F5F5F5]" />
          </motion.div>
        </AnimatePresence>
      )}
    </div>
  );
};

