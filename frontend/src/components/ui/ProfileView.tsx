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
            <div className="py-24 text-center bg-white border-3 border-black rounded-xl p-8 max-w-2xl mx-auto shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] bg-retro-cream">
                <div className="w-16 h-16 bg-retro-sand border-2 border-black rounded-xl flex items-center justify-center mx-auto mb-6 shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
                    <User className="w-8 h-8 text-black" />
                </div>
                <h3 className="text-xl font-black text-black mb-2 uppercase">No Profile Synced</h3>
                <p className="text-black/70 text-xs leading-relaxed max-w-sm mx-auto mb-6 font-bold">
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
        <div className="space-y-10 px-4 max-w-7xl mx-auto pb-20 bg-retro-cream text-black">
            {/* Upper profile header / quick info */}
            <div className="relative overflow-hidden bg-white border-3 border-black rounded-xl p-8 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                <div className="flex items-center space-x-5">
                    <div className="w-16 h-16 bg-retro-yellow text-black border-3 border-black rounded-xl flex items-center justify-center font-black text-2xl shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] profile-avatar">
                        {parsed_json?.full_name ? parsed_json.full_name.charAt(0) : 'U'}
                    </div>
                    <div>
                        <div className="flex items-center space-x-2.5">
                            <h2 className="text-2xl font-black text-black tracking-tight">{parsed_json?.full_name || "Unknown"}</h2>
                            <span className="bg-retro-green border-2 border-black text-white text-[9px] font-black uppercase tracking-widest px-2.5 py-0.5 rounded">
                                Profile Active
                            </span>
                        </div>
                        <p className="text-retro-green font-black text-xs mt-1 uppercase tracking-widest flex items-center">
                            <Mail className="w-3.5 h-3.5 mr-1.5 opacity-80" />
                            {parsed_json?.email || "No Email Provided"}
                        </p>
                    </div>
                </div>

                <div className="flex flex-wrap gap-4 text-xs font-bold">
                    <div className="bg-retro-cream border-2 border-black px-4 py-3 rounded-lg flex items-center space-x-2 shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
                        <FileText className="w-4 h-4 text-black/60" />
                        <span className="text-black/60">Source File:</span>
                        <span className="text-black font-black truncate max-w-40">{filename || "Active Resume"}</span>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Left Side: Skills & Metadata */}
                <div className="lg:col-span-5 space-y-8">
                    {/* Skills card */}
                    <div className="bg-white border-3 border-black rounded-xl p-8 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-xs font-black uppercase tracking-widest text-black flex items-center">
                                Professional Skills
                            </h3>
                            <span className="bg-retro-sand text-black border-2 border-black text-[10px] px-2 py-0.5 rounded font-black">
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
                                className="neo-input w-full px-4 py-2.5 rounded-lg text-xs font-extrabold text-black placeholder-gray-500 focus:outline-none"
                            />
                        </div>

                        <div className="flex flex-wrap gap-2 max-h-[300px] overflow-y-auto pr-1 custom-scrollbar">
                            {filteredSkills.map((skill: string, i: number) => (
                                <span 
                                    key={i} 
                                    className="px-3 py-1.5 bg-retro-mint text-black border-2 border-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] text-xs font-black cursor-default skill-tag"
                                >
                                    {skill}
                                </span>
                            ))}
                            {filteredSkills.length === 0 && (
                                <p className="text-black/60 text-xs italic py-4">No matching skills found.</p>
                            )}
                        </div>
                    </div>

                    {/* Metadata Card */}
                    <div className="bg-white border-3 border-black rounded-xl p-8 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
                        <h3 className="text-xs font-black uppercase tracking-widest text-black mb-6 flex items-center">
                            <User className="w-4 h-4 mr-2 text-retro-red" />
                            Target Roles & Meta
                        </h3>
                        
                        <div className="space-y-4 text-xs">
                            <div className="flex justify-between items-center py-2.5 border-b-2 border-black/10">
                                <span className="text-black/60 font-black uppercase tracking-wider">Target Role</span>
                                <span className="text-black font-black bg-retro-yellow border-2 border-black px-2.5 py-1 rounded shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
                                    {parsed_json?.target_role || "Not Specified"}
                                </span>
                            </div>
                            <div className="flex justify-between items-center py-2.5 border-b-2 border-black/10">
                                <span className="text-black/60 font-black uppercase tracking-wider">Target Location</span>
                                <span className="text-black font-black flex items-center">
                                    <MapPin className="w-3.5 h-3.5 text-black/60 mr-1" />
                                    {parsed_json?.target_location || "Remote"}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Side: Timeline and Markdown Source */}
                <div className="lg:col-span-7 space-y-8">
                    {/* Experience Timeline */}
                    <div className="bg-white border-3 border-black rounded-xl p-8 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
                        <h3 className="text-xs font-black uppercase tracking-widest text-black mb-8 flex items-center">
                            <Briefcase className="w-4 h-4 mr-2 text-retro-red" />
                            Work History Timeline
                        </h3>

                        {experiences.length === 0 ? (
                            <p className="text-black/60 text-xs italic">No experience blocks extracted.</p>
                        ) : (
                            <div className="space-y-8 relative before:content-[''] before:absolute before:left-3 before:top-2 before:bottom-2 before:w-1 before:bg-black">
                                {experiences.map((exp: any, i: number) => (
                                    <div key={i} className="relative pl-10 group">
                                        {/* Dot */}
                                        <div className="absolute left-1 top-1.5 w-4.5 h-4.5 rounded-none bg-retro-red border-2 border-black group-hover:bg-retro-yellow transition-colors"></div>
                                        
                                        <div className="bg-retro-cream border-2 border-black rounded-lg p-5 shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] transition-colors">
                                            <div className="flex flex-col sm:flex-row justify-between sm:items-center mb-2 gap-1">
                                                <h4 className="font-black text-black text-[15px]">{exp.title}</h4>
                                                <span className="text-[10px] text-black/60 font-black uppercase tracking-wider flex items-center">
                                                    <Calendar className="w-3.5 h-3.5 mr-1 text-black/40" />
                                                    {exp.duration}
                                                </span>
                                            </div>
                                            <p className="text-retro-green font-black text-xs mb-3 uppercase tracking-wider">{exp.company}</p>
                                            {exp.description && (
                                                <p className="text-black/80 text-xs leading-relaxed font-bold mt-2 whitespace-pre-line bg-white/50 p-3 border border-black/10 rounded">
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
                        <div className="bg-white border-3 border-black rounded-xl p-8 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
                            <div className="flex justify-between items-center mb-6">
                                <h3 className="text-xs font-black uppercase tracking-widest text-black flex items-center">
                                    <FileText className="w-4 h-4 mr-2 text-retro-red" />
                                    Resume Source (Markdown format)
                                </h3>
                                <button 
                                    onClick={handleCopy}
                                    className="px-3.5 py-1.5 bg-white border-2 border-black rounded-lg text-[10px] font-black uppercase tracking-wider text-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:bg-retro-cream hover:translate-x-[0.5px] hover:translate-y-[0.5px] hover:shadow-[1px_1px_0px_0px_rgba(0,0,0,1)] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none transition-all flex items-center"
                                >
                                    {copied ? (
                                        <>
                                            <Check className="w-3.5 h-3.5 mr-1.5 text-retro-green" />
                                            Copied
                                        </>
                                    ) : (
                                        <>
                                            <Copy className="w-3.5 h-3.5 mr-1.5" />
                                            Copy Code
                                        </>
                                    )}
                                </button>
                            </div>
                            
                            <div className="bg-retro-cream border-2 border-black rounded-lg p-6 max-h-[300px] overflow-y-auto custom-scrollbar">
                                <pre className="text-[11px] font-mono text-black whitespace-pre-wrap leading-relaxed select-text">
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
