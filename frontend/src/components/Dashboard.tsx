import { useState, useEffect } from 'react';
import {
  Home,
  Upload,
  Users,
  Briefcase,
  BarChart3,
  FileText,
  Settings,
  Search,
  Bell,
  ChevronDown,
  Plus,
  Filter,
  TrendingUp,
  Clock,
  Eye,
  Star,
  Download,
  Menu,
  X,
  Target,
  ExternalLink,
  CheckCircle
} from 'lucide-react';
import type { AuthUser, JobOut, ResumeOut } from '../types';
import Profile from './Profile';
import Footer from './Footer';
import Logo from './Logo';
import { listResumes, parseResume } from '../api/resumes';
import { listJobs, closeJob, duplicateJob, getSimilarJobs } from '../api/jobs';

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

type NavItem = {
  id: string;
  label: string;
  icon: typeof Home;
  badge?: string | number;
};

type Candidate = {
  id: string | number;
  name: string;
  role: string;
  score: number;
  skills: string[];
  avatar?: string;
};

type Stat = {
  label: string;
  value: string | number;
  change?: string;
  trend?: 'up' | 'down' | 'neutral';
  icon: typeof Users;
  color: 'blue' | 'cyan' | 'gold' | 'green';
};

type Activity = {
  id: string | number;
  type: 'upload' | 'match' | 'report' | 'update' | 'general';
  message: string;
  time: string;
};

type QuickAction = {
  id: string;
  label: string;
  icon: typeof Upload;
  onClick: () => void;
};

