"use client";

import { useState, useEffect, useCallback } from 'react';

interface ElapsedTimeProps {
  since: string | null;
}

const ElapsedTime = ({ since }: ElapsedTimeProps) => {
  const [elapsed, setElapsed] = useState('00:00');

  const formatDuration = (totalSeconds: number) => {
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;

    const pad = (num: number) => String(num).padStart(2, '0');

    if (hours > 0) {
      return `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
    }
    return `${pad(minutes)}:${pad(seconds)}`;
  };

  const updateTime = useCallback(() => {
    if (!since) return;

    // Convertimos la fecha del servidor (UTC) y la actual a milisegundos
    // Forzamos que se interprete como UTC si no trae la Z
    const startTime = new Date(since.endsWith('Z') ? since : `${since}Z`).getTime();
    const now = new Date().getTime();
    
    // Calculamos la diferencia
    let diffInSeconds = Math.floor((now - startTime) / 1000);
    
    // Si la diferencia es negativa (por milisegundos de desfase), empezamos en 0
    if (diffInSeconds < 0) diffInSeconds = 0;

    setElapsed(formatDuration(diffInSeconds));
  }, [since]);

  useEffect(() => {
    if (!since) return;

    updateTime();
    const interval = setInterval(updateTime, 1000);

    return () => clearInterval(interval);
  }, [since, updateTime]);

  if (!since) return null;

  return (
    <div className="flex items-center gap-1.5 mt-1 font-mono text-xs font-bold px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400 border border-blue-200 dark:border-blue-800">
      <span className="relative flex h-2 w-2">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
        <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
      </span>
      {elapsed}
    </div>
  );
};

export default ElapsedTime;
