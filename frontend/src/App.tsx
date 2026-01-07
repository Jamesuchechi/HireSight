import { ChangeEvent, FormEvent, useEffect, useMemo, useState } from 'react';
import { AxiosError } from 'axios';
import { createJob, listJobs } from './api/jobs';
import { uploadResume } from './api/resumes';
import type { CandidatePreview, JobCreatePayload, JobOut } from './types';

const heroStats = [
  { label: 'Resumes processed', value: '12k+' },
  { label: 'Average match score', value: '84%' },
  { label: 'Human hours saved', value: '1,200+' }
];

const sampleCandidates: CandidatePreview[] = [
  {
    id: 'c1',
    name: 'Ayodele Akintola',
    score: 98,
    match: 'Excellent',
    skills: ['Python', 'LangChain', 'PostgreSQL'],
    status: 'Shortlisted'
  },
  {
    id: 'c2',
    name: 'Maya Patel',
    score: 91,
    match: 'Strong',
    skills: ['TypeScript', 'React', 'AWS'],
    status: 'Interview'
  },
  {
    id: 'c3',
    name: 'Tom Burke',
    score: 76,
    match: 'Good',
    skills: ['Go', 'Docker', 'Rest'],
    status: 'Hold'
  }
];

const insightCards = [
  {
    title: 'Skill gaps visualized',
    body: 'Top missing requirements are highlighted in red and gold badges.'
  },
  {
    title: 'Experience spread',
    body: 'Breathing gradients show range from junior to senior contributions.'
  },
  {
    title: 'Confidence & fairness',
    body: 'Bias signals tracked through percentile tracking per cohort.'
  }
];

const tertiaryTags = ['purple', 'cyan', 'black', 'gold', 'red'] as const;

const initialFormState: JobCreatePayload = {
  title: '',
  company: '',
  description: '',
  requirements: '',
  required_skills: [],
  required_experience_years: undefined,
  required_education: ''
};

