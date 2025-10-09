'use client';

import { useEffect, useState } from 'react';
import { cn } from '@/lib/utils';
import { Check, Info, AlertTriangle, X } from 'lucide-react';

export interface Toast {
  id: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  duration?: number;
}

interface ToastSystemProps {
  className?: string;
}

// Global toast state management
let toastCallbacks: Array<(toasts: Toast[]) => void> = [];
let currentToasts: Toast[] = [];

export const showToast = (
  message: string, 
  type: Toast['type'] = 'info', 
  duration = 3000
) => {
  const toast: Toast = {
    id: crypto.randomUUID(),
    message,
    type,
    duration,
  };

  currentToasts = [...currentToasts, toast];
  toastCallbacks.forEach(callback => callback(currentToasts));

  // Auto-remove after duration
  setTimeout(() => {
    removeToast(toast.id);
  }, duration);
};

export const removeToast = (id: string) => {
  currentToasts = currentToasts.filter(toast => toast.id !== id);
  toastCallbacks.forEach(callback => callback(currentToasts));
};

export function ToastSystem({ className }: ToastSystemProps) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  useEffect(() => {
    const callback = (newToasts: Toast[]) => setToasts(newToasts);
    toastCallbacks.push(callback);

    // Set initial toasts
    setToasts(currentToasts);

    return () => {
      toastCallbacks = toastCallbacks.filter(cb => cb !== callback);
    };
  }, []);

  const getToastIcon = (type: Toast['type']) => {
    switch (type) {
      case 'success':
        return <Check className="w-4 h-4" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4" />;
      case 'error':
        return <AlertTriangle className="w-4 h-4" />;
      default:
        return <Info className="w-4 h-4" />;
    }
  };

  const getToastStyles = (type: Toast['type']) => {
    const baseStyles = 'flex items-center gap-3 p-3 rounded-lg shadow-lg backdrop-blur-md border';
    
    switch (type) {
      case 'success':
        return `${baseStyles} bg-green-500/20 border-green-400/50 text-green-100`;
      case 'warning':
        return `${baseStyles} bg-yellow-500/20 border-yellow-400/50 text-yellow-100`;
      case 'error':
        return `${baseStyles} bg-red-500/20 border-red-400/50 text-red-100`;
      default:
        return `${baseStyles} bg-blue-500/20 border-blue-400/50 text-blue-100`;
    }
  };

  if (toasts.length === 0) return null;

  return (
    <div className={cn(
      'fixed top-4 right-4 z-50 space-y-2 pointer-events-none',
      className
    )}>
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={cn(
            getToastStyles(toast.type),
            'animate-in slide-in-from-top-2 duration-300',
            'pointer-events-auto'
          )}
        >
          {getToastIcon(toast.type)}
          <span className="flex-1 text-sm font-medium">
            {toast.message}
          </span>
          <button
            onClick={() => removeToast(toast.id)}
            className="opacity-70 hover:opacity-100 transition-opacity"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ))}
    </div>
  );
}

// Utility functions for common toast types
export const showSuccessToast = (message: string, duration?: number) =>
  showToast(message, 'success', duration);

export const showErrorToast = (message: string, duration?: number) =>
  showToast(message, 'error', duration);

export const showWarningToast = (message: string, duration?: number) =>
  showToast(message, 'warning', duration);

export const showInfoToast = (message: string, duration?: number) =>
  showToast(message, 'info', duration);