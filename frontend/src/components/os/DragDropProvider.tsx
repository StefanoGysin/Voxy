'use client';

import type React from 'react';
import { useState, useCallback, useEffect, useMemo } from 'react';
import {
  DndContext,
  DragOverlay,
  closestCenter,
  rectIntersection,
  pointerWithin,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragStartEvent,
  type DragEndEvent,
  type DragOverEvent,
  type UniqueIdentifier,
  type CollisionDetection,
} from '@dnd-kit/core';
import {
  restrictToWindowEdges,
  restrictToParentElement,
} from '@dnd-kit/modifiers';
import {
  sortableKeyboardCoordinates,
} from '@dnd-kit/sortable';
import { useOSStore } from '@/lib/store/os-store';
import { 
  createContainerAwareGridModifier, 
  createSmartCollisionModifier,
  createDropZoneModifier,
  createDynamicProtectionModifier,
  createProfessionalEasingModifier 
} from './GridModifiers';
import { useScreenReaderAnnouncements, getDragDropMessages } from './hooks/useScreenReaderAnnouncements';
import { useResponsiveGrid } from './hooks/useResponsiveGrid';


interface DragDropProviderProps {
  children: React.ReactNode;
  gridRef?: React.RefObject<HTMLDivElement | null>;
  isPositionProtected?: (pos: { x: number; y: number }) => boolean;
  enableResponsive?: boolean;
  onDragStart?: (event: DragStartEvent) => void;
  onDragEnd?: (event: DragEndEvent) => void;
  onDragOver?: (event: DragOverEvent) => void;
}

