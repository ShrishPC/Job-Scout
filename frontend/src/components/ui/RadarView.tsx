"use client";

import React, { useMemo } from 'react';
import { Target, TrendingUp, AlertTriangle, CheckCircle, BarChart3, PieChart, ShieldAlert, Sparkles, MapPin, Zap } from 'lucide-react';

interface Job {
    id: number;
    title: string;
    company: string;
    description: string;
    location: string;
    experience_required: number;
    match_score: number;
    job_url: string;
}

interface RadarViewProps {
    jobs: Job[];
    parsedData: any;
}

const RadarView: React.FC<RadarViewProps> = ({ jobs, parsedData }) => {
    // 1. Core stats
    const totalJobs = jobs.length;
    const avgMatchScore = useMemo(() => {
        if (jobs.length === 0) return 0;
        return Math.round(jobs.reduce((sum, job) => sum + (job.match_score || 0), 0) / jobs.length);
    }, [jobs]);

    const avgExperience = useMemo(() => {
        const jobsWithExp = jobs.filter(j => j.experience_required !== undefined && j.experience_required > 0);
        if (jobsWithExp.length === 0) return 0;
        return Math.round((jobsWithExp.reduce((sum, job) => sum + (job.experience_required || 0), 0) / jobsWithExp.length) * 10) / 10;
    }, [jobs]);

    // 2. Experience level distribution
    const expDistribution = useMemo(() => {
        const dist = { entry: 0, mid: 0, senior: 0, lead: 0 };
        jobs.forEach(job => {
            const exp = job.experience_required || 0;
            if (exp <= 2) dist.entry++;
            else if (exp <= 5) dist.mid++;
            else if (exp <= 9) dist.senior++;
            else dist.lead++;
        });
        
        const total = Math.max(jobs.length, 1);
        return [
            { label: 'Entry (0-2 Yrs)', count: dist.entry, percentage: Math.round((dist.entry / total) * 100), color: '#38abf8' },
            { label: 'Mid (3-5 Yrs)', count: dist.mid, percentage: Math.round((dist.mid / total) * 100), color: '#34d399' },
            { label: 'Senior (6-9 Yrs)', count: dist.senior, percentage: Math.round((dist.senior / total) * 100), color: '#fbbf24' },
            { label: 'Lead (10+ Yrs)', count: dist.lead, percentage: Math.round((dist.lead / total) * 100), color: '#f87171' }
        ];
    }, [jobs]);

    // 3. Platform source distribution
    const sourceDistribution = useMemo(() => {
        const counts: Record<string, number> = {
            'LinkedIn': 0,
            'Indeed': 0,
            'Naukri': 0,
            'Remote OK': 0,
            'We Work Remotely': 0,
            'Other': 0
        };

        jobs.forEach(job => {
            const url = job.job_url?.toLowerCase() || '';
            if (url.includes('linkedin.com')) counts['LinkedIn']++;
            else if (url.includes('indeed.com')) counts['Indeed']++;
            else if (url.includes('naukri.com')) counts['Naukri']++;
            else if (url.includes('remoteok.com')) counts['Remote OK']++;
            else if (url.includes('weworkremotely.com')) counts['We Work Remotely']++;
            else counts['Other']++;
        });

        const total = Math.max(jobs.length, 1);
        return Object.entries(counts)
            .map(([name, count]) => ({
                name,
                count,
                percentage: Math.round((count / total) * 100),
                color: name === 'LinkedIn' ? '#0e91e9' 
                     : name === 'Indeed' ? '#2563eb' 
                     : name === 'Naukri' ? '#ff6f61' 
                     : name === 'Remote OK' ? '#e2e8f0' 
                     : name === 'We Work Remotely' ? '#ea580c' 
                     : '#64748b'
            }))
            .filter(item => item.count > 0)
            .sort((a, b) => b.count - a.count);
    }, [jobs]);

    // 4. Skills demand mapping & gap analysis
    const skillsAnalysis = useMemo(() => {
        if (!parsedData || !parsedData.parsed_json?.skills) return null;
        const userSkills: string[] = parsedData.parsed_json.skills.map((s: string) => s.toLowerCase());
        
        // Define common industry keywords to look for in job descriptions to discover gaps
        const popularIndustrySkills = [
            'react', 'next.js', 'typescript', 'javascript', 'nodejs', 'python', 'django', 'fastapi',
            'docker', 'kubernetes', 'aws', 'gcp', 'postgresql', 'mongodb', 'redis', 'graphql', 'rest api',
            'github', 'ci/cd', 'tailwind', 'redux', 'sql', 'nosql', 'terraform', 'graphql', 'css', 'html',
            'microservices', 'serverless', 'unit testing', 'agile', 'scrum', 'prompt engineering', 'pytorch', 'tensorflow'
        ];

        const skillMatches: Record<string, number> = {};
        const skillGaps: Record<string, number> = {};

        // Track how often these skills appear in scraped jobs
        jobs.forEach(job => {
            const desc = job.description?.toLowerCase() || '';
            
            // 1. Check user skills
            userSkills.forEach(skill => {
                if (desc.includes(skill)) {
                    skillMatches[skill] = (skillMatches[skill] || 0) + 1;
                }
            });

            // 2. Check general skills to find gaps (which ones does user not have, but are mentioned in jobs?)
            popularIndustrySkills.forEach(industrySkill => {
                if (!userSkills.includes(industrySkill) && desc.includes(industrySkill)) {
                    skillGaps[industrySkill] = (skillGaps[industrySkill] || 0) + 1;
                }
            });
        });

        // Format and sort
        const userSkillsMatched = Object.entries(skillMatches)
            .map(([name, count]) => ({
                name,
                count,
                percentage: Math.round((count / Math.max(jobs.length, 1)) * 100)
            }))
            .sort((a, b) => b.count - a.count);

        const gapsDiscovered = Object.entries(skillGaps)
            .map(([name, count]) => ({
                name,
                count,
                percentage: Math.round((count / Math.max(jobs.length, 1)) * 100)
            }))
            .filter(gap => gap.percentage >= 15) // Only display skills that appear in at least 15% of job posts
            .sort((a, b) => b.count - a.count)
            .slice(0, 5); // Limit to top 5 recommendations

        return {
            userSkillsMatched,
            gapsDiscovered
        };
    }, [jobs, parsedData]);

    return (
        <div className="space-y-10 px-4 pb-20">
            {/* Header Cards Row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-slate-900/40 border border-slate-800 rounded-3xl p-6 backdrop-blur-sm relative overflow-hidden group">
                    <div className="absolute top-0 right-0 w-24 h-24 bg-brand-500/5 rounded-full blur-2xl group-hover:bg-brand-500/10 transition-colors"></div>
                    <h3 className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-2">Total Jobs Scanned</h3>
                    <p className="text-4xl font-black text-slate-100">{totalJobs}</p>
                    <span className="text-[10px] text-slate-400 font-bold block mt-2">Active database pipeline</span>
                </div>
                <div className="bg-slate-900/40 border border-slate-800 rounded-3xl p-6 backdrop-blur-sm relative overflow-hidden group">
                    <div className="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 rounded-full blur-2xl group-hover:bg-emerald-500/10 transition-colors"></div>
                    <h3 className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-2">Avg. Match Score</h3>
                    <p className="text-4xl font-black text-brand-400">{avgMatchScore}%</p>
                    <span className="text-[10px] text-slate-400 font-bold block mt-2">Semantic similarity strength</span>
                </div>
                <div className="bg-slate-900/40 border border-slate-800 rounded-3xl p-6 backdrop-blur-sm relative overflow-hidden group">
                    <div className="absolute top-0 right-0 w-24 h-24 bg-yellow-500/5 rounded-full blur-2xl group-hover:bg-yellow-500/10 transition-colors"></div>
                    <h3 className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-2">Avg. Experience Req.</h3>
                    <p className="text-4xl font-black text-emerald-400">
                        {avgExperience} <span className="text-lg">Yrs</span>
                    </p>
                    <span className="text-[10px] text-slate-400 font-bold block mt-2">Ideal market alignment</span>
                </div>
            </div>

            {/* Core Distribution Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Experience Distribution Pie Chart */}
                <div className="bg-slate-900/40 border border-slate-800 rounded-3xl p-8 backdrop-blur-sm flex flex-col justify-between">
                    <div>
                        <h3 className="text-xs font-black uppercase tracking-widest text-slate-200 mb-6 flex items-center">
                            <PieChart className="w-4 h-4 mr-2 text-brand-400" />
                            Experience Requirements Distribution
                        </h3>
                        <p className="text-xs text-slate-400 font-medium mb-8">
                            A breakdown of the minimum required years of experience across all matching listings in your database.
                        </p>
                    </div>

                    <div className="flex flex-col sm:flex-row items-center justify-around gap-6">
                        {/* SVG Donut Ring */}
                        {totalJobs > 0 ? (
                            <div className="relative w-40 h-40 flex items-center justify-center flex-shrink-0">
                                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                                    {/* Background Circle */}
                                    <circle cx="50" cy="50" r="40" fill="transparent" stroke="#1e293b" strokeWidth="10" />
                                    {/* Dynamic slices */}
                                    {(() => {
                                        let accumulatedPercent = 0;
                                        return expDistribution.map((item, index) => {
                                            if (item.percentage === 0) return null;
                                            const r = 40;
                                            const circumference = 2 * Math.PI * r;
                                            const strokeDasharray = `${(item.percentage / 100) * circumference} ${circumference}`;
                                            const strokeDashoffset = -((accumulatedPercent / 100) * circumference);
                                            accumulatedPercent += item.percentage;
                                            return (
                                                <circle
                                                    key={index}
                                                    cx="50"
                                                    cy="50"
                                                    r={r}
                                                    fill="transparent"
                                                    stroke={item.color}
                                                    strokeWidth="10"
                                                    strokeDasharray={strokeDasharray}
                                                    strokeDashoffset={strokeDashoffset}
                                                    strokeLinecap="round"
                                                    className="transition-all duration-1000 ease-out"
                                                />
                                            );
                                        });
                                    })()}
                                </svg>
                                <div className="absolute flex flex-col items-center justify-center text-center">
                                    <span className="text-[10px] font-black uppercase text-slate-500 tracking-wider">Scanned</span>
                                    <span className="text-2xl font-black text-slate-100">{totalJobs}</span>
                                </div>
                            </div>
                        ) : (
                            <div className="w-40 h-40 rounded-full border-4 border-dashed border-slate-800 flex items-center justify-center text-xs text-slate-600 font-bold italic">
                                No Jobs
                            </div>
                        )}

                        {/* Legend */}
                        <div className="space-y-3 flex-1 w-full">
                            {expDistribution.map((item, idx) => (
                                <div key={idx} className="flex items-center justify-between text-xs">
                                    <div className="flex items-center">
                                        <div className="w-2.5 h-2.5 rounded-full mr-2.5" style={{ backgroundColor: item.color }}></div>
                                        <span className="text-slate-300 font-bold">{item.label}</span>
                                    </div>
                                    <div className="text-right flex items-center space-x-2">
                                        <span className="text-slate-500 font-bold">{item.count} roles</span>
                                        <span className="text-slate-100 font-black w-8">{item.percentage}%</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Platform Source Breakdown Bar Chart */}
                <div className="bg-slate-900/40 border border-slate-800 rounded-3xl p-8 backdrop-blur-sm flex flex-col justify-between">
                    <div>
                        <h3 className="text-xs font-black uppercase tracking-widest text-slate-200 mb-6 flex items-center">
                            <BarChart3 className="w-4 h-4 mr-2 text-brand-400" />
                            Market Job Sources Representation
                        </h3>
                        <p className="text-xs text-slate-400 font-medium mb-8">
                            A breakdown of where the active matching opportunities were harvested from.
                        </p>
                    </div>

                    <div className="space-y-5">
                        {totalJobs > 0 ? (
                            sourceDistribution.map((item, idx) => (
                                <div key={idx} className="space-y-1.5">
                                    <div className="flex justify-between items-center text-xs">
                                        <span className="font-bold text-slate-300">{item.name}</span>
                                        <div className="flex space-x-3 text-slate-400 font-bold">
                                            <span>{item.count} postings</span>
                                            <span className="text-brand-400 font-black">{item.percentage}%</span>
                                        </div>
                                    </div>
                                    <div className="h-3 bg-slate-950/80 rounded-full border border-slate-900 overflow-hidden relative">
                                        <div 
                                            className="h-full rounded-full transition-all duration-1000 ease-out shadow-[0_0_8px_rgba(56,171,248,0.2)]" 
                                            style={{ width: `${item.percentage}%`, backgroundColor: item.color }}
                                        ></div>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="py-12 text-center text-xs text-slate-600 font-bold italic">
                                Scrape job sources to build distribution graphs.
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Skills demand mapping & gap analysis */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-3xl p-8 backdrop-blur-sm">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                    <div>
                        <h3 className="text-sm font-black uppercase tracking-widest text-slate-200 flex items-center">
                            <Zap className="w-5 h-5 mr-3 text-brand-400" />
                            Skills Gap Matrix & AI Insights
                        </h3>
                        <p className="text-xs text-slate-500 font-bold uppercase tracking-wider mt-1">
                            Calculated by checking terms frequency in job descriptions relative to your profile
                        </p>
                    </div>

                    {parsedData && (
                        <div className="text-xs bg-brand-500/5 border border-brand-500/20 text-brand-400 px-4 py-2.5 rounded-2xl font-bold flex items-center">
                            <Sparkles className="w-4 h-4 mr-2" />
                            Analyzed using Active Neural Identity
                        </div>
                    )}
                </div>

                {!parsedData ? (
                    <div className="py-12 text-center border border-dashed border-slate-800 rounded-2xl">
                        <TrendingUp className="w-10 h-10 text-slate-700 mx-auto mb-3" />
                        <p className="text-slate-500 text-xs font-bold italic">Sync your resume profile to activate deep skills mismatch intelligence.</p>
                    </div>
                ) : !skillsAnalysis || (skillsAnalysis.userSkillsMatched.length === 0 && skillsAnalysis.gapsDiscovered.length === 0) ? (
                    <div className="py-12 text-center text-xs text-slate-500 italic">
                        Not enough job descriptions stored to perform statistical analysis. Trigger a scrape!
                    </div>
                ) : (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
                        {/* Current Matching Strength */}
                        <div className="space-y-6">
                            <h4 className="text-xs font-black text-slate-300 uppercase tracking-widest flex items-center">
                                <CheckCircle className="w-4 h-4 mr-2 text-emerald-400" />
                                Your Top Demanded Skills
                            </h4>
                            <div className="space-y-4">
                                {skillsAnalysis.userSkillsMatched.slice(0, 5).map((skill, idx) => (
                                    <div key={idx} className="flex items-center">
                                        <div className="w-28 text-xs font-bold text-slate-300 truncate pr-2 capitalize">{skill.name}</div>
                                        <div className="flex-1 h-2.5 bg-slate-950/80 rounded-full border border-slate-900 overflow-hidden">
                                            <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${skill.percentage}%` }}></div>
                                        </div>
                                        <div className="w-16 text-right text-xs font-black text-emerald-400">{skill.percentage}%</div>
                                    </div>
                                ))}
                                {skillsAnalysis.userSkillsMatched.length === 0 && (
                                    <p className="text-slate-600 text-xs italic">No matching skills detected in job descriptions. Try importing jobs matching your role.</p>
                                )}
                            </div>
                        </div>

                        {/* Gap Analysis Opportunities */}
                        <div className="space-y-6">
                            <h4 className="text-xs font-black text-slate-300 uppercase tracking-widest flex items-center">
                                <ShieldAlert className="w-4 h-4 mr-2 text-yellow-400" />
                                Identified Skills Gaps
                            </h4>
                            <div className="space-y-4">
                                {skillsAnalysis.gapsDiscovered.map((skill, idx) => (
                                    <div key={idx} className="flex items-center justify-between bg-slate-950/50 border border-slate-900 rounded-2xl p-4">
                                        <div>
                                            <span className="text-xs font-black text-slate-200 capitalize">{skill.name}</span>
                                            <span className="text-[9px] text-slate-500 font-bold block uppercase tracking-wider mt-0.5">
                                                Found in {skill.percentage}% of matching roles
                                            </span>
                                        </div>
                                        <div className="bg-yellow-500/10 border border-yellow-500/20 text-yellow-500 text-[10px] font-black uppercase tracking-wider px-3 py-1.5 rounded-xl">
                                            +{skill.percentage}% match boost
                                        </div>
                                    </div>
                                ))}
                                {skillsAnalysis.gapsDiscovered.length === 0 && (
                                    <div className="py-6 text-center text-xs text-slate-600 font-bold italic border border-dashed border-slate-800 rounded-2xl">
                                        Excellent match! No high-frequency skills gaps detected.
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default RadarView;
