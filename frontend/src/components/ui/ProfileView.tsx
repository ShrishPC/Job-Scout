"use client";

import React, { useState } from 'react';
import { User, Mail, Briefcase, FileText, Copy, Check, MapPin, Sparkles, Star, Calendar } from 'lucide-react';

interface ProfileViewProps {
    parsedData: any;
}

const ProfileView: React.FC<ProfileViewProps> = ({ parsedData }) => {
    const [copied, setCopied] = useState(false);
    const [skillsFilter, setSkillsFilter] = useState('');

    if (!parsedData) {
        return (
            <div className="py-24 text-center bg-slate-900/40 border border-slate-800 rounded-3xl p-8 max-w-2xl mx-auto backdrop-blur-sm">
                <div className="w-16 h-16 bg-slate-900 border border-slate-800 rounded-2xl flex items-center justify-center mx-auto mb-6">
                    <User className="w-8 h-8 text-slate-500" />
                </div>
                <h3 className="text-lg font-bold text-slate-200 mb-2">No Profile Synced</h3>
                <p className="text-slate-400 text-xs leading-relaxed max-w-sm mx-auto mb-6">
                    Please upload your resume first under the Hunt tab or Vault tab to generate your neural profile identity.
                </p>
            </div>
        );
    }

    const { parsed_json, resume_markdown, filename } = parsedData;

    const handleCopy = () => {
        if (!resume_markdown) return;
        navigator.clipboard.writeText(resume_markdown);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const skills = parsed_json?.skills || [];
    const experiences = parsed_json?.experience || [];

    const filteredSkills = skills.filter((skill: string) => 
        skill.toLowerCase().includes(skillsFilter.toLowerCase())
    );

    return (
        <div className="space-y-10 px-4 max-w-7xl mx-auto pb-20">
            {/* Upper profile header / quick info */}
            <div className="relative overflow-hidden bg-slate-900/40 border border-slate-800 rounded-3xl p-8 backdrop-blur-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                <div className="absolute top-0 right-0 w-80 h-80 bg-brand-500/5 rounded-full blur-3xl pointer-events-none"></div>
                <div className="flex items-center space-x-5">
                    <div className="w-16 h-16 bg-gradient-to-br from-brand-600 to-brand-400 rounded-2xl flex items-center justify-center text-slate-950 font-black text-2xl shadow-[0_0_20px_rgba(56,171,248,0.3)]">
                        {parsed_json?.full_name ? parsed_json.full_name.charAt(0) : 'U'}
                    </div>
                    <div>
                        <div className="flex items-center space-x-2.5">
                            <h2 className="text-2xl font-black text-slate-100 tracking-tight">{parsed_json?.full_name || "Unknown"}</h2>
                            <span className="bg-brand-500/10 border border-brand-500/30 text-brand-400 text-[9px] font-black uppercase tracking-widest px-2.5 py-0.5 rounded-full">
                                Profile Active
                            </span>
                        </div>
                        <p className="text-brand-400 text-xs font-bold mt-1 uppercase tracking-widest flex items-center">
                            <Mail className="w-3.5 h-3.5 mr-1.5 opacity-80" />
                            {parsed_json?.email || "No Email Provided"}
                        </p>
                    </div>
                </div>

                <div className="flex flex-wrap gap-4 text-xs font-bold">
                    <div className="bg-slate-950/60 border border-slate-900 px-4 py-3 rounded-2xl flex items-center space-x-2">
                        <FileText className="w-4 h-4 text-brand-400" />
                        <span className="text-slate-400">Source File:</span>
                        <span className="text-slate-200 truncate max-w-40">{filename || "Active Resume"}</span>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Left Side: Skills & Metadata */}
                <div className="lg:col-span-5 space-y-8">
                    {/* Skills card */}
                    <div className="bg-slate-900/40 border border-slate-800 rounded-3xl p-8 backdrop-blur-sm">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-xs font-black uppercase tracking-widest text-slate-200 flex items-center">
                                <Sparkles className="w-4 h-4 mr-2 text-brand-400" />
                                Professional Skills
                            </h3>
                            <span className="bg-slate-800 text-slate-400 text-[10px] px-2 py-0.5 rounded-md font-bold">
                                {skills.length} Total
                            </span>
                        </div>

                        {/* Search input for skills */}
                        <div className="mb-4">
                            <input 
                                type="text"
                                placeholder="Filter skills..."
                                value={skillsFilter}
                                onChange={(e) => setSkillsFilter(e.target.value)}
                                className="w-full bg-slate-950/60 border border-slate-800/80 rounded-xl px-4 py-2 text-xs font-bold text-slate-300 placeholder-slate-600 focus:outline-none focus:border-brand-500/50 transition-colors"
                            />
                        </div>

                        <div className="flex flex-wrap gap-2 max-h-[300px] overflow-y-auto pr-1 custom-scrollbar">
                            {filteredSkills.map((skill: string, i: number) => (
                                <span 
                                    key={i} 
                                    className="px-3 py-2 bg-slate-950/60 text-slate-300 rounded-xl text-xs font-bold border border-slate-900 hover:border-brand-500/20 transition-all cursor-default"
                                >
                                    {skill}
                                </span>
                            ))}
                            {filteredSkills.length === 0 && (
                                <p className="text-slate-600 text-xs italic py-4">No matching skills found.</p>
                            )}
                        </div>
                    </div>

                    {/* Metadata Card */}
                    <div className="bg-slate-900/40 border border-slate-800 rounded-3xl p-8 backdrop-blur-sm">
                        <h3 className="text-xs font-black uppercase tracking-widest text-slate-200 mb-6 flex items-center">
                            <User className="w-4 h-4 mr-2 text-brand-400" />
                            Target Roles & Meta
                        </h3>
                        
                        <div className="space-y-4 text-xs">
                            <div className="flex justify-between items-center py-2.5 border-b border-slate-800/50">
                                <span className="text-slate-500 font-bold uppercase tracking-wider">Target Role</span>
                                <span className="text-slate-200 font-black bg-brand-500/5 border border-brand-500/10 px-2.5 py-1 rounded-lg">
                                    {parsed_json?.target_role || "Not Specified"}
                                </span>
                            </div>
                            <div className="flex justify-between items-center py-2.5 border-b border-slate-800/50">
                                <span className="text-slate-500 font-bold uppercase tracking-wider">Target Location</span>
                                <span className="text-slate-200 font-black flex items-center">
                                    <MapPin className="w-3.5 h-3.5 text-slate-500 mr-1" />
                                    {parsed_json?.target_location || "Remote"}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Side: Timeline and Markdown Source */}
                <div className="lg:col-span-7 space-y-8">
                    {/* Experience Timeline */}
                    <div className="bg-slate-900/40 border border-slate-800 rounded-3xl p-8 backdrop-blur-sm">
                        <h3 className="text-xs font-black uppercase tracking-widest text-slate-200 mb-8 flex items-center">
                            <Briefcase className="w-4 h-4 mr-2 text-brand-400" />
                            Work History Timeline
                        </h3>

                        {experiences.length === 0 ? (
                            <p className="text-slate-500 text-xs italic">No experience blocks extracted.</p>
                        ) : (
                            <div className="space-y-8 relative before:content-[''] before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
                                {experiences.map((exp: any, i: number) => (
                                    <div key={i} className="relative pl-10 group">
                                        {/* Dot */}
                                        <div className="absolute left-1.5 top-1.5 w-3.5 h-3.5 rounded-full bg-slate-950 border-2 border-brand-400 group-hover:bg-brand-400 transition-colors shadow-[0_0_8px_rgba(56,171,248,0.4)]"></div>
                                        
                                        <div className="bg-slate-950/40 border border-slate-900 rounded-2xl p-5 hover:border-slate-800 transition-colors">
                                            <div className="flex flex-col sm:flex-row justify-between sm:items-center mb-2 gap-1">
                                                <h4 className="font-bold text-slate-100 text-[15px]">{exp.title}</h4>
                                                <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider flex items-center">
                                                    <Calendar className="w-3 h-3 mr-1 text-slate-600" />
                                                    {exp.duration}
                                                </span>
                                            </div>
                                            <p className="text-brand-400 text-xs font-bold mb-3 uppercase tracking-wider">{exp.company}</p>
                                            {exp.description && (
                                                <p className="text-slate-400 text-xs leading-relaxed font-medium mt-2 whitespace-pre-line">
                                                    {exp.description}
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Resume Markdown View */}
                    {resume_markdown && (
                        <div className="bg-slate-900/40 border border-slate-800 rounded-3xl p-8 backdrop-blur-sm">
                            <div className="flex justify-between items-center mb-6">
                                <h3 className="text-xs font-black uppercase tracking-widest text-slate-200 flex items-center">
                                    <FileText className="w-4 h-4 mr-2 text-brand-400" />
                                    Resume Source (Markdown format)
                                </h3>
                                <button 
                                    onClick={handleCopy}
                                    className="px-3.5 py-1.5 bg-slate-950 border border-slate-800 rounded-xl text-[10px] font-black uppercase tracking-wider text-slate-400 hover:text-slate-200 hover:bg-slate-900 transition-all flex items-center"
                                >
                                    {copied ? (
                                        <>
                                            <Check className="w-3 h-3 mr-1.5 text-green-400" />
                                            Copied
                                        </>
                                    ) : (
                                        <>
                                            <Copy className="w-3 h-3 mr-1.5" />
                                            Copy Code
                                        </>
                                    )}
                                </button>
                            </div>
                            
                            <div className="bg-slate-950/60 border border-slate-900 rounded-2xl p-6 max-h-[300px] overflow-y-auto custom-scrollbar">
                                <pre className="text-[11px] font-mono text-slate-400 whitespace-pre-wrap leading-relaxed select-text">
                                    {resume_markdown}
                                </pre>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ProfileView;
