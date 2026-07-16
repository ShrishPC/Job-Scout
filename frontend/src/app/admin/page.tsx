"use client";

import React, { useState, useEffect } from 'react';
import { Shield, Activity, Database, Server, Cpu, HardDrive, LogOut, RefreshCw } from 'lucide-react';
import axios from 'axios';

interface TelemetryData {
  total_jobs: number;
  total_resumes: number;
  system_cpu_usage_percent: number;
  system_ram_usage_percent: number;
  celery_active_tasks: number;
}

export default function AdminDashboard() {
  const [adminKey, setAdminKey] = useState<string>('');
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [stats, setStats] = useState<TelemetryData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [lastRefreshed, setLastRefreshed] = useState<Date | null>(null);

  const apiHost = typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.hostname}:8001` : 'http://127.0.0.1:8001';

  const fetchStats = async (key: string) => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.get(`${apiHost}/api/admin/stats`, {
        headers: { 'x-admin-key': key }
      });
      setStats(res.data);
      setIsAuthenticated(true);
      setLastRefreshed(new Date());
      sessionStorage.setItem('adminKey', key);
    } catch (err: any) {
      setError(err.response?.status === 401 ? 'INVALID ADMIN KEY' : 'CONNECTION FAILED');
      setIsAuthenticated(false);
      sessionStorage.removeItem('adminKey');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    fetchStats(adminKey);
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setStats(null);
    setAdminKey('');
    sessionStorage.removeItem('adminKey');
  };

  useEffect(() => {
    const savedKey = sessionStorage.getItem('adminKey');
    if (savedKey) {
      setAdminKey(savedKey);
      fetchStats(savedKey);
    }
  }, []);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isAuthenticated && adminKey) {
      interval = setInterval(() => {
        fetchStats(adminKey);
      }, 10000);
    }
    return () => clearInterval(interval);
  }, [isAuthenticated, adminKey]);

  // Dark Neo-Brutalist Styles
  const brutalBorder = "border-2 sm:border-[3px] border-white";
  
  const getBrutalHover = (shadowColor: string) => 
    `hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0px_0px_${shadowColor}] transition-transform`;

  // Circular Brutalist Progress (Scaled Down)
  const BrutalProgress = ({ percentage, color, hexColor, icon: Icon, label }: { percentage: number, color: string, hexColor: string, icon: any, label: string }) => {
    const radius = 36;
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference - (percentage / 100) * circumference;

    return (
      <div className={`p-5 bg-black ${brutalBorder} shadow-[4px_4px_0px_0px_${hexColor}] flex flex-col items-center justify-center relative min-h-[160px]`}>
        <div className={`absolute top-3 left-3 flex items-center gap-2 p-1.5 ${color} border-2 border-white`}>
          <Icon className="w-4 h-4 text-black" strokeWidth={3} />
          <span className="font-black text-black uppercase tracking-widest text-[10px]">{label}</span>
        </div>
        
        <div className="relative flex items-center justify-center mt-8">
          <svg className="w-24 h-24 transform -rotate-90">
            <circle
              className="text-[#404040]"
              strokeWidth="8"
              stroke="currentColor"
              fill="transparent"
              r={radius}
              cx="48"
              cy="48"
            />
            <circle
              style={{ color: hexColor }}
              strokeWidth="8"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="butt"
              stroke="currentColor"
              fill="transparent"
              r={radius}
              cx="48"
              cy="48"
              className="transition-all duration-1000 ease-out"
            />
          </svg>
          <div className="absolute flex flex-col items-center justify-center bg-black rounded-full w-14 h-14 border-[3px] border-white">
            <span className="text-sm font-black text-white">{percentage.toFixed(0)}%</span>
          </div>
        </div>
      </div>
    );
  };

  // Stat Card (Scaled Down)
  const BrutalCard = ({ title, value, icon: Icon, color, hexColor, subtitle }: any) => (
    <div className={`p-5 bg-black ${brutalBorder} shadow-[4px_4px_0px_0px_${hexColor}] flex flex-col`}>
      <div className="flex justify-between items-start mb-4">
        <div className={`p-2 ${color} border-2 border-white`}>
          <Icon className="w-5 h-5 text-black" strokeWidth={3} />
        </div>
      </div>
      <div>
        <h3 className="text-white font-black uppercase tracking-widest text-[10px] mb-1">{title}</h3>
        <div className="text-3xl font-black tracking-tighter text-white">{value}</div>
        {subtitle && <div className={`inline-block mt-2 px-1.5 py-0.5 bg-[#1A1A1A] border border-white text-white text-[9px] font-bold uppercase`}>{subtitle}</div>}
      </div>
    </div>
  );

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-[#121212] flex flex-col items-center justify-center p-4 font-mono">
        <div className={`w-full max-w-sm bg-black p-6 ${brutalBorder} shadow-[6px_6px_0px_0px_#FF5500]`}>
          <div className="flex flex-col items-center mb-6 border-b-2 border-white pb-4">
            <div className={`p-3 bg-[#FF5500] mb-3 border-2 border-white`}>
              <Shield className="w-8 h-8 text-white" strokeWidth={3} />
            </div>
            <h1 className="text-2xl font-black text-white uppercase tracking-tight">Admin Gateway</h1>
          </div>
          
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <input
                type="password"
                value={adminKey}
                onChange={(e) => setAdminKey(e.target.value)}
                placeholder="PASSWORD..."
                className={`w-full bg-[#1A1A1A] border-2 border-white px-3 py-3 text-white placeholder-gray-500 text-sm font-bold focus:outline-none focus:bg-black focus:border-[#FFC900] transition-colors uppercase`}
                autoFocus
              />
            </div>
            {error && <p className="text-white bg-[#FF5500] p-2 font-bold uppercase text-xs text-center tracking-widest border-2 border-white">{error}</p>}
            <button 
              type="submit" 
              disabled={loading || !adminKey}
              className={`w-full bg-[#FFC900] text-black font-black py-3 px-3 uppercase tracking-widest text-sm border-2 border-white shadow-[4px_4px_0px_0px_#FFFFFF] ${getBrutalHover('#FFFFFF')} disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center gap-2`}
            >
              {loading ? <RefreshCw className="w-4 h-4 animate-spin" strokeWidth={3} /> : 'Unlock'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#121212] text-white font-mono p-4 sm:p-6 selection:bg-[#FF5500] selection:text-white">
      <div className="max-w-5xl mx-auto">
        
        {/* Header */}
        <div className={`bg-black ${brutalBorder} shadow-[4px_4px_0px_0px_#FFC900] p-4 mb-8 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4`}>
          <div>
            <h1 className="text-2xl font-black uppercase tracking-tighter flex items-center gap-3 text-white">
              <Activity className="w-6 h-6 text-[#FFC900]" strokeWidth={4} />
              Telemetry
            </h1>
          </div>
          
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
            {lastRefreshed && (
              <span className={`px-2 py-1 bg-[#1A1A1A] text-white border-2 border-white font-bold text-[10px] uppercase flex items-center gap-1.5`}>
                <RefreshCw className="w-3 h-3 text-[#FF5500]" strokeWidth={3} /> {lastRefreshed.toLocaleTimeString()}
              </span>
            )}
            <button 
              onClick={handleLogout}
              className={`flex items-center gap-1.5 px-4 py-2 bg-[#FF5500] text-white uppercase font-black tracking-widest border-2 border-white shadow-[3px_3px_0px_0px_#FFFFFF] ${getBrutalHover('#FFFFFF')} text-xs`}
            >
              <LogOut className="w-3 h-3" strokeWidth={3} /> Exit
            </button>
          </div>
        </div>

        {/* Stats Grid */}
        {stats && (
          <div className="space-y-8">
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
              <BrutalCard 
                title="Jobs Indexed" 
                value={stats.total_jobs.toLocaleString()} 
                icon={Database} 
                color="bg-[#23A094]" 
                hexColor="#23A094"
              />
              <BrutalCard 
                title="Active Workers" 
                value={stats.celery_active_tasks} 
                icon={Server} 
                color="bg-[#FF5500]" 
                hexColor="#FF5500"
              />
              <BrutalCard 
                title="Total Resumes" 
                value={stats.total_resumes.toLocaleString()} 
                icon={Shield} 
                color="bg-[#90A8ED]" 
                hexColor="#90A8ED"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-6 border-t-4 border-white border-dashed">
              {/* Hardware */}
              <div className="md:col-span-2">
                <h2 className="text-xl font-black uppercase tracking-tighter mb-4 flex items-center gap-2 text-white">
                  <Server className="w-5 h-5 text-[#FFC900]" strokeWidth={3} /> Hardware
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                  <BrutalProgress 
                    percentage={stats.system_cpu_usage_percent} 
                    color="bg-[#FFC900]" 
                    hexColor="#FFC900"
                    icon={Cpu} 
                    label="CPU"
                  />
                  <BrutalProgress 
                    percentage={stats.system_ram_usage_percent} 
                    color="bg-[#23A094]" 
                    hexColor="#23A094"
                    icon={HardDrive} 
                    label="RAM"
                  />
                </div>
              </div>
              
              {/* Controls */}
              <div className="md:col-span-1">
                <h2 className="text-xl font-black uppercase tracking-tighter mb-4 flex items-center gap-2 text-white">
                  <Shield className="w-5 h-5 text-[#90A8ED]" strokeWidth={3} /> Controls
                </h2>
                <div className="flex flex-col gap-4">
                  <button 
                    onClick={async () => {
                      try {
                        await axios.post(`${apiHost}/ai/cache/clear`, {}, { headers: { 'x-admin-key': adminKey } });
                        alert("AI Cache Cleared!");
                      } catch (e) { alert("Failed to clear cache."); }
                    }}
                    className={`w-full bg-[#FF90E8] text-black font-black py-3 px-3 uppercase tracking-widest text-xs border-2 border-white shadow-[4px_4px_0px_0px_#FFFFFF] ${getBrutalHover('#FFFFFF')} flex justify-center items-center gap-2`}
                  >
                    <RefreshCw className="w-4 h-4" strokeWidth={3} /> Clear Cache
                  </button>
                  <button 
                    onClick={async () => {
                      try {
                        await axios.post(`${apiHost}/jobs/scrape?keyword=Engineer&location=Remote&limit=5&source=all`, {}, { headers: { 'x-admin-key': adminKey } });
                        alert("Background Scraper Triggered!");
                      } catch (e) { alert("Failed to trigger scraper."); }
                    }}
                    className={`w-full bg-[#FFC900] text-black font-black py-3 px-3 uppercase tracking-widest text-xs border-2 border-white shadow-[4px_4px_0px_0px_#FFFFFF] ${getBrutalHover('#FFFFFF')} flex justify-center items-center gap-2`}
                  >
                    <Database className="w-4 h-4" strokeWidth={3} /> Scrape
                  </button>
                  <button 
                    onClick={async () => {
                      try {
                        await axios.post(`${apiHost}/ai/config`, { device: "cuda" }, { headers: { 'x-admin-key': adminKey } });
                        alert("AI Switched to CUDA GPU!");
                      } catch (e) { alert("Failed to switch AI config."); }
                    }}
                    className={`w-full bg-[#23A094] text-black font-black py-3 px-3 uppercase tracking-widest text-xs border-2 border-white shadow-[4px_4px_0px_0px_#FFFFFF] ${getBrutalHover('#FFFFFF')} flex justify-center items-center gap-2`}
                  >
                    <Cpu className="w-4 h-4" strokeWidth={3} /> GPU Mode
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
