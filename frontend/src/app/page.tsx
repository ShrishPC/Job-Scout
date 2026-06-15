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
    <main className="min-h-screen bg-slate-950 text-slate-50 flex overflow-hidden">
      {/* Sidebar Navigation */}
      <nav className="w-20 bg-slate-900 border-r border-slate-800 flex flex-col items-center py-8 space-y-10 z-20 shadow-2xl relative">
        <div 
          onClick={() => setView('radar')}
          className={`w-12 h-12 rounded-2xl flex items-center justify-center shadow-[0_0_20px_rgba(56,171,248,0.3)] group cursor-pointer transition-transform active:scale-95 ${view === 'radar' ? 'bg-brand-400 text-slate-50 scale-105' : 'bg-brand-500 text-slate-50 hover:scale-105'}`}
          title="Market Intelligence Radar"
        >
          <Radar className="w-7 h-7" />
        </div>
        
        <div className="flex-1 flex flex-col space-y-6">
          <NavItem 
            icon={<Target className="w-5 h-5" />} 
            label="Hunt"
            active={view === 'hunt'} 
            onClick={() => setView('hunt')} 
          />
          <NavItem 
            icon={<Layout className="w-5 h-5" />} 
            label="Pipeline"
            active={view === 'board'} 
            onClick={() => setView('board')} 
          />
          <NavItem 
            icon={<Database className="w-5 h-5" />} 
            label="Vault" 
            active={view === 'vault'}
            onClick={() => setView('vault')}
          />
          <NavItem 
            icon={<User className="w-5 h-5" />} 
            label="Profile" 
            active={view === 'profile'}
            onClick={() => setView('profile')}
          />
        </div>

        <div className="pt-6 border-t border-slate-800 w-full flex flex-col items-center space-y-6">
            <NavItem icon={<SettingsIcon className="w-5 h-5" />} label="Config" />
            <NavItem icon={<LogOut className="w-5 h-5 text-red-400" />} label="Exit" />
        </div>
      </nav>

      {/* Main Container */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Header */}
        <header className="h-20 bg-slate-950/50 backdrop-blur-xl border-b border-slate-900 flex items-center justify-between px-10 flex-shrink-0 z-10">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-brand-500/10 rounded-lg flex items-center justify-center border border-brand-500/20">
               <Sparkles className="w-4 h-4 text-brand-400" />
            </div>
            <h1 className="text-xl font-black tracking-tighter uppercase">
              JOB<span className="text-brand-400">SCOUT</span>
            </h1>
          </div>

          {view === 'hunt' && (
            <div className="flex items-center space-x-6">
              <div className="flex bg-slate-900 border border-slate-800 rounded-2xl p-1.5 shadow-inner group transition-all hover:border-slate-700">
                  <div className="flex items-center px-4">
                    <Search className="w-3.5 h-3.5 text-slate-500 mr-2" />
                    <input 
                      type="text" 
                      placeholder="Filter by Role" 
                      className="bg-transparent border-none focus:ring-0 text-xs w-48 text-slate-200 placeholder-slate-600 font-bold"
                      value={searchParams.keyword}
                      onChange={(e) => setSearchParams({...searchParams, keyword: e.target.value})}
                    />
                    {searchParams.keyword && (
                      <button onClick={() => setSearchParams({...searchParams, keyword: ''})} className="ml-2">
                        <X className="w-3 h-3 text-slate-600 hover:text-slate-400" />
                      </button>
                    )}
                  </div>
                  <div className="w-px h-6 bg-slate-800 self-center"></div>
                  <div className="flex items-center px-4 relative">
                    <input 
                      type="text" 
                      placeholder="Location" 
                      className="bg-transparent border-none focus:ring-0 text-xs w-36 text-slate-200 placeholder-slate-600 font-bold"
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
                        <X className="w-3 h-3 text-slate-600 hover:text-slate-400" />
                      </button>
                    )}
                    
                    {showLocationSuggestions && uniqueLocations.length > 0 && (
                      <div className="absolute top-full left-0 mt-2 w-56 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl py-2 z-50 animate-in fade-in slide-in-from-top-1">
                        <div className="px-3 py-1 mb-1 border-b border-slate-800">
                           <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Available Locations</span>
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
                                className="px-4 py-2 text-xs font-bold text-slate-300 hover:bg-slate-800 hover:text-brand-400 cursor-pointer transition-colors flex items-center"
                              >
                                <MapPin className="w-3 h-3 mr-2 text-slate-500" />
                                {loc}
                              </div>
                            ))}
                        </div>
                        <div 
                          className="border-t border-slate-800 mt-1 px-4 py-2 text-[10px] text-center text-slate-500 hover:text-slate-300 cursor-pointer"
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
                className="h-11 bg-brand-500 text-slate-950 px-8 rounded-2xl text-[11px] font-black uppercase tracking-widest flex items-center hover:bg-brand-400 transition-all disabled:opacity-50 active:scale-95 shadow-lg shadow-brand-500/10"
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
                        <h2 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">Profile Sync</h2>
                        {parsedData && <div className="w-2 h-2 bg-brand-400 rounded-full shadow-[0_0_8px_rgba(56,171,248,0.5)]"></div>}
                      </div>
                      {parsedData && (
                        <button 
                          onClick={handleDeleteProfile}
                          className="p-1.5 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-400/5 transition-all"
                          title="Delete Stored Profile"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                    <FileUpload onUploadSuccess={handleResumeSync} />
                  </section>

                  {parsedData && (
                    <section className="bg-slate-900/40 border border-slate-800 rounded-2xl overflow-hidden backdrop-blur-sm animate-in fade-in slide-in-from-bottom-4 duration-500">
                      <div className="p-8 pb-6 border-b border-slate-800/50">
                          <h3 className="text-2xl font-black tracking-tight text-slate-100">{parsedData.parsed_json?.full_name}</h3>
                          <p className="text-brand-400 text-xs font-bold mt-1 uppercase tracking-widest opacity-90">{parsedData.parsed_json?.email}</p>
                      </div>
                      <div className="p-8 space-y-10">
                        <div>
                          <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-4">Key Skills</h4>
                          <div className="flex flex-wrap gap-2">
                            {parsedData.parsed_json?.skills?.map((skill: string, i: number) => (
                              <span key={i} className="px-3 py-2 bg-slate-800/50 text-slate-200 rounded-xl text-[11px] font-bold border border-slate-800 hover:border-brand-500/30 transition-colors">
                                {skill}
                              </span>
                            ))}
                          </div>
                        </div>
                        <div>
                          <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-4">Recent History</h4>
                          <div className="space-y-6">
                            {parsedData.parsed_json?.experience?.slice(0, 2).map((exp: any, i: number) => (
                              <div key={i} className="relative pl-6 before:content-[''] before:absolute before:left-0 before:top-1.5 before:w-1.5 before:h-1.5 before:bg-brand-500 before:rounded-full before:shadow-[0_0_10px_rgba(56,171,248,0.5)]">
                                <p className="font-bold text-slate-200 text-sm">{exp.title}</p>
                                <p className="text-brand-400 text-[11px] font-bold mt-0.5">{exp.company}</p>
                                <p className="text-slate-400 text-[10px] mt-1 uppercase font-black tracking-tighter opacity-70">{exp.duration}</p>
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
                      <h2 className="text-2xl font-black text-slate-100 tracking-tight uppercase italic">Best Matches</h2>
                      <p className="text-slate-400 text-[10px] font-bold uppercase tracking-widest mt-1">Found based on your resume</p>
                    </div>
                    <div className="flex space-x-3">
                      <button 
                        onClick={() => setShowFilters(!showFilters)}
                        className={`px-4 py-2.5 rounded-xl border flex items-center space-x-2 transition-all font-bold text-xs ${showFilters ? 'bg-brand-500/10 text-brand-400 border-brand-500/30' : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'}`}
                      >
                        <SlidersHorizontal className="w-4 h-4" />
                        <span>Filter & Sort</span>
                      </button>
                      <button 
                        onClick={() => parsedData?.embedding && fetchMatches(parsedData.embedding, selectedWorkplaceTypes)}
                        className="p-3 bg-slate-900 border border-slate-800 rounded-xl hover:bg-slate-800 transition-all active:scale-95"
                        title="Refresh Matches"
                      >
                        <RotateCw className={`w-4 h-4 text-slate-400 ${loadingJobs ? 'animate-spin text-brand-400' : ''}`} />
                      </button>
                    </div>
                  </div>

                  {showFilters && parsedData && (
                    <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 flex flex-wrap gap-6 animate-in fade-in slide-in-from-top-2">
                      <div className="flex flex-col space-y-2">
                        <label className="text-[10px] font-black uppercase tracking-widest text-slate-500">Max Experience Required</label>
                        <div className="flex items-center space-x-3">
                          <input 
                            type="range" 
                            min="0" 
                            max="15" 
                            step="1"
                            value={maxExperience === '' ? 15 : maxExperience}
                            onChange={(e) => setMaxExperience(Number(e.target.value))}
                            className="w-48 accent-brand-500"
                          />
                          <span className="text-xs font-bold text-brand-400 bg-brand-500/10 px-2 py-1 rounded-md border border-brand-500/20 w-16 text-center">
                            {maxExperience === '' ? 'Any' : `${maxExperience} Yrs`}
                          </span>
                          {maxExperience !== '' && (
                            <button onClick={() => setMaxExperience('')} className="text-[10px] text-slate-500 hover:text-red-400 uppercase font-bold tracking-wider ml-2">Clear</button>
                          )}
                        </div>
                      </div>

                      <div className="w-px bg-slate-800 hidden md:block"></div>

                      <div className="flex flex-col space-y-2">
                        <label className="text-[10px] font-black uppercase tracking-widest text-slate-500">Workplace Type</label>
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
                                className={`px-3 py-1.5 rounded-lg text-xs font-bold border transition-all ${
                                  isSelected 
                                    ? 'bg-brand-500/10 text-brand-400 border-brand-500/30 shadow-[0_0_10px_rgba(56,171,248,0.1)]' 
                                    : 'bg-slate-950 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-slate-300'
                                }`}
                              >
                                {label}
                              </button>
                            );
                          })}
                        </div>
                      </div>

                      <div className="w-px bg-slate-800 hidden md:block"></div>

                      <div className="flex flex-col space-y-2">
                        <label className="text-[10px] font-black uppercase tracking-widest text-slate-500">Sort By</label>
                        <div className="flex bg-slate-950 p-1 rounded-xl border border-slate-800">
                          <button 
                            onClick={() => setSortBy('match')}
                            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${sortBy === 'match' ? 'bg-slate-800 text-slate-100' : 'text-slate-500 hover:text-slate-300'}`}
                          >
                            Best Match
                          </button>
                          <button 
                            onClick={() => setSortBy('exp_asc')}
                            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${sortBy === 'exp_asc' ? 'bg-slate-800 text-slate-100' : 'text-slate-500 hover:text-slate-300'}`}
                          >
                            Exp: Low - High
                          </button>
                          <button 
                            onClick={() => setSortBy('exp_desc')}
                            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${sortBy === 'exp_desc' ? 'bg-slate-800 text-slate-100' : 'text-slate-500 hover:text-slate-300'}`}
                          >
                            Exp: High - Low
                          </button>
                        </div>
                      </div>
                    </div>
                  )}

                  {!parsedData ? (
                    <div className="bg-slate-900/20 rounded-3xl p-24 text-center border border-slate-800/50 border-dashed group">
                      <div className="w-16 h-16 bg-slate-900 rounded-2xl flex items-center justify-center mx-auto mb-6 border border-slate-800 group-hover:border-brand-500/40 transition-all transform group-hover:rotate-6">
                        <Target className="w-8 h-8 text-slate-600 group-hover:text-brand-400 transition-colors" />
                      </div>
                      <h3 className="text-lg font-bold text-slate-100 mb-2">Sync Profile</h3>
                      <p className="text-slate-300 max-w-xs mx-auto text-xs leading-relaxed font-medium">
                        Upload your resume to get personalized job matches based on your background.
                      </p>
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {loadingJobs ? (
                          <div className="col-span-full py-32 flex flex-col items-center">
                              <Loader2 className="w-10 h-10 animate-spin text-brand-500 mb-6" />
                              <p className="text-slate-400 font-black tracking-[0.3em] text-[10px] uppercase">Finding matches...</p>
                          </div>
                      ) : jobs.length === 0 ? (
                          <div className="col-span-full py-24 text-center bg-slate-900/40 rounded-3xl border border-slate-800">
                              <p className="text-slate-300 font-bold text-sm italic">No jobs found. Click "Sync Jobs" above.</p>
                          </div>
                      ) : filteredJobs.length === 0 ? (
                          <div className="col-span-full py-24 text-center bg-slate-900/40 rounded-3xl border border-slate-800 border-dashed">
                              <p className="text-slate-300 font-bold text-sm italic">No matches found for "{searchParams.keyword}" in "{searchParams.location}".</p>
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
                    <h2 className="text-3xl font-black text-slate-100 tracking-tighter uppercase italic">Job Tracker</h2>
                    <p className="text-slate-400 text-[10px] font-black uppercase tracking-[0.3em] mt-1">Manage your applications</p>
                 </div>
              </div>
              <KanbanBoard />
            </div>
          ) : view === 'vault' ? (
            <div className="max-w-[1600px] mx-auto p-10 pb-20">
              <div className="flex items-end justify-between mb-10 px-4">
                 <div>
                    <h2 className="text-3xl font-black text-slate-100 tracking-tighter uppercase italic">Resume Vault</h2>
                    <p className="text-slate-400 text-[10px] font-black uppercase tracking-[0.3em] mt-1">Manage your professional assets</p>
                 </div>
              </div>
              <VaultView onActiveProfileChanged={handleResumeSync} />
            </div>
          ) : view === 'profile' ? (
            <div className="max-w-[1600px] mx-auto p-10 pb-20">
              <div className="flex items-end justify-between mb-10 px-4">
                 <div>
                    <h2 className="text-3xl font-black text-slate-100 tracking-tighter uppercase italic">Neural Profile</h2>
                    <p className="text-slate-400 text-[10px] font-black uppercase tracking-[0.3em] mt-1">Active candidate details</p>
                 </div>
              </div>
              <ProfileView parsedData={parsedData} />
            </div>
          ) : (
            <div className="max-w-[1600px] mx-auto p-10 pb-20">
              <div className="flex items-end justify-between mb-10 px-4">
                 <div>
                    <h2 className="text-3xl font-black text-slate-100 tracking-tighter uppercase italic">Market Intelligence</h2>
                    <p className="text-slate-400 text-[10px] font-black uppercase tracking-[0.3em] mt-1">Real-time Radar Report</p>
                 </div>
              </div>
              <RadarView jobs={jobs} parsedData={parsedData} />
            </div>
          )}
        </div>
      </div>
    </main>
  );
}

function NavItem({ icon, label, active = false, onClick }: { icon: React.ReactNode, label: string, active?: boolean, onClick?: () => void }) {
  return (
    <div className="flex flex-col items-center space-y-1.5 group">
      <div 
        onClick={onClick}
        className={`
          w-11 h-11 rounded-xl cursor-pointer flex items-center justify-center transition-all duration-300
          ${active 
            ? 'bg-brand-500/10 text-brand-400 border border-brand-500/30 shadow-[0_0_15px_rgba(56,171,248,0.1)]' 
            : 'text-slate-600 hover:text-slate-300 hover:bg-slate-800/50'
          }
        `}
      >
        {icon}
      </div>
      <span className={`text-[9px] font-black uppercase tracking-tighter transition-colors ${active ? 'text-brand-400' : 'text-slate-700 group-hover:text-slate-500'}`}>
        {label}
      </span>
    </div>
  );
}
