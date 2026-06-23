"use client";

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Sparkles, Loader2, Copy, FileText, Download, Check, AlertCircle, RefreshCw, Briefcase, Plus, User, Laptop } from 'lucide-react';

interface BoardJob {
    id: number;
    title: string;
    company: string;
    location: string;
    status: string;
}

interface ActiveResume {
    filename: string;
    parsed_json?: {
        full_name?: string;
        email?: string;
    };
}

const AITailorView = () => {
    const [jobs, setJobs] = useState<BoardJob[]>([]);
    const [activeResume, setActiveResume] = useState<ActiveResume | null>(null);
    const [loadingJobs, setLoadingJobs] = useState(true);
    
    // Form states
    const [selectedJobId, setSelectedJobId] = useState<string>('');
    const [isCustomJob, setIsCustomJob] = useState(false);
    const [customTitle, setCustomTitle] = useState('');
    const [customCompany, setCustomCompany] = useState('');
    const [customDesc, setCustomDesc] = useState('');
    const [mode, setMode] = useState<'tailor' | 'cover_letter'>('tailor');
    
    // Output states
    const [generating, setGenerating] = useState(false);
    const [result, setResult] = useState<string>('');
    const [error, setError] = useState<string | null>(null);
    const [copied, setCopied] = useState(false);

    const apiHost = typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.hostname}:8000` : 'http://127.0.0.1:8000';

    const fetchData = async () => {
        setLoadingJobs(true);
        setError(null);
        try {
            // Fetch Board Jobs
            const jobsRes = await axios.get(`${apiHost}/jobs/board`);
            // filter out rejected/archived jobs
            const activeJobs = jobsRes.data.filter((j: BoardJob) => j.status !== 'rejected');
            setJobs(activeJobs);
            if (activeJobs.length > 0) {
                setSelectedJobId(activeJobs[0].id.toString());
            } else {
                setIsCustomJob(true);
            }

            // Fetch Active Resume
            const resumeRes = await axios.get(`${apiHost}/resume/active`);
            if (resumeRes.data) {
                setActiveResume(resumeRes.data);
            }
        } catch (err) {
            console.error("Failed to load initial data:", err);
            setError("Could not load tracking board jobs or active resume. Make sure backend is running.");
        } finally {
            setLoadingJobs(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handleGenerate = async () => {
        setGenerating(true);
        setError(null);
        setResult('');
        setCopied(false);

        const payload: any = {
            mode: mode
        };

        if (isCustomJob) {
            if (!customTitle.trim() || !customDesc.trim()) {
                setError("Please fill in the Job Title and Job Description.");
                setGenerating(false);
                return;
            }
            payload.custom_job_title = customTitle;
            payload.custom_company = customCompany || "Target Company";
            payload.custom_job_description = customDesc;
        } else {
            if (!selectedJobId) {
                setError("Please select a job from the list or check 'Use Custom Job'.");
                setGenerating(false);
                return;
            }
            payload.job_id = parseInt(selectedJobId);
        }

        try {
            const response = await axios.post(`${apiHost}/ai/generate`, payload);
            setResult(response.data.result);
        } catch (err: any) {
            console.error("Failed to generate AI assets:", err);
            setError(err.response?.data?.detail || "Local AI Generation failed. Ensure you have an active resume uploaded in the Vault.");
        } finally {
            setGenerating(false);
        }
    };

    const handleCopy = () => {
        if (!result) return;
        navigator.clipboard.writeText(result);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const handleDownload = () => {
        if (!result) return;
        const filename = mode === 'tailor' ? 'tailored_resume_suggestions.txt' : 'cover_letter.txt';
        const element = document.createElement("a");
        const file = new Blob([result], {type: 'text/plain'});
        element.href = URL.createObjectURL(file);
        element.download = filename;
        document.body.appendChild(element);
        element.click();
        document.body.removeChild(element);
    };

    return (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 min-h-[calc(100vh-12rem)] bg-retro-cream p-1">
            {/* Left Column: Form & Configuration */}
            <div className="lg:col-span-5 flex flex-col space-y-6">
                
                {/* Active Resume Status Card */}
                <div className="bg-white border-3 border-black rounded-xl p-5 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] relative overflow-hidden">
                    <div className="absolute right-0 top-0 bg-retro-mint border-b-3 border-l-3 border-black text-black text-[9px] font-black uppercase tracking-wider px-3 py-1.5 shadow-none">
                        Active Profile
                    </div>
                    <h3 className="text-xs font-black uppercase tracking-widest text-black/60 mb-3 flex items-center">
                        <User className="w-3.5 h-3.5 mr-1.5 text-black" />
                        Target Resume Source
                    </h3>
                    {activeResume ? (
                        <div>
                            <p className="font-extrabold text-black text-sm truncate">{activeResume.filename}</p>
                            <p className="text-retro-green text-xs font-black mt-0.5">
                                {activeResume.parsed_json?.full_name || 'Anonymous User'}
                            </p>
                        </div>
                    ) : (
                        <div className="bg-retro-pink/20 border-2 border-black border-dashed p-3 rounded-lg text-center">
                            <p className="text-xs font-black text-retro-red uppercase tracking-wider">No Active Resume Detected!</p>
                            <p className="text-[10px] font-bold text-black/60 mt-1">Please upload a resume in the Resume Vault tab first.</p>
                        </div>
                    )}
                </div>

                {/* Generator Configuration */}
                <div className="bg-white border-3 border-black rounded-xl p-6 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] flex-1 flex flex-col justify-between">
                    <div className="space-y-5">
                        <h3 className="text-xs font-black uppercase tracking-widest text-black/60 border-b-2 border-black/10 pb-2 flex items-center">
                            <Sparkles className="w-4 h-4 mr-2 text-retro-red" />
                            Local LLM Parameters
                        </h3>

                        {/* Mode Selection Toggles */}
                        <div className="flex border-2 border-black rounded-lg overflow-hidden bg-retro-cream p-1 gap-1">
                            <button
                                type="button"
                                onClick={() => setMode('tailor')}
                                className={`flex-1 py-2 text-[10px] font-black uppercase tracking-wider rounded-md border-2 border-transparent transition-all
                                    ${mode === 'tailor' 
                                        ? 'bg-retro-yellow text-black border-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]' 
                                        : 'text-black/60 hover:text-black hover:bg-white/50'
                                    }`}
                            >
                                Resume Tailor
                            </button>
                            <button
                                type="button"
                                onClick={() => setMode('cover_letter')}
                                className={`flex-1 py-2 text-[10px] font-black uppercase tracking-wider rounded-md border-2 border-transparent transition-all
                                    ${mode === 'cover_letter' 
                                        ? 'bg-retro-yellow text-black border-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]' 
                                        : 'text-black/60 hover:text-black hover:bg-white/50'
                                    }`}
                            >
                                Cover Letter
                            </button>
                        </div>

                        {/* Custom Job Switcher */}
                        <div className="flex items-center space-x-2 bg-retro-cream/40 p-3 rounded-lg border-2 border-black border-dashed">
                            <input
                                type="checkbox"
                                id="customJobCheck"
                                checked={isCustomJob}
                                onChange={(e) => {
                                    setIsCustomJob(e.target.checked);
                                    setError(null);
                                }}
                                className="w-4 h-4 accent-black cursor-pointer rounded border-2 border-black"
                            />
                            <label htmlFor="customJobCheck" className="text-xs font-black text-black cursor-pointer select-none">
                                Use Custom Job Details (Manual Paste)
                            </label>
                        </div>

                        {/* Job Details Forms */}
                        {!isCustomJob ? (
                            <div className="space-y-2">
                                <label className="block text-[10px] font-black uppercase tracking-widest text-black/60">
                                    Select Job from Pipeline
                                </label>
                                {loadingJobs ? (
                                    <div className="flex items-center space-x-2 text-xs font-bold text-black/50 py-2">
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                        <span>Loading pipeline...</span>
                                    </div>
                                ) : jobs.length > 0 ? (
                                    <select
                                        value={selectedJobId}
                                        onChange={(e) => setSelectedJobId(e.target.value)}
                                        className="w-full bg-white border-2 border-black rounded-lg p-3 text-xs font-bold text-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] focus:outline-none"
                                    >
                                        {jobs.map((job) => (
                                            <option key={job.id} value={job.id}>
                                                {job.title} @ {job.company}
                                            </option>
                                        ))}
                                    </select>
                                ) : (
                                    <p className="text-xs font-bold text-retro-red italic bg-retro-pink/10 p-3 border-2 border-retro-pink border-dashed rounded-lg">
                                        No jobs tracked yet. Switch to custom inputs or add jobs to Kanban.
                                    </p>
                                )}
                            </div>
                        ) : (
                            <div className="space-y-4">
                                <div className="grid grid-cols-2 gap-3">
                                    <div className="space-y-2">
                                        <label className="block text-[10px] font-black uppercase tracking-widest text-black/60">
                                            Job Title
                                        </label>
                                        <input
                                            type="text"
                                            value={customTitle}
                                            onChange={(e) => setCustomTitle(e.target.value)}
                                            placeholder="e.g. Frontend Engineer"
                                            className="w-full bg-white border-2 border-black rounded-lg p-2.5 text-xs font-bold text-black shadow-[1.5px_1.5px_0px_0px_rgba(0,0,0,1)] focus:outline-none"
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <label className="block text-[10px] font-black uppercase tracking-widest text-black/60">
                                            Company
                                        </label>
                                        <input
                                            type="text"
                                            value={customCompany}
                                            onChange={(e) => setCustomCompany(e.target.value)}
                                            placeholder="e.g. OpenAI"
                                            className="w-full bg-white border-2 border-black rounded-lg p-2.5 text-xs font-bold text-black shadow-[1.5px_1.5px_0px_0px_rgba(0,0,0,1)] focus:outline-none"
                                        />
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <label className="block text-[10px] font-black uppercase tracking-widest text-black/60">
                                        Job Description / Requirements
                                    </label>
                                    <textarea
                                        value={customDesc}
                                        onChange={(e) => setCustomDesc(e.target.value)}
                                        placeholder="Paste target job responsibilities and key requirements..."
                                        rows={6}
                                        className="w-full bg-white border-2 border-black rounded-lg p-3 text-xs font-bold text-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] focus:outline-none custom-scrollbar"
                                    />
                                </div>
                            </div>
                        )}
                    </div>

                    <div className="pt-6 border-t-2 border-black/10 mt-6 space-y-4">
                        {error && (
                            <div className="bg-retro-pink/20 border-2 border-black p-3 rounded-lg flex items-start space-x-2.5">
                                <AlertCircle className="w-4 h-4 text-retro-red shrink-0 mt-0.5" />
                                <span className="text-[10px] font-black text-black leading-normal">{error}</span>
                            </div>
                        )}

                        <button
                            type="button"
                            onClick={handleGenerate}
                            disabled={generating || !activeResume}
                            className="w-full bg-retro-red text-white py-4 rounded-xl font-black text-xs uppercase tracking-widest border-3 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] active:translate-x-[3px] active:translate-y-[3px] active:shadow-none transition-all disabled:opacity-50 disabled:pointer-events-none flex items-center justify-center space-x-2"
                        >
                            {generating ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    <span>Engaging Local AI Model...</span>
                                </>
                            ) : (
                                <>
                                    <Sparkles className="w-5 h-5" />
                                    <span>Generate Tailored Assets</span>
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </div>

            {/* Right Column: Output Viewer */}
            <div className="lg:col-span-7 flex flex-col h-full">
                <div className="bg-white border-3 border-black rounded-xl p-6 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] flex-1 flex flex-col h-full min-h-[50vh] lg:min-h-0 relative">
                    <div className="flex justify-between items-center pb-4 border-b-2 border-black/10 mb-4 shrink-0">
                        <h3 className="text-xs font-black uppercase tracking-widest text-black/60 flex items-center">
                            <FileText className="w-4 h-4 mr-2 text-retro-green" />
                            {mode === 'tailor' ? 'Resume Tailoring suggestions' : 'Generated Cover Letter'}
                        </h3>
                        {result && (
                            <div className="flex space-x-2">
                                <button
                                    onClick={handleCopy}
                                    className="p-2 border-2 border-black bg-white rounded-lg text-black hover:bg-retro-yellow shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[0.5px] hover:translate-y-[0.5px] hover:shadow-[1.5px_1.5px_0px_0px_rgba(0,0,0,1)] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none transition-all"
                                    title="Copy to Clipboard"
                                >
                                    {copied ? <Check className="w-4 h-4 text-retro-green" /> : <Copy className="w-4 h-4" />}
                                </button>
                                <button
                                    onClick={handleDownload}
                                    className="p-2 border-2 border-black bg-white rounded-lg text-black hover:bg-retro-mint shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[0.5px] hover:translate-y-[0.5px] hover:shadow-[1.5px_1.5px_0px_0px_rgba(0,0,0,1)] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none transition-all"
                                    title="Save to File"
                                >
                                    <Download className="w-4 h-4" />
                                </button>
                            </div>
                        )}
                    </div>

                    <div className="flex-1 min-h-[40vh] rounded-lg border-2 border-black/10 bg-retro-cream/20 overflow-hidden flex flex-col">
                        <div className="flex-1 overflow-y-auto overflow-x-hidden p-4 rounded-[inherit] custom-scrollbar font-mono text-xs leading-relaxed text-black/90">
                            {generating ? (
                                <div className="h-full flex flex-col items-center justify-center py-20 text-center">
                                    <Loader2 className="w-8 h-8 animate-spin text-retro-red mb-4" />
                                    <p className="text-[10px] font-black uppercase tracking-widest text-black/60 animate-pulse">Running Local AI...</p>
                                    <p className="text-[9px] font-bold text-black/40 mt-1 max-w-[250px]">Please stand by. Local generation is 100% free but takes a few seconds on CPU.</p>
                                </div>
                            ) : result ? (
                                <pre className="whitespace-pre-wrap break-words">{result}</pre>
                            ) : (
                                <div className="h-full flex flex-col items-center justify-center text-center py-20 opacity-30 select-none">
                                    <Sparkles className="w-10 h-10 mb-3 text-black" />
                                    <p className="text-[10px] font-black uppercase tracking-widest text-black">Awaiting generation parameters</p>
                                    <p className="text-[9px] font-bold text-black/70 mt-1 max-w-[200px]">Fill configuration on the left and click generate.</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AITailorView;
