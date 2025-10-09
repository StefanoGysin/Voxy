import type { Modifier } from '@dnd-kit/core';

/**
 * Professional grid positioning with container-aware calculations
 */
export const createContainerAwareGridModifier = (
  gridRef: React.RefObject<HTMLDivElement | null>,
  gridSize: { rows: number; cols: number }
): Modifier => {
  return ({ transform, over, active }) => {
    if (!gridRef?.current || !over || !active) return transform;

    const rect = gridRef.current.getBoundingClientRect();
    const cellWidth = rect.width / gridSize.cols;
    const cellHeight = rect.height / gridSize.rows;
    
    // High-precision snap calculation with proper centering
    const targetX = Math.round(transform.x / cellWidth) * cellWidth;
    const targetY = Math.round(transform.y / cellHeight) * cellHeight;

    // Ensure we stay within precise container bounds
    const clampedX = Math.max(0, Math.min(targetX, rect.width - cellWidth));
    const clampedY = Math.max(0, Math.min(targetY, rect.height - cellHeight));

    return {
      ...transform,
      x: clampedX,
      y: clampedY,
    };
  };
};

/**
 * Smart grid snap modifier that calculates grid positions based on container dimensions
 */
export const createSmartGridModifier = (
  gridRef: React.RefObject<HTMLDivElement | null>,
  gridSize: { rows: number; cols: number }
): Modifier => {
  return ({ transform, over, active }) => {
    if (!gridRef?.current || !over || !active) return transform;

    const rect = gridRef.current.getBoundingClientRect();
    const cellWidth = rect.width / gridSize.cols;
    const cellHeight = rect.height / gridSize.rows;
    
    // More precise snap calculation - snap to cell centers
    const targetX = Math.round(transform.x / cellWidth) * cellWidth + (cellWidth / 2);
    const targetY = Math.round(transform.y / cellHeight) * cellHeight + (cellHeight / 2);

    // Ensure we stay within grid bounds with proper margins
    const clampedX = Math.max(cellWidth / 2, Math.min(targetX, rect.width - (cellWidth / 2)));
    const clampedY = Math.max(
      cellHeight / 2, // Allow movement to all rows (removed row 3 restriction)
      Math.min(targetY, rect.height - (cellHeight / 2))
    );

    return {
      ...transform,
      x: clampedX,
      y: clampedY,
    };
  };
};

/**
 * Advanced collision detection with smart swapping capability
 */
export const createSmartCollisionModifier = (
  occupiedPositions: Array<{ x: number; y: number; id: string }>,
  activeId: string | null,
  gridSize: { rows: number; cols: number },
  allowSwapping: boolean = true
): Modifier => {
  return ({ transform, over, active }) => {
    if (!over || !active || !activeId) return transform;

    // Precise cell size calculation based on actual container
    const container = document.querySelector('[data-grid-container]') as HTMLElement;
    let cellWidth = window.innerWidth / gridSize.cols * 0.8;
    let cellHeight = window.innerHeight / gridSize.rows * 0.8;
    
    if (container) {
      const rect = container.getBoundingClientRect();
      cellWidth = rect.width / gridSize.cols;
      cellHeight = rect.height / gridSize.rows;
    }

    // High-precision grid position calculation
    const gridX = Math.round(transform.x / cellWidth) + 1;
    const gridY = Math.round(transform.y / cellHeight) + 1;

    // Ensure within bounds
    const clampedX = Math.max(1, Math.min(gridX, gridSize.cols));
    const clampedY = Math.max(1, Math.min(gridY, gridSize.rows));

    // Check if position is occupied by another icon
    const occupiedIcon = occupiedPositions.find(
      pos => pos.x === clampedX && pos.y === clampedY && pos.id !== activeId
    );

    if (occupiedIcon && allowSwapping) {
      // Allow overlap for swapping - the swap logic is handled in DragDropProvider
      return {
        ...transform,
        x: (clampedX - 1) * cellWidth + cellWidth / 2,
        y: (clampedY - 1) * cellHeight + cellHeight / 2,
      };
    } else if (occupiedIcon && !allowSwapping) {
      // Find nearest available position
      const nearestPosition = findNearestAvailablePosition(
        { x: clampedX, y: clampedY },
        occupiedPositions,
        activeId,
        gridSize
      );

      if (nearestPosition) {
        return {
          ...transform,
          x: (nearestPosition.x - 1) * cellWidth + cellWidth / 2,
          y: (nearestPosition.y - 1) * cellHeight + cellHeight / 2,
        };
      }
    }

    // Snap to grid position
    return {
      ...transform,
      x: (clampedX - 1) * cellWidth + cellWidth / 2,
      y: (clampedY - 1) * cellHeight + cellHeight / 2,
    };
  };
};

/**
 * Legacy collision avoidance modifier (backward compatibility)
 */
export const createCollisionAvoidanceModifier = (
  occupiedPositions: Array<{ x: number; y: number; id: string }>,
  activeId: string | null,
  gridSize: { rows: number; cols: number }
): Modifier => {
  return createSmartCollisionModifier(occupiedPositions, activeId, gridSize, false);
};

