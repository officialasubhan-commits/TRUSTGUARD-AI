import React from 'react';
import { Outlet } from 'react-router-dom';
import { Navigation } from '../components/layout/Navigation';
import { Footer } from '../components/layout/Footer';
import { PixelBackground } from '../components/geometric/PixelBackground';
import { MaintenanceOverlay } from '../components/common/MaintenanceOverlay';

export const RootLayout: React.FC = () => {
  return (
    <div className="relative min-h-screen flex flex-col bg-[#080808] text-[#F5F5F5]">
      <MaintenanceOverlay />
      <PixelBackground />
      <Navigation />
      <main className="relative z-10 flex-1 flex flex-col">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
};
