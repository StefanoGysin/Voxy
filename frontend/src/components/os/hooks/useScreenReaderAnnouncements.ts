import { useCallback, useRef, useEffect } from 'react';

/**
 * Custom hook for screen reader announcements during drag and drop operations
 */
export const useScreenReaderAnnouncements = () => {
  const announcementRef = useRef<HTMLDivElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Create announcement element on mount
  useEffect(() => {
    const announcementEl = document.createElement('div');
    announcementEl.id = 'dnd-live-region';
    announcementEl.setAttribute('aria-live', 'polite');
    announcementEl.setAttribute('aria-atomic', 'true');
    announcementEl.setAttribute('role', 'status');
    announcementEl.style.position = 'absolute';
    announcementEl.style.left = '-10000px';
    announcementEl.style.width = '1px';
    announcementEl.style.height = '1px';
    announcementEl.style.overflow = 'hidden';
    
    document.body.appendChild(announcementEl);
    announcementRef.current = announcementEl;

    return () => {
      if (announcementRef.current) {
        document.body.removeChild(announcementRef.current);
      }
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  // Announce message to screen readers
  const announce = useCallback((message: string, delay = 100) => {
    if (!announcementRef.current) return;

    // Clear previous timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    // Set message after delay to ensure it's announced
    timeoutRef.current = setTimeout(() => {
      if (announcementRef.current) {
        announcementRef.current.textContent = message;
        
        // Clear message after a brief moment to prepare for next announcement
        setTimeout(() => {
          if (announcementRef.current) {
            announcementRef.current.textContent = '';
          }
        }, 1000);
      }
    }, delay);
  }, []);

  return { announce };
};

/**
 * Generate accessibility messages for drag and drop operations
 */
export const getDragDropMessages = {
  dragStart: (appName: string, position: { x: number; y: number }) => 
    `Started dragging ${appName} from grid position column ${position.x}, row ${position.y}. Use arrow keys to move or press escape to cancel.`,
    
  dragMove: (appName: string, position: { x: number; y: number }, isValid: boolean) => 
    `${appName} moved to column ${position.x}, row ${position.y}${isValid ? '. Position is available' : '. Position is occupied, find another position'}.`,
    
  dragEnd: (appName: string, startPos: { x: number; y: number }, endPos: { x: number; y: number }, success: boolean) => {
    if (success && (startPos.x !== endPos.x || startPos.y !== endPos.y)) {
      return `${appName} moved successfully from column ${startPos.x}, row ${startPos.y} to column ${endPos.x}, row ${endPos.y}.`;
    } else if (success) {
      return `${appName} returned to original position column ${startPos.x}, row ${startPos.y}.`;
    } else {
      return `Move cancelled. ${appName} returned to column ${startPos.x}, row ${startPos.y}.`;
    }
  },
  
  dragCancel: (appName: string, position: { x: number; y: number }) => 
    `Drag cancelled. ${appName} returned to original position column ${position.x}, row ${position.y}.`,
    
  editModeToggle: (enabled: boolean) => 
    enabled ? 'Edit mode enabled. You can now drag app icons to reposition them.' : 'Edit mode disabled. App icons are now fixed in position.',
    
  gridInfo: (gridSize: { rows: number; cols: number }) => 
    `Grid layout: ${gridSize.cols} columns by ${gridSize.rows} rows. First two rows are reserved for date and time display.`,
};