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
        <div className="space-y-10 px-4 pb-20 bg-retro-cream text-black font-sans">
            {/* Header Cards Row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white border-3 border-black rounded-xl p-6 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] relative overflow-hidden group">
                    <h3 className="text-[11px] font-black uppercase tracking-widest text-black/60 mb-2">Total Jobs Scanned</h3>
                    <p className="text-4xl font-black text-black">{totalJobs}</p>
                    <span className="text-[10px] text-retro-green font-black block mt-2">Active database pipeline</span>
                </div>
                <div className="bg-white border-3 border-black rounded-xl p-6 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] relative overflow-hidden group">
                    <h3 className="text-[11px] font-black uppercase tracking-widest text-black/60 mb-2">Avg. Match Score</h3>
                    <p className="text-4xl font-black text-retro-red">{avgMatchScore}%</p>
                    <span className="text-[10px] text-retro-green font-black block mt-2">Semantic similarity strength</span>
                </div>
                <div className="bg-white border-3 border-black rounded-xl p-6 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] relative overflow-hidden group">
                    <h3 className="text-[11px] font-black uppercase tracking-widest text-black/60 mb-2">Avg. Experience Req.</h3>
                    <p className="text-4xl font-black text-black">
                        {avgExperience} <span className="text-lg">Yrs</span>
                    </p>
                    <span className="text-[10px] text-retro-green font-black block mt-2">Ideal market alignment</span>
                </div>
            </div>

            {/* Core Distribution Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Experience Distribution Pie Chart */}
                <div className="bg-white border-3 border-black rounded-xl p-8 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] flex flex-col justify-between">
                    <div>
                        <h3 className="text-xs font-black uppercase tracking-widest text-black mb-6 flex items-center">
                            <PieChart className="w-4 h-4 mr-2 text-retro-red" />
                            Experience Requirements Distribution
                        </h3>
                        <p className="text-xs text-black/60 font-bold mb-8">
                            A breakdown of the minimum required years of experience across all matching listings in your database.
                        </p>
                    </div>

                    <div className="flex flex-col sm:flex-row items-center justify-around gap-6">
                        {/* SVG Donut Ring */}
                        {totalJobs > 0 ? (
                            <div className="relative w-40 h-40 flex items-center justify-center flex-shrink-0">
                                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                                    {/* Black Outline base */}
                                    <circle cx="50" cy="50" r="40" fill="transparent" stroke="var(--retro-border)" strokeWidth="14" />
                                    {/* Inner core slice background */}
                                    <circle cx="50" cy="50" r="40" fill="transparent" stroke="var(--retro-card-bg)" strokeWidth="10" />
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
                                                    className="transition-all duration-1000 ease-out"
                                                />
                                            );
                                        });
                                    })()}
                                </svg>
                                <div className="absolute flex flex-col items-center justify-center text-center">
                                    <span className="text-[10px] font-black uppercase text-black/50 tracking-wider">Scanned</span>
                                    <span className="text-2xl font-black text-black">{totalJobs}</span>
                                </div>
                            </div>
                        ) : (
                            <div className="w-40 h-40 rounded-xl border-3 border-dashed border-black flex items-center justify-center text-xs text-black/60 font-black italic">
                                No Jobs
                            </div>
                        )}

                        {/* Legend */}
                        <div className="space-y-3 flex-1 w-full">
                            {expDistribution.map((item, idx) => (
                                <div key={idx} className="flex items-center justify-between text-xs font-bold">
                                    <div className="flex items-center">
                                        <div className="w-3.5 h-3.5 border-2 border-black mr-2.5" style={{ backgroundColor: item.color }}></div>
                                        <span className="text-black font-black">{item.label}</span>
                                    </div>
                                    <div className="text-right flex items-center space-x-2">
                                        <span className="text-black/60 font-bold">{item.count} roles</span>
                                        <span className="text-black font-black w-8">{item.percentage}%</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Platform Source Breakdown Bar Chart */}
                <div className="bg-white border-3 border-black rounded-xl p-8 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] flex flex-col justify-between">
                    <div>
                        <h3 className="text-xs font-black uppercase tracking-widest text-black mb-6 flex items-center">
                            <BarChart3 className="w-4 h-4 mr-2 text-retro-red" />
                            Market Job Sources Representation
                        </h3>
                        <p className="text-xs text-black/60 font-bold mb-8">
                            A breakdown of where the active matching opportunities were harvested from.
                        </p>
                    </div>

                    <div className="space-y-5">
                        {totalJobs > 0 ? (
                            sourceDistribution.map((item, idx) => (
                                <div key={idx} className="space-y-1.5">
                                    <div className="flex justify-between items-center text-xs font-bold">
                                        <span className="font-black text-black">{item.name}</span>
                                        <div className="flex space-x-3 text-black/60 font-bold">
                                            <span>{item.count} postings</span>
                                            <span className="text-retro-red font-black">{item.percentage}%</span>
                                        </div>
                                    </div>
                                    <div className="h-4 bg-retro-cream rounded-lg border-2 border-black overflow-hidden relative">
                                        <div 
                                            className="h-full rounded-none transition-all duration-1000 ease-out border-r-2 border-black" 
                                            style={{ width: `${item.percentage}%`, backgroundColor: item.color }}
                                        ></div>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="py-12 text-center text-xs text-black/60 font-black italic border-2 border-dashed border-black/30 rounded-lg">
                                Scrape job sources to build distribution graphs.
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Skills demand mapping & gap analysis */}
            <div className="bg-white border-3 border-black rounded-xl p-8 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                    <div>
                        <h3 className="text-sm font-black uppercase tracking-widest text-black flex items-center">
                            <Zap className="w-5 h-5 mr-3 text-retro-red animate-bounce" />
                            Skills Gap Matrix & AI Insights
                        </h3>
                        <p className="text-xs text-black/60 font-black uppercase tracking-wider mt-1">
                            Calculated by checking terms frequency in job descriptions relative to your profile
                        </p>
                    </div>

                    {parsedData && (
                        <div className="text-xs bg-retro-yellow border-2 border-black text-black px-4 py-2.5 rounded-lg font-black flex items-center shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
                            <Sparkles className="w-4 h-4 mr-2 text-retro-red fill-retro-red" />
                            Analyzed using Active Neural Identity
                        </div>
                    )}
                </div>

                {!parsedData ? (
                    <div className="py-12 text-center border-3 border-dashed border-black rounded-lg bg-retro-cream/20">
                        <TrendingUp className="w-10 h-10 text-black/40 mx-auto mb-3" />
                        <p className="text-black/70 text-xs font-black italic">Sync your resume profile to activate skills mismatch intelligence.</p>
                    </div>
                ) : !skillsAnalysis || (skillsAnalysis.userSkillsMatched.length === 0 && skillsAnalysis.gapsDiscovered.length === 0) ? (
                    <div className="py-12 text-center text-xs text-black/60 italic font-bold">
                        Not enough job descriptions stored to perform statistical analysis. Trigger a scrape!
                    </div>
                ) : (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
                        {/* Current Matching Strength */}
                        <div className="space-y-6">
                            <h4 className="text-xs font-black text-black uppercase tracking-widest flex items-center">
                                <CheckCircle className="w-4 h-4 mr-2 text-retro-green" />
                                Your Top Demanded Skills
                            </h4>
                            <div className="space-y-4">
                                {skillsAnalysis.userSkillsMatched.slice(0, 5).map((skill, idx) => (
                                    <div key={idx} className="flex items-center">
                                        <div className="w-28 text-xs font-black text-black truncate pr-2 capitalize">{skill.name}</div>
                                        <div className="flex-1 h-3 bg-retro-cream rounded-lg border-2 border-black overflow-hidden">
                                            <div className="h-full bg-retro-green border-r border-black" style={{ width: `${skill.percentage}%` }}></div>
                                        </div>
                                        <div className="w-16 text-right text-xs font-black text-retro-green">{skill.percentage}%</div>
                                    </div>
                                ))}
                                {skillsAnalysis.userSkillsMatched.length === 0 && (
                                    <p className="text-black/60 text-xs italic">No matching skills detected in job descriptions. Try importing jobs matching your role.</p>
                                )}
                            </div>
                        </div>

                        {/* Gap Analysis Opportunities */}
                        <div className="space-y-6">
                            <h4 className="text-xs font-black text-black uppercase tracking-widest flex items-center">
                                <ShieldAlert className="w-4 h-4 mr-2 text-retro-yellow fill-retro-yellow" />
                                Identified Skills Gaps
                            </h4>
                            <div className="space-y-4">
                                {skillsAnalysis.gapsDiscovered.map((skill, idx) => (
                                    <div key={idx} className="flex items-center justify-between bg-retro-cream border-2 border-black rounded-lg p-4 shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
                                        <div>
                                            <span className="text-xs font-black text-black capitalize">{skill.name}</span>
                                            <span className="text-[9px] text-black/60 font-black block uppercase tracking-wider mt-0.5">
                                                Found in {skill.percentage}% of matching roles
                                            </span>
                                        </div>
                                        <div className="bg-retro-pink border-2 border-black text-black text-[10px] font-black uppercase tracking-wider px-3 py-1.5 rounded shadow-[1.5px_1.5px_0px_0px_rgba(0,0,0,1)]">
                                            +{skill.percentage}% match boost
                                        </div>
                                    </div>
                                ))}
                                {skillsAnalysis.gapsDiscovered.length === 0 && (
                                    <div className="py-6 text-center text-xs text-black/60 font-bold italic border-2 border-dashed border-black/30 rounded-lg">
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
