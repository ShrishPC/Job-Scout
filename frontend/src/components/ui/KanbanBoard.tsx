"use client";

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ExternalLink, ArrowRight, Trash2, Loader2, Info, Calendar, MapPin, Briefcase } from 'lucide-react';

interface BoardJob {
    id: number;
    match_id: number;
    title: string;
    company: string;
    location: string;
    status: string;
    job_url: string;
    date_posted: string;
}

const KanbanBoard = () => {
    const [jobs, setJobs] = useState<BoardJob[]>([]);
    const [loading, setLoading] = useState(true);

    const apiHost = typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.hostname}:8000` : 'http://127.0.0.1:8000';

    const fetchBoard = async () => {
        setLoading(true);
        try {
            const response = await axios.get(`${apiHost}/jobs/board`);
            setJobs(response.data);
        } catch (err) {
            console.error("Failed to fetch board:", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchBoard();
    }, []);

    const updateStatus = async (jobId: number, newStatus: string) => {
        try {
            await axios.post(`${apiHost}/jobs/interest`, { job_id: jobId, status: newStatus });
            fetchBoard();
        } catch (err) {
            console.error("Failed to update status:", err);
        }
    };

    const columns = [
        { id: 'interested', title: 'Interested', color: 'slate' },
        { id: 'applied', title: 'Applied', color: 'brand' },
        { id: 'interviewing', title: 'Interviewing', color: 'emerald' },
        { id: 'offered', title: 'Offer', color: 'amber' }
    ];

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center py-32">
                <Loader2 className="w-8 h-8 animate-spin text-brand-500 mb-4" />
                <p className="text-slate-500 font-bold uppercase tracking-widest text-[10px]">Loading Tracker...</p>
            </div>
        );
    }

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 p-8 min-h-[calc(100vh-12rem)]">
            {columns.map((col) => (
                <div key={col.id} className="flex flex-col h-full bg-slate-900/30 border border-slate-800/50 rounded-2xl">
                    <div className="p-4 border-b border-slate-800/50 flex items-center justify-between">
                        <h3 className="text-xs font-black uppercase tracking-[0.2em] text-slate-300">
                            {col.title}
                        </h3>
                        <span className="bg-slate-800/80 text-slate-200 text-[10px] px-2 py-0.5 rounded-md border border-slate-700 font-bold">
                            {jobs.filter(j => j.status === col.id).length}
                        </span>
                    </div>
                    
                    <div className="p-3 space-y-3 overflow-y-auto flex-1 max-h-[70vh] custom-scrollbar">
                        {jobs.filter(j => j.status === col.id).map((job) => (
                            <div key={job.id} className="group bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-sm hover:border-slate-700 transition-all">
                                <div className="flex justify-between items-start mb-3">
                                    <div className="min-w-0 pr-2">
                                        <h4 className="font-bold text-slate-100 text-[13px] leading-tight truncate">{job.title}</h4>
                                        <p className="text-brand-400 text-[11px] font-semibold mt-0.5 truncate">{job.company}</p>
                                    </div>
                                    <a 
                                        href={job.job_url} 
                                        target="_blank" 
                                        rel="noopener noreferrer"
                                        className="text-slate-400 hover:text-brand-400 p-1.5 rounded-lg border border-slate-800 hover:bg-slate-800 transition-all"
                                    >
                                        <ExternalLink className="w-3 h-3" />
                                    </a>
                                </div>
                                
                                <div className="flex items-center space-x-3 text-[10px] text-slate-400 font-medium">
                                    <div className="flex items-center">
                                        <MapPin className="w-3 h-3 mr-1 opacity-50" />
                                        {job.location}
                                    </div>
                                    <div className="flex items-center text-slate-300">
                                        <Calendar className="w-3 h-3 mr-1 opacity-50" />
                                        {job.date_posted}
                                    </div>
                                </div>
                                
                                <div className="flex items-center justify-between mt-4 pt-3 border-t border-slate-800/50">
                                    <button 
                                        onClick={() => updateStatus(job.id, 'rejected')}
                                        className="p-1.5 rounded-lg text-slate-600 hover:text-red-400 hover:bg-red-400/5 border border-transparent hover:border-red-400/10 transition-all"
                                        title="Archive"
                                    >
                                        <Trash2 className="w-3.5 h-3.5" />
                                    </button>
                                    
                                    <div className="flex items-center">
                                        {col.id === 'interested' && (
                                            <button 
                                                onClick={() => updateStatus(job.id, 'applied')}
                                                className="bg-brand-500 text-slate-950 text-[10px] font-black uppercase px-3 py-1.5 rounded-lg hover:bg-brand-400 transition-all flex items-center"
                                            >
                                                <span>Apply</span>
                                                <ArrowRight className="w-3 h-3 ml-1.5" />
                                            </button>
                                        )}
                                        {col.id === 'applied' && (
                                            <button 
                                                onClick={() => updateStatus(job.id, 'interviewing')}
                                                className="bg-slate-800 text-slate-200 text-[10px] font-black uppercase px-3 py-1.5 rounded-lg hover:bg-slate-700 transition-all flex items-center"
                                            >
                                                <span>Interview</span>
                                                <ArrowRight className="w-3 h-3 ml-1.5" />
                                            </button>
                                        )}
                                        {col.id === 'interviewing' && (
                                            <button 
                                                onClick={() => updateStatus(job.id, 'offered')}
                                                className="bg-emerald-500 text-slate-950 text-[10px] font-black uppercase px-3 py-1.5 rounded-lg hover:bg-emerald-400 transition-all flex items-center"
                                            >
                                                <span>Offer</span>
                                                <ArrowRight className="w-3 h-3 ml-1.5" />
                                            </button>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                        
                        {jobs.filter(j => j.status === col.id).length === 0 && (
                            <div className="py-10 flex flex-col items-center justify-center opacity-20 group">
                                <Briefcase className="w-8 h-8 text-slate-600 mb-2 group-hover:scale-110 transition-transform" />
                                <p className="text-[9px] font-black uppercase tracking-widest text-slate-600">Empty</p>
                            </div>
                        )}
                    </div>
                </div>
            ))}
        </div>
    );
};

export default KanbanBoard;
