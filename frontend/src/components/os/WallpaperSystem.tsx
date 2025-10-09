'use client';

import { useOSStore } from '@/lib/store/os-store';
import type React from 'react';
import { useMemo } from 'react';

interface WallpaperSystemProps {
  children: React.ReactNode;
  className?: string;
}

// Wallpaper configurations
const wallpaperPresets = {
  // Landscape Wallpapers
  'mountain-sunset': {
    type: 'image',
    url: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1920&h=1080&fit=crop&q=80',
    fallback: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    description: 'Mountain Sunset',
  },
  'ocean-waves': {
    type: 'image',
    url: 'https://images.unsplash.com/photo-1439066615861-d1af74d74000?w=1920&h=1080&fit=crop&q=80',
    fallback: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    description: 'Ocean Waves',
  },
  'forest-morning': {
    type: 'image',
    url: 'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=1920&h=1080&fit=crop&q=80',
    fallback: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    description: 'Forest Morning',
  },
  'city-night': {
    type: 'image',
    url: 'https://images.unsplash.com/photo-1514565131-fce0801e5785?w=1920&h=1080&fit=crop&q=80',
    fallback: 'linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 100%)',
    description: 'City Night',
  },

  // Space Wallpapers
  'space-nebula': {
    type: 'image',
    url: 'https://images.unsplash.com/photo-1446776653964-20c1d3a81b06?w=1920&h=1080&fit=crop&q=80',
    fallback: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    description: 'Space Nebula',
  },
  'galaxy-spiral': {
    type: 'image',
    url: 'https://images.unsplash.com/photo-1502134249126-9f3755a50d78?w=1920&h=1080&fit=crop&q=80',
    fallback: 'linear-gradient(135deg, #0c0c0c 0%, #667eea 100%)',
    description: 'Spiral Galaxy',
  },

  // Gradient Wallpapers
  'gradient-blue': {
    type: 'gradient',
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    description: 'Blue Gradient',
  },
  'gradient-purple': {
    type: 'gradient',
    gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    description: 'Purple Gradient',
  },
  'gradient-ocean': {
    type: 'gradient',
    gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    description: 'Ocean Gradient',
  },
  'gradient-forest': {
    type: 'gradient',
    gradient: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    description: 'Forest Gradient',
  },

  // Abstract/Minimal
  'abstract-purple': {
    type: 'gradient',
    gradient:
      'radial-gradient(circle at 30% 20%, #667eea 0%, #764ba2 50%, #0c0c0c 100%)',
    description: 'Abstract Purple',
  },
  'minimal-dark': {
    type: 'gradient',
    gradient: 'linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 100%)',
    description: 'Minimal Dark',
  },
  'minimal-light': {
    type: 'gradient',
    gradient: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
    description: 'Minimal Light',
  },
} as const;

const WallpaperSystem: React.FC<WallpaperSystemProps> = ({
  children,
  className = '',
}) => {
  const { wallpaper } = useOSStore();

  const wallpaperStyle = useMemo(() => {
    const preset =
      wallpaperPresets[wallpaper.preset as keyof typeof wallpaperPresets];

    if (!preset) {
      // Fallback to default gradient using backgroundImage to avoid CSS conflicts
      return {
        backgroundImage: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        opacity: wallpaper.opacity,
        filter: wallpaper.blur > 0 ? `blur(${wallpaper.blur}px)` : 'none',
      };
    }

    let backgroundStyle: React.CSSProperties = {};

    if (preset.type === 'image') {
      // FIXED: Use specific properties to avoid CSS shorthand conflicts
      // Previously: background shorthand conflicted with backgroundSize/Position/Repeat
      // This caused React warnings during re-renders when changing wallpapers
      backgroundStyle = {
        // Layer 1: Overlay for better readability
        // Layer 2: Main image
        // Layer 3: Fallback gradient (will show if image fails to load)
        backgroundImage: `
          linear-gradient(rgba(0,0,0,0.1), rgba(0,0,0,0.1)),
          url("${preset.url}"),
          ${preset.fallback}
        `,
        backgroundSize: 'cover, cover, cover',
        backgroundPosition: 'center, center, center',
        backgroundRepeat: 'no-repeat, no-repeat, no-repeat',
        backgroundAttachment: 'fixed', // Performance optimization
      };
    } else if (preset.type === 'gradient') {
      backgroundStyle = {
        backgroundImage: preset.gradient,
      };
    }

    return {
      ...backgroundStyle,
      opacity: wallpaper.opacity,
      filter: wallpaper.blur > 0 ? `blur(${wallpaper.blur}px)` : 'none',
      transition: 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)',
      willChange: 'background-image, opacity, filter', // GPU optimization
    };
  }, [wallpaper]);

  return (
    <div className={`relative min-h-screen overflow-hidden ${className}`}>
      {/* Wallpaper Background */}
      <div
        className="fixed inset-0 -z-10"
        style={wallpaperStyle}
        aria-hidden="true"
      />

      {/* Overlay for better content readability */}
      <div className="fixed inset-0 -z-10 bg-black/10" aria-hidden="true" />

      {/* Gradient overlay at bottom for better icon visibility */}
      <div
        className="fixed bottom-0 left-0 right-0 h-32 -z-10"
        style={{
          background: 'linear-gradient(transparent, rgba(0,0,0,0.3))',
        }}
        aria-hidden="true"
      />

      {/* Content */}
      <div className="relative z-10">{children}</div>
    </div>
  );
};

export default WallpaperSystem;

// Export wallpaper presets for configuration UI
export { wallpaperPresets };
export type WallpaperPresetKey = keyof typeof wallpaperPresets;