const DragDropProvider: React.FC<DragDropProviderProps> = ({ 
  children, 
  gridRef,
  isPositionProtected,
  enableResponsive = true,
  onDragStart,
  onDragEnd,
  onDragOver 
}) => {
  const [activeId, setActiveId] = useState<UniqueIdentifier | null>(null);
  const [, setOverId] = useState<UniqueIdentifier | null>(null);
  const [dragStartPosition, setDragStartPosition] = useState<{ x: number; y: number } | null>(null);
  const { gridSize, apps, iconPositions, updateIconPosition, editMode } = useOSStore();
  const { announce } = useScreenReaderAnnouncements();
  
  // Responsive drag configuration
  const { getDragSensitivity } = useResponsiveGrid();
  
  // Professional collision detection with swap capability
  const customCollisionDetection: CollisionDetection = useCallback(
    (args) => {
      // Start with pointer detection for immediate feedback
      const pointerCollisions = pointerWithin(args);
      
      if (pointerCollisions.length > 0) {
        return pointerCollisions;
      }
      
      // Fallback to rectangle intersection for better collision detection
      const intersectionCollisions = rectIntersection(args);
      
      if (intersectionCollisions.length > 0) {
        // Sort by overlap area to get the best match
        return intersectionCollisions.sort((a, b) => {
          const aData = a.data?.droppableContainer?.data?.current;
          const bData = b.data?.droppableContainer?.data?.current;
          
          if (aData?.type === 'grid-cell' && bData?.type === 'grid-cell') {
            // Prefer cells closer to the center of the drag
            return 0; // Keep original order from rectIntersection
          }
          
          return 0;
        });
      }
      
      // Final fallback to closest center
      return closestCenter(args);
    },
    []
  );
  
  // Debounced position update to prevent rapid state changes
  const [pendingUpdate, setPendingUpdate] = useState<{
    id: string;
    x: number;
    y: number;
  } | null>(null);
  
  useEffect(() => {
    if (pendingUpdate) {
      const timeoutId = setTimeout(() => {
        updateIconPosition(pendingUpdate.id, pendingUpdate.x, pendingUpdate.y);
        setPendingUpdate(null);
      }, 50); // Reduced debounce to 50ms for better responsiveness
      
      return () => clearTimeout(timeoutId);
    }
  }, [pendingUpdate, updateIconPosition]);

  // Configure sensors for different input methods with responsive settings
  const sensors = useSensors(
    // Responsive pointer sensor optimized for current device
    useSensor(PointerSensor, enableResponsive ? {
      ...getDragSensitivity().pointerActivationConstraint,
      activationConstraint: getDragSensitivity().activationConstraint,
    } : {
      activationConstraint: { distance: 5 },
    }),
    // Keyboard sensor for accessibility
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  // Calculate grid dimensions
  const getGridDimensions = useCallback(() => {
    if (!gridRef?.current) return { cellWidth: 80, cellHeight: 100 };
    
    const rect = gridRef.current.getBoundingClientRect();
    const cellWidth = rect.width / gridSize.cols;
    const cellHeight = rect.height / gridSize.rows;
    
    return { cellWidth, cellHeight };
  }, [gridRef, gridSize]);

  // Handle drag start
  const handleDragStart = useCallback((event: DragStartEvent) => {
    if (!editMode) {
      console.log('🚫 Drag start blocked - Edit mode disabled');
      return;
    }
    
    const app = apps.find(a => a.id === event.active.id);
    const currentPos = iconPositions.find(pos => pos.id === event.active.id);
    
    console.log('🎯 Drag Start:', {
      app: app?.title,
      position: currentPos,
      editMode,
      activeId: event.active.id
    });
    
    if (app && currentPos) {
      setActiveId(event.active.id);
      setDragStartPosition({ x: currentPos.x, y: currentPos.y });
      
      // Announce drag start to screen readers
      announce(getDragDropMessages.dragStart(app.title, currentPos));
      
      // Haptic feedback on supported devices
      if ('navigator' in window && 'vibrate' in navigator) {
        navigator.vibrate(50);
      }
    }
    
    onDragStart?.(event);
  }, [editMode, apps, iconPositions, announce, onDragStart]);

  // Handle drag over (for visual feedback and accessibility)
  const handleDragOver = useCallback((event: DragOverEvent) => {
    if (!editMode || !activeId) return;
    
    setOverId(event.over?.id || null);
    
    // Announce position changes for screen readers
    if (event.over?.data.current?.type === 'grid-cell') {
      const app = apps.find(a => a.id === activeId);
      const position = event.over.data.current.position;
      const isOccupied = event.over.data.current.isOccupied;
      
      if (app && position) {
        announce(getDragDropMessages.dragMove(app.title, position, !isOccupied));
      }
    }
    
    onDragOver?.(event);
  }, [editMode, activeId, apps, announce, onDragOver]);

  // Handle drag end with position update and accessibility
  const handleDragEnd = useCallback((event: DragEndEvent) => {
    const { active, over } = event;
    const app = apps.find(a => a.id === active.id);
    const startPos = dragStartPosition;
    
    if (!editMode || !active || !app || !startPos) {
      setActiveId(null);
      setOverId(null);
      setDragStartPosition(null);
      return;
    }

    let finalPosition = startPos;
    let success = false;

    // Extract position from droppable data or calculate from coordinates
    let newPosition: { x: number; y: number } | null = null;
    
    if (over?.data.current?.type === 'grid-cell') {
      // Dropped on grid cell - use cell position
      newPosition = over.data.current.position;
    } else if (over && gridRef?.current) {
      // Dropped on grid area - calculate position from coordinates
      const rect = gridRef.current.getBoundingClientRect();
      const { cellWidth, cellHeight } = getGridDimensions();
      
      const dropX = (active.rect.current.translated?.left || 0) - rect.left;
      const dropY = (active.rect.current.translated?.top || 0) - rect.top;
      
      newPosition = {
        x: Math.max(1, Math.min(Math.round(dropX / cellWidth) + 1, gridSize.cols)),
        y: Math.max(1, Math.min(Math.round(dropY / cellHeight) + 1, gridSize.rows)) // Allow all rows
      };
    }

    // Update position if valid and different from current
    if (newPosition) {
      const currentPos = iconPositions.find(pos => pos.id === active.id);
      const isNewPosition = !currentPos || 
        currentPos.x !== newPosition.x || 
        currentPos.y !== newPosition.y;
        
      if (isNewPosition) {
        // Check for collisions and handle swapping
        const occupiedIcon = iconPositions.find(
          pos => pos.id !== active.id && 
          pos.x === newPosition!.x && 
          pos.y === newPosition!.y
        );
        
        if (!occupiedIcon) {
          // Empty position - direct placement
          console.log('✅ Position Update:', {
            app: app?.title,
            from: startPos,
            to: newPosition,
            success: true
          });
          
          // Use debounced update for smoother performance
          setPendingUpdate({
            id: active.id as string,
            x: newPosition.x,
            y: newPosition.y
          });
          finalPosition = newPosition;
          success = true;
          
          // Success haptic feedback
          if ('navigator' in window && 'vibrate' in navigator) {
            navigator.vibrate([30, 10, 30]);
          }
        } else {
          // Smart swapping - move the occupying icon to the dragged icon's original position
          const currentPos = iconPositions.find(pos => pos.id === active.id);
          
          if (currentPos && (currentPos.x !== newPosition.x || currentPos.y !== newPosition.y)) {
            console.log('🔄 Smart Swap:', {
              draggedApp: app?.title,
              from: currentPos,
              to: newPosition,
              swappedIcon: occupiedIcon.id,
              swapTo: currentPos
            });
            
            // Perform atomic swap - update both positions
            updateIconPosition(active.id as string, newPosition.x, newPosition.y);
            updateIconPosition(occupiedIcon.id, currentPos.x, currentPos.y);
            
            finalPosition = newPosition;
            success = true;
            
            // Special swap haptic feedback
            if ('navigator' in window && 'vibrate' in navigator) {
              navigator.vibrate([40, 20, 40, 20, 60]); // Swap pattern
            }
            
            // Announce swap to screen readers
            const swappedApp = apps.find(a => a.id === occupiedIcon.id);
            if (swappedApp) {
              announce(`${app.title} and ${swappedApp.title} have swapped positions`);
            }
          } else {
            console.log('❌ Invalid swap attempt:', {
              app: app?.title,
              reason: 'Same position or no current position found'
            });
          }
        }
      } else {
        // Same position - consider it successful
        success = true;
      }
    }
    
    // Announce the result to screen readers
    announce(getDragDropMessages.dragEnd(app.title, startPos, finalPosition, success));
    
    setActiveId(null);
    setOverId(null);
    setDragStartPosition(null);
    onDragEnd?.(event);
  }, [editMode, apps, dragStartPosition, gridRef, getGridDimensions, gridSize, iconPositions, setPendingUpdate, announce, onDragEnd, updateIconPosition]);

  
  // Professional modifier stack (memoized for performance)
  const modifiers = useMemo(() => {
    const baseModifiers = [
      restrictToWindowEdges,
      restrictToParentElement,
      createProfessionalEasingModifier(0.92), // Smooth professional easing
      createDropZoneModifier(gridSize, isPositionProtected),
    ];
    
    // Only add grid-specific modifiers if gridRef is available
    if (gridRef) {
      baseModifiers.push(
        createContainerAwareGridModifier(gridRef, gridSize), // Precise container calculations
        createSmartCollisionModifier(
          iconPositions.map(pos => ({ x: pos.x, y: pos.y, id: pos.id })),
          activeId as string,
          gridSize,
          true // Enable smart swapping
        )
      );
    }
    
    // Add dynamic protection modifier if available
    if (isPositionProtected) {
      baseModifiers.push(
        createDynamicProtectionModifier(isPositionProtected, gridSize)
      );
    }
    
    return baseModifiers;
  }, [gridRef, gridSize, iconPositions, activeId, isPositionProtected]);
  
  // Memoize active app to prevent unnecessary re-renders
  const activeApp = useMemo(() => 
    activeId ? apps.find(app => app.id === activeId) : null, 
    [activeId, apps]
  );

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={customCollisionDetection}
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragEnd={handleDragEnd}
      modifiers={modifiers}
    >
      {children}
      
      {/* Drag Overlay for active item */}
      <DragOverlay
        modifiers={[restrictToWindowEdges]}
        style={{
          cursor: editMode ? 'grabbing' : 'default',
        }}
      >
        {activeApp && (
          <div className="opacity-90 scale-110 transform rotate-3 shadow-2xl">
            <div 
              className="w-20 h-20 rounded-2xl backdrop-blur-sm border border-white/40 flex items-center justify-center"
              style={{
                background: `linear-gradient(135deg, ${activeApp.color}FF 0%, ${activeApp.color}CC 50%, ${activeApp.color}99 100%)`,
              }}
            >
              <div className="text-white text-2xl">📱</div>
            </div>
          </div>
        )}
      </DragOverlay>
    </DndContext>
  );
};

export default DragDropProvider;