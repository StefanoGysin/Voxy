'use client';

import { useDroppable } from '@dnd-kit/core';
import type React from 'react';
import { useMemo } from 'react';

interface DroppableGridCellProps {
  id: string;
  row: number;
  col: number;
  gridSize: { rows: number; cols: number };
  isEditMode: boolean;
  isOccupied: boolean;
  isPreview?: boolean;
  isProtected?: boolean; // NEW: Dynamic protection vs hardcoded
  children?: React.ReactNode;
}

const DroppableGridCell: React.FC<DroppableGridCellProps> = ({
  id,
  row,
  col,
  isEditMode,
  isOccupied,
  isPreview = false,
  isProtected = false,
  children,
}) => {
  const {
    isOver,
    setNodeRef,
  } = useDroppable({
    id,
    disabled: !isEditMode || isProtected, // NEW: Dynamic protection
    data: {
      type: 'grid-cell',
      position: { x: col, y: row },
      isOccupied,
      isProtected,
    },
  });

  // Calculate cell position styles
  const cellStyle = useMemo(() => ({
    gridColumn: col,
    gridRow: row,
    position: 'relative' as const,
  }), [col, row]);

  // Determine cell appearance based on state
  const cellClassName = useMemo(() => {
    const baseClasses = 'transition-all duration-200 rounded-lg';
    
    if (!isEditMode) {
      return `${baseClasses} transparent`;
    }

    // Edit mode styling
    let classes = `${baseClasses} border border-white/10`;

    if (isProtected) {
      // Protected area - no drop allowed (dynamic)
      classes += ' bg-red-500/10 border-red-400/30';
    } else if (isOver && !isOccupied) {
      // Valid drop target
      classes += ' bg-green-400/20 border-green-400/50 shadow-lg';
    } else if (isOver && isOccupied) {
      // Invalid drop (occupied)
      classes += ' bg-red-400/20 border-red-400/50 shadow-lg';
    } else if (isPreview) {
      // Preview position
      classes += ' bg-blue-400/20 border-blue-400/50 shadow-md';
    } else if (isOccupied) {
      // Occupied cell
      classes += ' bg-white/5 border-white/15';
    } else {
      // Empty cell
      classes += ' hover:bg-white/5 border-white/10';
    }

    return classes;
  }, [isEditMode, isOver, isOccupied, isPreview, isProtected]);

  // Cell content based on state
  const cellContent = useMemo(() => {
    if (!isEditMode) return null;

    // Show grid coordinates in development/debug mode
    const showDebug = process.env.NODE_ENV === 'development';
    
    return (
      <>
        {/* Hidden accessibility helper */}
        {isEditMode && !isProtected && (
          <div 
            id={`grid-help-${col}-${row}`}
            className="sr-only"
          >
            {isOccupied 
              ? `This grid cell is occupied. Drop here to swap positions.`
              : `This is an empty grid cell. Drop an app icon here to place it at column ${col}, row ${row}.`
            }
          </div>
        )}
        
        {/* Grid coordinates for debugging */}
        {showDebug && (
          <div className="absolute top-1 left-1 text-xs text-white/40 font-mono">
            {col},{row}
          </div>
        )}
        
        {/* Drop indicators */}
        {isOver && (
          <div className="absolute inset-0 flex items-center justify-center">
            {isOccupied ? (
              <div className="w-6 h-6 text-red-400 opacity-60" role="img" aria-label="Invalid drop zone">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M15 9l-6 6"/>
                  <path d="M9 9l6 6"/>
                </svg>
              </div>
            ) : (
              <div className="w-6 h-6 text-green-400 opacity-60" role="img" aria-label="Valid drop zone">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M9 12l2 2l4-4"/>
                </svg>
              </div>
            )}
          </div>
        )}

        {/* Cell position indicator */}
        {!isOccupied && !isOver && !isProtected && (
          <div className="absolute inset-0 flex items-center justify-center opacity-0 hover:opacity-30 transition-opacity duration-200">
            <div className="w-2 h-2 bg-white/40 rounded-full" aria-hidden="true"></div>
          </div>
        )}
        
        {/* Protected area indicator */}
        {isProtected && isEditMode && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-4 h-4 text-red-400/60" role="img" aria-label="Protected area">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                <path d="M9 12l2 2l4-4"/>
              </svg>
            </div>
          </div>
        )}
      </>
    );
  }, [isEditMode, isOver, isOccupied, isProtected, row, col]);

  return (
    <div
      ref={setNodeRef}
      className={cellClassName}
      style={cellStyle}
      data-grid-cell={`${col}-${row}`}
      data-occupied={isOccupied}
      data-droppable={isEditMode && !isProtected}
      aria-label={isEditMode ? `Grid cell column ${col}, row ${row}${isOccupied ? ' (occupied)' : ' (available)'}${isProtected ? ' (protected area)' : ''}` : undefined}
      role={isEditMode ? 'gridcell' : undefined}
      aria-describedby={isEditMode && !isProtected ? `grid-help-${col}-${row}` : undefined}
      tabIndex={isEditMode && !isProtected && !isOccupied ? 0 : -1}
    >
      {cellContent}
      {children}
    </div>
  );
};

export default DroppableGridCell;