/**
 * Enhanced nearest position finder with intelligent placement
 */
const findNearestAvailablePosition = (
  targetPos: { x: number; y: number },
  occupiedPositions: Array<{ x: number; y: number; id: string }>,
  activeId: string,
  gridSize: { rows: number; cols: number },
  protectedChecker?: (pos: { x: number; y: number }) => boolean
): { x: number; y: number } | null => {
  const maxDistance = Math.max(gridSize.rows, gridSize.cols);

  // Priority search pattern: nearest first, then expanding spiral
  for (let distance = 1; distance <= maxDistance; distance++) {
    const candidates: Array<{ x: number; y: number; score: number }> = [];
    
    // Generate candidates in expanding pattern
    for (let dx = -distance; dx <= distance; dx++) {
      for (let dy = -distance; dy <= distance; dy++) {
        if (Math.abs(dx) !== distance && Math.abs(dy) !== distance) continue;

        const x = targetPos.x + dx;
        const y = targetPos.y + dy;

        // Check bounds
        if (x < 1 || x > gridSize.cols || y < 1 || y > gridSize.rows) continue;

        // Check if position is available
        const isOccupied = occupiedPositions.some(
          pos => pos.x === x && pos.y === y && pos.id !== activeId
        );
        
        const isProtected = protectedChecker ? protectedChecker({ x, y }) : false;
        
        if (!isOccupied && !isProtected) {
          // Score based on distance and preferential placement
          const distanceScore = Math.sqrt(dx * dx + dy * dy);
          const rowPreference = y > 2 ? 0 : 1; // Slight preference for lower rows
          const score = distanceScore + rowPreference;
          
          candidates.push({ x, y, score });
        }
      }
    }
    
    // Return best candidate (lowest score = closest + preferred)
    if (candidates.length > 0) {
      candidates.sort((a, b) => a.score - b.score);
      return { x: candidates[0].x, y: candidates[0].y };
    }
  }

  return null;
};

/**
 * Professional easing modifier with natural movement
 */
export const createProfessionalEasingModifier = (
  easingStrength: number = 0.92
): Modifier => {
  return ({ transform }) => {
    // Cubic-bezier inspired easing for professional feel
    const easeOutCubic = (t: number): number => {
      return 1 - Math.pow(1 - t, 3);
    };
    
    // Apply sophisticated easing
    const dampingFactor = easeOutCubic(easingStrength);
    
    return {
      ...transform,
      x: transform.x * dampingFactor,
      y: transform.y * dampingFactor,
    };
  };
};

/**
 * Legacy smooth transition (backward compatibility)
 */
export const createSmoothTransitionModifier = (): Modifier => {
  return createProfessionalEasingModifier(0.95);
};

/**
 * Dynamic protected area modifier - replaces hardcoded restrictions
 */
export const createDynamicProtectionModifier = (
  isPositionProtected: (pos: { x: number; y: number }) => boolean,
  gridSize: { rows: number; cols: number }
): Modifier => {
  return ({ transform, over, active }) => {
    if (!over || !active) return transform;
    
    // Calculate grid position from transform
    const cellWidth = window.innerWidth / gridSize.cols * 0.8;
    const cellHeight = window.innerHeight / gridSize.rows * 0.8;
    
    const gridX = Math.round((transform.x - cellWidth / 2) / cellWidth) + 1;
    const gridY = Math.round((transform.y - cellHeight / 2) / cellHeight) + 1;
    
    // Check if position is dynamically protected
    if (isPositionProtected({ x: gridX, y: gridY })) {
      // Return original transform to prevent movement into protected area
      return {
        ...transform,
        x: 0,
        y: 0,
      };
    }
    
    return transform;
  };
};

/**
 * Advanced drop zone modifier with intelligent boundaries
 */
export const createDropZoneModifier = (
  gridSize: { rows: number; cols: number },
  isPositionProtected?: (pos: { x: number; y: number }) => boolean
): Modifier => {
  return ({ transform, over, active }) => {
    // Precise container-based calculations
    const container = document.querySelector('[data-grid-container]') as HTMLElement;
    let cellWidth = window.innerWidth / gridSize.cols * 0.8;
    let cellHeight = window.innerHeight / gridSize.rows * 0.8;
    
    if (container) {
      const rect = container.getBoundingClientRect();
      cellWidth = rect.width / gridSize.cols;
      cellHeight = rect.height / gridSize.rows;
    }
    
    // Enhanced position calculation
    const gridX = Math.max(1, Math.min(
      Math.round(transform.x / cellWidth) + 1, 
      gridSize.cols
    ));
    const gridY = Math.max(1, Math.min(
      Math.round(transform.y / cellHeight) + 1, 
      gridSize.rows
    ));
    
    // Dynamic protection check
    if (isPositionProtected && over && active) {
      if (isPositionProtected({ x: gridX, y: gridY })) {
        // Smoothly resist movement into protected areas
        return {
          ...transform,
          x: transform.x * 0.5, // Gentle resistance
          y: transform.y * 0.5,
        };
      }
    }
    
    return transform;
  };
};