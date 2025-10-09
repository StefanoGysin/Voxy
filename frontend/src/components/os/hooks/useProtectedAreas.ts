import { useCallback, useEffect, useState, RefObject } from 'react';

interface ProtectedArea {
  id: string;
  rect: DOMRect;
  type: 'datetime' | 'widget' | 'reserved';
  priority: number; // Higher priority areas override lower ones
}

interface GridPosition {
  x: number;
  y: number;
}

/**
 * Hook for dynamic protected area management in the VOXY Web OS
 * Replaces hardcoded restrictions with intelligent dynamic zones
 */
export const useProtectedAreas = (
  gridRef: RefObject<HTMLDivElement | null>,
  gridSize: { rows: number; cols: number },
  dateTimeRef?: RefObject<HTMLDivElement | null>
) => {
  const [protectedAreas, setProtectedAreas] = useState<ProtectedArea[]>([]);

  // Calculate grid cell dimensions
  const getGridDimensions = useCallback(() => {
    if (!gridRef.current) return { cellWidth: 100, cellHeight: 100 };
    
    const rect = gridRef.current.getBoundingClientRect();
    return {
      cellWidth: rect.width / gridSize.cols,
      cellHeight: rect.height / gridSize.rows,
    };
  }, [gridRef, gridSize]);

  // Convert pixel coordinates to grid position
  const pixelToGrid = useCallback((x: number, y: number): GridPosition => {
    if (!gridRef.current) return { x: 1, y: 1 };
    
    const containerRect = gridRef.current.getBoundingClientRect();
    const { cellWidth, cellHeight } = getGridDimensions();
    
    const relativeX = x - containerRect.left;
    const relativeY = y - containerRect.top;
    
    return {
      x: Math.max(1, Math.min(Math.ceil(relativeX / cellWidth), gridSize.cols)),
      y: Math.max(1, Math.min(Math.ceil(relativeY / cellHeight), gridSize.rows)),
    };
  }, [gridRef, gridSize, getGridDimensions]);

  // Convert grid position to pixel coordinates
  const gridToPixel = useCallback((gridPos: GridPosition) => {
    if (!gridRef.current) return { x: 0, y: 0 };
    
    const containerRect = gridRef.current.getBoundingClientRect();
    const { cellWidth, cellHeight } = getGridDimensions();
    
    return {
      x: containerRect.left + (gridPos.x - 1) * cellWidth,
      y: containerRect.top + (gridPos.y - 1) * cellHeight,
    };
  }, [gridRef, getGridDimensions]);

  // Update protected areas dynamically
  const updateProtectedAreas = useCallback(() => {
    const areas: ProtectedArea[] = [];

    // DateTime widget protection (dynamic)
    if (dateTimeRef?.current) {
      const dateTimeRect = dateTimeRef.current.getBoundingClientRect();
      areas.push({
        id: 'datetime-widget',
        rect: dateTimeRect,
        type: 'datetime',
        priority: 100, // Highest priority
      });
    }

    // Future: Add other dynamic protected areas here
    // Example: Notification areas, dock, etc.

    setProtectedAreas(areas);
  }, [dateTimeRef]);

  // Check if a grid position is within any protected area
  const isPositionProtected = useCallback((gridPos: GridPosition): boolean => {
    if (protectedAreas.length === 0) return false;

    const pixelPos = gridToPixel(gridPos);
    const { cellWidth, cellHeight } = getGridDimensions();
    
    // Create rect for the grid cell
    const cellRect = {
      left: pixelPos.x,
      top: pixelPos.y,
      right: pixelPos.x + cellWidth,
      bottom: pixelPos.y + cellHeight,
    };

    // Check overlap with any protected area
    return protectedAreas.some(area => {
      return !(
        cellRect.right <= area.rect.left ||
        cellRect.left >= area.rect.right ||
        cellRect.bottom <= area.rect.top ||
        cellRect.top >= area.rect.bottom
      );
    });
  }, [protectedAreas, gridToPixel, getGridDimensions]);

  // Get all protected grid positions
  const getProtectedGridPositions = useCallback((): GridPosition[] => {
    const positions: GridPosition[] = [];

    protectedAreas.forEach(area => {
      const topLeft = pixelToGrid(area.rect.left, area.rect.top);
      const bottomRight = pixelToGrid(area.rect.right, area.rect.bottom);

      for (let x = topLeft.x; x <= bottomRight.x; x++) {
        for (let y = topLeft.y; y <= bottomRight.y; y++) {
          positions.push({ x, y });
        }
      }
    });

    return positions;
  }, [protectedAreas, pixelToGrid]);

  // Find nearest available position if current is protected
  const findNearestAvailablePosition = useCallback(
    (targetPos: GridPosition, occupiedPositions: GridPosition[] = []): GridPosition | null => {
      if (!isPositionProtected(targetPos) && 
          !occupiedPositions.some(pos => pos.x === targetPos.x && pos.y === targetPos.y)) {
        return targetPos;
      }

      const maxDistance = Math.max(gridSize.rows, gridSize.cols);

      for (let distance = 1; distance <= maxDistance; distance++) {
        // Search in expanding square pattern
        for (let dx = -distance; dx <= distance; dx++) {
          for (let dy = -distance; dy <= distance; dy++) {
            if (Math.abs(dx) !== distance && Math.abs(dy) !== distance) continue;

            const x = targetPos.x + dx;
            const y = targetPos.y + dy;

            // Check bounds
            if (x < 1 || x > gridSize.cols || y < 1 || y > gridSize.rows) continue;

            const candidate = { x, y };

            // Check if position is available
            if (!isPositionProtected(candidate) && 
                !occupiedPositions.some(pos => pos.x === x && pos.y === y)) {
              return candidate;
            }
          }
        }
      }

      return null; // No available position found
    },
    [isPositionProtected, gridSize]
  );

  // Update protected areas when layout changes
  useEffect(() => {
    updateProtectedAreas();

    // Listen for resize events
    const handleResize = () => {
      setTimeout(updateProtectedAreas, 100); // Debounce
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [updateProtectedAreas]);

  // Update on grid size changes
  useEffect(() => {
    updateProtectedAreas();
  }, [gridSize, updateProtectedAreas]);

  return {
    protectedAreas,
    isPositionProtected,
    getProtectedGridPositions,
    findNearestAvailablePosition,
    updateProtectedAreas,
    pixelToGrid,
    gridToPixel,
    getGridDimensions,
  };
};