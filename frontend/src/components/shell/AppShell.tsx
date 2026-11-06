import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { ActivityBar } from './ActivityBar';
import { GlobalStatusBar } from './GlobalStatusBar';
import { systemClient } from '../../api/systemClient';

export const AppShell: React.FC = () => {
  const [isBackendHealthy, setIsBackendHealthy] = useState<boolean>(true);

  useEffect(() => {
    let isMounted = true;

    const checkHealth = async () => {
      try {
        const res = await systemClient.getHealthLive();
        if (isMounted) {
          setIsBackendHealthy(res.status === 'alive');
        }
      } catch (e) {
        if (isMounted) {
          setIsBackendHealthy(false);
        }
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 5000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="h-screen w-screen bg-zinc-950 text-zinc-100 flex flex-col font-sans overflow-hidden select-text antialiased">
      {/* Main Row: ActivityBar + Main Stage */}
      <div className="flex-1 flex overflow-hidden">
        <ActivityBar isBackendHealthy={isBackendHealthy} />

        <main className="flex-1 bg-zinc-950 overflow-y-auto relative flex flex-col">
          <Outlet />
        </main>
      </div>

      {/* Global Status Bar */}
      <GlobalStatusBar isBackendHealthy={isBackendHealthy} />
    </div>
  );
};
