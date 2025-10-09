'use client';

import { useOSStore } from '@/lib/store/os-store';
import { Edit3, RotateCcw } from 'lucide-react';
import type React from 'react';
import { useEffect, useRef, useState } from 'react';
import DateTimeWidget from './DateTimeWidget';
import DragDropProvider from './DragDropProvider';
import DraggableAppIcon from './DraggableAppIcon';
import DroppableGridCell from './DroppableGridCell';
import WallpaperSystem from './WallpaperSystem';
import { ToastSystem, showToast } from './ToastSystem';
import { HelpOverlay } from './HelpOverlay';
import { useProtectedAreas } from './hooks/useProtectedAreas';
import { useResponsiveGrid } from './hooks/useResponsiveGrid';

interface EnhancedOSDashboardProps {
  className?: string;
}

const EnhancedOSDashboard: React.FC<EnhancedOSDashboardProps> = ({
  className = '',
}) => {
  const gridRef = useRef<HTMLDivElement>(null);
  const dateTimeRef = useRef<HTMLDivElement>(null);
  const [mounted, setMounted] = useState(false);

  // Store state
  const {
    apps,
    iconPositions,
    editMode,
    gridSize,
    toggleEditMode,
    resetLayout,
    nextWallpaper,
    toggleHelpOverlay,
    updateGridSize, // Add this to store
  } = useOSStore();

  // Responsive grid system
  const {
    getGridConfig,
    currentBreakpoint,
    getDeviceType,
  } = useResponsiveGrid();

  // Protected areas management (dynamic)
  const {
    isPositionProtected,
  } = useProtectedAreas(gridRef, gridSize, dateTimeRef);

  // Update grid size based on responsive breakpoint
  useEffect(() => {
    const config = getGridConfig();
    
    // Only update if grid size actually changed
    if (gridSize.rows !== config.rows || gridSize.cols !== config.cols) {
      console.log('📐 Responsive Grid Update:', {
        from: gridSize,
        to: { rows: config.rows, cols: config.cols },
        breakpoint: currentBreakpoint?.name,
        device: getDeviceType(),
      });
      
      // Update store with new grid configuration
      if (updateGridSize) {
        updateGridSize(config.rows, config.cols);
      }
    }
  }, [getGridConfig, gridSize, currentBreakpoint, getDeviceType, updateGridSize]);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Keyboard shortcuts - Fixed to work without Ctrl/Cmd modifiers
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Enhanced context detection - don't interfere with interactive elements
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement ||
        e.target instanceof HTMLSelectElement ||
        (e.target as HTMLElement)?.contentEditable === 'true' ||
        (e.target as Element)?.closest('[role="dialog"]') ||
        (e.target as Element)?.closest('.modal') ||
        (e.target as Element)?.closest('[data-chat-input]')
      ) {
        return;
      }

      // Simple shortcuts without modifiers (as documented)
      switch (e.key.toLowerCase()) {
        case 'e':
          e.preventDefault();
          toggleEditMode();
          showToast(
            `Edit mode ${editMode ? 'disabled' : 'enabled'}`, 
            'success'
          );
          break;
          
        case 'w':
          e.preventDefault();
          nextWallpaper();
          showToast('Wallpaper changed', 'info');
          break;
          
        case 'r':
          if (editMode) { // Only works in edit mode
            e.preventDefault();
            resetLayout();
            showToast('Layout reset', 'success');
          } else {
            showToast('Layout reset only works in edit mode. Press E first.', 'warning');
          }
          break;
          
        case 'h':
          e.preventDefault();
          toggleHelpOverlay();
          break;
          
        case 'escape':
          if (editMode) {
            toggleEditMode();
            showToast('Edit mode disabled', 'info');
          }
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [editMode, toggleEditMode, resetLayout, nextWallpaper, toggleHelpOverlay]);


  // Get enabled apps
  const enabledApps = apps.filter(app => app.isEnabled);

  // Get app position
  const getAppPosition = (appId: string) => {
    const position = iconPositions.find(pos => pos.id === appId);
    return position ? { x: position.x, y: position.y } : { x: 1, y: 3 };
  };



  if (!mounted) {
    return (
      <WallpaperSystem className={className}>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-white text-xl">Loading VOXY OS...</div>
        </div>
      </WallpaperSystem>
    );
  }

  return (
    <DragDropProvider 
      gridRef={gridRef}
      isPositionProtected={isPositionProtected}
      enableResponsive={true}
      onDragEnd={() => {
        // Optional: Add success feedback
        if ('navigator' in window && 'vibrate' in navigator) {
          navigator.vibrate([30, 10, 30]);
        }
      }}
    >
      <WallpaperSystem className={className}>
        <div className="min-h-screen p-4 md:p-6 lg:p-8 relative">
          {/* Top Controls */}
          <div className="absolute top-4 right-4 z-20 flex gap-2">
            {/* Edit Mode Toggle */}
            <button
              type="button"
              onClick={toggleEditMode}
              className={`
                p-3 rounded-full backdrop-blur-md border border-white/20
                transition-all duration-300 shadow-lg
                ${
                  editMode
                    ? 'bg-blue-500/30 border-blue-400/50 text-blue-100 shadow-blue-500/30'
                    : 'bg-black/20 hover:bg-black/30 text-white/80 hover:text-white'
                }
              `}
              aria-label={
                editMode ? 'Exit edit mode' : 'Enter edit mode'
              }
            >
              <Edit3 className="w-5 h-5" />
            </button>

            {/* Reset Layout (only in edit mode) */}
            {editMode && (
              <button
                type="button"
                onClick={resetLayout}
                className="
                  p-3 rounded-full backdrop-blur-md border border-white/20
                  bg-red-500/30 border-red-400/50 text-red-100
                  hover:bg-red-500/40 transition-all duration-300 shadow-lg shadow-red-500/30
                "
                aria-label="Reset layout"
              >
                <RotateCcw className="w-5 h-5" />
              </button>
            )}
          </div>

          {/* Enhanced Help text in edit mode */}
          {editMode && (
            <div className="absolute top-20 right-4 z-20 max-w-xs">
              <div className="bg-black/60 backdrop-blur-md rounded-lg p-4 border border-white/20 text-white/90 text-sm shadow-xl">
                <p className="font-medium mb-2 text-blue-200">
                  🎯 Edit Mode Active
                </p>
                <div className="space-y-1 text-xs text-white/70">
                  <p>• Drag icons to reorganize</p>
                  <p>• Visual grid for positioning</p>
                  <p>
                    • <kbd className="bg-white/20 px-1 rounded">Esc</kbd> to
                    exit
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Main Grid Container */}
          <div
            ref={gridRef}
            data-grid-container
            className={`
              grid w-full h-screen relative
              ${editMode ? 'edit-mode-active' : ''}
            `}
            style={{
              gridTemplateRows: `repeat(${gridSize.rows}, minmax(0, 1fr))`,
              gridTemplateColumns: `repeat(${gridSize.cols}, minmax(0, 1fr))`,
              gap: getGridConfig().gap,
              padding: getGridConfig().padding,
            }}
            role="grid"
            aria-label={`App icons grid (${gridSize.cols} columns, ${gridSize.rows} rows)`}
          >
            {/* Grid Cells with Drop Zones */}
            {Array.from({ length: gridSize.rows }, (_, row) =>
              Array.from({ length: gridSize.cols }, (_, col) => {
                const cellId = `cell-${col + 1}-${row + 1}`;
                const gridPos = { x: col + 1, y: row + 1 };
                const isOccupied = enabledApps.some(app => {
                  const pos = getAppPosition(app.id);
                  return pos.x === gridPos.x && pos.y === gridPos.y;
                });
                const isProtected = isPositionProtected(gridPos);
                
                return (
                  <DroppableGridCell
                    key={cellId}
                    id={cellId}
                    row={gridPos.y}
                    col={gridPos.x}
                    gridSize={gridSize}
                    isEditMode={editMode}
                    isOccupied={isOccupied}
                    isProtected={isProtected}
                  />
                );
              })
            )}

            {/* DateTime Widget */}
            <div
              ref={dateTimeRef}
              className="flex items-center justify-center z-10"
              style={{
                gridColumn: '1 / -1',
                gridRow: '1 / 3',
              }}
            >
              <DateTimeWidget />
            </div>

            {/* Draggable App Icons */}
            {enabledApps.map(app => {
              const position = getAppPosition(app.id);
              
              return (
                <DraggableAppIcon
                  key={app.id}
                  app={app}
                  position={position}
                  size={getGridConfig().iconSize}
                />
              );
            })}
          </div>

          {/* Bottom Gradient for Better Icon Visibility */}
          <div
            className="fixed bottom-0 left-0 right-0 h-24 pointer-events-none"
            style={{
              background: 'linear-gradient(transparent, rgba(0,0,0,0.4))',
            }}
          />

          {/* Quick Keyboard Shortcuts Hint */}
          <div className="absolute bottom-4 left-4 text-white/60 text-xs space-y-1">
            <div className="flex items-center gap-2">
              <kbd className="bg-white/20 px-1 rounded text-xs">H</kbd>
              <span>Show Keyboard Shortcuts</span>
            </div>
            <div className="flex items-center gap-2">
              <kbd className="bg-white/20 px-1 rounded text-xs">E</kbd>
              <span>Edit Mode</span>
            </div>
            <div className="flex items-center gap-2">
              <kbd className="bg-white/20 px-1 rounded text-xs">W</kbd>
              <span>Next Wallpaper</span>
            </div>
            {editMode && (
              <div className="flex items-center gap-2">
                <kbd className="bg-white/20 px-1 rounded text-xs">R</kbd>
                <span>Reset Layout</span>
              </div>
            )}
          </div>
        </div>
      </WallpaperSystem>
      
      {/* Toast System for keyboard shortcut feedback */}
      <ToastSystem />
      
      {/* Help Overlay for keyboard shortcuts */}
      <HelpOverlay />
    </DragDropProvider>
  );
};

export default EnhancedOSDashboard;