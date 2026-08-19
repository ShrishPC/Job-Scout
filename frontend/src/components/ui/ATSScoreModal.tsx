"use client";

import React, { useState, useEffect } from 'react';
import { 
  X, 
  CheckCircle2, 
  AlertTriangle, 
  Sparkles, 
  Download, 
  FileText, 
  Check, 
  Copy, 
  Loader2, 
  ChevronRight, 
  TrendingUp, 
  Layers, 
  Zap, 
  Plus, 
  ArrowRight,
  ShieldCheck,
  Target
} from 'lucide-react';
import axios from 'axios';

interface ATSScoreModalProps {
  isOpen: boolean;
  onClose: () => void;
  job: any;
  parsedData?: any;
  onOpenTailor?: (job: any, initialInstruction?: string) => void;
}

const ATSScoreModal: React.FC<ATSScoreModalProps> = ({
  isOpen,
  onClose,
  job,
  parsedData,
  onOpenTailor
}) => {
  const [loading, setLoading] = useState(true);
  const [atsData, setAtsData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [copiedBullet, setCopiedBullet] = useState(false);
  const [exportingFormat, setExportingFormat] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && job) {
      fetchATSAnalysis();
    }
  }, [isOpen, job]);

  const fetchATSAnalysis = async () => {
    setLoading(true);
    setError(null);
    const apiHost = typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.hostname}:8001` : 'http://127.0.0.1:8001';

    try {
      const payload: any = {
        job_id: job.id || undefined,
        job_title: job.title,
        company: job.company,
        job_description: job.description
      };

      if (parsedData?.resume_markdown) {
        payload.resume_text = parsedData.resume_markdown;
      }

      const response = await axios.post(`${apiHost}/ai/ats-analyze`, payload);
      setAtsData(response.data);
      setLoading(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to analyze ATS compatibility. Please ensure a resume is uploaded.");
      setLoading(false);
    }
  };

  const handleCopyBullet = (text: string) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedBullet(true);
    setTimeout(() => setCopiedBullet(false), 2000);
  };

  const handleExportReport = async (format: 'pdf' | 'docx') => {
    if (!atsData) return;
    setExportingFormat(format);
    const apiHost = typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.hostname}:8001` : 'http://127.0.0.1:8001';

    try {
      const response = await axios.post(
        `${apiHost}/export/ats-report`,
        {
          ats_data: atsData,
          format: format,
          candidate_name: parsedData?.parsed_json?.full_name || "Applicant"
        },
        { responseType: 'blob' }
      );

      const blob = new Blob([response.data], {
        type: format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      const safeCompany = (job.company || "Company").replace(/[^a-zA-Z0-9_-]/g, '_');
      link.setAttribute('download', `ATS_Report_${safeCompany}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Export error:", err);
    } finally {
      setExportingFormat(null);
    }
  };

  const handleInjectToCopilot = (missingSkillName: string) => {
    if (onOpenTailor) {
      const instruction = `Weave '${missingSkillName}' naturally into one of my experience bullet points showcasing measurable impact.`;
      onOpenTailor(job, instruction);
      onClose();
    }
  };

  if (!isOpen) return null;

  const score = atsData?.overall_score || 0;
  const ratingLabel = atsData?.rating_label || "EVALUATED";
  const ratingColor = atsData?.rating_color || "yellow";

  const getScoreBadgeStyles = () => {
    if (score >= 80) return "bg-retro-green text-white border-black";
    if (score >= 60) return "bg-retro-yellow text-black border-black";
    return "bg-retro-pink text-black border-black";
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-150" onClick={onClose}>
      <div 
        className="bg-retro-cream border-4 border-black rounded-xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] overflow-hidden text-black"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header Bar */}
        <div className="bg-white border-b-3 border-black p-5 px-8 flex justify-between items-center shrink-0">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-retro-yellow border-2 border-black rounded-lg flex items-center justify-center shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] font-black">
              <Target className="w-5 h-5 text-black" />
            </div>
            <div>
              <h2 className="text-lg font-black tracking-tight text-black flex items-center gap-2">
                ATS Compatibility & Keyword Diagnostic
              </h2>
              <p className="text-black/60 text-xs font-bold truncate max-w-md">
                {job?.title} • <span className="text-retro-green font-black">{job?.company}</span>
              </p>
            </div>
          </div>

          <button 
            onClick={onClose}
            className="w-9 h-9 bg-white border-2 border-black rounded-lg flex items-center justify-center shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:bg-retro-pink hover:translate-x-[0.5px] hover:translate-y-[0.5px] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none transition-all cursor-pointer"
          >
            <X className="w-5 h-5 text-black" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-8 space-y-8 custom-scrollbar">
          {loading ? (
            <div className="py-24 text-center space-y-4">
              <Loader2 className="w-12 h-12 animate-spin mx-auto text-retro-red" />
              <h3 className="text-lg font-black text-black uppercase tracking-wider">Analyzing ATS Alignment...</h3>
              <p className="text-xs font-bold text-black/60 max-w-sm mx-auto">
                Extracting technical entity keywords, measuring embedding cosine similarity, and calculating rubric weights.
              </p>
            </div>
          ) : error ? (
            <div className="bg-retro-pink border-3 border-black rounded-xl p-8 text-center space-y-4 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
              <AlertTriangle className="w-12 h-12 text-black mx-auto" />
              <h3 className="text-base font-black text-black">Analysis Unavailable</h3>
              <p className="text-xs font-bold text-black/80 max-w-md mx-auto">{error}</p>
              <button 
                onClick={fetchATSAnalysis}
                className="px-6 py-2.5 bg-white border-2 border-black rounded-lg font-black text-xs uppercase shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:bg-retro-cream cursor-pointer"
              >
                Retry Analysis
              </button>
            </div>
          ) : (
            <>
              {/* Hero Score Section */}
              <div className="bg-white border-3 border-black rounded-xl p-6 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
                <div className="md:col-span-4 flex flex-col items-center justify-center p-6 bg-retro-cream border-3 border-black rounded-xl shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] text-center">
                  <span className="text-[10px] font-black uppercase tracking-widest text-black/60 mb-1">ATS Score</span>
                  <div className="text-5xl font-black tracking-tight text-black mb-2 flex items-baseline">
                    {Math.round(score)}<span className="text-2xl text-black/50">%</span>
                  </div>
                  <span className={`px-3 py-1 rounded-md text-[10px] font-black uppercase tracking-wider border-2 ${getScoreBadgeStyles()}`}>
                    {ratingLabel}
                  </span>
                </div>

                <div className="md:col-span-8 space-y-3">
                  <h3 className="text-xs font-black uppercase tracking-widest text-black flex items-center">
                    <ShieldCheck className="w-4 h-4 mr-1.5 text-retro-green" />
                    Executive ATS Match Verdict
                  </h3>
                  <p className="text-xs font-bold text-black/80 leading-relaxed bg-retro-cream/40 p-4 border-2 border-black border-dashed rounded-lg">
                    {atsData?.summary_verdict}
                  </p>
                  
                  <div className="flex flex-wrap gap-2 pt-1 text-[11px] font-extrabold text-black/70">
                    <span className="bg-retro-sand px-2.5 py-1 rounded border-2 border-black">
                      Keywords Matched: {atsData?.keyword_matrix?.matched_count} / {atsData?.keyword_matrix?.total_jd_keywords}
                    </span>
                    <span className="bg-retro-sand px-2.5 py-1 rounded border-2 border-black">
                      Quantifiable Bullets: {atsData?.formatting_checks?.metric_percentage}%
                    </span>
                    <span className="bg-retro-sand px-2.5 py-1 rounded border-2 border-black">
                      Action Verbs: {atsData?.formatting_checks?.action_verb_percentage}%
                    </span>
                  </div>
                </div>
              </div>

              {/* Category Rubrics (HackerRank-Inspired Scoring Engine) */}
              <div className="space-y-4">
                <h3 className="text-xs font-black uppercase tracking-widest text-black flex items-center">
                  <Layers className="w-4 h-4 mr-2 text-retro-red" />
                  Category Score Breakdown
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {atsData?.category_scores && Object.entries(atsData.category_scores).map(([key, val]: [string, any]) => {
                    const pct = Math.round((val.score / val.max) * 100);
                    return (
                      <div key={key} className="bg-white border-3 border-black rounded-xl p-5 shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] space-y-3">
                        <div className="flex justify-between items-center text-xs font-black">
                          <span className="text-black uppercase tracking-wide">{val.label}</span>
                          <span className="bg-retro-cream px-2 py-0.5 rounded border-2 border-black text-black">
                            {val.score} / {val.max} pts
                          </span>
                        </div>

                        {/* Custom Neo-Brutalist Progress Bar */}
                        <div className="w-full bg-retro-cream h-4 border-2 border-black rounded-md overflow-hidden p-0.5">
                          <div 
                            className={`h-full rounded-sm border-r-2 border-black transition-all duration-500 ${
                              pct >= 75 ? 'bg-retro-green' : pct >= 50 ? 'bg-retro-yellow' : 'bg-retro-pink'
                            }`}
                            style={{ width: `${Math.max(pct, 5)}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Keyword Gap Matrix (Present vs Missing) */}
              <div className="bg-white border-3 border-black rounded-xl p-6 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] space-y-6">
                <div className="flex justify-between items-center">
                  <h3 className="text-xs font-black uppercase tracking-widest text-black flex items-center">
                    <Zap className="w-4 h-4 mr-2 text-retro-yellow" />
                    Keyword Gap Analysis
                  </h3>
                  <span className="text-[10px] font-black text-black/60 uppercase">
                    Click '+' to auto-inject missing skill into Copilot
                  </span>
                </div>

                {/* Missing Skills Section */}
                <div className="space-y-2">
                  <div className="text-[11px] font-black uppercase tracking-wider text-retro-red flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-retro-red" />
                    Missing in Resume ({atsData?.keyword_matrix?.missing_skills?.length || 0})
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {atsData?.keyword_matrix?.missing_skills?.length > 0 ? (
                      atsData.keyword_matrix.missing_skills.map((skill: any, idx: number) => (
                        <div 
                          key={idx}
                          className="flex items-center space-x-1.5 bg-retro-pink border-2 border-black px-3 py-1.5 rounded-lg shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] text-xs font-black text-black"
                        >
                          <span>{skill.name}</span>
                          {skill.importance === 'critical' && (
                            <span className="text-[9px] bg-retro-red text-white px-1 rounded uppercase font-black">
                              REQ
                            </span>
                          )}
                          <button
                            onClick={() => handleInjectToCopilot(skill.name)}
                            title={`Inject ${skill.name} into AI Copilot`}
                            className="ml-1 p-0.5 bg-white border border-black rounded hover:bg-black hover:text-white transition-colors cursor-pointer"
                          >
                            <Plus className="w-3 h-3" />
                          </button>
                        </div>
                      ))
                    ) : (
                      <span className="text-xs font-bold text-retro-green">All key job skills were detected in your resume!</span>
                    )}
                  </div>
                </div>

                {/* Matched Skills Section */}
                <div className="space-y-2 pt-2 border-t-2 border-black/10">
                  <div className="text-[11px] font-black uppercase tracking-wider text-retro-green flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-retro-green" />
                    Detected in Resume ({atsData?.keyword_matrix?.matched_skills?.length || 0})
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {atsData?.keyword_matrix?.matched_skills?.length > 0 ? (
                      atsData.keyword_matrix.matched_skills.map((skill: any, idx: number) => (
                        <div 
                          key={idx}
                          className="flex items-center space-x-1.5 bg-retro-mint border-2 border-black px-3 py-1.5 rounded-lg shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] text-xs font-black text-black"
                        >
                          <Check className="w-3.5 h-3.5 text-black" />
                          <span>{skill.name}</span>
                        </div>
                      ))
                    ) : (
                      <span className="text-xs font-bold text-black/50">No direct keyword matches detected.</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Actionable Recommendations & Suggested Rewrite */}
              <div className="bg-white border-3 border-black rounded-xl p-6 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] space-y-5">
                <h3 className="text-xs font-black uppercase tracking-widest text-black flex items-center">
                  <Sparkles className="w-4 h-4 mr-2 text-retro-yellow" />
                  Actionable ATS Optimization Steps
                </h3>

                <ul className="space-y-2 text-xs font-bold text-black/80">
                  {atsData?.recommendations?.map((rec: string, idx: number) => (
                    <li key={idx} className="flex items-start space-x-2">
                      <ChevronRight className="w-4 h-4 text-retro-red shrink-0 mt-0.5" />
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>

                {atsData?.suggested_bullet_rewrite && (
                  <div className="bg-retro-cream border-2 border-black rounded-lg p-4 space-y-2 mt-3">
                    <div className="flex justify-between items-center">
                      <span className="text-[10px] font-black uppercase tracking-wider text-black/60">
                        Suggested Bullet Point Rewrite (Keyword-Optimized)
                      </span>
                      <button 
                        onClick={() => handleCopyBullet(atsData.suggested_bullet_rewrite)}
                        className="px-2.5 py-1 bg-white border-2 border-black rounded text-[10px] font-black uppercase tracking-wider flex items-center gap-1 shadow-[1px_1px_0px_0px_rgba(0,0,0,1)] hover:bg-retro-sand cursor-pointer"
                      >
                        {copiedBullet ? <Check className="w-3 h-3 text-retro-green" /> : <Copy className="w-3 h-3" />}
                        {copiedBullet ? "Copied" : "Copy"}
                      </button>
                    </div>
                    <p className="text-xs font-mono font-bold text-black leading-relaxed">
                      "{atsData.suggested_bullet_rewrite}"
                    </p>
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        {/* Footer Action Bar */}
        <div className="bg-white border-t-3 border-black p-5 px-8 flex flex-wrap gap-4 justify-between items-center shrink-0">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => handleExportReport('pdf')}
              disabled={loading || !!error || exportingFormat !== null}
              className="px-4 py-3 bg-white border-2 border-black rounded-lg text-xs font-black uppercase tracking-wider flex items-center space-x-2 shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:bg-retro-cream hover:translate-x-[0.5px] hover:translate-y-[0.5px] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none transition-all cursor-pointer disabled:opacity-50"
            >
              {exportingFormat === 'pdf' ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4 text-retro-red" />}
              <span>Download PDF</span>
            </button>

            <button
              onClick={() => handleExportReport('docx')}
              disabled={loading || !!error || exportingFormat !== null}
              className="px-4 py-3 bg-white border-2 border-black rounded-lg text-xs font-black uppercase tracking-wider flex items-center space-x-2 shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] hover:bg-retro-cream hover:translate-x-[0.5px] hover:translate-y-[0.5px] active:translate-x-[2px] active:translate-y-[2px] active:shadow-none transition-all cursor-pointer disabled:opacity-50"
            >
              {exportingFormat === 'docx' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4 text-blue-600" />}
              <span>Download DOCX</span>
            </button>
          </div>

          {onOpenTailor && (
            <button
              onClick={() => {
                onOpenTailor(job);
                onClose();
              }}
              className="px-6 py-3.5 bg-retro-yellow text-black border-3 border-black rounded-lg text-xs font-black uppercase tracking-widest flex items-center space-x-2 shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[2px_2px_0px_0px_rgba(0,0,0,1)] active:translate-x-[3px] active:translate-y-[3px] active:shadow-none transition-all cursor-pointer"
            >
              <Sparkles className="w-4 h-4 text-black" />
              <span>Tailor Resume in Copilot</span>
              <ArrowRight className="w-4 h-4 ml-1" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ATSScoreModal;
