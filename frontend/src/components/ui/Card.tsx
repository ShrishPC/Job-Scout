"use client";

import React from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'yellow' | 'mint' | 'pink' | 'sand';
  elevation?: 'sm' | 'md' | 'lg';
}

export const Card: React.FC<CardProps> = ({
  children,
  variant = 'default',
  elevation = 'md',
  className = '',
  ...props
}) => {
  const variantStyles = {
    default: "bg-white text-black",
    yellow: "bg-retro-yellow text-black",
    mint: "bg-retro-mint text-black",
    pink: "bg-retro-pink text-black",
    sand: "bg-retro-sand text-black"
  };

  const elevationStyles = {
    sm: "shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]",
    md: "shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]",
    lg: "shadow-[6px_6px_0px_0px_rgba(0,0,0,1)]"
  };

  return (
    <div
      className={`border-3 border-black rounded-xl p-6 transition-all ${variantStyles[variant]} ${elevationStyles[elevation]} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export default Card;
