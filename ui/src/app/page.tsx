'use client';

import React, { useState, useEffect } from 'react';
import { 
  Briefcase, 
  Search, 
  FileText, 
  CheckCircle2, 
  Play, 
  Users, 
  ExternalLink,
  Loader2,
  AlertCircle,
  X,
  HelpCircle,
  Check,
  AlertTriangle,
  ArrowRight
} from 'lucide-react';

interface JobCard {
  id: string;
  title: string;
  company: string;
  location: string;
  url: string;
  salary?: string;
  matchScore?: number;
  status: 'Found' | 'Scored' | 'Tailoring' | 'Pending Approval' | 'Applied' | 'Rejected';
  customQuestion?: string;
  customAnswer?: string;
}

export default function KanbanDashboard() {
  const [jobs, setJobs] = useState<JobCard[]>([
    {
      id: '1',
      title: 'Principal Software Engineer',
      company: 'TechCorp Inc.',
      location: 'Remote (US)',
      url: 'https://example.com/job/1',
      salary: '$180k - $220k',
      status: 'Found'
    },
    {
      id: '2',
      title: 'Staff Platform Architect',
      company: 'InnoVentures',
      location: 'San Francisco, CA',
      url: 'https://example.com/job/2',
      salary: '$210k - $250k',
      matchScore: 88,
      status: 'Scored'
    },
    {
      id: '3',
      title: 'Lead Cloud Infrastructure Engineer',
      company: 'DataFlow Systems',
      location: 'Remote',
      url: 'https://example.com/job/3',
      matchScore: 92,
      status: 'Tailoring'
    },
    {
      id: '4',
      title: 'Principal Developer Advocate',
      company: 'SaaSify',
      location: 'New York, NY',
      url: 'https://example.com/job/4',
      matchScore: 84,
      status: 'Pending Approval',
      customQuestion: 'What is your expected annual compensation, and what is your experience leading Kubernetes migrations?'
    },
    {
      id: '5',
      title: 'Staff Backend Engineer',
      company: 'Stripe (Mock)',
      location: 'Remote',
      url: 'https://example.com/job/5',
      matchScore: 95,
      status: 'Applied'
    },
    {
      id: '6',
      title: 'Solutions Architect',
      company: 'LegacyCorp',
      location: 'Hybrid',
      url: 'https://example.com/job/6',
      matchScore: 68,
      status: 'Rejected'
    }
  ]);

  const BACKEND_URL = 'http://localhost:8000';

  const [selectedJob, setSelectedJob] = useState<JobCard | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [answerInput, setAnswerInput] = useState('');
  const [triggeringCrew, setTriggeringCrew] = useState(false);
  const [searchingLinkedIn, setSearchingLinkedIn] = useState(false);
  const [searchResults, setSearchResults] = useState<JobCard[]>([]);
  const [searchUrl, setSearchUrl] = useState('');
  const [statusMessage, setStatusMessage] = useState('');

  const [uploading, setUploading] = useState(false);
  const [resumeStatus, setResumeStatus] = useState<any>(null);

  const fetchResumeStatus = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/resume-status`);
      if (res.ok) {
        const data = await res.json();
        setResumeStatus(data);
      }
    } catch (err) {
      console.error("Error fetching resume status:", err);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setStatusMessage("Only PDF files are accepted.");
      setTimeout(() => setStatusMessage(''), 4000);
      return;
    }

    const MAX_SIZE = 300 * 1024 * 1024;
    if (file.size > MAX_SIZE) {
      setStatusMessage("File size exceeds the 300MB limit.");
      setTimeout(() => setStatusMessage(''), 4000);
      return;
    }

    setUploading(true);
    setStatusMessage("Uploading and analyzing master resume PDF...");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/upload-resume`, {
        method: 'POST',
        body: formData
      });

      if (res.ok) {
        const data = await res.json();
        setStatusMessage("Resume uploaded, ingested into Vector DB, and analyzed successfully!");
        setResumeStatus(data);
      } else {
        const errData = await res.json();
        setStatusMessage(`Upload failed: ${errData.detail || "Unknown error"}`);
      }
    } catch (err) {
      console.error("Upload error:", err);
      setStatusMessage("Error connecting to backend API for upload.");
    } finally {
      setUploading(false);
      setTimeout(() => setStatusMessage(''), 4500);
    }
  };

  // Kanban Column definitions
  const columns: JobCard['status'][] = [
    'Found',
    'Scored',
    'Tailoring',
    'Pending Approval',
    'Applied',
    'Rejected'
  ];

  const refreshApplications = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/applications`);
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) {
          setJobs(data);
        }
      }
    } catch (err) {
      console.error("Error fetching applications:", err);
    }
  };

  useEffect(() => {
    refreshApplications();
    fetchResumeStatus();
  }, []);

  const getStatusColor = (status: JobCard['status']) => {
    switch(status) {
      case 'Found': return 'border-t-sky-500 bg-sky-950/10 text-sky-400';
      case 'Scored': return 'border-t-purple-500 bg-purple-950/10 text-purple-400';
      case 'Tailoring': return 'border-t-pink-500 bg-pink-950/10 text-pink-400';
      case 'Pending Approval': return 'border-t-amber-500 bg-amber-950/10 text-amber-400';
      case 'Applied': return 'border-t-emerald-500 bg-emerald-950/10 text-emerald-400';
      case 'Rejected': return 'border-t-rose-500 bg-rose-950/10 text-rose-400';
    }
  };

  const handleOpenApproval = (job: JobCard) => {
    setSelectedJob(job);
    setAnswerInput(job.customAnswer || '');
    setModalOpen(true);
  };

  const handleCloseApproval = () => {
    setModalOpen(false);
    setSelectedJob(null);
  };

  const handleSubmitAnswer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedJob) return;

    try {
      setStatusMessage(`Submitting custom answer for ${selectedJob.company}...`);
      const res = await fetch(`${BACKEND_URL}/api/v1/applications/${selectedJob.id}/submit-answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answer: answerInput })
      });
      if (res.ok) {
        setStatusMessage(`Answer submitted! Resuming application automation for ${selectedJob.company}...`);
        refreshApplications();
      } else {
        setStatusMessage('Failed to submit answer.');
      }
    } catch (err) {
      console.error(err);
      setStatusMessage('Error submitting answer to server.');
    }
    setTimeout(() => setStatusMessage(''), 4000);
    handleCloseApproval();
  };

  const triggerSearchCrew = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchUrl) return;

    setTriggeringCrew(true);
    setStatusMessage('Kicking off CrewAI Application Flow...');
    
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/trigger-apply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: searchUrl })
      });
      if (res.ok) {
        setStatusMessage('Application workflow initiated successfully!');
        setSearchUrl('');
        refreshApplications();
      } else {
        setStatusMessage('Failed to initiate application flow.');
      }
    } catch (err) {
      console.error(err);
      setStatusMessage('Error connecting to backend API.');
    } finally {
      setTriggeringCrew(false);
      setTimeout(() => setStatusMessage(''), 4000);
    }
  };

  const handleLinkedInSearch = async () => {
    setSearchingLinkedIn(true);
    setStatusMessage('Loading resume.pdf and querying LinkedIn for jobs...');
    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/search-linkedin-jobs`, {
        method: 'POST'
      });
      if (res.ok) {
        const data = await res.json();
        if (data.status === 'success' && Array.isArray(data.jobs)) {
          setSearchResults(data.jobs);
          setStatusMessage(`Found ${data.jobs.length} matching jobs on LinkedIn based on resume!`);
        } else {
          setStatusMessage('Failed to parse search results.');
        }
      } else {
        setStatusMessage('Failed to retrieve LinkedIn job matches.');
      }
    } catch (err) {
      console.error(err);
      setStatusMessage('Error contacting backend server.');
    } finally {
      setSearchingLinkedIn(false);
      setTimeout(() => setStatusMessage(''), 4000);
    }
  };

  const handleProceedAndApply = async (job: JobCard) => {
    setStatusMessage(`Triggering apply flow for ${job.title} at ${job.company}...`);
    try {
      // Optimistically add to Kanban board
      if (!jobs.some(j => j.url === job.url)) {
        setJobs(prev => [...prev, { ...job, status: 'Found' }]);
      }
      
      const res = await fetch(`${BACKEND_URL}/api/v1/trigger-apply`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: job.url })
      });
      if (res.ok) {
        setStatusMessage(`Successfully initiated apply flow!`);
        setSearchResults(prev => prev.filter(j => j.url !== job.url));
        refreshApplications();
      } else {
        setStatusMessage('Failed to trigger apply flow.');
      }
    } catch (err) {
      console.error(err);
      setStatusMessage('Error connecting to backend.');
    }
    setTimeout(() => setStatusMessage(''), 4000);
  };

  const updateJobStatus = (id: string, newStatus: JobCard['status']) => {
    setJobs(prevJobs => 
      prevJobs.map(job => 
        job.id === id ? { ...job, status: newStatus } : job
      )
    );
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Navbar */}
      <header className="border-b border-slate-900 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="bg-gradient-to-tr from-indigo-600 to-purple-600 p-2.5 rounded-xl text-white shadow-lg shadow-indigo-500/20">
            <Briefcase className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-indigo-400 bg-clip-text text-transparent">
              CrewAI Auto-Apply Core
            </h1>
            <p className="text-xs text-slate-400">Autonomous Job Headhunting & Submission Dashboard</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs bg-slate-800/80 px-3 py-1.5 rounded-full border border-slate-700/50">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
            <span className="text-slate-300 font-medium">Auto-Pilot Engaged</span>
          </div>
        </div>
      </header>

      {/* Control Panel Section Wrapper */}
      <div className="max-w-7xl w-full mx-auto px-6 pt-6 space-y-6">
        
        {/* Control Panel: 2-Column Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Master Resume Profile (5 cols) */}
        <div className="lg:col-span-5 bg-slate-900/40 border border-slate-850 rounded-2xl p-5 backdrop-blur-sm flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
                <FileText className="w-4 h-4 text-indigo-400" />
                Master Resume Profile
              </h3>
              {resumeStatus && resumeStatus.exists && (
                <span className="text-[10px] bg-indigo-500/10 text-indigo-400 font-bold px-2 py-0.5 rounded-full border border-indigo-500/25">
                  Vector DB Ingested
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 mb-4">
              Upload your master PDF resume. The system will parse it, chunk it, and index it into the vector database.
            </p>

            {/* Upload Area */}
            <div className="relative">
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileUpload}
                disabled={uploading}
                id="resume-upload"
                className="hidden"
              />
              <label
                htmlFor="resume-upload"
                className={`flex flex-col items-center justify-center border border-dashed rounded-xl p-4 cursor-pointer transition-all ${
                  uploading
                    ? 'border-indigo-500/50 bg-indigo-950/5'
                    : 'border-slate-800 hover:border-slate-700 bg-slate-950/40 hover:bg-slate-950/60'
                }`}
              >
                {uploading ? (
                  <div className="flex flex-col items-center py-2">
                    <Loader2 className="w-6 h-6 text-indigo-500 animate-spin mb-2" />
                    <span className="text-xs text-indigo-400 font-medium">Processing & Indexing Vector DB...</span>
                  </div>
                ) : (
                  <div className="flex flex-col items-center py-2 text-center">
                    <FileText className="w-6 h-6 text-slate-400 mb-2 group-hover:text-indigo-400" />
                    <span className="text-xs text-slate-300 font-semibold mb-1">Click to Upload Resume</span>
                    <span className="text-[10px] text-slate-500">PDF only, max 300MB</span>
                  </div>
                )}
              </label>
            </div>

            {/* Profile Overview (parsed details) */}
            {resumeStatus && resumeStatus.exists && resumeStatus.analysis && (
              <div className="mt-4 p-3 bg-slate-950/60 border border-slate-900 rounded-xl space-y-2.5 animate-in fade-in duration-300">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-slate-400 font-medium">Candidate Name:</span>
                  <span className="text-slate-200 font-semibold">{resumeStatus.analysis.name || "Ravishankar"}</span>
                </div>
                <div className="flex justify-between items-center text-xs">
                  <span className="text-slate-400 font-medium">Experience:</span>
                  <span className="text-slate-200 font-semibold">{resumeStatus.analysis.experience_years || "18+ years"}</span>
                </div>
                <div className="text-xs space-y-1">
                  <span className="text-slate-400 font-medium">Top Extracted Skills:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {resumeStatus.analysis.skills && resumeStatus.analysis.skills.map((skill: string) => (
                      <span key={skill} className="text-[9px] bg-slate-800/80 text-slate-300 px-2 py-0.5 rounded border border-slate-700/40">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
                {resumeStatus.analysis.summary && (
                  <div className="text-[10px] text-slate-400 italic bg-slate-900/20 p-2 rounded border border-slate-900/40 mt-1">
                    "{resumeStatus.analysis.summary}"
                  </div>
                )}
                <div className="text-[9px] text-slate-500 flex justify-between items-center border-t border-slate-900/60 pt-2">
                  <span>File: {resumeStatus.filename || "resume.pdf"} ({typeof resumeStatus.size_bytes === 'number' ? (resumeStatus.size_bytes / (1024 * 1024)).toFixed(2) : "0.00"} MB)</span>
                  {resumeStatus.last_modified && <span>Updated: {new Date(resumeStatus.last_modified).toLocaleDateString()}</span>}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Autonomous Job Headhunting (7 cols) */}
        <div className="lg:col-span-7 bg-slate-900/40 border border-slate-850 rounded-2xl p-5 backdrop-blur-sm flex flex-col justify-between space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-slate-300 mb-1">Trigger Autonomous Apply Flow</h3>
            <p className="text-xs text-slate-500 mb-4">Insert any Lever/Greenhouse posting URL to launch custom tailoring and apply agents.</p>
            
            <form onSubmit={triggerSearchCrew} className="flex items-center gap-2 mb-4">
              <input 
                type="url"
                required
                value={searchUrl}
                onChange={(e) => setSearchUrl(e.target.value)}
                placeholder="https://jobs.lever.co/company/role"
                className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 transition-all"
              />
              <button
                type="submit"
                disabled={triggeringCrew}
                className="bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm px-5 py-2.5 rounded-xl transition-all flex items-center gap-2 shrink-0 disabled:opacity-50 shadow-lg shadow-indigo-600/10"
              >
                {triggeringCrew ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-current" />}
                Launch
              </button>
            </form>
          </div>

          <div className="border-t border-slate-850 pt-4 flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="text-xs text-slate-400">
              Or automatically scan and search roles tailored to your master resume:
            </div>
            <button
              type="button"
              onClick={handleLinkedInSearch}
              disabled={searchingLinkedIn || !resumeStatus?.exists}
              title={!resumeStatus?.exists ? "Please upload a resume first" : ""}
              className="w-full sm:w-auto bg-sky-600 hover:bg-sky-500 text-white font-medium text-sm px-5 py-2.5 rounded-xl transition-all flex items-center justify-center gap-2 shrink-0 disabled:opacity-50 shadow-lg shadow-sky-600/10"
            >
              {searchingLinkedIn ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
              Search LinkedIn (Resume)
            </button>
          </div>
        </div>

      </div>

        {/* LinkedIn Search Results Panel */}
        {searchResults.length > 0 && (
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm animate-in fade-in slide-in-from-top-4 duration-300">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-sm font-semibold text-sky-400 flex items-center gap-2">
                <Search className="w-4 h-4" />
                LinkedIn Job Matches (Extracted from resume.pdf)
              </h4>
              <button 
                onClick={() => setSearchResults([])}
                className="text-slate-400 hover:text-slate-200 text-xs flex items-center gap-1 bg-slate-800/60 px-2.5 py-1 rounded-lg border border-slate-700/50"
              >
                Clear Results <X className="w-3.5 h-3.5" />
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {searchResults.map((job) => (
                <div key={job.url} className="bg-slate-950 border border-slate-850 p-4 rounded-xl flex flex-col justify-between hover:border-slate-700 transition-all">
                  <div>
                    <div className="flex justify-between items-start gap-1">
                      <h5 className="font-bold text-xs text-slate-200 line-clamp-1">{job.title}</h5>
                      <span className="text-[10px] bg-emerald-500/10 text-emerald-400 font-bold px-1.5 py-0.5 rounded">
                        {job.matchScore}% Fit
                      </span>
                    </div>
                    <p className="text-[10px] text-slate-400 mt-0.5">{job.company}</p>
                    <p className="text-[10px] text-slate-500 mt-2 line-clamp-2 italic">{job.salary || "Salary not listed"}</p>
                  </div>
                  <button
                    onClick={() => handleProceedAndApply(job)}
                    className="mt-3 w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-[10px] py-2 rounded-lg transition-all flex items-center justify-center gap-1"
                  >
                    <ArrowRight className="w-3 h-3" />
                    Proceed & Apply
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {statusMessage && (
          <div className="p-3.5 rounded-xl bg-indigo-950/20 border border-indigo-900/50 text-xs flex gap-2.5 text-indigo-300 items-center">
            <AlertCircle className="w-4 h-4 text-indigo-400 shrink-0" />
            <span>{statusMessage}</span>
          </div>
        )}
      </div>

      {/* Kanban Board Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 overflow-x-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 min-w-[1100px]">
          {columns.map((col) => {
            const filteredJobs = jobs.filter(j => j.status === col);
            return (
              <div key={col} className="bg-slate-900/20 border border-slate-900 rounded-2xl p-4 flex flex-col min-h-[500px]">
                {/* Column Title */}
                <div className={`border-t-2 ${getStatusColor(col)} pt-2 pb-4 flex items-center justify-between`}>
                  <span className="font-semibold text-sm tracking-wide">{col}</span>
                  <span className="text-xs bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full font-medium">
                    {filteredJobs.length}
                  </span>
                </div>

                {/* Column Cards */}
                <div className="space-y-3 flex-1 overflow-y-auto">
                  {filteredJobs.map((job) => (
                    <div 
                      key={job.id} 
                      className={`bg-slate-950 border border-slate-850 hover:border-slate-750 p-3.5 rounded-xl flex flex-col justify-between transition-all group relative ${
                        job.status === 'Pending Approval' ? 'ring-1 ring-amber-500/20 border-amber-900/30' : ''
                      }`}
                    >
                      <div>
                        <div className="flex justify-between items-start gap-1">
                          <h4 className="font-semibold text-xs text-slate-200 group-hover:text-indigo-400 transition-colors line-clamp-2">
                            {job.title}
                          </h4>
                          {job.matchScore && (
                            <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                              job.matchScore >= 85 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-purple-500/10 text-purple-400'
                            }`}>
                              {job.matchScore}%
                            </span>
                          )}
                        </div>
                        <p className="text-[10px] text-slate-400 mt-1">{job.company} • {job.location}</p>
                      </div>

                      {/* Display Salary if Found */}
                      {job.salary && (
                        <p className="text-[10px] text-slate-500 mt-2 font-medium bg-slate-900/40 w-fit px-1.5 py-0.5 rounded">
                          {job.salary}
                        </p>
                      )}

                      {/* Applied State Actions */}
                      {job.status === 'Applied' && (
                        <div className="mt-3 grid grid-cols-2 gap-2 border-t border-slate-900/60 pt-2.5">
                          <button
                            onClick={async () => {
                              setStatusMessage(`Generating referral outreach for ${job.company}...`);
                              try {
                                const res = await fetch(`${BACKEND_URL}/api/v1/applications/${job.id}/referrals`, { method: 'POST' });
                                if (res.ok) {
                                  const data = await res.json();
                                  setStatusMessage(`Referral draft generated: ${data.referral.referral_draft}`);
                                } else {
                                  setStatusMessage('Failed to generate referral draft.');
                                }
                              } catch (err) {
                                setStatusMessage('Error generating referral draft.');
                              }
                            }}
                            className="bg-indigo-950/40 hover:bg-indigo-900/40 text-[9px] text-indigo-400 border border-indigo-900/30 font-medium py-1.5 rounded flex items-center justify-center gap-1 transition-all"
                          >
                            <Users className="w-3 h-3" />
                            Get Referral
                          </button>
                          <button
                            onClick={async () => {
                              setStatusMessage(`Generating interview prep sheet for ${job.company}...`);
                              try {
                                const res = await fetch(`${BACKEND_URL}/api/v1/applications/${job.id}/schedule-interview`, {
                                  method: 'POST',
                                  headers: { 'Content-Type': 'application/json' },
                                  body: JSON.stringify({ scheduled_at: new Date().toISOString() })
                                });
                                if (res.ok) {
                                  const data = await res.json();
                                  setStatusMessage(`Interview Prep sheet generated! Access content at API endpoint.`);
                                } else {
                                  setStatusMessage('Failed to generate interview prep.');
                                }
                              } catch (err) {
                                setStatusMessage('Error generating interview prep.');
                              }
                            }}
                            className="bg-purple-950/40 hover:bg-purple-900/40 text-[9px] text-purple-400 border border-purple-900/30 font-medium py-1.5 rounded flex items-center justify-center gap-1 transition-all"
                          >
                            <FileText className="w-3 h-3" />
                            Interview Prep
                          </button>
                        </div>
                      )}

                      {/* Conditional Render Actions */}
                      {job.status === 'Pending Approval' ? (
                        <button
                          onClick={() => handleOpenApproval(job)}
                          className="mt-3 w-full bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold text-[10px] py-2 rounded-lg transition-all flex items-center justify-center gap-1.5 shadow-md shadow-amber-600/10"
                        >
                          <HelpCircle className="w-3.5 h-3.5" />
                          Resolve Custom Question
                        </button>
                      ) : (
                        <div className="flex items-center justify-between mt-4 pt-2 border-t border-slate-900/80">
                          {/* Manual Transition Helpers */}
                          <select 
                            value={job.status} 
                            onChange={(e) => updateJobStatus(job.id, e.target.value as JobCard['status'])}
                            className="bg-transparent text-[10px] text-slate-500 focus:outline-none border-none cursor-pointer hover:text-slate-300"
                          >
                            {columns.map(c => <option key={c} value={c}>{c}</option>)}
                          </select>
                          
                          <a 
                            href={job.url}
                            target="_blank" 
                            rel="noreferrer"
                            className="text-[10px] text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
                          >
                            Link <ExternalLink className="w-3 h-3" />
                          </a>
                        </div>
                      )}
                    </div>
                  ))}
                  {filteredJobs.length === 0 && (
                    <div className="border border-dashed border-slate-900/60 rounded-xl h-24 flex items-center justify-center text-slate-600 text-xs">
                      No roles
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </main>

      {/* Approval Modal */}
      {modalOpen && selectedJob && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            {/* Modal Header */}
            <div className="px-6 py-4 bg-slate-850/60 border-b border-slate-800 flex justify-between items-center">
              <div className="flex items-center gap-2 text-amber-400">
                <AlertTriangle className="w-5 h-5" />
                <h3 className="font-semibold text-sm">Greenhouse Custom Question</h3>
              </div>
              <button 
                onClick={handleCloseApproval}
                className="text-slate-400 hover:text-slate-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <form onSubmit={handleSubmitAnswer} className="p-6 space-y-4">
              <div>
                <h4 className="font-bold text-base text-slate-200">{selectedJob.title}</h4>
                <p className="text-xs text-slate-400 mt-1">{selectedJob.company} • {selectedJob.location}</p>
              </div>

              <div className="p-4 rounded-xl bg-slate-950 border border-slate-850 flex gap-3">
                <HelpCircle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
                <div>
                  <h5 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">Agent Blocked On:</h5>
                  <p className="text-sm text-slate-200 leading-relaxed font-medium">
                    {selectedJob.customQuestion}
                  </p>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                  Your Answer (Required)
                </label>
                <textarea
                  required
                  rows={4}
                  value={answerInput}
                  onChange={(e) => setAnswerInput(e.target.value)}
                  placeholder="Provide your experience, numbers, or standard text to continue the automation..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 transition-all resize-none"
                />
                <p className="text-[10px] text-slate-500 mt-1">
                  Once submitted, this answer is used by the application agent, and cached for future similar prompts.
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={handleCloseApproval}
                  className="bg-transparent hover:bg-slate-850 text-slate-300 font-medium text-xs px-4 py-2.5 rounded-xl transition-all"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs px-5 py-2.5 rounded-xl transition-all flex items-center gap-1.5 shadow-lg shadow-amber-500/10"
                >
                  <Check className="w-4 h-4" />
                  Resume & Apply
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-500 mt-12 bg-slate-950">
        <p>© 2026 CrewAI Auto-Apply Core Dashboard. Powered by Next.js, Tailwind CSS, & Playwright.</p>
      </footer>
    </div>
  );
}
