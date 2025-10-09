'use client';

import { useEffect } from 'react';
import { cn } from '@/lib/utils';
import { X, Keyboard, Edit3, Palette, RotateCcw, HelpCircle } from 'lucide-react';
import { useOSStore } from '@/lib/store/os-store';

interface HelpOverlayProps {
  className?: string;
}

interface KeyboardShortcut {
  key: string;
  description: string;
  icon: React.ReactNode;
  context?: string;
}

const shortcuts: KeyboardShortcut[] = [
  {
    key: 'E',
    description: 'Toggle Edit Mode',
    icon: <Edit3 className="w-4 h-4" />,
  },
  {
    key: 'W', 
    description: 'Next Wallpaper',
    icon: <Palette className="w-4 h-4" />,
  },
  {
    key: 'R',
    description: 'Reset Layout',
    icon: <RotateCcw className="w-4 h-4" />,
    context: 'Edit Mode only',
  },
  {
    key: 'H',
    description: 'Show/Hide Help',
    icon: <HelpCircle className="w-4 h-4" />,
  },
  {
    key: 'Escape',
    description: 'Exit Edit Mode',
    icon: <X className="w-4 h-4" />,
    context: 'When in Edit Mode',
  },
];

export function HelpOverlay({ className }: HelpOverlayProps) {
  const { showHelp, toggleHelpOverlay, editMode } = useOSStore();

  // Close help overlay when clicking outside or pressing Escape
  useEffect(() => {
    if (!showHelp) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' || e.key === 'h') {
        e.preventDefault();
        toggleHelpOverlay();
      }
    };

    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as Element;
      if (target?.closest('.help-overlay-content')) return;
      toggleHelpOverlay();
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('mousedown', handleClickOutside);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showHelp, toggleHelpOverlay]);

  if (!showHelp) return null;

  return (
    <div className={cn(
      'fixed inset-0 z-50 flex items-center justify-center',
      'bg-black/60 backdrop-blur-sm',
      'animate-in fade-in duration-200',
      className
    )}>
      <div className={cn(
        'help-overlay-content',
        'bg-black/80 backdrop-blur-md border border-white/20 rounded-xl',
        'p-6 max-w-md w-full mx-4',
        'animate-in slide-in-from-bottom-4 duration-300'
      )}>
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/20 border border-blue-400/50 rounded-lg">
              <Keyboard className="w-5 h-5 text-blue-300" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">
                Keyboard Shortcuts
              </h2>
              <p className="text-sm text-gray-400">
                VOXY Web OS shortcuts
              </p>
            </div>
          </div>
          <button
            onClick={toggleHelpOverlay}
            className={cn(
              'p-2 rounded-lg transition-colors',
              'hover:bg-white/10 active:bg-white/20',
              'text-gray-400 hover:text-white'
            )}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Edit Mode Indicator */}
        {editMode && (
          <div className="mb-4 p-3 bg-orange-500/20 border border-orange-400/50 rounded-lg">
            <div className="flex items-center gap-2">
              <Edit3 className="w-4 h-4 text-orange-300" />
              <span className="text-sm text-orange-200 font-medium">
                Edit Mode Active
              </span>
            </div>
          </div>
        )}

        {/* Shortcuts Grid */}
        <div className="space-y-3">
          {shortcuts.map((shortcut) => (
            <div
              key={shortcut.key}
              className={cn(
                'flex items-center justify-between p-3 rounded-lg',
                'bg-white/5 border border-white/10',
                'hover:bg-white/10 transition-colors'
              )}
            >
              <div className="flex items-center gap-3">
                <div className="text-gray-400">
                  {shortcut.icon}
                </div>
                <div>
                  <span className="text-white font-medium">
                    {shortcut.description}
                  </span>
                  {shortcut.context && (
                    <p className="text-xs text-gray-500 mt-1">
                      {shortcut.context}
                    </p>
                  )}
                </div>
              </div>
              <div className={cn(
                'px-2 py-1 bg-gray-700 border border-gray-600 rounded text-xs font-mono text-gray-300',
                shortcut.key === 'Escape' ? 'text-[10px]' : ''
              )}>
                {shortcut.key}
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="mt-6 pt-4 border-t border-white/10">
          <p className="text-center text-xs text-gray-400">
            Press <kbd className="px-1 bg-gray-700 border border-gray-600 rounded text-gray-300">H</kbd> or{' '}
            <kbd className="px-1 bg-gray-700 border border-gray-600 rounded text-gray-300">Escape</kbd> to close
          </p>
        </div>
      </div>
    </div>
  );
}