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
        <div className="space-y-10 px-4 bg-retro-cream text-black">
            {/* Upper grid: Stats and upload */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Stats Panel */}
                <div className="lg:col-span-5 bg-white border-3 border-black rounded-xl p-8 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] flex flex-col justify-between">
                    <div>
                        <div className="flex items-center space-x-3 mb-6">
                            <div className="w-10 h-10 rounded-lg bg-retro-sand border-2 border-black flex items-center justify-center text-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
                                <Database className="w-5 h-5" />
                            </div>
                            <div>
                                <h3 className="text-sm font-black uppercase tracking-widest text-black">Vault Overview</h3>
                                <p className="text-[10px] text-black/60 font-black uppercase tracking-wider">Multi-version tracking</p>
                            </div>
                        </div>
                        <p className="text-black/85 text-xs leading-relaxed font-bold mb-6">
                            The Resume Vault houses all your uploaded professional profiles. Switch between tailored resumes for different roles, industries, or seniority levels. The active resume dictates your neural matching score.
                        </p>
                    </div>

                    <div className="grid grid-cols-2 gap-4 border-t-2 border-black/10 pt-6">
                        <div className="bg-retro-cream border-2 border-black rounded-lg p-4 text-center shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
                            <span className="text-[10px] font-black text-black/60 uppercase tracking-wider block">Total Resumes</span>
                            <span className="text-3xl font-black text-black">{resumes.length}</span>
                        </div>
                        <div className="bg-retro-cream border-2 border-black rounded-lg p-4 text-center shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
                            <span className="text-[10px] font-black text-black/60 uppercase tracking-wider block">Active Profile</span>
                            <span className="text-xs font-black text-retro-red block truncate mt-2">
                                {resumes.find(r => r.is_active)?.filename || "None"}
                            </span>
                        </div>
                    </div>
                </div>

                {/* Upload Card */}
                <div className="lg:col-span-7 bg-white border-3 border-black rounded-xl p-8 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
                    <h3 className="text-sm font-black uppercase tracking-widest text-black mb-6 flex items-center">
                        <Upload className="w-4 h-4 mr-2 text-retro-red" />
                        Add Resume to Vault
                    </h3>
                    
                    <div className="space-y-4">
                        <label className="relative group block cursor-pointer">
                            <div className={`
                                flex flex-col items-center justify-center p-8 border-3 border-dashed rounded-lg transition-all duration-100
                                ${uploadFile ? 'border-retro-green bg-retro-mint/20' : 'border-black bg-white hover:bg-retro-cream'}
                            `}>
                                <FileText className={`w-8 h-8 mb-2 transition-colors ${uploadFile ? 'text-retro-green' : 'text-black/40 group-hover:text-black'}`} />
                                <span className="text-xs font-black text-black text-center px-4">
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
                            <div className="flex items-center space-x-2 text-retro-red text-xs bg-retro-pink/20 border-2 border-black p-3 rounded-lg font-bold">
                                <ShieldAlert className="w-4 h-4 flex-shrink-0" />
                                <span>{error}</span>
                            </div>
                        )}

                        <button
                            onClick={handleUpload}
                            disabled={!uploadFile || uploading}
                            className={`
                                w-full py-3.5 rounded-lg font-black text-[11px] uppercase tracking-[0.2em] transition-all flex items-center justify-center space-x-2 border-3 border-black
                                ${!uploadFile || uploading 
                                    ? 'bg-gray-100 text-black/35 border-black/30 cursor-not-allowed shadow-none' 
                                    : 'bg-retro-yellow text-black shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[0.5px] hover:translate-y-[0.5px] hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:translate-x-[2.5px] active:translate-y-[2.5px] active:shadow-none'
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
                    <h3 className="text-lg font-black text-black tracking-tight uppercase italic">Stored Resumes</h3>
                    <p className="text-black/60 text-[10px] font-black uppercase tracking-wider mt-1">Manage and select your active profiles</p>
                </div>

                {loading ? (
                    <div className="py-20 flex flex-col items-center">
                        <Loader2 className="w-8 h-8 animate-spin text-retro-red mb-4" />
                        <p className="text-black font-black uppercase tracking-widest text-[10px]">Loading Vault files...</p>
                    </div>
                ) : resumes.length === 0 ? (
                    <div className="py-16 text-center bg-white border-3 border-dashed border-black rounded-xl shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
                        <Database className="w-10 h-10 text-black/40 mx-auto mb-4" />
                        <p className="text-black/70 font-black text-sm italic">No resumes in vault. Upload one above to get started.</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {resumes.map((resume) => (
                            <div 
                                key={resume.id}
                                className={`
                                    relative bg-white border-3 border-black rounded-xl p-6 transition-all duration-100 flex flex-col justify-between group
                                    ${resume.is_active 
                                        ? 'bg-retro-mint/20 shadow-[6px_6px_0px_0px_rgba(0,0,0,1)] translate-x-[-2px] translate-y-[-2px]' 
                                        : 'shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[-1px] hover:translate-y-[-1px] hover:shadow-[5px_5px_0px_0px_rgba(0,0,0,1)]'
                                    }
                                `}
                            >
                                <div>
                                    {/* Top Line */}
                                    <div className="flex justify-between items-start mb-4">
                                        <div className="flex items-center space-x-3 min-w-0 pr-4">
                                            <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 border-2 border-black shadow-[1.5px_1.5px_0px_0px_rgba(0,0,0,1)] ${resume.is_active ? 'bg-retro-yellow text-black' : 'bg-retro-cream text-black'}`}>
                                                <FileText className="w-5 h-5" />
                                            </div>
                                            <div className="min-w-0">
                                                <h4 className="font-black text-black text-sm truncate leading-tight">{resume.filename}</h4>
                                                <span className="text-[10px] text-retro-green font-black uppercase tracking-wider">
                                                    {resume.parsed_data.full_name || "Unparsed"}
                                                </span>
                                            </div>
                                        </div>

                                        {resume.is_active ? (
                                            <span className="bg-retro-yellow border-2 border-black text-black text-[9px] font-black uppercase tracking-widest px-2.5 py-1 rounded shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] flex items-center">
                                                <Star className="w-2.5 h-2.5 mr-1 fill-black text-black" />
                                                Active
                                            </span>
                                        ) : (
                                            <span className="bg-retro-cream border-2 border-black text-black/50 text-[9px] font-black uppercase tracking-widest px-2.5 py-1 rounded shadow-[1.5px_1.5px_0px_0px_rgba(0,0,0,1)]">
                                                Vaulted
                                            </span>
                                        )}
                                    </div>

                                    {/* Stats grid */}
                                    <div className="grid grid-cols-2 gap-3 bg-retro-cream rounded-lg p-3 border-2 border-black mb-6">
                                        <div>
                                            <span className="text-[8px] font-black text-black/50 uppercase tracking-wider block">Candidate Email</span>
                                            <span className="text-xs font-bold text-black truncate block mt-0.5 flex items-center">
                                                <Mail className="w-3 h-3 mr-1 text-black/50" />
                                                {resume.parsed_data.email || "N/A"}
                                            </span>
                                        </div>
                                        <div>
                                            <span className="text-[8px] font-black text-black/50 uppercase tracking-wider block">Skills Extracted</span>
                                            <span className="text-xs font-black text-black block mt-0.5">
                                                {resume.parsed_data.skills_count} skills
                                            </span>
                                        </div>
                                    </div>
                                </div>

                                {/* Footer Actions */}
                                <div className="flex items-center justify-between border-t-2 border-black/10 pt-4 mt-2">
                                    <span className="text-[9px] text-black/50 font-black uppercase tracking-wider flex items-center">
                                        <Clock className="w-3 h-3 mr-1 opacity-70" />
                                        {formatDate(resume.created_at)}
                                    </span>

                                    <div className="flex items-center space-x-2">
                                        <button
                                            onClick={() => handleDelete(resume.id)}
                                            disabled={actionLoading === resume.id}
                                            className="p-2 text-black hover:text-white border-2 border-black bg-white hover:bg-retro-red rounded shadow-[1.5px_1.5px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[0.5px] hover:translate-y-[0.5px] hover:shadow-[1px_1px_0px_0px_rgba(0,0,0,1)] active:translate-x-[1.5px] active:translate-y-[1.5px] active:shadow-none transition-all"
                                            title="Delete resume"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                        
                                        {!resume.is_active && (
                                            <button
                                                onClick={() => handleActivate(resume.id)}
                                                disabled={actionLoading !== null}
                                                className="bg-retro-green text-white border-2 border-black text-[10px] font-black uppercase tracking-wider px-3.5 py-2 rounded shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[0.5px] hover:translate-y-[0.5px] hover:shadow-[1.5px_1.5px_0px_0px_rgba(0,0,0,1)] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none transition-all flex items-center"
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
