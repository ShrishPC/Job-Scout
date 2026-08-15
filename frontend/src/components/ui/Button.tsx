"use client";

import React from 'react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'accent' | 'outline' | 'mint';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  className = '',
  disabled,
  ...props
}) => {
  const baseStyles = "font-black uppercase tracking-wider transition-all flex items-center justify-center border-3 border-black rounded-lg cursor-pointer select-none";

  const sizeStyles = {
    sm: "px-3 py-1.5 text-[10px] shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[0.5px] hover:translate-y-[0.5px] hover:shadow-[1px_1px_0px_0px_rgba(0,0,0,1)] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none",
    md: "px-5 py-2.5 text-xs shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:translate-x-[3px] active:translate-y-[3px] active:shadow-none",
    lg: "px-8 py-3.5 text-sm shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[2.5px_2.5px_0px_0px_rgba(0,0,0,1)] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none"
  };

  const variantStyles = {
    primary: "bg-retro-yellow text-black hover:bg-yellow-300",
    secondary: "bg-retro-cream text-black hover:bg-retro-sand",
    danger: "bg-retro-red text-white hover:bg-red-600",
    accent: "bg-retro-pink text-black hover:bg-pink-300",
    mint: "bg-retro-mint text-black hover:bg-teal-200",
    outline: "bg-white text-black hover:bg-retro-cream"
  };

  const disabledStyles = disabled || loading 
    ? "opacity-50 cursor-not-allowed translate-x-0 translate-y-0 shadow-none hover:shadow-none pointer-events-none" 
    : "";

  return (
    <button
      disabled={disabled || loading}
      className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${disabledStyles} ${className}`}
      {...props}
    >
      {loading ? (
        <span className="inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-2" />
      ) : null}
      {children}
    </button>
  );
};

export default Button;
