"use client";

import React, { useMemo } from 'react';
import { Target, TrendingUp, AlertTriangle, CheckCircle, BarChart3, PieChart, ShieldAlert, Sparkles, MapPin, Zap, Crosshair } from 'lucide-react';

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
            'microservices', 'serverless', 'unit testing', 'agile', 'scrum', 'prompt engineering', 'pytorch', 'tensorflow',
            'java', 'spring', 'go', 'rust', 'c++', 'c#'
        ];

        const skillMatches: Record<string, number> = {};
        const skillGaps: Record<string, number> = {};
        const allSkillFreq: Record<string, number> = {};

        // Track how often these skills appear in scraped jobs
        jobs.forEach(job => {
            const desc = job.description?.toLowerCase() || '';
            
            // Check all popular skills for overall frequency
            popularIndustrySkills.forEach(skill => {
                if (desc.includes(skill)) {
                    allSkillFreq[skill] = (allSkillFreq[skill] || 0) + 1;
                }
            });

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

        const total = Math.max(jobs.length, 1);

        // Format and sort
        const userSkillsMatched = Object.entries(skillMatches)
            .map(([name, count]) => ({
                name,
                count,
                percentage: Math.round((count / total) * 100)
            }))
            .sort((a, b) => b.count - a.count);

        const gapsDiscovered = Object.entries(skillGaps)
            .map(([name, count]) => ({
                name,
                count,
                percentage: Math.round((count / total) * 100)
            }))
            .filter(gap => gap.percentage >= 15) // Only display skills that appear in at least 15% of job posts
            .sort((a, b) => b.count - a.count)
            .slice(0, 5); // Limit to top 5 recommendations

        // Top 6 skills overall for the Radar Chart
        const top6Overall = Object.entries(allSkillFreq)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 6)
            .map(([name, count]) => {
                const marketPct = Math.round((count / total) * 100);
                const userHas = userSkills.includes(name);
                // If user has it, their score is 100. If they don't, it's 0.
                const userPct = userHas ? 100 : 0;
                return { name, marketPct, userPct };
            });

        // If we don't have enough data to form a polygon (needs at least 3, ideally 6)
        while (top6Overall.length > 0 && top6Overall.length < 6) {
            top6Overall.push({ name: 'N/A', marketPct: 0, userPct: 0 });
        }

        return {
            userSkillsMatched,
            gapsDiscovered,
            radarData: top6Overall
        };
    }, [jobs, parsedData]);

    // Render Custom Brutalist SVG Radar Chart
    const renderRadarChart = () => {
        if (!skillsAnalysis || skillsAnalysis.radarData.length < 3) return null;

        const size = 320;
        const center = size / 2;
        const radius = 100;
        const data = skillsAnalysis.radarData;
        const numSides = data.length;
        const angleStep = (Math.PI * 2) / numSides;

        // Calculate points for polygons
        const getPolygonPoints = (dataKey: 'marketPct' | 'userPct' | 'bg') => {
            return data.map((item, i) => {
                const angle = i * angleStep - Math.PI / 2; // start at top
                const value = dataKey === 'bg' ? 100 : item[dataKey];
                const r = (value / 100) * radius;
                const x = center + r * Math.cos(angle);
                const y = center + r * Math.sin(angle);
                return `${x},${y}`;
            }).join(' ');
        };

        const bgPoints = getPolygonPoints('bg');
        const marketPoints = getPolygonPoints('marketPct');
        const userPoints = getPolygonPoints('userPct');

        return (
            <div className="relative w-full flex flex-col items-center justify-center pt-8">
                <svg width={size} height={size} className="overflow-visible">
                    {/* Background Web */}
                    <polygon points={bgPoints} fill="#fff" stroke="#000" strokeWidth="3" />
                    
                    {/* Inner Web Lines (Ticks) */}
                    {[0.25, 0.5, 0.75].map((scale, i) => {
                        const tickPoints = data.map((_, idx) => {
                            const angle = idx * angleStep - Math.PI / 2;
                            const r = radius * scale;
                            return `${center + r * Math.cos(angle)},${center + r * Math.sin(angle)}`;
                        }).join(' ');
                        return <polygon key={i} points={tickPoints} fill="none" stroke="#000" strokeWidth="1" strokeDasharray="4 4" opacity="0.3" />;
                    })}

                    {/* Spokes */}
                    {data.map((_, i) => {
                        const angle = i * angleStep - Math.PI / 2;
                        const x = center + radius * Math.cos(angle);
                        const y = center + radius * Math.sin(angle);
                        return <line key={i} x1={center} y1={center} x2={x} y2={y} stroke="#000" strokeWidth="2" />;
                    })}

                    {/* Market Demand Polygon */}
                    <polygon 
                        points={marketPoints} 
                        fill="#FF90E8" 
                        fillOpacity="0.7" 
                        stroke="#FF90E8" 
                        strokeWidth="4" 
                        style={{ mixBlendMode: 'multiply' }}
                    />

                    {/* User Skill Polygon */}
                    <polygon 
                        points={userPoints} 
                        fill="#FFC900" 
                        fillOpacity="0.7" 
                        stroke="#FFC900" 
                        strokeWidth="4" 
                        style={{ mixBlendMode: 'multiply' }}
                    />
                    
                    {/* Outline for the User Polygon for pop */}
                    <polygon 
                        points={userPoints} 
                        fill="none" 
                        stroke="#000" 
                        strokeWidth="3" 
                        strokeLinejoin="round"
                    />

                    {/* Plot Points for User */}
                    {data.map((item, i) => {
                        const angle = i * angleStep - Math.PI / 2;
                        const r = (item.userPct / 100) * radius;
                        const x = center + r * Math.cos(angle);
                        const y = center + r * Math.sin(angle);
                        return (
                            <circle key={`u-${i}`} cx={x} cy={y} r="5" fill="#FFC900" stroke="#000" strokeWidth="2" />
                        );
                    })}

                    {/* Axis Labels */}
                    {data.map((item, i) => {
                        const angle = i * angleStep - Math.PI / 2;
                        // Push text further out
                        const r = radius + 30;
                        const x = center + r * Math.cos(angle);
                        const y = center + r * Math.sin(angle);
                        
                        let textAnchor = "middle";
                        if (x < center - 10) textAnchor = "end";
                        if (x > center + 10) textAnchor = "start";

                        return (
                            <text 
                                key={`label-${i}`} 
                                x={x} 
                                y={y + 4} 
                                textAnchor={textAnchor} 
                                className="text-[10px] font-black uppercase tracking-widest fill-black"
                            >
                                {item.name}
                            </text>
                        );
                    })}
                </svg>
                
                {/* Legend */}
                <div className="flex space-x-6 mt-8 border-3 border-black p-3 bg-white shadow-[3px_3px_0px_0px_rgba(0,0,0,1)]">
                    <div className="flex items-center space-x-2">
                        <div className="w-4 h-4 bg-[#FF90E8] border-2 border-black"></div>
                        <span className="text-[10px] font-black uppercase text-black">Market Demand</span>
                    </div>
                    <div className="flex items-center space-x-2">
                        <div className="w-4 h-4 bg-[#FFC900] border-2 border-black"></div>
                        <span className="text-[10px] font-black uppercase text-black">Your Skills</span>
                    </div>
                </div>
            </div>
        );
    };

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

            {/* Skills Gap Radar & Matrix */}
            <div className="bg-white border-3 border-black rounded-xl p-8 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8 border-b-3 border-black pb-6">
                    <div>
                        <h3 className="text-2xl font-black uppercase tracking-tight text-black flex items-center">
                            <Crosshair className="w-8 h-8 mr-3 text-retro-red" />
                            Skill Gap Analysis Radar
                        </h3>
                        <p className="text-xs text-black/60 font-black uppercase tracking-wider mt-2">
                            Comparing your resume's capabilities against market demand requirements
                        </p>
                    </div>
                    {parsedData && (
                        <div className="text-[10px] bg-retro-yellow border-2 border-black text-black px-4 py-2.5 rounded-lg font-black flex items-center justify-center shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] uppercase tracking-widest">
                            AI-Powered Mapping
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
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
                        {/* Radar Chart Visual */}
                        <div className="flex flex-col items-center justify-center w-full h-full min-h-[400px]">
                            {renderRadarChart()}
                        </div>

                        {/* Analysis Matrix */}
                        <div className="space-y-10">
                            {/* Current Matching Strength */}
                            <div className="space-y-6">
                                <h4 className="text-xs font-black text-black uppercase tracking-widest flex items-center bg-retro-green/20 border-2 border-black p-2 inline-flex shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
                                    <CheckCircle className="w-4 h-4 mr-2 text-retro-green" />
                                    Your Top Demanded Skills
                                </h4>
                                <div className="space-y-4">
                                    {skillsAnalysis.userSkillsMatched.slice(0, 4).map((skill, idx) => (
                                        <div key={idx} className="flex items-center group">
                                            <div className="w-32 text-xs font-black text-black truncate pr-2 capitalize group-hover:text-retro-green transition-colors">{skill.name}</div>
                                            <div className="flex-1 h-4 bg-retro-cream rounded-lg border-2 border-black overflow-hidden relative">
                                                <div className="h-full bg-retro-green border-r-2 border-black" style={{ width: `${skill.percentage}%` }}></div>
                                            </div>
                                            <div className="w-16 text-right text-xs font-black text-retro-green">{skill.percentage}%</div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Gap Analysis Opportunities */}
                            <div className="space-y-6">
                                <h4 className="text-xs font-black text-black uppercase tracking-widest flex items-center bg-retro-pink/20 border-2 border-black p-2 inline-flex shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
                                    <ShieldAlert className="w-4 h-4 mr-2 text-retro-red" />
                                    High Priority Gaps
                                </h4>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                    {skillsAnalysis.gapsDiscovered.map((skill, idx) => (
                                        <div key={idx} className="flex flex-col bg-retro-cream border-2 border-black p-4 shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] transition-all cursor-default group">
                                            <span className="text-sm font-black text-black capitalize mb-1 group-hover:text-retro-red transition-colors">{skill.name}</span>
                                            <span className="text-[9px] text-black/70 font-black uppercase tracking-widest mb-3">
                                                In {skill.percentage}% of roles
                                            </span>
                                            <div className="bg-retro-red text-white text-[10px] font-black uppercase tracking-widest px-2 py-1 border-2 border-black w-max">
                                                Learn to boost match
                                            </div>
                                        </div>
                                    ))}
                                    {skillsAnalysis.gapsDiscovered.length === 0 && (
                                        <div className="py-6 text-center text-xs text-black/60 font-bold italic border-2 border-dashed border-black/30 rounded-lg col-span-2">
                                            Excellent match! No high-frequency skills gaps detected.
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default RadarView;
