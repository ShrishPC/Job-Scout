"use client";

import React, { useState } from 'react';
import { ExternalLink, Check, X, MapPin, DollarSign, Loader2, Calendar, Eye, RotateCw, Target, Briefcase, Laptop } from 'lucide-react';
import axios from 'axios';

interface Job {
  id: number;
  title: string;
  company: string;
  description: string;
  location: string;
  salary?: string;
  job_url: string;
  date_posted: string;
  match_score: number;
  experience_required?: number;
  is_rejected?: boolean;
  workplace_type?: string;
}

interface JobCardProps {
  job: Job;
  onApply: (id: number) => void;
  onReject: (id: number) => void;
}

const JobCard: React.FC<JobCardProps> = ({ job, onApply, onReject }) => {
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  const handleInterest = async (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent modal from opening
    setLoading(true);
    const apiHost = typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.hostname}:8000` : 'http://127.0.0.1:8000';
    try {
      await axios.post(`${apiHost}/jobs/interest`, { job_id: job.id, status: 'interested' });
      setSuccess(true);
      setTimeout(() => {
        onApply(job.id);
      }, 1000);
    } catch (err) {
      console.error("Failed to mark interest:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleRejectClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onReject(job.id);
  };

  const scoreColor = job.match_score > 90 ? 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20' : 
                   job.match_score > 75 ? 'text-blue-400 bg-blue-400/10 border-blue-400/20' : 
                   'text-slate-300 bg-slate-400/10 border-slate-400/20';

  const workplaceLabels: { [key: string]: string } = {
    remote: 'Remote',
    hybrid: 'Hybrid',
    onsite: 'On-site',
    negotiable: 'Negotiable',
    unspecified: 'Workplace N/A'
  };

  const workplaceColors: { [key: string]: string } = {
    remote: 'text-sky-400 bg-sky-400/10 border-sky-400/20',
    hybrid: 'text-indigo-400 bg-indigo-400/10 border-indigo-400/20',
    onsite: 'text-amber-400 bg-amber-400/10 border-amber-400/20',
    negotiable: 'text-purple-400 bg-purple-400/10 border-purple-400/20',
    unspecified: 'text-slate-400 bg-slate-400/10 border-slate-400/20'
  };

  return (
    <>
    <div 
      onClick={() => setIsExpanded(true)}
      className={`
      relative group flex flex-col h-full bg-slate-900/40 border rounded-2xl p-6 transition-all duration-300 cursor-pointer
      ${job.is_rejected 
        ? 'border-red-500/10 opacity-60 hover:opacity-100' 
        : 'border-slate-800 hover:border-brand-500/30 hover:bg-slate-900/80 shadow-lg hover:shadow-brand-500/10'
      }
    `}>
      {job.is_rejected && (
        <div className="absolute top-4 right-4 z-10">
          <span className="bg-red-500/10 text-red-400 text-[10px] px-2 py-1 rounded-full border border-red-500/20 font-bold uppercase tracking-widest">
            Archived
          </span>
        </div>
      )}

      <div className="flex justify-between items-start mb-4">
        <div className="flex-1 min-w-0 pr-8">
          <h3 className="font-bold text-slate-100 text-lg leading-snug truncate group-hover:text-brand-400 transition-colors">
            {job.title}
          </h3>
          <p className="text-brand-400 font-semibold text-sm mt-0.5">{job.company}</p>
        </div>
        {!job.is_rejected && (
          <div className={`shrink-0 px-3 py-1 rounded-full border text-[11px] font-black tracking-tight ${scoreColor}`}>
            {Math.round(job.match_score)}%
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3 mb-5">
        <div className="flex items-center text-[11px] font-bold text-slate-200 bg-slate-800/80 px-3 py-2 rounded-xl border border-slate-700 shadow-sm">
          <MapPin className="w-3.5 h-3.5 mr-2 text-brand-400" />
          <span className="truncate">{job.location}</span>
        </div>
        <div className={`flex items-center text-[11px] font-bold px-3 py-2 rounded-xl border shadow-sm ${workplaceColors[job.workplace_type || 'unspecified']}`}>
          <Laptop className="w-3.5 h-3.5 mr-2" />
          <span className="truncate">{workplaceLabels[job.workplace_type || 'unspecified']}</span>
        </div>
        {job.experience_required !== undefined && job.experience_required >= 0 && (
          <div className="flex items-center text-[11px] font-bold text-brand-50 bg-brand-500/20 px-3 py-2 rounded-xl border border-brand-500/40 shadow-sm">
            <Briefcase className="w-3.5 h-3.5 mr-2 text-brand-400" />
            <span className="truncate">{job.experience_required}+ Yrs Exp</span>
          </div>
        )}
        <div className="flex items-center text-[11px] font-bold text-slate-200 bg-slate-800/80 px-3 py-2 rounded-xl border border-slate-700 shadow-sm">
          <Calendar className="w-3.5 h-3.5 mr-2 text-brand-400" />
          <span className="truncate">{job.date_posted}</span>
        </div>
        {job.salary && (
          <div className="col-span-2 flex items-center text-[11px] font-bold text-emerald-50 bg-emerald-500/20 px-3 py-2 rounded-xl border border-emerald-500/40 shadow-sm">
            <DollarSign className="w-3.5 h-3.5 mr-2 text-emerald-400" />
            <span className="truncate">{job.salary}</span>
          </div>
        )}
      </div>

      <p className="text-slate-300 text-xs leading-relaxed line-clamp-3 mb-6 italic opacity-80">
        "{job.description}"
      </p>

      <div className="mt-auto space-y-3">
        <div className="flex space-x-2">
          <button 
            onClick={handleInterest}
            disabled={loading || success}
            className={`
              flex-1 py-3.5 rounded-xl font-black text-[10px] uppercase tracking-[0.15em] flex items-center justify-center space-x-2 transition-all border
              ${success 
                ? 'bg-emerald-500 text-slate-950 border-emerald-400' 
                : job.is_rejected
                  ? 'bg-slate-800 text-slate-300 hover:bg-slate-700 border-slate-700'
                  : 'bg-gradient-to-r from-brand-600 to-brand-400 text-slate-50 border-brand-400/50 hover:from-brand-500 hover:to-brand-300 shadow-lg shadow-brand-500/10'
              }
            `}
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : success ? <Check className="w-4 h-4" /> : job.is_rejected ? <RotateCw className="w-4 h-4" /> : <Target className="w-4 h-4" />}
            <span>{success ? 'In Pipeline' : job.is_rejected ? 'Restore' : 'Track Job'}</span>
          </button>
          
          {!job.is_rejected && (
            <button 
              onClick={handleRejectClick}
              className="px-4 bg-slate-800/50 text-slate-500 rounded-xl hover:bg-red-500/10 hover:text-red-400 border border-slate-800 hover:border-red-500/20 transition-all"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>
    </div>

    {/* Expanded Modal */}
    {isExpanded && (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm" onClick={() => setIsExpanded(false)}>
        <div 
          className="bg-slate-900 border border-slate-800 rounded-3xl p-8 max-w-2xl w-full max-h-[85vh] overflow-y-auto shadow-2xl custom-scrollbar"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex justify-between items-start mb-6">
            <div>
              <h2 className="text-2xl font-black text-slate-100">{job.title}</h2>
              <p className="text-brand-400 font-bold mt-1 text-sm">{job.company}</p>
            </div>
            <button onClick={() => setIsExpanded(false)} className="p-2 rounded-full hover:bg-slate-800 text-slate-400 transition-colors">
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="flex flex-wrap gap-3 mb-8 pb-6 border-b border-slate-800">
            <div className="flex items-center text-xs font-semibold text-slate-300 bg-slate-800/50 px-3 py-1.5 rounded-lg border border-slate-700">
              <MapPin className="w-4 h-4 mr-2 text-slate-500" />
              {job.location}
            </div>
            <div className={`flex items-center text-xs font-semibold px-3 py-1.5 rounded-lg border ${workplaceColors[job.workplace_type || 'unspecified']}`}>
              <Laptop className="w-4 h-4 mr-2" />
              {workplaceLabels[job.workplace_type || 'unspecified']}
            </div>
            {job.experience_required !== undefined && job.experience_required >= 0 && (
              <div className="flex items-center text-xs font-semibold text-brand-300 bg-brand-900/20 px-3 py-1.5 rounded-lg border border-brand-500/20">
                <Briefcase className="w-4 h-4 mr-2 text-brand-500" />
                {job.experience_required}+ Years Experience
              </div>
            )}
            <div className="flex items-center text-xs font-semibold text-slate-300 bg-slate-800/50 px-3 py-1.5 rounded-lg border border-slate-700">
              <Calendar className="w-4 h-4 mr-2 text-slate-500" />
              {job.date_posted}
            </div>
            {job.salary && (
              <div className="flex items-center text-xs font-semibold text-emerald-400 bg-emerald-400/10 px-3 py-1.5 rounded-lg border border-emerald-400/20">
                <DollarSign className="w-4 h-4 mr-1 text-emerald-500" />
                {job.salary}
              </div>
            )}
          </div>

          <div className="mb-8">
            <h4 className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-4">Job Description</h4>
            <div className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap break-words">
              {job.description || "No description available."}
            </div>
          </div>

          <div className="flex space-x-4 pt-6 border-t border-slate-800">
            <button 
              onClick={handleInterest}
              disabled={loading || success}
              className={`
                flex-1 py-4 rounded-xl font-black text-xs uppercase tracking-widest flex items-center justify-center space-x-2 transition-all
                ${success 
                  ? 'bg-emerald-500 text-slate-950' 
                  : 'bg-brand-500 text-slate-950 hover:bg-brand-400 active:scale-[0.98]'
                }
              `}
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : success ? <Check className="w-5 h-5" /> : <Target className="w-5 h-5" />}
              <span>{success ? 'In Pipeline' : 'Track Job'}</span>
            </button>
            <a 
              href={job.job_url}
              target="_blank"
              rel="noopener noreferrer"
              className="px-8 py-4 rounded-xl text-xs font-black uppercase tracking-widest flex items-center justify-center space-x-2 bg-slate-800 text-slate-200 hover:bg-slate-700 transition-all border border-slate-700"
            >
              <Eye className="w-4 h-4" />
              <span>Original Post</span>
            </a>
          </div>
        </div>
      </div>
    )}
    </>
  );
};

export default JobCard;