function App() {
  const [formState, setFormState] = useState(initialFormState);
  const [skillInput, setSkillInput] = useState('');
  const [jobResult, setJobResult] = useState<JobOut | null>(null);
  const [jobError, setJobError] = useState<string | null>(null);
  const [isSavingJob, setIsSavingJob] = useState(false);
  const [resumeMessage, setResumeMessage] = useState('');
  const [jobs, setJobs] = useState<JobOut[]>([]);
  const [jobsError, setJobsError] = useState<string | null>(null);
  const [loadingJobs, setLoadingJobs] = useState(false);

  const requiredSkills = useMemo(
    () =>
      skillInput
        .split(',')
        .map((skill) => skill.trim())
        .filter(Boolean),
    [skillInput]
  );

  const handleJobChange = (field: keyof JobCreatePayload) => (
    event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const value =
      field === 'required_experience_years'
        ? event.target.value === ''
          ? undefined
          : Number(event.target.value)
        : event.target.value;
    setFormState((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setJobError(null);
    setIsSavingJob(true);
    try {
      const payload: JobCreatePayload = {
        ...formState,
        required_skills: requiredSkills
      };
      const { data } = await createJob(payload);
      setJobResult(data);
      setResumeMessage('Job saved. Upload resumes to match against it.');
    } catch (error) {
      console.error(error);
      setJobError('Unable to save job right now. Please try again.');
    } finally {
      setIsSavingJob(false);
    }
  };

  const handleResumeUpload = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    setResumeMessage('Uploading resume...');
    const formData = new FormData();
    formData.append('file', file);
    try {
      await uploadResume(formData);
      setResumeMessage(`Queued ${file.name} for parsing and scoring.`);
    } catch (error) {
      console.error(error);
      const detail =
        error instanceof AxiosError
          ? (error.response?.data as { detail?: string })?.detail
          : undefined;
      setResumeMessage(
        detail ? `Upload failed: ${detail}` : 'Upload failed. Please try another file.'
      );
    }
  };

  useEffect(() => {
    let isMounted = true;
    setLoadingJobs(true);
    listJobs()
      .then(({ data }) => {
        if (isMounted) {
          setJobs(data);
          setJobsError(null);
        }
      })
      .catch((error) => {
        console.error(error);
        if (isMounted) {
          setJobsError('Unable to sync jobs right now.');
        }
      })
      .finally(() => {
        if (isMounted) {
          setLoadingJobs(false);
        }
      });
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">HireSight • AI Recruiting Intelligence</p>
          <h1>
            Build modern, <span>glassmorphic</span> experiences while the backend
            handles the intelligence.
          </h1>
          <p className="lede">
            White primary surfaces, luminous blue accents, and tertiary gradients
            help recruiters focus on what matters—ranked candidates, evidence-backed
            decisions, and transparent scoring.
          </p>
          <div className="hero-stats">
            {heroStats.map((stat) => (
              <div key={stat.label}>
                <strong>{stat.value}</strong>
                <span>{stat.label}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="hero-card">
          <p className="hero-card-title">Live match velocity</p>
          <p className="hero-card-value">76% &rarr; 94% in 2 minutes</p>
          <p className="hero-card-foot">Optimized for fast decision reviews.</p>
        </div>
      </header>

      <main>
        <section className="saved-jobs-panel">
          <h3>Saved jobs</h3>
          <p className="hint">Real jobs retrieved from the API.</p>
          <div className="job-stack">
            {loadingJobs && <span className="hint">loading…</span>}
            {jobs.length === 0 && !loadingJobs && (
              <span className="hint">No jobs recorded yet.</span>
            )}
            {jobs.map((job) => (
              <div key={job.id} className="job-chip">
                <strong>{job.title}</strong>
                <span>{job.company || 'Private company'}</span>
                <div className="chip-row">
                  {(job.required_skills || []).slice(0, 3).map((skill) => (
                    <span key={skill} className="chip chip-gold">
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
          {jobsError && <p className="error">{jobsError}</p>}
        </section>

        <section className="glass-grid">
          <article className="glass-card form-panel">
            <div className="panel-header">
              <h2>Job definition</h2>
              <span>Validated through backend schemas</span>
            </div>
            <form onSubmit={handleSubmit}>
              <div className="field-group">
                <label htmlFor="title">Role title</label>
                <input
                  id="title"
                  value={formState.title}
                  onChange={handleJobChange('title')}
                  placeholder="Lead ML Engineer"
                  required
                />
              </div>

              <div className="field-group">
                <label htmlFor="company">Company</label>
                <input
                  id="company"
                  value={formState.company}
                  onChange={handleJobChange('company')}
                  placeholder="Visionary Labs"
                />
              </div>

              <div className="field-group">
                <label htmlFor="description">Description</label>
                <textarea
                  id="description"
                  value={formState.description}
                  onChange={handleJobChange('description')}
                  placeholder="Ask for Python, NLP, attention to accessibility."
                  required
                />
              </div>

              <div className="field-group">
                <label htmlFor="requirements">Requirements</label>
                <textarea
                  id="requirements"
                  value={formState.requirements}
                  onChange={handleJobChange('requirements')}
                  placeholder="Protocols, leadership, reporting structure..."
                />
              </div>

              <div className="field-group">
                <label htmlFor="skills">Required skills (comma separated)</label>
                <input
                  id="skills"
                  value={skillInput}
                  onChange={(event) => setSkillInput(event.target.value)}
                  placeholder="Python, SQL, Design Systems"
                />
                <p className="hint">
                  Normalized to lowercase before hitting the backend.
                </p>
              </div>

              <div className="flex-split">
                <div className="field-group">
                  <label htmlFor="experience">Experience (years)</label>
                  <input
                    id="experience"
                    type="number"
                    min={0}
                    max={70}
                    value={formState.required_experience_years || ''}
                    onChange={handleJobChange('required_experience_years')}
                  />
                </div>
                <div className="field-group">
                  <label htmlFor="education">Education</label>
                  <input
                    id="education"
                    value={formState.required_education}
                    onChange={handleJobChange('required_education')}
                    placeholder="Bachelor's degree or equivalent"
                  />
                </div>
              </div>

              <button type="submit" className="primary-button" disabled={isSavingJob}>
                {isSavingJob ? 'Saving job...' : 'Save job and generate embed'}
              </button>
              {jobError && <p className="error">{jobError}</p>}
              {jobResult && (
                <div className="success">
                  <p>Job saved with ID {jobResult.id}</p>
                  <p>Created {new Date(jobResult.created_date).toLocaleString()}</p>
                </div>
              )}
            </form>
          </article>

          <article className="glass-card upload-panel">
            <div className="panel-header">
              <h2>Resume intake</h2>
              <span>Upload PDFs or DOCX</span>
            </div>
            <label className="dropzone">
              <input type="file" accept=".pdf,.doc,.docx" onChange={handleResumeUpload} />
              <div>
                <p>Drop resume or click to browse</p>
                <p className="hint">Parsing keyed on pyresparser + PyMuPDF.</p>
              </div>
            </label>
            {resumeMessage && <p className="status">{resumeMessage}</p>}
            <div className="chip-row">
              {requiredSkills.slice(0, 5).map((skill) => (
                <span key={skill} className="chip">
                  {skill}
                </span>
              ))}
            </div>
          </article>
        </section>

        <section className="glass-grid candidate-section">
          <article className="glass-card leaderboard-card">
            <div className="panel-header">
              <h2>Ranked candidates</h2>
              <span>Powered by embeddings + semantic scoring</span>
            </div>
            <div className="candidate-list">
              {sampleCandidates.map((candidate, index) => (
                <div key={candidate.id} className="candidate-row">
                  <div className="candidate-index">{index + 1}</div>
                  <div>
                    <strong>{candidate.name}</strong>
                    <p>{candidate.match} • {candidate.status}</p>
                    <div className="skill-row">
                      {candidate.skills.map((skill, idx) => (
                        <span key={skill + idx} className={`chip chip-${tertiaryTags[idx % tertiaryTags.length]}`}>
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="score-pill">{candidate.score}</div>
                </div>
              ))}
            </div>
          </article>

          <article className="glass-card insights-card">
            <div className="panel-header">
              <h2>Insights</h2>
              <span>Glassmorphic dashboard cues</span>
            </div>
            <div className="insight-grid">
              {insightCards.map((card) => (
                <div key={card.title} className="insight">
                  <h3>{card.title}</h3>
                  <p>{card.body}</p>
                </div>
              ))}
            </div>
          </article>
        </section>
      </main>
    </div>
  );
}

export default App;
