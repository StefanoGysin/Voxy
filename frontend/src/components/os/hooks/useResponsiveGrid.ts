import { useState, useEffect, useCallback, useMemo } from 'react';

interface GridBreakpoint {
  name: string;
  minWidth: number;
  maxWidth?: number;
  gridConfig: {
    rows: number;
    cols: number;
    gap: string;
    padding: string;
    iconSize: 'small' | 'medium' | 'large';
  };
}

/**
 * Professional responsive grid system for VOXY Web OS
 * Adapts grid layout based on screen size and device type
 */
export const useResponsiveGrid = () => {
  const [currentBreakpoint, setCurrentBreakpoint] = useState<GridBreakpoint | null>(null);
  const [screenDimensions, setScreenDimensions] = useState({ width: 0, height: 0 });

  // Responsive breakpoints with optimized grid configurations
  const breakpoints: GridBreakpoint[] = useMemo(() => [
    {
      name: 'mobile-portrait',
      minWidth: 0,
      maxWidth: 480,
      gridConfig: {
        rows: 8,
        cols: 4,
        gap: '1rem',
        padding: '0.5rem',
        iconSize: 'small',
      },
    },
    {
      name: 'mobile-landscape',
      minWidth: 481,
      maxWidth: 768,
      gridConfig: {
        rows: 6,
        cols: 6,
        gap: '1.25rem',
        padding: '0.75rem',
        iconSize: 'small',
      },
    },
    {
      name: 'tablet-portrait',
      minWidth: 769,
      maxWidth: 1024,
      gridConfig: {
        rows: 6,
        cols: 6,
        gap: '1.5rem',
        padding: '1rem',
        iconSize: 'medium',
      },
    },
    {
      name: 'tablet-landscape',
      minWidth: 1025,
      maxWidth: 1366,
      gridConfig: {
        rows: 6,
        cols: 8,
        gap: '1.75rem',
        padding: '1.25rem',
        iconSize: 'medium',
      },
    },
    {
      name: 'desktop',
      minWidth: 1367,
      maxWidth: 1920,
      gridConfig: {
        rows: 6,
        cols: 8,
        gap: '2rem',
        padding: '1.5rem',
        iconSize: 'medium',
      },
    },
    {
      name: 'large-desktop',
      minWidth: 1921,
      gridConfig: {
        rows: 6,
        cols: 10,
        gap: '2.5rem',
        padding: '2rem',
        iconSize: 'large',
      },
    },
  ], []);

  // Calculate current breakpoint based on screen width
  const calculateBreakpoint = useCallback((width: number): GridBreakpoint => {
    for (const breakpoint of breakpoints) {
      if (width >= breakpoint.minWidth && 
          (!breakpoint.maxWidth || width <= breakpoint.maxWidth)) {
        return breakpoint;
      }
    }
    
    // Default fallback to desktop
    return breakpoints.find(bp => bp.name === 'desktop') || breakpoints[0];
  }, [breakpoints]);

  // Update screen dimensions and breakpoint
  const updateDimensions = useCallback(() => {
    const width = window.innerWidth;
    const height = window.innerHeight;
    
    setScreenDimensions({ width, height });
    
    const newBreakpoint = calculateBreakpoint(width);
    
    // Only update if breakpoint actually changed
    if (!currentBreakpoint || currentBreakpoint.name !== newBreakpoint.name) {
      setCurrentBreakpoint(newBreakpoint);
      
      console.log('📱 Responsive Grid Update:', {
        breakpoint: newBreakpoint.name,
        dimensions: { width, height },
        gridConfig: newBreakpoint.gridConfig,
      });
    }
  }, [calculateBreakpoint, currentBreakpoint]);

  // Get device type for specialized behavior
  const getDeviceType = useCallback(() => {
    if (!currentBreakpoint) return 'desktop';
    
    const name = currentBreakpoint.name;
    
    if (name.includes('mobile')) return 'mobile';
    if (name.includes('tablet')) return 'tablet';
    return 'desktop';
  }, [currentBreakpoint]);

  // Check if device supports touch
  const isTouchDevice = useCallback(() => {
    return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
  }, []);

  // Get optimized grid configuration
  const getGridConfig = useCallback(() => {
    if (!currentBreakpoint) {
      // Default configuration
      return {
        rows: 6,
        cols: 8,
        gap: '2rem',
        padding: '1rem',
        iconSize: 'medium' as const,
      };
    }
    
    return currentBreakpoint.gridConfig;
  }, [currentBreakpoint]);

  // Get responsive drag sensitivity
  const getDragSensitivity = useCallback(() => {
    const deviceType = getDeviceType();
    
    switch (deviceType) {
      case 'mobile':
        return {
          activationConstraint: { distance: 8 }, // More tolerant for touch
          pointerActivationConstraint: { delay: 100, tolerance: 10 },
        };
      case 'tablet':
        return {
          activationConstraint: { distance: 6 },
          pointerActivationConstraint: { delay: 50, tolerance: 8 },
        };
      default:
        return {
          activationConstraint: { distance: 5 },
          pointerActivationConstraint: { delay: 0, tolerance: 5 },
        };
    }
  }, [getDeviceType]);

  // Initialize and set up event listeners
  useEffect(() => {
    // Initial calculation
    updateDimensions();
    
    // Debounced resize handler
    let timeoutId: NodeJS.Timeout;
    const handleResize = () => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(updateDimensions, 150);
    };
    
    // Orientation change handler for mobile devices
    const handleOrientationChange = () => {
      // Small delay to ensure dimensions are updated after orientation change
      setTimeout(updateDimensions, 200);
    };
    
    window.addEventListener('resize', handleResize);
    window.addEventListener('orientationchange', handleOrientationChange);
    
    return () => {
      clearTimeout(timeoutId);
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('orientationchange', handleOrientationChange);
    };
  }, [updateDimensions]);

  return {
    // Current state
    currentBreakpoint,
    screenDimensions,
    
    // Configuration getters
    getGridConfig,
    getDragSensitivity,
    getDeviceType,
    
    // Device detection
    isTouchDevice: isTouchDevice(),
    
    // Utility functions
    isBreakpoint: (name: string) => currentBreakpoint?.name === name,
    isMobile: () => getDeviceType() === 'mobile',
    isTablet: () => getDeviceType() === 'tablet',
    isDesktop: () => getDeviceType() === 'desktop',
    
    // Grid utilities
    getOptimalIconCount: () => {
      const config = getGridConfig();
      return config.rows * config.cols - 2; // Reserve space for DateTime widget
    },
    
    // Performance utilities
    shouldUseReducedMotion: () => {
      return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    },
  };
};