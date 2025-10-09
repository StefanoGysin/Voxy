'use client';

import type { AppIcon as AppIconType } from '@/lib/store/os-store';
import { useOSStore } from '@/lib/store/os-store';
import {
  Activity,
  Image,
  LayoutDashboard,
  MessageSquare,
  Settings,
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import type React from 'react';

interface AppIconProps {
  app: AppIconType;
  position: { x: number; y: number };
  size?: 'small' | 'medium' | 'large';
  isEditMode?: boolean;
  onMove?: (x: number, y: number) => void;
  className?: string;
}

// Icon mapping
const iconMap = {
  MessageSquare,
  LayoutDashboard,
  Settings,
  Activity,
  Image,
} as const;

const AppIconComponent: React.FC<AppIconProps> = ({
  app,
  position,
  size = 'medium',
  isEditMode = false,
  className = '',
}) => {
  const router = useRouter();
  const { addToRecent } = useOSStore();

  // Get icon component
  const IconComponent =
    iconMap[app.icon as keyof typeof iconMap] || MessageSquare;

  // Size configurations
  const sizeConfig = {
    small: {
      container: 'w-16 h-16',
      icon: 'w-6 h-6',
      text: 'text-xs',
      gap: 'gap-1',
    },
    medium: {
      container: 'w-20 h-20',
      icon: 'w-8 h-8',
      text: 'text-sm',
      gap: 'gap-2',
    },
    large: {
      container: 'w-24 h-24',
      icon: 'w-10 h-10',
      text: 'text-base',
      gap: 'gap-2',
    },
  };

  const config = sizeConfig[size];

  const handleClick = () => {
    if (isEditMode) return;

    // Add to recent apps
    addToRecent(app.id);

    // Navigate to app
    router.push(app.route);
  };

  const handleDragStart = (e: React.DragEvent) => {
    if (!isEditMode) {
      e.preventDefault();
      return;
    }

    // Store app id for drop handling
    e.dataTransfer.setData('text/plain', app.id);
    e.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div
      className={`
        flex flex-col items-center justify-center cursor-pointer
        transition-all duration-300 ease-out
        ${config.container} ${config.gap}
        ${isEditMode ? 'animate-wiggle' : 'hover:scale-110 active:scale-95'}
        ${className}
      `}
      style={{
        gridColumn: position.x,
        gridRow: position.y,
        transformOrigin: 'center',
      }}
      onClick={handleClick}
      draggable={isEditMode}
      onDragStart={handleDragStart}
      role="button"
      tabIndex={0}
      onKeyDown={e => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleClick();
        }
      }}
      aria-label={`${app.title} - ${app.description}`}
    >
      {/* Icon Container */}
      <div
        className={`
          relative flex items-center justify-center rounded-2xl
          backdrop-blur-sm border border-white/20
          transition-all duration-300 ease-out
          shadow-lg hover:shadow-xl
          ${config.container}
          ${isEditMode ? 'border-white/40' : 'hover:border-white/30'}
        `}
        style={{
          background: `
            linear-gradient(135deg, 
              ${app.color}CC 0%, 
              ${app.color}AA 50%, 
              ${app.color}88 100%
            ),
            rgba(255, 255, 255, 0.1)
          `,
          boxShadow: `
            0 8px 32px rgba(0, 0, 0, 0.12),
            0 2px 8px rgba(0, 0, 0, 0.08),
            inset 0 1px 0 rgba(255, 255, 255, 0.2),
            inset 0 -1px 0 rgba(0, 0, 0, 0.1)
          `,
        }}
      >
        {/* Icon */}
        <IconComponent
          className={`${config.icon} text-white drop-shadow-sm`}
          strokeWidth={1.5}
        />

        {/* Glow effect on hover */}
        <div
          className={`
            absolute inset-0 rounded-2xl opacity-0 
            transition-opacity duration-300
            ${!isEditMode && 'hover:opacity-30'}
          `}
          style={{
            background: `radial-gradient(circle, ${app.color}66 0%, transparent 70%)`,
            filter: 'blur(4px)',
          }}
          aria-hidden="true"
        />

        {/* Edit mode indicator */}
        {isEditMode && (
          <div className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full border border-white shadow-sm" />
        )}
      </div>

      {/* App Label */}
      <span
        className={`
          ${config.text} font-medium text-white text-center
          drop-shadow-sm max-w-full truncate px-1
          transition-all duration-300
        `}
        style={{
          textShadow: '0 1px 2px rgba(0, 0, 0, 0.5)',
        }}
      >
        {app.title}
      </span>
    </div>
  );
};

export default AppIconComponent;