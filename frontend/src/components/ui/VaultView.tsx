"use client";

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Database, Upload, FileText, CheckCircle2, Trash2, Clock, Star, Loader2, Mail, ShieldAlert } from 'lucide-react';

interface ResumeListItem {
    id: number;
    filename: string;
    created_at: string;
    is_active: boolean;
    parsed_data: {
        full_name: string | null;
        email: string | null;
        skills_count: number;
    };
}

interface VaultViewProps {
    onActiveProfileChanged: (profile: any) => void;
}

const VaultView: React.FC<VaultViewProps> = ({ onActiveProfileChanged }) => {
    const [resumes, setResumes] = useState<ResumeListItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);
    const [uploadFile, setUploadFile] = useState<File | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [actionLoading, setActionLoading] = useState<number | null>(null);

    const apiHost = typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.hostname}:8000` : 'http://127.0.0.1:8000';

    const fetchResumes = async () => {
        try {
            const response = await axios.get(`${apiHost}/resumes`);
            setResumes(response.data);
        } catch (err) {
            console.error("Failed to fetch resumes from vault:", err);
            setError("Failed to load resumes from the database.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchResumes();
    }, []);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setUploadFile(e.target.files[0]);
            setError(null);
        }
    };

    const handleUpload = async () => {
        if (!uploadFile) return;
        setUploading(true);
        setError(null);

        const formData = new FormData();
        formData.append('file', uploadFile);

        try {
            const response = await axios.post(`${apiHost}/resume/parse`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            
            // Clear selected file
            setUploadFile(null);
            
            // Refresh resumes list
            await fetchResumes();
            
            // Notify parent to update current active profile
            onActiveProfileChanged(response.data);
        } catch (err: any) {
            console.error("Failed to upload resume:", err);
            setError(err.response?.data?.detail || 'Failed to upload and parse resume.');
        } finally {
            setUploading(false);
        }
    };

    const handleActivate = async (id: number) => {
        setActionLoading(id);
        setError(null);
        try {
            const response = await axios.post(`${apiHost}/resumes/${id}/activate`);
            // Refresh resumes
            await fetchResumes();
            // Sync with parent
            onActiveProfileChanged(response.data.profile);
        } catch (err) {
            console.error("Failed to activate resume:", err);
            setError("Failed to activate resume.");
        } finally {
            setActionLoading(null);
        }
    };

    const handleDelete = async (id: number) => {
        if (!confirm("Are you sure you want to delete this resume? If it is the active profile, your active profile will be reset.")) return;
        
        setActionLoading(id);
        setError(null);
        try {
            await axios.delete(`${apiHost}/resumes/${id}`);
            // Refresh resumes
            await fetchResumes();
            
            // Check if deleted resume was active, if so we reload active profile from backend
            const deletedResume = resumes.find(r => r.id === id);
            if (deletedResume?.is_active) {
                // Fetch the new active profile (backend will auto-activate another or set None)
                const activeRes = await axios.get(`${apiHost}/resume/active`);
                onActiveProfileChanged(activeRes.data || null);
            }
        } catch (err) {
            console.error("Failed to delete resume:", err);
            setError("Failed to delete resume.");
        } finally {
            setActionLoading(null);
        }
    };

    const formatDate = (isoStr: string) => {
        if (!isoStr) return "Unknown date";
        const date = new Date(isoStr);
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <div className="space-y-10 px-4">
            {/* Upper grid: Stats and upload */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Stats Panel */}
                <div className="lg:col-span-5 bg-slate-900/40 border border-slate-800 rounded-3xl p-8 backdrop-blur-sm flex flex-col justify-between">
                    <div>
                        <div className="flex items-center space-x-3 mb-6">
                            <div className="w-10 h-10 rounded-xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-400">
                                <Database className="w-5 h-5" />
                            </div>
                            <div>
                                <h3 className="text-sm font-black uppercase tracking-widest text-slate-200">Vault Overview</h3>
                                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Multi-version tracking</p>
                            </div>
                        </div>
                        <p className="text-slate-300 text-xs leading-relaxed font-medium mb-6">
                            The Resume Vault houses all your uploaded professional profiles. Switch between tailored resumes for different roles, industries, or seniority levels. The active resume dictates your neural matching score.
                        </p>
                    </div>

                    <div className="grid grid-cols-2 gap-4 border-t border-slate-800/60 pt-6">
                        <div className="bg-slate-950/60 border border-slate-900 rounded-2xl p-4 text-center">
                            <span className="text-[10px] font-black text-slate-500 uppercase tracking-wider block">Total Resumes</span>
                            <span className="text-3xl font-black text-slate-100">{resumes.length}</span>
                        </div>
                        <div className="bg-slate-950/60 border border-slate-900 rounded-2xl p-4 text-center">
                            <span className="text-[10px] font-black text-slate-500 uppercase tracking-wider block">Active Profile</span>
                            <span className="text-xs font-bold text-brand-400 block truncate mt-2">
                                {resumes.find(r => r.is_active)?.filename || "None"}
                            </span>
                        </div>
                    </div>
                </div>

                {/* Upload Card */}
                <div className="lg:col-span-7 bg-slate-900/40 border border-slate-800 rounded-3xl p-8 backdrop-blur-sm">
                    <h3 className="text-sm font-black uppercase tracking-widest text-slate-200 mb-6 flex items-center">
                        <Upload className="w-4 h-4 mr-2 text-brand-400" />
                        Add Resume to Vault
                    </h3>
                    
                    <div className="space-y-4">
                        <label className="relative group block cursor-pointer">
                            <div className={`
                                flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-2xl transition-all duration-300
                                ${uploadFile ? 'border-brand-500/40 bg-brand-500/5' : 'border-slate-800 hover:border-slate-700 hover:bg-slate-800/20'}
                            `}>
                                <FileText className={`w-8 h-8 mb-2 transition-colors ${uploadFile ? 'text-brand-400' : 'text-slate-600 group-hover:text-slate-400'}`} />
                                <span className="text-xs font-bold text-slate-300 text-center px-4">
                                    {uploadFile ? uploadFile.name : 'Choose a new PDF, DOCX, or MD resume'}
                                </span>
                            </div>
                            <input 
                                type="file" 
                                className="hidden" 
                                accept=".pdf,.docx,.md,.markdown" 
                                onChange={handleFileChange} 
                            />
                        </label>

                        {error && (
                            <div className="flex items-center space-x-2 text-red-400 text-xs bg-red-400/5 border border-red-400/20 p-3 rounded-xl">
                                <ShieldAlert className="w-4 h-4 flex-shrink-0" />
                                <span>{error}</span>
                            </div>
                        )}

                        <button
                            onClick={handleUpload}
                            disabled={!uploadFile || uploading}
                            className={`
                                w-full py-3.5 rounded-xl font-black text-[11px] uppercase tracking-[0.2em] transition-all flex items-center justify-center space-x-2 border
                                ${!uploadFile || uploading 
                                    ? 'bg-slate-900 text-slate-600 border-slate-800 cursor-not-allowed' 
                                    : 'bg-brand-500 text-slate-950 border-brand-400 hover:bg-brand-400 hover:text-slate-950 active:scale-[0.98]'
                                }
                            `}
                        >
                            {uploading ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    <span>Analyzing & Saving...</span>
                                </>
                            ) : (
                                <span>Parse & Add to Vault</span>
                            )}
                        </button>
                    </div>
                </div>
            </div>

            {/* Resumes List Section */}
            <div className="space-y-6">
                <div>
                    <h3 className="text-lg font-black text-slate-200 tracking-tight uppercase italic">Stored Resumes</h3>
                    <p className="text-slate-500 text-[10px] font-bold uppercase tracking-wider mt-1">Manage and select your active profiles</p>
                </div>

                {loading ? (
                    <div className="py-20 flex flex-col items-center">
                        <Loader2 className="w-8 h-8 animate-spin text-brand-500 mb-4" />
                        <p className="text-slate-500 font-bold uppercase tracking-widest text-[10px]">Loading Vault files...</p>
                    </div>
                ) : resumes.length === 0 ? (
                    <div className="py-16 text-center bg-slate-900/10 border border-slate-800/80 border-dashed rounded-3xl">
                        <Database className="w-10 h-10 text-slate-700 mx-auto mb-4" />
                        <p className="text-slate-400 font-bold text-sm italic">No resumes in vault. Upload one above to get started.</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {resumes.map((resume) => (
                            <div 
                                key={resume.id}
                                className={`
                                    relative bg-slate-900/40 border rounded-3xl p-6 transition-all duration-300 flex flex-col justify-between group
                                    ${resume.is_active 
                                        ? 'border-brand-500/50 shadow-[0_0_20px_rgba(56,171,248,0.08)] bg-gradient-to-br from-brand-950/20 to-slate-900/40' 
                                        : 'border-slate-800 hover:border-slate-700'
                                    }
                                `}
                            >
                                <div>
                                    {/* Top Line */}
                                    <div className="flex justify-between items-start mb-4">
                                        <div className="flex items-center space-x-3 min-w-0 pr-4">
                                            <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${resume.is_active ? 'bg-brand-500/15 text-brand-400' : 'bg-slate-800 text-slate-400'}`}>
                                                <FileText className="w-5 h-5" />
                                            </div>
                                            <div className="min-w-0">
                                                <h4 className="font-bold text-slate-100 text-sm truncate leading-tight">{resume.filename}</h4>
                                                <span className="text-[10px] text-brand-400 font-bold uppercase tracking-wider opacity-85">
                                                    {resume.parsed_data.full_name || "Unparsed"}
                                                </span>
                                            </div>
                                        </div>

                                        {resume.is_active ? (
                                            <span className="bg-brand-500/10 border border-brand-500/30 text-brand-400 text-[9px] font-black uppercase tracking-widest px-2.5 py-1 rounded-full shadow-[0_0_10px_rgba(56,171,248,0.15)] flex items-center">
                                                <Star className="w-2.5 h-2.5 mr-1 fill-brand-400 text-brand-400" />
                                                Active
                                            </span>
                                        ) : (
                                            <span className="bg-slate-800/80 border border-slate-700/80 text-slate-500 text-[9px] font-black uppercase tracking-widest px-2.5 py-1 rounded-full">
                                                Vaulted
                                            </span>
                                        )}
                                    </div>

                                    {/* Stats grid */}
                                    <div className="grid grid-cols-2 gap-3 bg-slate-950/40 rounded-xl p-3 border border-slate-900 mb-6">
                                        <div>
                                            <span className="text-[8px] font-black text-slate-500 uppercase tracking-wider block">Candidate Email</span>
                                            <span className="text-xs font-semibold text-slate-300 truncate block mt-0.5 flex items-center">
                                                <Mail className="w-3 h-3 mr-1 text-slate-500" />
                                                {resume.parsed_data.email || "N/A"}
                                            </span>
                                        </div>
                                        <div>
                                            <span className="text-[8px] font-black text-slate-500 uppercase tracking-wider block">Skills Extracted</span>
                                            <span className="text-xs font-black text-slate-300 block mt-0.5">
                                                {resume.parsed_data.skills_count} skills
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                {/* Footer Actions */}
                                <div className="flex items-center justify-between border-t border-slate-800/50 pt-4 mt-2">
                                    <span className="text-[9px] text-slate-500 font-bold uppercase tracking-wider flex items-center">
                                        <Clock className="w-3 h-3 mr-1 opacity-70" />
                                        {formatDate(resume.created_at)}
                                    </span>

                                    <div className="flex items-center space-x-2">
                                        <button
                                            onClick={() => handleDelete(resume.id)}
                                            disabled={actionLoading === resume.id}
                                            className="p-2 text-slate-500 hover:text-red-400 hover:bg-red-400/5 border border-transparent hover:border-red-400/10 rounded-xl transition-all"
                                            title="Delete resume"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                        
                                        {!resume.is_active && (
                                            <button
                                                onClick={() => handleActivate(resume.id)}
                                                disabled={actionLoading !== null}
                                                className="bg-slate-800 text-slate-200 border border-slate-700 text-[10px] font-black uppercase tracking-wider px-3.5 py-2 rounded-xl hover:bg-slate-700 hover:text-slate-100 transition-all flex items-center"
                                            >
                                                {actionLoading === resume.id ? (
                                                    <Loader2 className="w-3.5 h-3.5 animate-spin mr-1.5" />
                                                ) : (
                                                    <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" />
                                                )}
                                                Activate
                                            </button>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default VaultView;
