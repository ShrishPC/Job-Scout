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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 p-8 min-h-[calc(100vh-12rem)] bg-retro-cream">
            {columns.map((col) => (
                <div key={col.id} className="flex flex-col h-full bg-white border-3 border-black rounded-xl shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] overflow-hidden">
                    <div className="p-4 border-b-3 border-black bg-retro-sand flex items-center justify-between">
                        <h3 className="text-xs font-black uppercase tracking-[0.2em] text-black">
                            {col.title}
                        </h3>
                        <span className="bg-white text-black text-[10px] px-2..5 py-1 rounded border-2 border-black font-black shadow-[1.5px_1.5px_0px_0px_rgba(0,0,0,1)]">
                            {jobs.filter(j => j.status === col.id).length}
                        </span>
                    </div>
                    
                    <div className="p-4 space-y-4 overflow-y-auto flex-1 max-h-[70vh] custom-scrollbar bg-white">
                        {jobs.filter(j => j.status === col.id).map((job) => (
                            <div key={job.id} className="bg-white border-2 border-black rounded-lg p-4 shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[-1px] hover:translate-y-[-1px] hover:shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] transition-all">
                                <div className="flex justify-between items-start mb-3">
                                    <div className="min-w-0 pr-2">
                                        <h4 className="font-extrabold text-black text-[13px] leading-tight truncate">{job.title}</h4>
                                        <p className="text-retro-green text-[11px] font-black mt-0.5 truncate">{job.company}</p>
                                    </div>
                                    <a 
                                        href={job.job_url} 
                                        target="_blank" 
                                        rel="noopener noreferrer"
                                        className="text-black hover:text-retro-red p-1.5 rounded border-2 border-black bg-white shadow-[1.5px_1.5px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[0.5px] hover:translate-y-[0.5px] hover:shadow-[1px_1px_0px_0px_rgba(0,0,0,1)] active:translate-x-[1.5px] active:translate-y-[1.5px] active:shadow-none transition-all"
                                    >
                                        <ExternalLink className="w-3.5 h-3.5" />
                                    </a>
                                </div>
                                
                                <div className="flex items-center space-x-3 text-[10px] text-black/60 font-bold">
                                    <div className="flex items-center">
                                        <MapPin className="w-3.5 h-3.5 mr-1 text-black/40" />
                                        {job.location}
                                    </div>
                                    <div className="flex items-center text-black/75">
                                        <Calendar className="w-3.5 h-3.5 mr-1 text-black/40" />
                                        {job.date_posted}
                                    </div>
                                </div>
                                
                                <div className="flex items-center justify-between mt-4 pt-3 border-t-2 border-black/10">
                                    <button 
                                        onClick={() => updateStatus(job.id, 'rejected')}
                                        className="p-1.5 rounded border-2 border-black bg-white text-black hover:bg-retro-pink shadow-[1.5px_1.5px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[0.5px] hover:translate-y-[0.5px] hover:shadow-[1px_1px_0px_0px_rgba(0,0,0,1)] active:translate-x-[1.5px] active:translate-y-[1.5px] active:shadow-none transition-all"
                                        title="Archive"
                                    >
                                        <Trash2 className="w-3.5 h-3.5" />
                                    </button>
                                    
                                    <div className="flex items-center">
                                        {col.id === 'interested' && (
                                            <button 
                                                onClick={() => updateStatus(job.id, 'applied')}
                                                className="bg-retro-yellow text-black text-[9px] font-black uppercase px-3 py-1.5 rounded border-2 border-black shadow-[1.5px_1.5px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[0.5px] hover:translate-y-[0.5px] hover:shadow-[1px_1px_0px_0px_rgba(0,0,0,1)] active:translate-x-[1.5px] active:translate-y-[1.5px] active:shadow-none transition-all flex items-center"
                                            >
                                                <span>Apply</span>
                                                <ArrowRight className="w-3 h-3 ml-1.5" />
                                            </button>
                                        )}
                                        {col.id === 'applied' && (
                                            <button 
                                                onClick={() => updateStatus(job.id, 'interviewing')}
                                                className="bg-retro-mint text-black text-[9px] font-black uppercase px-3 py-1.5 rounded border-2 border-black shadow-[1.5px_1.5px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[0.5px] hover:translate-y-[0.5px] hover:shadow-[1px_1px_0px_0px_rgba(0,0,0,1)] active:translate-x-[1.5px] active:translate-y-[1.5px] active:shadow-none transition-all flex items-center"
                                            >
                                                <span>Interview</span>
                                                <ArrowRight className="w-3 h-3 ml-1.5" />
                                            </button>
                                        )}
                                        {col.id === 'interviewing' && (
                                            <button 
                                                onClick={() => updateStatus(job.id, 'offered')}
                                                className="bg-retro-green text-white text-[9px] font-black uppercase px-3 py-1.5 rounded border-2 border-black shadow-[1.5px_1.5px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[0.5px] hover:translate-y-[0.5px] hover:shadow-[1px_1px_0px_0px_rgba(0,0,0,1)] active:translate-x-[1.5px] active:translate-y-[1.5px] active:shadow-none transition-all flex items-center"
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
                            <div className="py-12 flex flex-col items-center justify-center opacity-30 group border-2 border-dashed border-black/30 rounded-lg bg-retro-cream/20">
                                <Briefcase className="w-8 h-8 text-black mb-2 group-hover:scale-110 transition-transform" />
                                <p className="text-[9px] font-black uppercase tracking-widest text-black">Empty</p>
                            </div>
                        )}
                    </div>
                </div>
            ))}
        </div>
    );
};

export default KanbanBoard;
