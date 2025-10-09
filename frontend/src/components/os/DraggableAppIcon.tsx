'use client';

import type { AppIcon as AppIconType } from '@/lib/store/os-store';
import { useOSStore } from '@/lib/store/os-store';
import { useDraggable } from '@dnd-kit/core';
import {
  Activity,
  LayoutDashboard,
  MessageSquare,
  Settings,
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import type React from 'react';
import { useCallback, useMemo, useEffect } from 'react';

interface DraggableAppIconProps {
  app: AppIconType;
  position: { x: number; y: number };
  size?: 'small' | 'medium' | 'large';
  className?: string;
}

// Icon mapping
const iconMap = {
  MessageSquare,
  LayoutDashboard,
  Settings,
  Activity,
} as const;

const DraggableAppIcon: React.FC<DraggableAppIconProps> = ({
  app,
  position,
  size = 'medium',
  className = '',
}) => {
  const router = useRouter();
  const { 
    editMode, 
    addToRecent, 
    trackAppInteraction 
  } = useOSStore();

  // Setup draggable functionality
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    isDragging,
  } = useDraggable({
    id: app.id,
    disabled: !editMode,
    data: {
      type: 'app-icon',
      app,
      position,
    },
  });
  
  // Debug transform changes
  useEffect(() => {
    if (isDragging && transform) {
      console.log('📱 Icon Transform:', {
        app: app.title,
        transform,
        isDragging,
        position
      });
    }
  }, [transform, isDragging, app.title, position]);

  // Get icon component
  const IconComponent = useMemo(() => 
    iconMap[app.icon as keyof typeof iconMap] || MessageSquare,
    [app.icon]
  );

  // Size configurations
  const sizeConfig = useMemo(() => ({
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
  }), []);

  const config = sizeConfig[size];

  // Handle app click/activation
  const handleClick = useCallback((e: React.MouseEvent) => {
    if (editMode || isDragging) {
      e.preventDefault();
      return;
    }

    // Track interaction and add to recent
    trackAppInteraction(app.id);
    addToRecent(app.id);

    // Navigate to app
    router.push(app.route);
  }, [editMode, isDragging, app.id, app.route, trackAppInteraction, addToRecent, router]);

  // Handle keyboard activation
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      if (!editMode && !isDragging) {
        // Simulate mouse click for keyboard activation
        const mouseEvent = {
          preventDefault: () => {},
        } as React.MouseEvent;
        handleClick(mouseEvent);
      }
    }
  }, [editMode, isDragging, handleClick]);

  // Calculate transform style with absolute positioning during drag
  const transformStyle = useMemo(() => {
    if (!transform || !isDragging) return undefined;
    
    return {
      position: 'fixed' as const,
      transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
      zIndex: 1000,
      pointerEvents: 'none' as const, // Prevent interference during drag
    };
  }, [transform, isDragging]);

  return (
    <div
      ref={setNodeRef}
      className={`
        flex flex-col items-center justify-center relative z-10
        transition-all duration-300 ease-out
        ${config.container} ${config.gap}
        ${editMode ? 'cursor-grab active:cursor-grabbing' : 'cursor-pointer'}
        ${isDragging ? 'opacity-50 scale-105 z-50' : ''}
        ${editMode && !isDragging ? 'animate-wiggle hover:scale-105' : 'hover:scale-110 active:scale-95'}
        ${className}
      `}
      style={{
        gridColumn: isDragging ? 'unset' : position.x,
        gridRow: isDragging ? 'unset' : position.y,
        ...transformStyle,
      }}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      {...attributes}
      {...(editMode ? listeners : {})}
      role="button"
      tabIndex={0}
      aria-label={`${app.title} - ${app.description}${editMode ? ' (draggable)' : ''}`}
      aria-describedby={editMode ? `${app.id}-edit-help` : undefined}
    >
      {/* Hidden help text for screen readers in edit mode */}
      {editMode && (
        <div 
          id={`${app.id}-edit-help`}
          className="sr-only"
        >
          Drag to reposition this app icon. Use arrow keys or drag with mouse to move.
        </div>
      )}

      {/* Icon Container */}
      <div
        className={`
          relative flex items-center justify-center rounded-2xl
          backdrop-blur-sm border border-white/20
          transition-all duration-300 ease-out
          shadow-lg hover:shadow-xl
          ${config.container}
          ${editMode ? 'border-white/40' : 'hover:border-white/30'}
          ${isDragging ? 'shadow-2xl border-blue-400/60 bg-white/10' : ''}
        `}
        style={{
          background: isDragging
            ? `linear-gradient(135deg, ${app.color}FF 0%, ${app.color}CC 50%, ${app.color}99 100%), rgba(255, 255, 255, 0.2)`
            : `linear-gradient(135deg, ${app.color}CC 0%, ${app.color}AA 50%, ${app.color}88 100%), rgba(255, 255, 255, 0.1)`,
          boxShadow: isDragging
            ? '0 20px 40px rgba(59, 130, 246, 0.4), 0 8px 32px rgba(0, 0, 0, 0.2)'
            : '0 8px 32px rgba(0, 0, 0, 0.12), 0 2px 8px rgba(0, 0, 0, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.2)',
        }}
      >
        {/* Icon */}
        <IconComponent
          className={`${config.icon} text-white drop-shadow-sm transition-all duration-200 ${isDragging ? 'scale-110' : ''}`}
          strokeWidth={1.5}
          aria-hidden="true"
        />

        {/* Glow effect on hover */}
        <div
          className={`
            absolute inset-0 rounded-2xl opacity-0 
            transition-opacity duration-300
            ${!editMode && !isDragging && 'hover:opacity-30'}
          `}
          style={{
            background: `radial-gradient(circle, ${app.color}66 0%, transparent 70%)`,
            filter: 'blur(4px)',
          }}
          aria-hidden="true"
        />

        {/* Edit mode indicator */}
        {editMode && !isDragging && (
          <div 
            className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full border border-white shadow-sm animate-pulse" 
            aria-hidden="true"
          />
        )}

        {/* Drag indicator */}
        {isDragging && (
          <div 
            className="absolute inset-0 rounded-2xl border-2 border-blue-400 bg-blue-400/10 animate-pulse" 
            aria-hidden="true"
          />
        )}
      </div>

      {/* App Label */}
      <span
        className={`
          ${config.text} font-medium text-white text-center drop-shadow-sm 
          leading-tight transition-all duration-200 max-w-20 md:max-w-24 lg:max-w-28
          ${isDragging ? 'text-blue-200 scale-110' : ''}
          ${app.title.length > 8 ? 'text-xs' : 'text-sm'}
        `}
        style={{
          textShadow: '0 1px 2px rgba(0, 0, 0, 0.8)',
          wordWrap: 'break-word',
          hyphens: 'auto',
          lineHeight: '1.1',
        }}
        title={app.title}
      >
        {app.title}
      </span>

      {/* Focus indicator for keyboard navigation */}
      <div 
        className="absolute inset-0 rounded-2xl border-2 border-transparent focus-within:border-blue-400 focus-within:shadow-lg focus-within:shadow-blue-400/25 transition-all duration-200"
        aria-hidden="true"
      />
    </div>
  );
};

export default DraggableAppIcon;