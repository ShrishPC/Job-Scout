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

  const scoreColor = job.match_score > 90 ? 'text-white bg-retro-green border-2 border-black' : 
                   job.match_score > 75 ? 'text-black bg-retro-yellow border-2 border-black' : 
                   'text-black bg-retro-sand border-2 border-black';

  const workplaceLabels: { [key: string]: string } = {
    remote: 'Remote',
    hybrid: 'Hybrid',
    onsite: 'On-site',
    negotiable: 'Negotiable',
    unspecified: 'Workplace N/A'
  };

  const workplaceColors: { [key: string]: string } = {
    remote: 'text-black bg-retro-mint border-2 border-black shadow-[1.5px_1.5px_0px_0px_rgba(0,0,0,1)]',
    hybrid: 'text-black bg-retro-yellow border-2 border-black shadow-[1.5px_1.5px_0px_0px_rgba(0,0,0,1)]',
    onsite: 'text-black bg-retro-pink border-2 border-black shadow-[1.5px_1.5px_0px_0px_rgba(0,0,0,1)]',
    negotiable: 'text-black bg-retro-sand border-2 border-black shadow-[1.5px_1.5px_0px_0px_rgba(0,0,0,1)]',
    unspecified: 'text-black bg-white border-2 border-black shadow-[1.5px_1.5px_0px_0px_rgba(0,0,0,1)]'
  };

  const cardBackgrounds = ['bg-white', 'bg-retro-yellow', 'bg-retro-pink', 'bg-retro-sand', 'bg-retro-mint'];
  const bgIndex = typeof job.id === 'number' ? job.id : 0;
  const cardBg = job.is_rejected ? 'bg-gray-100' : cardBackgrounds[bgIndex % cardBackgrounds.length];

  return (
    <>
    <div 
      onClick={() => setIsExpanded(true)}
      className={`
      relative group flex flex-col h-full ${cardBg} border-3 border-black rounded-xl p-6 transition-all duration-100 cursor-pointer job-card
      ${job.is_rejected 
        ? 'opacity-60 hover:opacity-100 border-2 shadow-none' 
        : 'shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[3px_3px_0px_0px_rgba(0,0,0,1)]'
      }
    `}>
      {job.is_rejected && (
        <div className="absolute top-4 right-4 z-10">
          <span className="bg-retro-red text-white text-[10px] px-2 py-1 border-2 border-black font-black uppercase tracking-widest">
            Archived
          </span>
        </div>
      )}

      <div className="flex justify-between items-start mb-4">
        <div className="flex-1 min-w-0 pr-8">
          <h3 className="font-black text-black text-lg leading-snug truncate group-hover:text-retro-red transition-colors">
            {job.title}
          </h3>
          <p className="text-retro-green font-black text-sm mt-0.5">{job.company}</p>
        </div>
        {!job.is_rejected && (
          <div className={`shrink-0 px-3 py-1 rounded-md text-[11px] font-black tracking-tight score-tag ${scoreColor}`}>
            {Math.round(job.match_score)}%
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3 mb-5">
        <div className="flex items-center text-[11px] font-black text-black bg-white px-3 py-2 rounded-lg border-2 border-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
          <MapPin className="w-3.5 h-3.5 mr-2 text-black/60" />
          <span className="truncate">{job.location}</span>
        </div>
        <div className={`flex items-center text-[11px] font-black px-3 py-2 rounded-lg ${workplaceColors[job.workplace_type || 'unspecified']}`}>
          <Laptop className="w-3.5 h-3.5 mr-2 text-black/60" />
          <span className="truncate">{workplaceLabels[job.workplace_type || 'unspecified']}</span>
        </div>
        {job.experience_required !== undefined && job.experience_required >= 0 && (
          <div className="flex items-center text-[11px] font-black text-black bg-retro-sand px-3 py-2 rounded-lg border-2 border-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
            <Briefcase className="w-3.5 h-3.5 mr-2 text-black/60" />
            <span className="truncate">{job.experience_required}+ Yrs Exp</span>
          </div>
        )}
        <div className="flex items-center text-[11px] font-black text-black bg-white px-3 py-2 rounded-lg border-2 border-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
          <Calendar className="w-3.5 h-3.5 mr-2 text-black/60" />
          <span className="truncate">{job.date_posted}</span>
        </div>
        {job.salary && (
          <div className="col-span-2 flex items-center text-[11px] font-black text-black bg-retro-pink px-3 py-2 rounded-lg border-2 border-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
            <DollarSign className="w-3.5 h-3.5 mr-2 text-black/60" />
            <span className="truncate">{job.salary}</span>
          </div>
        )}
      </div>

      <p className="text-black/80 text-xs leading-relaxed line-clamp-2 overflow-hidden mb-6 font-bold bg-retro-cream/40 pt-2 pb-4 px-4 border-2 border-black border-dashed rounded-lg text-left">
        "{job.description}"
      </p>

      <div className="mt-auto space-y-3">
        <div className="flex space-x-3">
          <button 
            onClick={handleInterest}
            disabled={loading || success}
            className={`
              flex-1 py-3.5 rounded-lg font-black text-[10px] uppercase tracking-[0.15em] flex items-center justify-center space-x-2 transition-all border-2 border-black
              ${success 
                ? 'bg-retro-green text-white shadow-none translate-x-[2px] translate-y-[2px]' 
                : job.is_rejected
                  ? 'bg-retro-sand text-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[0.5px] hover:translate-y-[0.5px] hover:shadow-[1.5px_1.5px_0px_0px_rgba(0,0,0,1)] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none'
                  : 'bg-retro-red text-white shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[0.5px] hover:translate-y-[0.5px] hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none'
              }
            `}
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : success ? <Check className="w-4 h-4" /> : job.is_rejected ? <RotateCw className="w-4 h-4" /> : <Target className="w-4 h-4" />}
            <span>{success ? 'In Pipeline' : job.is_rejected ? 'Restore' : 'Track Job'}</span>
          </button>
          
          {!job.is_rejected && (
            <button 
              onClick={handleRejectClick}
              className="px-4 bg-white text-black border-2 border-black rounded-lg shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:bg-retro-pink hover:translate-x-[0.5px] hover:translate-y-[0.5px] hover:shadow-[1.5px_1.5px_0px_0px_rgba(0,0,0,1)] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none transition-all"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>
    </div>

    {/* Expanded Modal */}
    {isExpanded && (
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60" onClick={() => setIsExpanded(false)}>
        <div 
          className="bg-retro-cream border-4 border-black rounded-xl max-w-2xl w-full max-h-[85vh] flex flex-col shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex-1 overflow-y-auto overflow-x-hidden p-8 rounded-[inherit] custom-scrollbar">
            <div className="flex justify-between items-start mb-6">
            <div>
              <h2 className="text-2xl font-black text-black">{job.title}</h2>
              <p className="text-retro-green font-black mt-1 text-sm">{job.company}</p>
            </div>
            <button onClick={() => setIsExpanded(false)} className="p-2 border-2 border-black bg-white rounded-lg text-black hover:bg-retro-pink shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[0.5px] hover:translate-y-[0.5px] hover:shadow-[1.5px_1.5px_0px_0px_rgba(0,0,0,1)] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none transition-all">
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="flex flex-wrap gap-3 mb-8 pb-6 border-b-2 border-black/20">
            <div className="flex items-center text-xs font-black text-black bg-white px-3 py-1.5 rounded-lg border-2 border-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
              <MapPin className="w-4 h-4 mr-2 text-black/60" />
              {job.location}
            </div>
            <div className={`flex items-center text-xs font-black px-3 py-1.5 rounded-lg ${workplaceColors[job.workplace_type || 'unspecified']}`}>
              <Laptop className="w-4 h-4 mr-2 text-black/60" />
              {workplaceLabels[job.workplace_type || 'unspecified']}
            </div>
            {job.experience_required !== undefined && job.experience_required >= 0 && (
              <div className="flex items-center text-xs font-black text-black bg-retro-sand px-3 py-1.5 rounded-lg border-2 border-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
                <Briefcase className="w-4 h-4 mr-2 text-black/60" />
                {job.experience_required}+ Years Experience
              </div>
            )}
            <div className="flex items-center text-xs font-black text-black bg-white px-3 py-1.5 rounded-lg border-2 border-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
              <Calendar className="w-4 h-4 mr-2 text-black/60" />
              {job.date_posted}
            </div>
            {job.salary && (
              <div className="flex items-center text-xs font-black text-black bg-retro-pink px-3 py-1.5 rounded-lg border-2 border-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
                <DollarSign className="w-4 h-4 mr-1 text-black/60" />
                {job.salary}
              </div>
            )}
          </div>

          <div className="mb-8 bg-white p-6 border-3 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] rounded-lg">
            <h4 className="text-[11px] font-black uppercase tracking-widest text-black/60 mb-4 border-b-2 border-black/10 pb-2">Job Description</h4>
            <div className="text-sm text-black font-medium leading-relaxed whitespace-pre-wrap break-words">
              {job.description || "No description available."}
            </div>
          </div>

          <div className="flex space-x-4 pt-6 border-t-2 border-black/20">
            <button 
              onClick={handleInterest}
              disabled={loading || success}
              className={`
                flex-1 py-4 rounded-lg font-black text-xs uppercase tracking-widest flex items-center justify-center space-x-2 transition-all border-3 border-black
                ${success 
                  ? 'bg-retro-green text-white shadow-none translate-x-[2px] translate-y-[2px]' 
                  : 'bg-retro-red text-white shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:translate-x-[3px] active:translate-y-[3px] active:shadow-none'
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
              className="px-8 py-4 rounded-lg text-xs font-black uppercase tracking-widest flex items-center justify-center space-x-2 bg-white text-black border-3 border-black shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:translate-x-[3px] active:translate-y-[3px] active:shadow-none transition-all"
            >
              <Eye className="w-4 h-4" />
              <span>Original Post</span>
            </a>
          </div>
          </div>
        </div>
      </div>
    )}
    </>
  );
};

export default JobCard;
