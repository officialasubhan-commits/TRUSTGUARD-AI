import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../utils/cn';

export interface GeometricTransitionProps {
  children: React.ReactNode;
  staggerDelay?: number;
  className?: string;
}

export const GeometricTransition: React.FC<GeometricTransitionProps> = ({
  children,
  staggerDelay = 0.08,
  className,
}) => {
  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: staggerDelay,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 8 },
    show: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.35,
        ease: [0.16, 1, 0.3, 1],
      },
    },
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="show"
      className={cn('w-full', className)}
    >
      {React.Children.map(children, (child) => (
        <motion.div variants={itemVariants}>{child}</motion.div>
      ))}
    </motion.div>
  );
};

