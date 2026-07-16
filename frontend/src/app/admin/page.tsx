"use client";

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
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
      // Save key to session storage for persistence across reloads
      sessionStorage.setItem('adminKey', key);
    } catch (err: any) {
      setError(err.response?.status === 401 ? 'Invalid Admin Key' : 'Failed to connect to backend.');
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

  // Poll every 10 seconds if authenticated
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isAuthenticated && adminKey) {
      interval = setInterval(() => {
        fetchStats(adminKey);
      }, 10000);
    }
    return () => clearInterval(interval);
  }, [isAuthenticated, adminKey]);

  // UI Components
  const CircularProgress = ({ percentage, color, icon: Icon, label }: { percentage: number, color: string, icon: any, label: string }) => {
    const radius = 38;
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference - (percentage / 100) * circumference;

    return (
      <div className="flex flex-col items-center justify-center p-6 bg-gray-800/50 rounded-2xl border border-gray-700 backdrop-blur-sm">
        <div className="flex items-center gap-2 text-gray-400 mb-4">
          <Icon className="w-5 h-5" />
          <span className="font-medium">{label}</span>
        </div>
        <div className="relative flex items-center justify-center">
          <svg className="w-32 h-32 transform -rotate-90">
            <circle
              className="text-gray-700"
              strokeWidth="8"
              stroke="currentColor"
              fill="transparent"
              r={radius}
              cx="64"
              cy="64"
            />
            <motion.circle
              className={color}
              strokeWidth="8"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              stroke="currentColor"
              fill="transparent"
              r={radius}
              cx="64"
              cy="64"
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset }}
              transition={{ duration: 1, ease: "easeOut" }}
            />
          </svg>
          <div className="absolute flex flex-col items-center">
            <span className="text-3xl font-bold text-white">{percentage.toFixed(1)}%</span>
          </div>
        </div>
      </div>
    );
  };

  const StatCard = ({ title, value, icon: Icon, colorClass, subtitle }: any) => (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-6 bg-gray-800/50 rounded-2xl border border-gray-700 backdrop-blur-sm flex flex-col"
    >
      <div className="flex justify-between items-start mb-4">
        <div className={`p-3 rounded-lg ${colorClass} bg-opacity-10`}>
          <Icon className={`w-6 h-6 ${colorClass.replace('bg-', 'text-')}`} />
        </div>
      </div>
      <div>
        <h3 className="text-gray-400 text-sm font-medium mb-1">{title}</h3>
        <div className="text-3xl font-bold text-white">{value}</div>
        {subtitle && <p className="text-xs text-gray-500 mt-2">{subtitle}</p>}
      </div>
    </motion.div>
  );

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 font-sans selection:bg-indigo-500/30">
      <AnimatePresence mode="wait">
        {!isAuthenticated ? (
          <motion.div 
            key="login"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center justify-center min-h-screen p-4"
          >
            <div className="w-full max-w-md p-8 bg-gray-900 rounded-2xl border border-gray-800 shadow-2xl">
              <div className="flex flex-col items-center mb-8">
                <div className="p-4 bg-indigo-500/10 rounded-full mb-4">
                  <Shield className="w-10 h-10 text-indigo-400" />
                </div>
                <h1 className="text-2xl font-bold text-white">Admin Authentication</h1>
                <p className="text-gray-400 text-sm mt-2 text-center">Enter your secure key to access telemetry.</p>
              </div>
              
              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <input
                    type="password"
                    value={adminKey}
                    onChange={(e) => setAdminKey(e.target.value)}
                    placeholder="Enter Admin Key"
                    className="w-full bg-gray-950 border border-gray-800 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                    autoFocus
                  />
                </div>
                {error && <p className="text-red-400 text-sm text-center">{error}</p>}
                <button 
                  type="submit" 
                  disabled={loading || !adminKey}
                  className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-3 px-4 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center gap-2"
                >
                  {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : 'Authenticate'}
                </button>
              </form>
            </div>
          </motion.div>
        ) : (
          <motion.div 
            key="dashboard"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="max-w-7xl mx-auto p-4 sm:p-6 lg:p-8"
          >
            {/* Header */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
              <div>
                <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                  <Activity className="text-indigo-400" /> System Telemetry
                </h1>
                <p className="text-gray-400 text-sm mt-1">Live metrics from the Job Scout architecture.</p>
              </div>
              
              <div className="flex items-center gap-4">
                {lastRefreshed && (
                  <span className="text-xs text-gray-500 flex items-center gap-1">
                    <RefreshCw className="w-3 h-3" /> Updated {lastRefreshed.toLocaleTimeString()}
                  </span>
                )}
                <button 
                  onClick={handleLogout}
                  className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors border border-gray-700 text-sm font-medium"
                >
                  <LogOut className="w-4 h-4" /> Disconnect
                </button>
              </div>
            </div>

            {/* Main Stats Grid */}
            {stats && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  <StatCard 
                    title="Total Jobs Indexed" 
                    value={stats.total_jobs.toLocaleString()} 
                    icon={Database} 
                    colorClass="text-emerald-400 bg-emerald-400" 
                    subtitle="In PostgreSQL Vector DB"
                  />
                  <StatCard 
                    title="Active Celery Tasks" 
                    value={stats.celery_active_tasks} 
                    icon={Server} 
                    colorClass="text-amber-400 bg-amber-400" 
                    subtitle="Background workers currently executing"
                  />
                  <StatCard 
                    title="Candidate Resumes" 
                    value={stats.total_resumes.toLocaleString()} 
                    icon={Shield} 
                    colorClass="text-indigo-400 bg-indigo-400" 
                    subtitle="Total unique resumes parsed"
                  />
                </div>

                <h2 className="text-xl font-bold text-gray-200 mt-10 mb-4 flex items-center gap-2">
                  <Server className="w-5 h-5 text-gray-400" /> Host Performance
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                  <CircularProgress 
                    percentage={stats.system_cpu_usage_percent} 
                    color="text-sky-500" 
                    icon={Cpu} 
                    label="CPU Load"
                  />
                  <CircularProgress 
                    percentage={stats.system_ram_usage_percent} 
                    color="text-fuchsia-500" 
                    icon={HardDrive} 
                    label="Memory Usage"
                  />
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
