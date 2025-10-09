'use client';

import { useOSStore } from '@/lib/store/os-store';
import type React from 'react';
import { useEffect, useState } from 'react';

const DateTimeWidget: React.FC = () => {
  const { dateTimeFormat, showDateTime } = useOSStore();
  const [currentDateTime, setCurrentDateTime] = useState(new Date());
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!showDateTime || !mounted) return;

    const timer = setInterval(() => {
      setCurrentDateTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, [showDateTime, mounted]);

  if (!showDateTime || !mounted) {
    return null;
  }

  const formatTime = (date: Date) => {
    const options: Intl.DateTimeFormatOptions = {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: dateTimeFormat === '12h',
    };
    return date.toLocaleTimeString('en-US', options);
  };

  const formatDate = (date: Date) => {
    const options: Intl.DateTimeFormatOptions = {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    };
    return date.toLocaleDateString('en-US', options);
  };

  const timeString = formatTime(currentDateTime);
  const dateString = formatDate(currentDateTime);

  return (
    <div className="flex flex-col items-center justify-center text-center text-white space-y-2 select-none">
      {/* Time Display */}
      <div
        className="text-4xl md:text-5xl lg:text-6xl font-light tracking-wider drop-shadow-lg"
        style={{
          textShadow: '0 2px 4px rgba(0, 0, 0, 0.5)',
          fontFeatureSettings: '"tnum"',
        }}
      >
        {timeString}
      </div>

      {/* Date Display */}
      <div
        className="text-lg md:text-xl lg:text-2xl font-medium opacity-90 drop-shadow-md"
        style={{
          textShadow: '0 1px 2px rgba(0, 0, 0, 0.5)',
        }}
      >
        {dateString}
      </div>

      {/* Subtle accent line */}
      <div className="w-16 h-0.5 bg-white/30 rounded-full mt-2" />
    </div>
  );
};

export default DateTimeWidget;