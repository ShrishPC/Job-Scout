"use client";
import React, { useState, useEffect } from 'react';
import { Upload, FileText, AlertCircle, Loader2, CheckCircle2 } from 'lucide-react';

interface FileUploadProps {
  globalFile: File | null;
  globalUploading: boolean;
  globalUploadError: string | null;
  globalUploadSuccess: boolean;
  onStartUpload: (file: File) => void;
}

const FileUpload: React.FC<FileUploadProps> = ({
  globalFile,
  globalUploading,
  globalUploadError,
  globalUploadSuccess,
  onStartUpload
}) => {
  const [file, setFile] = useState<File | null>(null);

  // Sync selected file with globalFile if started
  useEffect(() => {
    if (globalFile) {
      setFile(globalFile);
    }
  }, [globalFile]);

  // Clear selected file if upload succeeds and then resets
  useEffect(() => {
    if (!globalFile && !globalUploadSuccess) {
      setFile(null);
    }
  }, [globalFile, globalUploadSuccess]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = () => {
    if (file) {
      onStartUpload(file);
    }
  };

  return (
    <div className="w-full bg-white border-3 border-black rounded-xl p-6 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] upload-card">
      <div className="flex flex-col space-y-5">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 bg-retro-sand rounded-lg flex items-center justify-center border-2 border-black text-black shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]">
            {globalUploadSuccess ? <CheckCircle2 className="w-6 h-6 text-retro-green" /> : <Upload className="w-6 h-6" />}
          </div>
          <div>
            <h2 className="text-lg font-black text-black">Upload Resume</h2>
            <p className="text-black/60 text-xs font-bold">PDF, DOCX, or MD • Max 5MB</p>
          </div>
        </div>

        <label className="relative group block cursor-pointer">
          <div className={`
            flex flex-col items-center justify-center p-8 border-3 border-dashed rounded-lg transition-all duration-100 upload-dropzone
            ${file ? 'border-retro-green bg-retro-mint/20 bg-opacity-30' : 'border-black bg-white hover:bg-retro-cream'}
          `}>
            <FileText className={`w-10 h-10 mb-3 transition-colors ${file ? 'text-retro-green' : 'text-black/40 group-hover:text-black'}`} />
            <span className="text-sm font-extrabold text-black text-center px-4">
              {file ? file.name : 'Click to select or drag resume'}
            </span>
          </div>
          <input 
            type="file" 
            className="hidden" 
            accept=".pdf,.docx,.md,.markdown" 
            onChange={handleFileChange} 
            disabled={globalUploading}
          />
        </label>

        {globalUploadError && (
          <div className="flex items-center space-x-2 text-retro-red text-xs bg-retro-pink/20 border-2 border-black p-3 rounded-lg animate-in fade-in slide-in-from-top-2 font-bold">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{globalUploadError}</span>
          </div>
        )}

        <button
          onClick={handleUpload}
          disabled={!file || globalUploading || globalUploadSuccess}
          className={`
            w-full py-4 rounded-lg font-black text-[11px] uppercase tracking-[0.2em] transition-all flex items-center justify-center space-x-3 border-3 border-black sync-profile-btn
            ${!file || globalUploading || globalUploadSuccess 
              ? 'bg-gray-100 text-black/35 border-black/30 cursor-not-allowed shadow-none' 
              : globalUploadSuccess
                ? 'bg-retro-green text-white shadow-none translate-x-[2px] translate-y-[2px]'
                : 'bg-retro-yellow text-black shadow-[3px_3px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[0.5px] hover:translate-y-[0.5px] hover:shadow-[2.5px_2.5px_0px_0px_rgba(0,0,0,1)] active:translate-x-[2.5px] active:translate-y-[2.5px] active:shadow-none'
            }
          `}
        >
          {globalUploading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Analyzing Resume...</span>
            </>
          ) : globalUploadSuccess ? (
            <div className="flex items-center text-white">
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
