"use client";

import React, { useState, useEffect, useMemo } from 'react';
import FileUpload from '@/components/ui/FileUpload';
import JobCard from '@/components/ui/JobCard';
import KanbanBoard from '@/components/ui/KanbanBoard';
import VaultView from '@/components/ui/VaultView';
import ProfileView from '@/components/ui/ProfileView';
import RadarView from '@/components/ui/RadarView';
import { Search, Briefcase, User, Settings as SettingsIcon, Play, Loader2, Sparkles, LogOut, Layout, Radar, Target, Database, RotateCw, Trash2, X, ChevronDown, SlidersHorizontal, MapPin } from 'lucide-react';
import axios from 'axios';

export default function Home() {
  const [parsedData, setParsedData] = useState<any>(null);
  const [jobs, setJobs] = useState<any[]>([]);
  const [view, setView] = useState<'hunt' | 'board' | 'radar' | 'vault' | 'profile'>('hunt');
  const [theme, setTheme] = useState<'light' | 'dark' | 'system'>('system');
  const [showConfig, setShowConfig] = useState(false);
  const [scraping, setScraping] = useState(false);
  const [loadingJobs, setLoadingJobs] = useState(false);
  const [searchParams, setSearchParams] = useState({
    keyword: '',
    location: ''
  });
  const [maxExperience, setMaxExperience] = useState<number | ''>('');
  const [sortBy, setSortBy] = useState<'match' | 'exp_asc' | 'exp_desc'>('match');
  const [showFilters, setShowFilters] = useState(false);
  const [showLocationSuggestions, setShowLocationSuggestions] = useState(false);
  const [selectedWorkplaceTypes, setSelectedWorkplaceTypes] = useState<string[]>([]);

  const filteredJobs = useMemo(() => {
    let result = jobs.filter(job => {
      const kw = searchParams.keyword.toLowerCase();
      const loc = searchParams.location.toLowerCase();
      const matchesKeyword = job.title.toLowerCase().includes(kw) || 
                           job.company.toLowerCase().includes(kw) || 
                           job.description.toLowerCase().includes(kw);
      const matchesLocation = job.location.toLowerCase().includes(loc);
      
      const jobExp = job.experience_required || 0;
      const matchesExp = maxExperience === '' || jobExp <= Number(maxExperience);

      return matchesKeyword && matchesLocation && matchesExp;
    });

    result.sort((a, b) => {
      if (sortBy === 'match') {
        return b.match_score - a.match_score;
      } else if (sortBy === 'exp_asc') {
        return (a.experience_required || 0) - (b.experience_required || 0);
      } else if (sortBy === 'exp_desc') {
        return (b.experience_required || 0) - (a.experience_required || 0);
      }
      return 0;
    });

    return result;
  }, [jobs, searchParams, maxExperience, sortBy]);

  const uniqueLocations = useMemo(() => {
    const locs = Array.from(new Set(jobs.map(j => j.location))).filter(Boolean);
    return locs.sort();
  }, [jobs]);

  const fetchMatches = async (embedding: number[], workplaceTypes: string[]) => {
    if (!embedding || embedding.length === 0) return;
    setLoadingJobs(true);
    const apiHost = typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.hostname}:8000` : 'http://127.0.0.1:8000';
    try {
      const response = await axios.post(`${apiHost}/jobs/matches`, {
        embedding: embedding,
        limit: 12,
        workplace_types: workplaceTypes.length > 0 ? workplaceTypes : null
      });
      setJobs(response.data);
    } catch (err) {
      console.error("Failed to fetch matches:", err);
    } finally {
      setLoadingJobs(false);
    }
  };

  const fetchActiveProfile = async () => {
    const apiHost = typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.hostname}:8000` : 'http://127.0.0.1:8000';
    try {
      const response = await axios.get(`${apiHost}/resume/active`);
      if (response.data) {
        setParsedData(response.data);
      }
    } catch (err) {
      console.error("Failed to fetch active profile:", err);
    }
  };

  useEffect(() => {
    fetchActiveProfile();
  }, []);

  // Read theme from localStorage on load
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | 'system' | null;
    if (savedTheme) {
      setTheme(savedTheme);
    }
  }, []);

  // Sync theme changes to localStorage and update document class list
  useEffect(() => {
    const updateTheme = () => {
      if (theme === 'dark') {
        document.documentElement.classList.add('dark');
        localStorage.setItem('theme', 'dark');
      } else if (theme === 'light') {
        document.documentElement.classList.remove('dark');
        localStorage.setItem('theme', 'light');
      } else {
        localStorage.setItem('theme', 'system');
        const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        if (systemPrefersDark) {
          document.documentElement.classList.add('dark');
        } else {
          document.documentElement.classList.remove('dark');
        }
      }
    };

    updateTheme();

    if (theme === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const listener = (e: MediaQueryListEvent) => {
        if (e.matches) {
          document.documentElement.classList.add('dark');
        } else {
          document.documentElement.classList.remove('dark');
        }
      };
      mediaQuery.addEventListener('change', listener);
      return () => mediaQuery.removeEventListener('change', listener);
    }
  }, [theme]);

  useEffect(() => {
    if (parsedData?.embedding) {
      fetchMatches(parsedData.embedding, selectedWorkplaceTypes); 
    }
  }, [parsedData, selectedWorkplaceTypes]);

  const triggerScrape = async () => {
    setScraping(true);
    const apiHost = typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.hostname}:8000` : 'http://127.0.0.1:8000';
    const scrapeKw = searchParams.keyword.trim() || 'Software Engineer';
    const scrapeLoc = searchParams.location.trim() || 'Remote';
    try {
      await axios.post(`${apiHost}/jobs/scrape?keyword=${scrapeKw}&location=${scrapeLoc}&limit=15`);
      alert(`Search initiated for ${scrapeKw} in ${scrapeLoc}.`);
    } catch (err) {
      console.error("Failed to start scraping:", err);
    } finally {
      setScraping(false);
    }
  };

  const handleApply = (id: number) => {
    if (parsedData?.embedding) fetchMatches(parsedData.embedding, selectedWorkplaceTypes);
  };

  const handleReject = (id: number) => {
    setJobs(jobs.map(j => j.id === id ? { ...j, is_rejected: true } : j));
  };

  const handleDeleteProfile = async () => {
    const apiHost = typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.hostname}:8000` : 'http://127.0.0.1:8000';
    try {
      await axios.delete(`${apiHost}/resume/reset`);
      setParsedData(null);
      setJobs([]);
      setSearchParams({ keyword: '', location: '' });
    } catch (err) {
      console.error("Failed to delete profile:", err);
      alert("Failed to clear profile data.");
    }
  };

  const handleResumeSync = (data: any) => {
    setParsedData(data);
    if (data.parsed_json?.target_role) {
      setSearchParams({
        keyword: data.parsed_json.target_role,
        location: data.parsed_json.target_location || 'Remote'
      });
    }
  };

  return (
    <main className="min-h-screen bg-retro-cream text-retro-black flex overflow-hidden font-sans">
      {/* Sidebar Navigation */}
      <nav className="w-24 bg-retro-mint border-r-4 border-black flex flex-col items-center py-8 space-y-10 z-20 relative text-black">
        <div 
          onClick={() => setView('radar')}
          className="w-14 h-14 bg-retro-yellow text-black border-3 border-black shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:translate-x-[3px] active:translate-y-[3px] active:shadow-none flex items-center justify-center rounded-xl cursor-pointer transition-all duration-100"
          title="Market Intelligence Radar"
        >
          <Radar className="w-8 h-8" />
        </div>
        
        <div className="flex-1 flex flex-col space-y-8">
          <NavItem 
            icon={<Target className="w-6 h-6" />} 
            label="Hunt"
            active={view === 'hunt'} 
            onClick={() => setView('hunt')} 
          />
          <NavItem 
            icon={<Layout className="w-6 h-6" />} 
            label="Pipeline"
            active={view === 'board'} 
            onClick={() => setView('board')} 
          />
          <NavItem 
            icon={<Database className="w-6 h-6" />} 
            label="Vault" 
            active={view === 'vault'}
            onClick={() => setView('vault')}
          />
          <NavItem 
            icon={<User className="w-6 h-6" />} 
            label="Profile" 
            active={view === 'profile'}
            onClick={() => setView('profile')}
          />
        </div>

        <div className="pt-6 border-t-3 border-black w-full flex flex-col items-center space-y-8">
            <NavItem 
              icon={<SettingsIcon className="w-6 h-6" />} 
              label="Config" 
              active={showConfig}
              onClick={() => setShowConfig(true)} 
            />
            <NavItem icon={<LogOut className="w-6 h-6 text-retro-red" />} label="Exit" />
        </div>
      </nav>

      {/* Main Container */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Header */}
        <header className="h-24 bg-retro-cream border-b-4 border-black flex items-center justify-between px-10 flex-shrink-0 z-10">
          <div className="flex items-center space-x-3">
            <div className="px-4 py-2 bg-retro-yellow border-3 border-black shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] rounded-xl flex items-center justify-center font-black text-xl tracking-tighter uppercase italic">
               JOB<span className="text-retro-red">SCOUT</span>
            </div>
          </div>

          {view === 'hunt' && (
            <div className="flex items-center space-x-6">
              <div className="flex bg-white border-3 border-black rounded-xl p-1.5 shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] group transition-all">
                  <div className="flex items-center px-4">
                    <Search className="w-4 h-4 text-black mr-2" />
                    <input 
                      type="text" 
                      placeholder="Filter by Role" 
                      className="bg-transparent border-none focus:ring-0 text-xs w-48 text-black placeholder-gray-500 font-extrabold"
                      value={searchParams.keyword}
                      onChange={(e) => setSearchParams({...searchParams, keyword: e.target.value})}
                    />
                    {searchParams.keyword && (
                      <button onClick={() => setSearchParams({...searchParams, keyword: ''})} className="ml-2">
                        <X className="w-3.5 h-3.5 text-black hover:text-retro-red" />
                      </button>
                    )}
                  </div>
                  <div className="w-0.5 h-6 bg-black self-center"></div>
                  <div className="flex items-center px-4 relative">
                    <MapPin className="w-4 h-4 text-black mr-2" />
                    <input 
                      type="text" 
                      placeholder="Location" 
                      className="bg-transparent border-none focus:ring-0 text-xs w-36 text-black placeholder-gray-500 font-extrabold"
                      value={searchParams.location}
                      onChange={(e) => {
                        setSearchParams({...searchParams, location: e.target.value});
                        setShowLocationSuggestions(true);
                      }}
                      onFocus={() => setShowLocationSuggestions(true)}
                    />
                    {searchParams.location && (
                      <button onClick={() => {
                        setSearchParams({...searchParams, location: ''});
                        setShowLocationSuggestions(false);
                      }} className="ml-2">
                        <X className="w-3.5 h-3.5 text-black hover:text-retro-red" />
                      </button>
                    )}
                    
                    {showLocationSuggestions && uniqueLocations.length > 0 && (
                      <div className="absolute top-full left-0 mt-3 w-56 bg-white border-3 border-black rounded-xl shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] py-2 z-50 animate-in fade-in slide-in-from-top-1">
                        <div className="px-3 py-1 mb-1 border-b-2 border-black bg-retro-sand">
                           <span className="text-[10px] font-black text-black uppercase tracking-widest">Available Locations</span>
                        </div>
                        <div className="max-h-48 overflow-y-auto custom-scrollbar">
                          {uniqueLocations
                            .filter(loc => loc.toLowerCase().includes(searchParams.location.toLowerCase()))
                            .map((loc, i) => (
                              <div 
                                key={i}
                                onClick={() => {
                                  setSearchParams({...searchParams, location: loc});
                                  setShowLocationSuggestions(false);
                                }}
                                className="px-4 py-2 text-xs font-black text-black hover:bg-retro-mint cursor-pointer transition-colors flex items-center border-b border-black/10 last:border-b-0"
                              >
                                <MapPin className="w-3.5 h-3.5 mr-2 text-black/60" />
                                {loc}
                              </div>
                            ))}
                        </div>
                        <div 
                          className="border-t-2 border-black bg-retro-cream mt-1 px-4 py-2 text-[10px] font-black text-center text-black hover:bg-retro-sand cursor-pointer"
                          onClick={() => setShowLocationSuggestions(false)}
                        >
                          Close Suggestions
                        </div>
                      </div>
                    )}
                  </div>
              </div>
              <button 
                onClick={triggerScrape}
                disabled={scraping}
                className="h-12 bg-retro-red text-white px-8 rounded-xl text-[11px] font-black uppercase tracking-widest flex items-center border-3 border-black shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:translate-x-[3px] active:translate-y-[3px] active:shadow-none transition-all disabled:opacity-50 disabled:translate-x-0 disabled:translate-y-0 disabled:shadow-[3px_3px_0px_0px_rgba(0,0,0,1)]"
              >
                {scraping ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 mr-2 fill-current" />}
                Sync Jobs
              </button>
            </div>
          )}
        </header>

        {/* Scrollable Content Area */}
        <div className="flex-1 overflow-y-auto custom-scrollbar">
          {view === 'hunt' ? (
            <div className="max-w-7xl mx-auto p-10 pb-20">
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
                {/* Left Panel: Persona */}
                <div className="lg:col-span-4 space-y-10">
                  <section>
                    <div className="flex items-center justify-between mb-4 px-1">
                      <div className="flex items-center space-x-2">
                        <h2 className="text-[11px] font-black text-black uppercase tracking-[0.2em]">Profile Sync</h2>
                        {parsedData && <div className="w-3 h-3 bg-retro-green rounded-full border-2 border-black shadow-[1px_1px_0px_0px_rgba(0,0,0,1)]"></div>}
                      </div>
                      {parsedData && (
                        <button 
                          onClick={handleDeleteProfile}
                          className="p-2 bg-white border-2 border-black rounded-lg text-black hover:bg-retro-red hover:text-white transition-all shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[0.5px] hover:translate-y-[0.5px] hover:shadow-[1.5px_1.5px_0px_0px_rgba(0,0,0,1)] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none"
                          title="Delete Stored Profile"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                    <FileUpload onUploadSuccess={handleResumeSync} />
                  </section>

                  {parsedData && (
                    <section className="bg-white border-3 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] rounded-xl overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-300 persona-card">
                      <div className="p-8 pb-6 border-b-3 border-black bg-retro-sand text-black flex items-center space-x-4">
                        <div className="w-12 h-12 bg-retro-yellow text-black border-2 border-black rounded-full flex items-center justify-center font-black text-lg shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] profile-avatar shrink-0">
                          {parsedData.parsed_json?.full_name ? parsedData.parsed_json.full_name.charAt(0) : 'U'}
                        </div>
                        <div className="min-w-0">
                          <h3 className="text-xl font-black tracking-tight truncate">{parsedData.parsed_json?.full_name}</h3>
                          <p className="text-black/85 text-xs font-extrabold mt-0.5 uppercase tracking-widest truncate">{parsedData.parsed_json?.email}</p>
                        </div>
                      </div>
                      <div className="p-8 space-y-10 bg-white">
                        <div>
                          <h4 className="text-[11px] font-black text-black/60 uppercase tracking-[0.2em] mb-4">Key Skills</h4>
                          <div className="flex flex-wrap gap-2">
                            {parsedData.parsed_json?.skills?.map((skill: string, i: number) => (
                              <span key={i} className="px-3 py-1.5 bg-retro-mint text-black border-2 border-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] text-[11px] font-black skill-tag">
                                {skill}
                              </span>
                            ))}
                          </div>
                        </div>
                        <div>
                          <h4 className="text-[11px] font-black text-black/60 uppercase tracking-[0.2em] mb-4">Recent History</h4>
                          <div className="space-y-6">
                            {parsedData.parsed_json?.experience?.slice(0, 2).map((exp: any, i: number) => (
                              <div key={i} className="relative pl-6 before:content-[''] before:absolute before:left-0 before:top-1.5 before:w-2 before:h-2 before:bg-retro-red before:border before:border-black before:rounded-none">
                                <p className="font-extrabold text-black text-sm">{exp.title}</p>
                                <p className="text-retro-green text-[11px] font-black mt-0.5">{exp.company}</p>
                                <p className="text-black/50 text-[10px] mt-1 uppercase font-black tracking-tighter">{exp.duration}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    </section>
                  )}
                </div>

                {/* Right Panel: Best Matches */}
                <div className="lg:col-span-8 space-y-8">
                  <div className="flex items-center justify-between px-2">
                    <div>
                      <h2 className="text-3xl font-black text-black tracking-tight uppercase italic">Best Matches</h2>
                      <p className="text-black/60 text-[11px] font-black uppercase tracking-widest mt-1">Found based on your resume</p>
                    </div>
                    <div className="flex space-x-3">
                      <button 
                        onClick={() => setShowFilters(!showFilters)}
                        className={`px-4 py-2.5 rounded-xl border-3 border-black flex items-center space-x-2 transition-all font-black text-xs ${showFilters ? 'bg-retro-yellow text-black shadow-none translate-x-[2px] translate-y-[2px]' : 'bg-white text-black shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:translate-x-[3px] active:translate-y-[3px] active:shadow-none'}`}
                      >
                        <SlidersHorizontal className="w-4 h-4" />
                        <span>Filter & Sort</span>
                      </button>
                      <button 
                        onClick={() => parsedData?.embedding && fetchMatches(parsedData.embedding, selectedWorkplaceTypes)}
                        className="p-3 bg-white border-3 border-black rounded-xl shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:translate-x-[3px] active:translate-y-[3px] active:shadow-none transition-all"
                        title="Refresh Matches"
                      >
                        <RotateCw className={`w-4 h-4 text-black ${loadingJobs ? 'animate-spin' : ''}`} />
                      </button>
                    </div>
                  </div>

                  {showFilters && parsedData && (
                    <div className="bg-white border-3 border-black rounded-xl p-6 flex flex-wrap gap-6 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] animate-in fade-in slide-in-from-top-2">
                      <div className="flex flex-col space-y-2">
                        <label className="text-[10px] font-black uppercase tracking-widest text-black/60">Max Experience Required</label>
                        <div className="flex items-center space-x-3">
                          <input 
                            type="range" 
                            min="0" 
                            max="15" 
                            step="1"
                            value={maxExperience === '' ? 15 : maxExperience}
                            onChange={(e) => setMaxExperience(Number(e.target.value))}
                            className="w-48 accent-retro-red"
                          />
                          <span className="text-xs font-black text-black bg-retro-sand px-2 py-1 rounded-md border-2 border-black w-18 text-center">
                            {maxExperience === '' ? 'Any' : `${maxExperience} Yrs`}
                          </span>
                          {maxExperience !== '' && (
                            <button onClick={() => setMaxExperience('')} className="text-[10px] text-black/60 hover:text-retro-red uppercase font-black tracking-wider ml-2">Clear</button>
                          )}
                        </div>
                      </div>

                      <div className="w-0.5 bg-black hidden md:block"></div>

                      <div className="flex flex-col space-y-2">
                        <label className="text-[10px] font-black uppercase tracking-widest text-black/60">Workplace Type</label>
                        <div className="flex flex-wrap gap-2 pt-1">
                          {['remote', 'hybrid', 'onsite', 'negotiable'].map((type) => {
                            const isSelected = selectedWorkplaceTypes.includes(type);
                            const label = type === 'onsite' ? 'On-site' : type.charAt(0).toUpperCase() + type.slice(1);
                            return (
                              <button
                                key={type}
                                onClick={() => {
                                  if (isSelected) {
                                    setSelectedWorkplaceTypes(selectedWorkplaceTypes.filter(t => t !== type));
                                  } else {
                                    setSelectedWorkplaceTypes([...selectedWorkplaceTypes, type]);
                                  }
                                }}
                                className={`px-3 py-1.5 rounded-lg text-xs font-black border-2 border-black transition-all ${
                                  isSelected 
                                    ? 'bg-retro-green text-white shadow-none translate-x-[1px] translate-y-[1px]' 
                                    : 'bg-white text-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:bg-retro-cream'
                                }`}
                              >
                                {label}
                              </button>
                            );
                          })}
                        </div>
                      </div>

                      <div className="w-0.5 bg-black hidden md:block"></div>

                      <div className="flex flex-col space-y-2">
                        <label className="text-[10px] font-black uppercase tracking-widest text-black/60">Sort By</label>
                        <div className="flex bg-retro-cream p-1 rounded-lg border-2 border-black">
                          <button 
                            onClick={() => setSortBy('match')}
                            className={`px-3 py-1.5 rounded text-xs font-black transition-all border border-transparent ${sortBy === 'match' ? 'bg-white text-black border-black/10 shadow-sm' : 'text-black/50 hover:text-black'}`}
                          >
                            Best Match
                          </button>
                          <button 
                            onClick={() => setSortBy('exp_asc')}
                            className={`px-3 py-1.5 rounded text-xs font-black transition-all border border-transparent ${sortBy === 'exp_asc' ? 'bg-white text-black border-black/10 shadow-sm' : 'text-black/50 hover:text-black'}`}
                          >
                            Exp: Low - High
                          </button>
                          <button 
                            onClick={() => setSortBy('exp_desc')}
                            className={`px-3 py-1.5 rounded text-xs font-black transition-all border border-transparent ${sortBy === 'exp_desc' ? 'bg-white text-black border-black/10 shadow-sm' : 'text-black/50 hover:text-black'}`}
                          >
                            Exp: High - Low
                          </button>
                        </div>
                      </div>
                    </div>
                  )}

                  {!parsedData ? (
                    <div className="bg-white rounded-xl p-24 text-center border-3 border-dashed border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] group">
                      <div className="w-16 h-16 bg-retro-cream border-3 border-black rounded-xl flex items-center justify-center mx-auto mb-6 transition-all transform group-hover:rotate-6 shadow-[3px_3px_0px_0px_rgba(0,0,0,1)]">
                        <Target className="w-8 h-8 text-black" />
                      </div>
                      <h3 className="text-xl font-black text-black mb-2 uppercase">Sync Profile</h3>
                      <p className="text-black/70 max-w-xs mx-auto text-xs leading-relaxed font-bold">
                        Upload your resume to get personalized job matches based on your background.
                      </p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {loadingJobs ? (
                          <div className="col-span-full py-32 flex flex-col items-center">
                              <Loader2 className="w-10 h-10 animate-spin text-retro-red mb-6" />
                              <p className="text-black font-black tracking-[0.3em] text-[11px] uppercase">Finding matches...</p>
                          </div>
                      ) : jobs.length === 0 ? (
                          <div className="col-span-full py-24 text-center bg-white rounded-xl border-3 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
                              <p className="text-black font-black text-sm italic">No jobs found. Click "Sync Jobs" above.</p>
                          </div>
                      ) : filteredJobs.length === 0 ? (
                          <div className="col-span-full py-24 text-center bg-white rounded-xl border-3 border-dashed border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
                              <p className="text-black font-black text-sm italic">No matches found for "{searchParams.keyword}" in "{searchParams.location}".</p>
                          </div>
                      ) : (
                          filteredJobs.map((job) => (
                            <JobCard 
                              key={job.id} 
                              job={job} 
                              onApply={handleApply} 
                              onReject={handleReject} 
                            />
                          ))
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : view === 'board' ? (
            <div className="max-w-[1600px] mx-auto p-10 pb-20">
              <div className="flex items-end justify-between mb-10 px-4">
                 <div>
                    <h2 className="text-3xl font-black text-black tracking-tighter uppercase italic">Job Tracker</h2>
                    <p className="text-black/60 text-[11px] font-black uppercase tracking-[0.3em] mt-1">Manage your applications</p>
                 </div>
              </div>
              <KanbanBoard />
            </div>
          ) : view === 'vault' ? (
            <div className="max-w-[1600px] mx-auto p-10 pb-20">
              <div className="flex items-end justify-between mb-10 px-4">
                 <div>
                    <h2 className="text-3xl font-black text-black tracking-tighter uppercase italic">Resume Vault</h2>
                    <p className="text-black/60 text-[11px] font-black uppercase tracking-[0.3em] mt-1">Manage your professional assets</p>
                 </div>
              </div>
              <VaultView onActiveProfileChanged={handleResumeSync} />
            </div>
          ) : view === 'profile' ? (
            <div className="max-w-[1600px] mx-auto p-10 pb-20">
              <div className="flex items-end justify-between mb-10 px-4">
                 <div>
                    <h2 className="text-3xl font-black text-black tracking-tighter uppercase italic">Neural Profile</h2>
                    <p className="text-black/60 text-[11px] font-black uppercase tracking-[0.3em] mt-1">Active candidate details</p>
                 </div>
              </div>
              <ProfileView parsedData={parsedData} />
            </div>
          ) : (
            <div className="max-w-[1600px] mx-auto p-10 pb-20">
              <div className="flex items-end justify-between mb-10 px-4">
                 <div>
                    <h2 className="text-3xl font-black text-black tracking-tighter uppercase italic">Market Intelligence</h2>
                    <p className="text-black/60 text-[11px] font-black uppercase tracking-[0.3em] mt-1">Real-time Radar Report</p>
                 </div>
              </div>
              <RadarView jobs={jobs} parsedData={parsedData} />
            </div>
          )}
        </div>
      </div>

      {/* Dynamic Settings/Configuration Modal */}
      {showConfig && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-retro-cream border-4 border-black rounded-xl p-8 max-w-md w-full shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] dark:shadow-[8px_8px_0px_0px_#ffffff] animate-in zoom-in-95 duration-200 text-black dark:text-white">
            <div className="flex justify-between items-center mb-6 pb-4 border-b-3 border-black bg-retro-yellow -mx-8 -mt-8 p-6 rounded-t-lg">
              <div className="flex items-center space-x-2 text-black">
                <SettingsIcon className="w-6 h-6" />
                <h3 className="text-xl font-black uppercase tracking-tight italic">System Configuration</h3>
              </div>
              <button 
                onClick={() => setShowConfig(false)}
                className="p-1.5 border-2 border-black bg-white rounded-lg text-black hover:bg-retro-pink shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[0.5px] hover:translate-y-[0.5px] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none transition-all cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-6">
              <div>
                <label className="text-xs font-black text-black/60 dark:text-white/60 uppercase tracking-[0.2em] block mb-3">
                  Visual Interface Theme
                </label>
                <div className="grid grid-cols-3 gap-3">
                  <button
                    onClick={() => setTheme('light')}
                    className={`px-4 py-3 border-2 border-black rounded-xl font-black text-xs uppercase tracking-wider transition-all flex flex-col items-center justify-center space-y-2 cursor-pointer ${
                      theme === 'light'
                        ? 'bg-retro-yellow text-black shadow-none translate-x-[2px] translate-y-[2px]'
                        : 'bg-white text-black shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]'
                    }`}
                  >
                    <span className="text-lg">☀️</span>
                    <span>Light</span>
                  </button>

                  <button
                    onClick={() => setTheme('dark')}
                    className={`px-4 py-3 border-2 border-black rounded-xl font-black text-xs uppercase tracking-wider transition-all flex flex-col items-center justify-center space-y-2 cursor-pointer ${
                      theme === 'dark'
                        ? 'bg-retro-pink text-black shadow-none translate-x-[2px] translate-y-[2px]'
                        : 'bg-white text-black shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]'
                    }`}
                  >
                    <span className="text-lg">🌙</span>
                    <span>Dark</span>
                  </button>

                  <button
                    onClick={() => setTheme('system')}
                    className={`px-4 py-3 border-2 border-black rounded-xl font-black text-xs uppercase tracking-wider transition-all flex flex-col items-center justify-center space-y-2 cursor-pointer ${
                      theme === 'system'
                        ? 'bg-retro-mint text-black shadow-none translate-x-[2px] translate-y-[2px]'
                        : 'bg-white text-black shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]'
                    }`}
                  >
                    <span className="text-lg">💻</span>
                    <span>System</span>
                  </button>
                </div>
                <p className="text-[10px] text-black/50 dark:text-white/50 font-bold mt-3 uppercase tracking-wide">
                  {theme === 'system' 
                    ? 'Currently syncing with your operating system theme preference.' 
                    : `Theme set manually to ${theme} mode.`}
                </p>
              </div>

              <div className="border-t-2 border-black/10 dark:border-white/10 pt-4">
                <label className="text-xs font-black text-black/60 dark:text-white/60 uppercase tracking-[0.2em] block mb-2">
                  System Diagnostics
                </label>
                <div className="bg-white dark:bg-black/30 border-2 border-black rounded-lg p-3 text-[10px] font-mono text-black dark:text-white space-y-1.5 shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] dark:shadow-[2px_2px_0px_0px_#ffffff]">
                  <div className="flex justify-between">
                    <span className="font-extrabold uppercase">Backend Server:</span>
                    <span className="text-retro-green font-black">ONLINE (8000)</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="font-extrabold uppercase">Vector Index:</span>
                    <span className="text-retro-green font-black">ACTIVE</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="font-extrabold uppercase">Environment:</span>
                    <span className="text-retro-red font-black">DEVELOPMENT</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-8 flex justify-end">
              <button
                onClick={() => setShowConfig(false)}
                className="px-6 py-2.5 bg-black dark:bg-white text-white dark:text-black font-black text-xs uppercase tracking-wider rounded-xl border-3 border-black dark:border-white shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] dark:shadow-[3px_3px_0px_0px_#ffffff] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] dark:hover:shadow-[2px_2px_0px_0px_#ffffff] active:translate-x-[3px] active:translate-y-[3px] active:shadow-none transition-all cursor-pointer"
              >
                Close Settings
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}

function NavItem({ icon, label, active = false, onClick }: { icon: React.ReactNode, label: string, active?: boolean, onClick?: () => void }) {
  return (
    <div className="flex flex-col items-center space-y-1.5 group">
      <div 
        onClick={onClick}
        className={`
          w-13 h-13 rounded-xl cursor-pointer flex items-center justify-center transition-all duration-100 border-3 border-black
          ${active 
            ? 'bg-retro-sand text-black shadow-none translate-x-[2px] translate-y-[2px]' 
            : 'bg-white text-black shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:translate-x-[3px] active:translate-y-[3px] active:shadow-none'
          }
        `}
      >
        {icon}
      </div>
      <span className={`text-[10px] font-black uppercase tracking-tight transition-colors ${active ? 'text-black font-extrabold' : 'text-black/60 group-hover:text-black'}`}>
        {label}
      </span>
    </div>
  );
}