type DashboardProps = {
  user: AuthUser & {
    avatar?: string;
  };
  stats?: Stat[];
  candidates?: Candidate[];
  activities?: Activity[];
  quickActions?: QuickAction[];
  onSignOut: () => void;
  onNavigate?: (route: string) => void;
  isLoading?: boolean;
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function Dashboard({
  user,
  stats = [],
  candidates = [],
  activities = [],
  quickActions = [],
  onSignOut,
  onNavigate,
  isLoading = false
}: DashboardProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [searchQuery, setSearchQuery] = useState('');
  const [isMobile, setIsMobile] = useState(false);

  // Detect mobile screen size
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      // Close sidebar on mobile by default
      if (mobile) {
        setSidebarOpen(false);
      } else {
        setSidebarOpen(true);
      }
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Navigation configuration
  const navSections = [
    {
      title: 'Main',
      items: [
        { id: 'overview', label: 'Overview', icon: Home },
        { id: 'upload', label: 'Upload Resumes', icon: Upload },
        { id: 'candidates', label: 'All Candidates', icon: Users, badge: candidates.length || undefined },
        { id: 'jobs', label: 'Job Postings', icon: Briefcase }
      ]
    },
    {
      title: 'Insights',
      items: [
        { id: 'analytics', label: 'Analytics', icon: BarChart3 },
        { id: 'reports', label: 'Reports', icon: FileText }
      ]
    },
    {
      title: 'System',
      items: [{ id: 'settings', label: 'Settings', icon: Settings }]
    }
  ];

  const handleNavigation = (route: string) => {
    setActiveTab(route);
    if (onNavigate) {
      onNavigate(route);
    }
  };

  const getScoreStatus = (score: number): string => {
    if (score >= 90) return 'excellent';
    if (score >= 75) return 'good';
    if (score >= 60) return 'average';
    return 'poor';
  };

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'upload':
        return Upload;
      case 'match':
        return Target;
      case 'report':
        return FileText;
      case 'update':
        return CheckCircle;
      default:
        return Bell;
    }
  };

  const getInitials = (name: string): string => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const firstName = (user.full_name || user.company_name || user.email || '').split(' ')[0] || '';

  const [resumes, setResumes] = useState<ResumeOut[]>([]);
  const [resumesLoading, setResumesLoading] = useState(false);
  const [parsingResumeId, setParsingResumeId] = useState<string | null>(null);
  const [resumeMessage, setResumeMessage] = useState<string | null>(null);

  const [companyJobs, setCompanyJobs] = useState<JobOut[]>([]);
  const [similarJobs, setSimilarJobs] = useState<JobOut[]>([]);
  const [jobMessage, setJobMessage] = useState<string | null>(null);
  const [jobActionLoading, setJobActionLoading] = useState<string | null>(null);

  const loadResumes = async () => {
    setResumesLoading(true);
    try {
      const { data } = await listResumes();
      setResumes(data.resumes);
    } catch (error) {
      console.warn('Failed to load resumes', error);
    } finally {
      setResumesLoading(false);
    }
  };

  const loadCompanyJobs = async () => {
    try {
      const { data } = await listJobs();
      setCompanyJobs(data);
    } catch (error) {
      console.warn('Failed to load company jobs', error);
    }
  };

  useEffect(() => {
    if (user.account_type === 'personal') {
      loadResumes();
    }
  }, [user.account_type]);

  useEffect(() => {
    if (user.account_type === 'company') {
      loadCompanyJobs();
    }
  }, [user.account_type]);

  const handleParseResume = async (resumeId: string) => {
    setParsingResumeId(resumeId);
    try {
      const { data } = await parseResume(resumeId);
      setResumeMessage(`Parsed ${data.filename}`);
      await loadResumes();
    } catch (error) {
      setResumeMessage('Unable to parse resume right now.');
    } finally {
      setParsingResumeId(null);
    }
  };

  const handleCloseJob = async (jobId: string) => {
    setJobActionLoading(jobId);
    try {
      const { data } = await closeJob(jobId);
      setJobMessage(data.message);
      await loadCompanyJobs();
    } catch (error) {
      setJobMessage('Failed to close the job.');
    } finally {
      setJobActionLoading(null);
    }
  };

  const handleDuplicateJob = async (jobId: string) => {
    setJobActionLoading(jobId);
    try {
      const { data } = await duplicateJob(jobId);
      setJobMessage(`Duplicated ${data.title}`);
      await loadCompanyJobs();
    } catch (error) {
      setJobMessage('Unable to duplicate job.');
    } finally {
      setJobActionLoading(null);
    }
  };

  const handleFetchSimilar = async (jobId: string) => {
    try {
      const { data } = await getSimilarJobs(jobId);
      setSimilarJobs(data);
      setJobMessage(data.length ? `Found ${data.length} similar jobs` : 'No similar postings yet');
    } catch (error) {
      setJobMessage('Could not fetch similar jobs right now.');
    }
  };

  return (
    <div className="dashboard">
      <style>{`
        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }

        :root {
          --white: #FFFFFF;
          --off-white: #FAFBFC;
          --blue: #0066FF;
          --blue-light: #E6F0FF;
          --blue-dark: #0052CC;
          --gold: #FFB800;
          --gold-light: #FFF5CC;
          --cyan: #00D4FF;
          --cyan-light: #E0F7FF;
          --green: #00C853;
          --green-light: #E0F7E9;
          --gray-50: #F8F9FA;
          --gray-100: #E9ECEF;
          --gray-200: #DEE2E6;
          --gray-300: #CED4DA;
          --gray-400: #ADB5BD;
          --gray-600: #6C757D;
          --gray-700: #495057;
          --gray-800: #343A40;
          --gray-900: #0A0E14;
          --red: #FF3B30;
          --orange: #FF9500;
        }

        body {
          font-family: 'Sora', -apple-system, BlinkMacSystemFont, sans-serif;
          background: var(--gray-50);
          color: var(--gray-900);
          overflow-x: hidden;
          scroll-behavior: smooth;
        }

        .dashboard {
          display: flex;
          flex-direction: column;
          height: 100vh;
          position: relative;
          overflow-x: hidden;
          overflow-y: auto;
          scroll-behavior: smooth;
        }

        /* ============================================================================
           SIDEBAR
           ============================================================================ */

        .sidebar {
          width: 280px;
          background: var(--white);
          border-right: 1px solid var(--gray-200);
          display: flex;
          flex-direction: column;
          position: fixed;
          height: 100vh;
          left: 0;
          top: 0;
          z-index: 100;
          transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .sidebar.closed {
          transform: translateX(-100%);
        }

        .sidebar-header {
          padding: 1.5rem;
          border-bottom: 1px solid var(--gray-200);
        }

        .sidebar-nav {
          flex: 1;
          padding: 1.5rem 1rem;
          overflow-y: auto;
        }

        .nav-section {
          margin-bottom: 2rem;
        }

        .nav-section:last-child {
          margin-bottom: 0;
        }

        .nav-section-title {
          font-size: 0.75rem;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          color: var(--gray-600);
          padding: 0 0.75rem;
          margin-bottom: 0.75rem;
        }

        .nav-item {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 0.75rem;
          margin-bottom: 0.25rem;
          border-radius: 12px;
          color: var(--gray-700);
          cursor: pointer;
          transition: all 0.2s ease;
          text-decoration: none;
          position: relative;
          font-weight: 500;
          border: none;
          background: transparent;
          width: 100%;
          text-align: left;
          font-family: 'Sora', sans-serif;
          font-size: 0.95rem;
        }

        .nav-item:hover {
          background: var(--gray-50);
          color: var(--gray-900);
        }

        .nav-item.active {
          background: var(--blue-light);
          color: var(--blue);
          font-weight: 600;
        }

        .nav-item.active::before {
          content: '';
          position: absolute;
          left: 0;
          top: 50%;
          transform: translateY(-50%);
          width: 3px;
          height: 60%;
          background: var(--blue);
          border-radius: 0 3px 3px 0;
        }

        .nav-badge {
          margin-left: auto;
          background: var(--blue);
          color: white;
          font-size: 0.75rem;
          font-weight: 600;
          padding: 0.25rem 0.5rem;
          border-radius: 6px;
          min-width: 24px;
          text-align: center;
        }

        .sidebar-footer {
          padding: 1.5rem;
          border-top: 1px solid var(--gray-200);
        }

        .user-profile {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 0.75rem;
          border-radius: 12px;
          cursor: pointer;
          transition: background 0.2s ease;
        }

        .user-profile:hover {
          background: var(--gray-50);
        }

        .user-avatar {
          width: 44px;
          height: 44px;
          border-radius: 12px;
          background: linear-gradient(135deg, var(--gold), var(--orange));
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: 600;
          font-size: 1rem;
          flex-shrink: 0;
        }

        .user-info {
          flex: 1;
          min-width: 0;
        }

        .user-name {
          font-weight: 600;
          font-size: 0.95rem;
          color: var(--gray-900);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .user-role {
          font-size: 0.8rem;
          color: var(--gray-600);
        }

        /* ============================================================================
           MAIN CONTENT
           ============================================================================ */

        .main-content {
          flex: 1;
          margin-left: 280px;
          transition: margin-left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          display: flex;
          flex-direction: column;
        }

        .main-content.full {
          margin-left: 0;
        }

        /* ============================================================================
           TOPBAR
           ============================================================================ */

        .topbar {
          background: var(--white);
          border-bottom: 1px solid var(--gray-200);
          padding: 1.25rem 2rem;
          display: flex;
          align-items: center;
          gap: 1.5rem;
          position: sticky;
          top: 0;
          z-index: 90;
        }

        .menu-toggle {
          background: none;
          border: none;
          cursor: pointer;
          color: var(--gray-700);
          padding: 0.5rem;
          border-radius: 8px;
          transition: all 0.2s ease;
        }

        .menu-toggle:hover {
          background: var(--gray-100);
          color: var(--gray-900);
        }

        .search-bar {
          flex: 1;
          max-width: 500px;
          position: relative;
        }

        .search-input {
          width: 100%;
          padding: 0.75rem 1rem 0.75rem 3rem;
          border: 1px solid var(--gray-300);
          border-radius: 12px;
          font-size: 0.95rem;
          font-family: 'Sora', sans-serif;
          transition: all 0.2s ease;
        }

        .search-input:focus {
          outline: none;
          border-color: var(--blue);
          box-shadow: 0 0 0 3px var(--blue-light);
        }

        .search-icon {
          position: absolute;
          left: 1rem;
          top: 50%;
          transform: translateY(-50%);
          color: var(--gray-600);
          pointer-events: none;
        }

        .topbar-actions {
          display: flex;
          align-items: center;
          gap: 1rem;
          margin-left: auto;
        }

        .icon-button {
          width: 40px;
          height: 40px;
          border-radius: 10px;
          background: var(--gray-50);
          border: none;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.2s ease;
          color: var(--gray-700);
          position: relative;
        }

        .icon-button:hover {
          background: var(--gray-200);
          color: var(--gray-900);
        }

        .notification-badge {
          position: absolute;
          top: 8px;
          right: 8px;
          width: 8px;
          height: 8px;
          background: var(--red);
          border-radius: 50%;
          border: 2px solid var(--white);
        }

        .primary-button {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.75rem 1.5rem;
          background: var(--blue);
          color: white;
          border: none;
          border-radius: 12px;
          font-weight: 600;
          font-size: 0.95rem;
          cursor: pointer;
          transition: all 0.2s ease;
          font-family: 'Sora', sans-serif;
        }

        .primary-button:hover {
          background: var(--blue-dark);
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(0, 102, 255, 0.3);
        }

        /* ============================================================================
           CONTENT AREA
           ============================================================================ */

        .content {
          padding: 2rem;
          flex: 1;
        }

        .page-header {
          margin-bottom: 2rem;
        }

        .page-title {
          font-family: 'Clash Display', sans-serif;
          font-size: 2rem;
          font-weight: 700;
          color: var(--gray-900);
          margin-bottom: 0.5rem;
        }

        .page-subtitle {
          color: var(--gray-600);
          font-size: 1rem;
        }

        /* ============================================================================
           STATS GRID
           ============================================================================ */

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 1.5rem;
          margin-bottom: 2rem;
        }

        .stat-card {
          background: var(--white);
          padding: 1.5rem;
          border-radius: 16px;
          border: 1px solid var(--gray-200);
          transition: all 0.3s ease;
        }

        .stat-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
        }

        .stat-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 1rem;
        }

        .stat-icon {
          width: 48px;
          height: 48px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .stat-icon.blue {
          background: var(--blue-light);
          color: var(--blue);
        }

        .stat-icon.cyan {
          background: var(--cyan-light);
          color: var(--cyan);
        }

        .stat-icon.gold {
          background: var(--gold-light);
          color: var(--gold);
        }

        .stat-icon.green {
          background: var(--green-light);
          color: var(--green);
        }

        .stat-change {
          display: flex;
          align-items: center;
          gap: 0.25rem;
          font-size: 0.85rem;
          font-weight: 600;
          color: var(--green);
        }

        .stat-change.down {
          color: var(--red);
        }

        .stat-value {
          font-family: 'Clash Display', sans-serif;
          font-size: 2rem;
          font-weight: 700;
          color: var(--gray-900);
          margin-bottom: 0.25rem;
        }

        .stat-label {
          color: var(--gray-600);
          font-size: 0.9rem;
        }

        /* ============================================================================
           CARDS GRID
           ============================================================================ */

        .cards-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
          gap: 1.5rem;
          margin-bottom: 2rem;
        }

        .card {
          background: var(--white);
          border: 1px solid var(--gray-200);
          border-radius: 16px;
          padding: 1.5rem;
        }

        .card.wide {
          grid-column: 1 / -1;
        }

        .card-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 1.5rem;
        }

        .card-title {
          font-family: 'Clash Display', sans-serif;
          font-size: 1.25rem;
          font-weight: 600;
          color: var(--gray-900);
        }

        .card-action {
          color: var(--blue);
          font-size: 0.9rem;
          font-weight: 600;
          cursor: pointer;
          text-decoration: none;
          display: flex;
          align-items: center;
          gap: 0.25rem;
          transition: all 0.2s ease;
        }

        .card-action:hover {
          text-decoration: underline;
        }

        /* ============================================================================
           CANDIDATES LIST
           ============================================================================ */

        .candidates-list {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .candidate-card {
          display: flex;
          align-items: center;
          gap: 1rem;
          padding: 1rem;
          background: var(--gray-50);
          border-radius: 12px;
          transition: all 0.2s ease;
          cursor: pointer;
        }

        .candidate-card:hover {
          background: var(--blue-light);
          transform: translateX(4px);
        }

        .candidate-avatar {
          width: 56px;
          height: 56px;
          border-radius: 12px;
          background: linear-gradient(135deg, var(--blue), var(--cyan));
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: 700;
          font-size: 1.1rem;
          flex-shrink: 0;
        }

        .candidate-info {
          flex: 1;
          min-width: 0;
        }

        .candidate-name {
          font-weight: 600;
          font-size: 1rem;
          color: var(--gray-900);
          margin-bottom: 0.25rem;
        }

        .candidate-role {
          font-size: 0.85rem;
          color: var(--gray-600);
          margin-bottom: 0.5rem;
        }

        .candidate-skills {
          display: flex;
          gap: 0.5rem;
          flex-wrap: wrap;
        }

        .skill-tag {
          padding: 0.25rem 0.75rem;
          background: var(--white);
          border-radius: 6px;
          font-size: 0.75rem;
          font-weight: 500;
          color: var(--gray-700);
        }

        .candidate-score {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.25rem;
          padding: 0.75rem 1rem;
          background: var(--white);
          border-radius: 10px;
          flex-shrink: 0;
        }

        .score-value {
          font-family: 'Clash Display', sans-serif;
          font-size: 1.5rem;
          font-weight: 700;
        }

        .score-value.excellent {
          color: var(--green);
        }

        .score-value.good {
          color: var(--blue);
        }

        .score-value.average {
          color: var(--orange);
        }

        .score-value.poor {
          color: var(--red);
        }

        .score-label {
          font-size: 0.75rem;
          color: var(--gray-600);
          font-weight: 500;
        }

        .candidate-actions {
          display: flex;
          gap: 0.5rem;
        }

        .action-button {
          width: 36px;
          height: 36px;
          border-radius: 8px;
          background: var(--white);
          border: 1px solid var(--gray-300);
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.2s ease;
          color: var(--gray-600);
        }

        .action-button:hover {
          background: var(--gray-50);
          color: var(--gray-900);
          border-color: var(--gray-400);
        }

        .action-button.primary {
          background: var(--blue);
          border-color: var(--blue);
          color: white;
        }

        .action-button.primary:hover {
          background: var(--blue-dark);
        }

        /* ============================================================================
           ACTIVITY FEED
           ============================================================================ */

        .activity-feed {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .activity-item {
          display: flex;
          gap: 1rem;
          padding: 1rem;
          background: var(--gray-50);
          border-radius: 12px;
          border-left: 3px solid var(--blue);
        }

        .activity-icon {
          width: 40px;
          height: 40px;
          border-radius: 10px;
          background: var(--blue-light);
          color: var(--blue);
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }

        .activity-content {
          flex: 1;
        }

        .activity-message {
          font-size: 0.9rem;
          color: var(--gray-900);
          margin-bottom: 0.25rem;
        }

        .activity-time {
          font-size: 0.8rem;
          color: var(--gray-600);
        }

        /* ============================================================================
           QUICK ACTIONS
           ============================================================================ */

        .quick-actions {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 1rem;
        }

        .quick-action {
          padding: 1.5rem;
          background: var(--white);
          border: 2px dashed var(--gray-300);
          border-radius: 12px;
          text-align: center;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .quick-action:hover {
          border-color: var(--blue);
          border-style: solid;
          background: var(--blue-light);
        }

        .quick-action-icon {
          width: 48px;
          height: 48px;
          margin: 0 auto 0.75rem;
          border-radius: 12px;
          background: var(--gray-50);
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--blue);
          transition: all 0.2s ease;
        }

        .quick-action:hover .quick-action-icon {
          background: var(--blue);
          color: white;
          transform: scale(1.1);
        }

        .quick-action-label {
          font-weight: 600;
          font-size: 0.9rem;
          color: var(--gray-900);
        }

        /* ============================================================================
           EMPTY STATES
           ============================================================================ */

        .empty-state {
          text-align: center;
          padding: 3rem 2rem;
        }

        .empty-state-icon {
          width: 64px;
          height: 64px;
          margin: 0 auto 1rem;
          border-radius: 16px;
          background: var(--gray-100);
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--gray-400);
        }

        .empty-state-title {
          font-family: 'Clash Display', sans-serif;
          font-size: 1.25rem;
          font-weight: 600;
          color: var(--gray-900);
          margin-bottom: 0.5rem;
        }

        .empty-state-description {
          color: var(--gray-600);
          font-size: 0.95rem;
        }

        /* ============================================================================
           LOADING STATES
           ============================================================================ */

        .loading-overlay {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(255, 255, 255, 0.8);
          backdrop-filter: blur(4px);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .loading-spinner {
          width: 48px;
          height: 48px;
          border: 4px solid var(--gray-200);
          border-top-color: var(--blue);
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }

        /* ============================================================================
           FOOTER
           ============================================================================ */

        .dashboard-footer {
          background: var(--white);
          border-top: 1px solid var(--gray-200);
          padding: 2rem;
          margin-top: auto;
        }

        .footer-content {
          max-width: 1200px;
          margin: 0 auto;
          display: flex;
          justify-content: space-between;
          align-items: center;
          flex-wrap: wrap;
          gap: 1rem;
        }

        .footer-logo {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .footer-logo .logo-text {
          font-family: 'Clash Display', sans-serif;
          font-size: 1.25rem;
          font-weight: 700;
          color: var(--gray-900);
        }

        .footer-links {
          display: flex;
          gap: 2rem;
        }

        .footer-link {
          color: var(--gray-600);
          text-decoration: none;
          font-size: 0.9rem;
          transition: color 0.2s ease;
        }

        .footer-link:hover {
          color: var(--blue);
        }

        .footer-copyright {
          color: var(--gray-500);
          font-size: 0.85rem;
        }

        @media (max-width: 768px) {
          .footer-content {
            flex-direction: column;
            text-align: center;
          }

          .footer-links {
            order: 3;
            width: 100%;
            justify-content: center;
          }
        }

        .panel-grid {
          display: grid;
          gap: 1.25rem;
          margin: 2rem 2rem 3rem;
          grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        }

        .panel {
          background: var(--white);
          border-radius: 20px;
          border: 1px solid var(--gray-200);
          padding: 1.5rem;
          box-shadow: 0 20px 45px rgba(15, 23, 42, 0.08);
        }

        .panel-heading {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 1rem;
          gap: 1rem;
        }

        .panel-heading h3 {
          margin-top: 0.25rem;
          margin-bottom: 0;
          font-size: 1.4rem;
        }

        .panel-tag {
          font-size: 0.75rem;
          font-weight: 700;
          color: var(--gray-500);
          letter-spacing: 0.08em;
          text-transform: uppercase;
        }

        .panel-meta {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .panel-meta-btn {
          border: none;
          background: transparent;
          color: var(--blue);
          font-weight: 600;
          cursor: pointer;
        }

        .panel-badge {
          padding: 0.35rem 0.75rem;
          border-radius: 999px;
          background: rgba(0, 212, 255, 0.12);
          color: #00b0d0;
          font-size: 0.8rem;
        }

        .panel-badge.success {
          background: rgba(34, 197, 94, 0.12);
          color: #22c55e;
        }

        .panel-body {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .panel-list {
          list-style: none;
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
          padding: 0;
          margin: 0;
        }

        .panel-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 1rem;
          padding: 0.85rem 1rem;
          border-radius: 14px;
          border: 1px solid var(--gray-200);
          background: var(--gray-50);
        }

        .muted-text {
          color: var(--gray-500);
          font-size: 0.85rem;
        }

        .panel-action {
          border: none;
          border-radius: 12px;
          padding: 0.6rem 1rem;
          font-weight: 600;
          cursor: pointer;
          background: var(--blue);
          color: var(--white);
        }

        .panel-action.ghost {
          background: transparent;
          border: 1px solid var(--gray-400);
          color: var(--gray-700);
        }

        .button-group {
          display: flex;
          flex-wrap: wrap;
          gap: 0.5rem;
          justify-content: flex-end;
        }

        .panel-empty {
          color: var(--gray-600);
        }

        .panel-subsection {
          border-top: 1px dashed var(--gray-200);
          padding-top: 0.85rem;
        }

        .panel-subsection-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.5rem;
        }

        .similar-list {
          list-style: none;
          padding: 0;
          margin: 0;
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .similar-list li {
          display: flex;
          justify-content: space-between;
          font-weight: 500;
          color: var(--gray-700);
        }

        .tag {
          padding: 0.15rem 0.6rem;
          border-radius: 999px;
          font-size: 0.75rem;
          background: var(--gray-100);
        }

        .sidebar-overlay {
          display: none;
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          z-index: 99;
          opacity: 0;
          transition: opacity 0.3s ease;
        }

        .sidebar-overlay.active {
          opacity: 1;
        }

        /* ============================================================================
           RESPONSIVE
           ============================================================================ */

        @media (max-width: 1024px) {
          .cards-grid {
            grid-template-columns: 1fr;
          }

          .card.wide {
            grid-column: 1;
          }
        }

        @media (max-width: 768px) {
          .sidebar {
            transform: translateX(-100%);
          }

          .sidebar.open {
            transform: translateX(0);
          }

          .sidebar-overlay {
            display: block;
          }

          .main-content {
            margin-left: 0;
          }

          .menu-toggle {
            display: block;
          }

          .topbar {
            padding: 1rem;
          }

          .search-bar {
            max-width: 100%;
          }

          .content {
            padding: 1rem;
          }

          .stats-grid {
            grid-template-columns: 1fr;
          }

          .candidate-card {
            flex-wrap: wrap;
          }

          .candidate-actions {
            width: 100%;
            justify-content: flex-end;
          }

          .quick-actions {
            grid-template-columns: repeat(2, 1fr);
          }
        }
      `}</style>

      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <Logo size="small" animated={true} />
        </div>

        <nav className="sidebar-nav">
          {navSections.map((section) => (
            <div key={section.title} className="nav-section">
              <div className="nav-section-title">{section.title}</div>
              {section.items.map((item) => (
                <button
                  key={item.id}
                  className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
                  onClick={() => handleNavigation(item.id)}
                  type="button"
                >
                  <item.icon size={20} />
                  <span>{item.label}</span>
                  {item.badge && <span className="nav-badge">{item.badge}</span>}
                </button>
              ))}
            </div>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="user-profile" onClick={() => handleNavigation('profile')}>
            <div className="user-avatar">
              {user.avatar || getInitials(user.full_name || user.company_name || user.email || '')}
            </div>
            <div className="user-info">
              <div className="user-name">{user.full_name || user.company_name || user.email}</div>
              <div className="user-role">
                {user.account_type === 'company' ? 'Company Partner' : 'Talent Seeker'}
              </div>
            </div>
            <ChevronDown size={16} />
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className={`main-content ${!sidebarOpen ? 'full' : ''}`}>
        {/* Topbar */}
        <div className="topbar">
          <button
            className="menu-toggle"
            onClick={() => setSidebarOpen((prev) => !prev)}
            type="button"
          >
            {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
          </button>

          <div className="search-bar">
            <Search className="search-icon" size={20} />
            <input
              type="text"
              className="search-input"
              placeholder="Search candidates, jobs, or reports..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <div className="topbar-actions">
            <button className="icon-button" type="button">
              <Filter size={20} />
            </button>
            <button className="icon-button" type="button">
              <Bell size={20} />
              <span className="notification-badge"></span>
            </button>
            <button className="icon-button" onClick={onSignOut} type="button" title="Sign Out">
              <ChevronDown size={20} />
            </button>
            <button className="primary-button" type="button">
              <Plus size={20} />
              <span>New Job</span>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="content">
          {activeTab === 'overview' && (
            <>
              <div className="page-header">
                <h1 className="page-title">Dashboard Overview</h1>
                <p className="page-subtitle">
                  Welcome back, {firstName}! Here's your recruitment overview.
                </p>
              </div>

              {/* Stats Grid */}
              {stats.length > 0 && (
                <div className="stats-grid">
                  {stats.map((stat, index) => (
                    <div key={index} className="stat-card">
                      <div className="stat-header">
                        <div className={`stat-icon ${stat.color}`}>
                          <stat.icon size={24} />
                        </div>
                        {stat.change && (
                          <div className={`stat-change ${stat.trend === 'down' ? 'down' : ''}`}>
                            <TrendingUp size={14} />
                            <span>{stat.change}</span>
                          </div>
                        )}
                      </div>
                      <div className="stat-value">{stat.value}</div>
                      <div className="stat-label">{stat.label}</div>
                    </div>
                  ))}
                </div>
              )}

              {/* Main Cards Grid */}
              <div className="cards-grid">
                {/* Candidates List */}
                <div className="card wide">
                  <div className="card-header">
                    <h2 className="card-title">Recent Candidates</h2>
                    {candidates.length > 0 && (
                      <a href="#" className="card-action">
                        View All
                        <ExternalLink size={14} />
                      </a>
                    )}
                  </div>
                  {candidates.length > 0 ? (
                    <div className="candidates-list">
                      {candidates.slice(0, 5).map((candidate) => (
                        <div key={candidate.id} className="candidate-card">
                          <div className="candidate-avatar">
                            {candidate.avatar || getInitials(candidate.name)}
                          </div>
                          <div className="candidate-info">
                            <div className="candidate-name">{candidate.name}</div>
                            <div className="candidate-role">{candidate.role}</div>
                            <div className="candidate-skills">
                              {candidate.skills.slice(0, 3).map((skill, idx) => (
                                <span key={idx} className="skill-tag">
                                  {skill}
                                </span>
                              ))}
                            </div>
                          </div>
                          <div className="candidate-score">
                            <div className={`score-value ${getScoreStatus(candidate.score)}`}>
                              {candidate.score}
                            </div>
                            <div className="score-label">Match</div>
                          </div>
                          <div className="candidate-actions">
                            <button className="action-button primary" type="button">
                              <Eye size={16} />
                            </button>
                            <button className="action-button" type="button">
                              <Star size={16} />
                            </button>
                            <button className="action-button" type="button">
                              <Download size={16} />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="empty-state">
                      <div className="empty-state-icon">
                        <Users size={32} />
                      </div>
                      <div className="empty-state-title">No candidates yet</div>
                      <div className="empty-state-description">
                        Upload resumes to start screening candidates
                      </div>
                    </div>
                  )}
                </div>

                {/* Recent Activity */}
                <div className="card">
                  <div className="card-header">
                    <h2 className="card-title">Recent Activity</h2>
                  </div>
                  {activities.length > 0 ? (
                    <div className="activity-feed">
                      {activities.slice(0, 4).map((activity) => {
                        const ActivityIcon = getActivityIcon(activity.type);
                        return (
                          <div key={activity.id} className="activity-item">
                            <div className="activity-icon">
                              <ActivityIcon size={18} />
                            </div>
                            <div className="activity-content">
                              <div className="activity-message">{activity.message}</div>
                              <div className="activity-time">{activity.time}</div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="empty-state">
                      <div className="empty-state-icon">
                        <Clock size={32} />
                      </div>
                      <div className="empty-state-title">No recent activity</div>
                      <div className="empty-state-description">
                        Activity will appear here as you use the platform
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Quick Actions */}
              {quickActions.length > 0 && (
                <div className="card">
                  <div className="card-header">
                    <h2 className="card-title">Quick Actions</h2>
                  </div>
                  <div className="quick-actions">
                    {quickActions.map((action) => (
                      <div
                        key={action.id}
                        className="quick-action"
                        onClick={action.onClick}
                      >
                        <div className="quick-action-icon">
                          <action.icon size={24} />
                        </div>
                        <div className="quick-action-label">{action.label}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {activeTab === 'profile' && (
            <Profile
              user={user}
              onNavigate={onNavigate}
              isLoading={isLoading}
            />
          )}

          {activeTab !== 'overview' && activeTab !== 'profile' && (
            <div className="page-header">
              <h1 className="page-title">
                {navSections
                  .flatMap((section) => section.items)
                  .find((item) => item.id === activeTab)?.label || 'Page'}
              </h1>
              <p className="page-subtitle">
                This page is under development. Check back soon!
              </p>
            </div>
          )}

          <section className="panel-grid">
            <div className="panel">
              <div className="panel-heading">
                <div>
                  <span className="panel-tag">Resume Manager</span>
                  <h3>AI parsing & sync</h3>
                </div>
                <div className="panel-meta">
                  {resumeMessage && <span className="panel-badge success">{resumeMessage}</span>}
                  {user.account_type === 'personal' && (
                    <button type="button" className="panel-meta-btn" onClick={loadResumes}>
                      Refresh
                    </button>
                  )}
                </div>
              </div>
              <div className="panel-body">
                {user.account_type === 'personal' ? (
                  resumesLoading ? (
                    <p className="panel-empty">Loading resumes…</p>
                  ) : resumes.length ? (
                    <ul className="panel-list">
                      {resumes.map((resume) => (
                        <li key={resume.id} className="panel-item">
                          <div>
                            <strong>{resume.filename}</strong>
                            <p className="muted-text">
                              {resume.version_name} · {resume.is_primary ? 'Primary' : 'Alternate'}
                            </p>
                            <small className="muted-text">
                              {new Date(resume.uploaded_at).toLocaleString()}
                            </small>
                          </div>
                          <button
                            type="button"
                            className="panel-action"
                            disabled={parsingResumeId === resume.id}
                            onClick={() => handleParseResume(resume.id)}
                          >
                            {parsingResumeId === resume.id ? 'Parsing…' : 'Re-run parser'}
                          </button>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="panel-empty">Upload a resume to unlock parsing insights.</p>
                  )
                ) : (
                  <p className="panel-empty">
                    Resume manager is available for personal accounts. Invite talent to upload their
                    documents.
                  </p>
                )}
              </div>
            </div>

            {user.account_type === 'company' && (
              <div className="panel">
                <div className="panel-heading">
                  <div>
                    <span className="panel-tag">Job Controls</span>
                    <h3>Close, duplicate, and compare roles</h3>
                  </div>
                  <div className="panel-meta">
                    {jobMessage && <span className="panel-badge">{jobMessage}</span>}
                    <button type="button" className="panel-meta-btn" onClick={loadCompanyJobs}>
                      Refresh
                    </button>
                  </div>
                </div>
                <div className="panel-body">
                  {companyJobs.length ? (
                    <ul className="panel-list">
                      {companyJobs.map((job) => (
                        <li key={job.id} className="panel-item">
                          <div>
                            <strong>{job.title}</strong>
                            <p className="muted-text">{job.location ?? 'Remote / Hybrid'}</p>
                            <small className="tag">{job.status}</small>
                          </div>
                          <div className="button-group">
                            <button
                              type="button"
                              className="panel-action"
                              disabled={jobActionLoading === job.id}
                              onClick={() => handleCloseJob(job.id)}
                            >
                              {jobActionLoading === job.id ? 'Working…' : 'Close'}
                            </button>
                            <button
                              type="button"
                              className="panel-action"
                              disabled={jobActionLoading === job.id}
                              onClick={() => handleDuplicateJob(job.id)}
                            >
                              {jobActionLoading === job.id ? 'Working…' : 'Duplicate'}
                            </button>
                            <button
                              type="button"
                              className="panel-action ghost"
                              onClick={() => handleFetchSimilar(job.id)}
                            >
                              Similar
                            </button>
                          </div>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="panel-empty">No active jobs available. Publish one to start screening.</p>
                  )}

                  {similarJobs.length > 0 && (
                    <div className="panel-subsection">
                      <div className="panel-subsection-header">
                        <h4>Similar jobs</h4>
                        <span className="muted-text">Suggested based on shared skills</span>
                      </div>
                      <ul className="similar-list">
                        {similarJobs.map((item) => (
                          <li key={item.id}>
                            <span>{item.title}</span>
                            <span className="tag muted">{item.status}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}
          </section>
        </div>

        {/* Loading Overlay */}
        {isLoading && (
          <div className="loading-overlay">
            <div className="loading-spinner" />
          </div>
        )}
      </main>

      {/* Footer */}
      <Footer />

      {/* Mobile Sidebar Overlay */}
      <div
        className={`sidebar-overlay ${sidebarOpen && isMobile ? 'active' : ''}`}
        onClick={() => isMobile && setSidebarOpen(false)}
      />
    </div>
  );
}
