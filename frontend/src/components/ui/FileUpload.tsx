"use client";

import React, { useState } from 'react';
import { Upload, FileText, AlertCircle, Loader2, CheckCircle2 } from 'lucide-react';
import axios from 'axios';

interface FileUploadProps {
  onUploadSuccess: (data: any) => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ onUploadSuccess }) => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
      setSuccess(false);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    const apiHost = typeof window !== 'undefined' ? `${window.location.protocol}//${window.location.hostname}:8000` : 'http://127.0.0.1:8000';
    try {
      const response = await axios.post(`${apiHost}/resume/parse`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setSuccess(true);
      setTimeout(() => {
        onUploadSuccess(response.data);
      }, 1000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload and parse resume.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="w-full bg-slate-900/50 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-sm">
      <div className="flex flex-col space-y-5">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 bg-brand-500/10 rounded-xl flex items-center justify-center border border-brand-500/20 text-brand-400">
            {success ? <CheckCircle2 className="w-6 h-6 text-green-400" /> : <Upload className="w-6 h-6" />}
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-100">Upload Resume</h2>
            <p className="text-slate-400 text-xs">PDF, DOCX, or MD • Max 5MB</p>
          </div>
        </div>

        <label className="relative group block cursor-pointer">
          <div className={`
            flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-xl transition-all duration-300
            ${file ? 'border-brand-500/40 bg-brand-500/5' : 'border-slate-800 hover:border-slate-700 hover:bg-slate-800/30'}
          `}>
            <FileText className={`w-10 h-10 mb-3 transition-colors ${file ? 'text-brand-400' : 'text-slate-600 group-hover:text-slate-400'}`} />
            <span className="text-sm font-medium text-slate-300 text-center px-4">
              {file ? file.name : 'Click to select or drag resume'}
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
          <div className="flex items-center space-x-2 text-red-400 text-xs bg-red-400/5 border border-red-400/20 p-3 rounded-xl animate-in fade-in slide-in-from-top-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <button
          onClick={handleUpload}
          disabled={!file || uploading || success}
          className={`
            w-full py-4 rounded-xl font-black text-[11px] uppercase tracking-[0.2em] transition-all flex items-center justify-center space-x-3 border
            ${!file || uploading || success 
              ? 'bg-slate-900 text-slate-600 border-slate-800 cursor-not-allowed' 
              : 'bg-gradient-to-r from-brand-600 to-brand-400 text-slate-50 border-brand-400/50 hover:from-brand-500 hover:to-brand-300 active:scale-[0.98] shadow-[0_0_20px_rgba(56,171,248,0.2)]'
            }
          `}
        >
          {uploading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Analyzing Resume...</span>
            </>
          ) : success ? (
            <div className="flex items-center text-slate-950">
              <CheckCircle2 className="w-4 h-4 mr-2" />
              <span>Resume Synced</span>
            </div>
          ) : (
            <span>Sync Profile</span>
          )}
        </button>
      </div>
    </div>
  );
};

export default FileUpload;
