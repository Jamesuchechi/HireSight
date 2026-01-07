import React, { useState, useEffect } from 'react';
import {
  Upload,
  Zap,
  BarChart3,
  FileText,
  Sparkles,
  Target,
  ArrowRight,
  Star,
  Quote,
  X,
  CheckCircle,
  XCircle,
  Clock,
  TrendingUp,
  Users,
  Shield,
  Loader
} from 'lucide-react';
import type { SignInPayload, SignUpPayload, AuthRole } from '../types';

type AuthFormState = {
  fullName: string;
  email: string;
  password: string;
  role: AuthRole;
  companyName: string;
};

type Props = {
  onSignIn: (payload: SignInPayload) => Promise<void> | void;
  onSignUp: (payload: SignUpPayload) => Promise<void> | void;
  authError?: string | null;
  isLoading?: boolean;
};

const AUTH_FORM_DEFAULT: AuthFormState = {
  fullName: '',
  email: '',
  password: '',
  role: 'job_seeker',
  companyName: ''
};

export default function HireSightLanding({ onSignIn, onSignUp, authError, isLoading }: Props) {
  const [scrollY, setScrollY] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authMode, setAuthMode] = useState<'signin' | 'signup'>('signin');
  const [formData, setFormData] = useState<AuthFormState>({ ...AUTH_FORM_DEFAULT });

  useEffect(() => {
    setIsVisible(true);
    const handleScroll = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    if (showAuthModal) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
  }, [showAuthModal]);

  const handleChange =
    (field: keyof AuthFormState) => (e: React.ChangeEvent<HTMLInputElement>) => {
      setFormData((prev) => ({ ...prev, [field]: e.target.value }));
    };

  const handleRoleChange = (role: AuthRole) => {
    setFormData((prev) => ({
      ...prev,
      role,
      companyName: role === 'company' ? prev.companyName : ''
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (authMode === 'signin') {
      await onSignIn({
        email: formData.email.trim(),
        password: formData.password
      });
      return;
    }

    await onSignUp({
      full_name: formData.fullName.trim(),
      email: formData.email.trim(),
      password: formData.password,
      role: formData.role,
      company_name:
        formData.role === 'company' ? formData.companyName.trim() || undefined : undefined
    });
  };

  const resetFormState = () => setFormData({ ...AUTH_FORM_DEFAULT });

  const openAuthModal = (mode: 'signin' | 'signup') => {
    setAuthMode(mode);
    resetFormState();
    setShowAuthModal(true);
  };

  const features = [
    {
      icon: Upload,
      title: 'Smart Resume Parsing',
      description:
        'Upload multiple resumes in PDF or DOCX format. Our AI instantly extracts structured data including skills, experience, education, and contact information with 95% accuracy.',
      color: 'cyan',
      size: 'large'
    },
    {
      icon: Target,
      title: 'Semantic Matching',
      description:
        'Advanced NLP understands context and nuance, not just keywords. Get true compatibility scores based on deep semantic analysis.',
      color: 'blue',
      size: 'large'
    },
    {
      icon: BarChart3,
      title: 'Visual Insights',
      description:
        'Interactive dashboards reveal skill gaps, experience distribution, and candidate strengths at a glance.',
      color: 'gold',
      size: 'small'
    },
    {
      icon: FileText,
      title: 'Smart Reports',
      description:
        'Export comprehensive reports in Excel or PDF. Share insights with your team instantly.',
      color: 'cyan',
      size: 'small'
    },
    {
      icon: Shield,
      title: 'Bias-Free Screening',
      description:
        'AI-powered objective evaluation removes unconscious bias from the hiring process.',
      color: 'blue',
      size: 'small'
    },
    {
      icon: Clock,
      title: 'Lightning Fast',
      description:
        'Process 50+ resumes per minute. What took hours now takes minutes.',
      color: 'gold',
      size: 'small'
    }
  ];

  const testimonials = [
    {
      company: 'TechCorp',
      logo: 'TC',
      quote:
        'HireSight reduced our screening time from 5 hours to 15 minutes. The semantic matching is incredibly accurate—we found our best hire in the first batch.',
      author: 'Sarah Johnson',
      role: 'Head of Talent Acquisition',
      rating: 5,
      avatar: 'SJ'
    },
    {
      company: 'StartupXYZ',
      logo: 'SX',
      quote:
        "As a small team, we couldn't afford to waste time on unqualified candidates. HireSight's AI does the heavy lifting and we focus on conversations that matter.",
      author: 'Michael Chen',
      role: 'Co-Founder & CTO',
      rating: 5,
      avatar: 'MC'
    },
    {
      company: 'Enterprise Inc',
      logo: 'EI',
      quote:
        "We process 200+ applications per role. HireSight's bias-free scoring gives us confidence that we're not missing great talent due to unconscious bias.",
      author: 'Emily Rodriguez',
      role: 'VP of Human Resources',
      rating: 5,
      avatar: 'ER'
    }
  ];

  const stats = [
    { value: '500+', label: 'Companies', suffix: 'trust HireSight' },
    { value: '10K+', label: 'Resumes', suffix: 'processed daily' },
    { value: '95%', label: 'Time Saved', suffix: 'on screening' },
    { value: '4.9/5', label: 'Rating', suffix: 'from users' }
  ];

  const comparison = [
    {
      aspect: 'Time per Resume',
      manual: '5-10 minutes',
      hiresight: '5 seconds',
      manualIcon: XCircle,
      hiresightIcon: CheckCircle
    },
    {
      aspect: 'Bias Risk',
      manual: 'High (unconscious)',
      hiresight: 'Minimized (objective)',
      manualIcon: XCircle,
      hiresightIcon: CheckCircle
    },
    {
      aspect: 'Skill Matching',
      manual: 'Keyword-based',
      hiresight: 'Semantic AI',
      manualIcon: XCircle,
      hiresightIcon: CheckCircle
    },
    {
      aspect: 'Scalability',
      manual: 'Limited',
      hiresight: 'Unlimited',
      manualIcon: XCircle,
      hiresightIcon: CheckCircle
    }
  ];

  return (
    <div className="landing-container">
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
          --gray-50: #F8F9FA;
          --gray-100: #E9ECEF;
          --gray-200: #DEE2E6;
          --gray-300: #CED4DA;
          --gray-400: #ADB5BD;
          --gray-600: #6C757D;
          --gray-700: #495057;
          --gray-800: #343A40;
          --gray-900: #0A0E14;
          --green: #00C853;
          --green-light: #E0F7E9;
          --red: #FF3B30;
          --red-light: #FFE5E5;
        }

        body {
          font-family: 'Sora', -apple-system, BlinkMacSystemFont, sans-serif;
          background: var(--white);
          color: var(--gray-900);
          overflow-x: hidden;
          line-height: 1.6;
        }

        .landing-container {
          position: relative;
          min-height: 100vh;
        }

        /* Animated Background */
        .bg-gradient {
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          z-index: -1;
          opacity: 0.35;
          pointer-events: none;
        }

        .gradient-orb {
          position: absolute;
          border-radius: 50%;
          filter: blur(100px);
          animation: float 25s infinite ease-in-out;
        }

        .orb-1 {
          width: 600px;
          height: 600px;
          background: radial-gradient(circle, var(--cyan) 0%, transparent 70%);
          top: -15%;
          right: -10%;
          animation-delay: 0s;
        }

        .orb-2 {
          width: 500px;
          height: 500px;
          background: radial-gradient(circle, var(--blue) 0%, transparent 70%);
          bottom: -15%;
          left: -10%;
          animation-delay: -8s;
        }

        .orb-3 {
          width: 400px;
          height: 400px;
          background: radial-gradient(circle, var(--gold) 0%, transparent 70%);
          top: 40%;
          left: 50%;
          animation-delay: -16s;
        }

        @keyframes float {
          0%, 100% { transform: translate(0, 0) scale(1); }
          33% { transform: translate(40px, -40px) scale(1.1); }
          66% { transform: translate(-30px, 30px) scale(0.9); }
        }

        /* Header */
        .header {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          z-index: 100;
          padding: 1.5rem 2rem;
          display: flex;
          justify-content: space-between;
          align-items: center;
          background: rgba(255, 255, 255, 0.7);
          backdrop-filter: blur(20px);
          border-bottom: 1px solid transparent;
          transition: all 0.3s ease;
        }

        .header.scrolled {
          padding: 1rem 2rem;
          background: rgba(255, 255, 255, 0.9);
          border-bottom-color: var(--gray-200);
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
        }

        .logo {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          font-family: 'Clash Display', sans-serif;
          font-size: 1.75rem;
          font-weight: 700;
          color: var(--gray-900);
          text-decoration: none;
        }

        .logo-icon {
          width: 44px;
          height: 44px;
          background: linear-gradient(135deg, var(--blue), var(--cyan));
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: 700;
          font-size: 1.35rem;
        }

        .nav {
          display: flex;
          gap: 2.5rem;
          align-items: center;
        }

        .nav-link {
          color: var(--gray-600);
          text-decoration: none;
          font-weight: 500;
          font-size: 0.95rem;
          transition: color 0.3s ease;
          position: relative;
        }

        .nav-link:hover {
          color: var(--blue);
        }

        .nav-link::after {
          content: '';
          position: absolute;
          bottom: -4px;
          left: 0;
          width: 0;
          height: 2px;
          background: var(--blue);
          transition: width 0.3s ease;
        }

        .nav-link:hover::after {
          width: 100%;
        }

        .header-cta {
          padding: 0.75rem 1.75rem;
          background: var(--blue);
          color: white;
          border: none;
          border-radius: 12px;
          font-weight: 600;
          font-size: 0.95rem;
          cursor: pointer;
          transition: all 0.3s ease;
          box-shadow: 0 4px 16px rgba(0, 102, 255, 0.2);
          font-family: 'Sora', sans-serif;
        }

        .header-cta:hover {
          background: var(--blue-dark);
          transform: translateY(-2px);
          box-shadow: 0 6px 24px rgba(0, 102, 255, 0.3);
        }

        /* Hero Section */
        .hero {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 8rem 2rem 4rem;
          position: relative;
        }

        .hero-content {
          max-width: 1200px;
          text-align: center;
          opacity: 0;
          animation: fadeInUp 1s ease forwards;
          animation-delay: 0.2s;
        }

        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(40px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .badge {
          display: inline-flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.6rem 1.5rem;
          background: var(--blue-light);
          color: var(--blue);
          border-radius: 50px;
          font-size: 0.9rem;
          font-weight: 600;
          margin-bottom: 2.5rem;
          animation: pulse 3s infinite;
        }

        @keyframes pulse {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.05); }
        }

        .hero-title {
          font-family: 'Clash Display', sans-serif;
          font-size: clamp(3.5rem, 10vw, 7rem);
          font-weight: 700;
          line-height: 1.05;
          margin-bottom: 2rem;
          background: linear-gradient(135deg, var(--gray-900) 0%, var(--blue) 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          letter-spacing: -0.02em;
        }

        .hero-subtitle {
          font-size: clamp(1.15rem, 2.5vw, 1.5rem);
          color: var(--gray-600);
          max-width: 850px;
          margin: 0 auto 3.5rem;
          line-height: 1.7;
        }

        .hero-cta {
          display: flex;
          gap: 1.5rem;
          justify-content: center;
          flex-wrap: wrap;
        }

        .primary-btn {
          display: inline-flex;
          align-items: center;
          gap: 0.75rem;
          padding: 1.5rem 3rem;
          background: var(--blue);
          color: white;
          border: none;
          border-radius: 16px;
          font-weight: 600;
          font-size: 1.15rem;
          cursor: pointer;
          transition: all 0.3s ease;
          box-shadow: 0 8px 28px rgba(0, 102, 255, 0.3);
          font-family: 'Sora', sans-serif;
        }

        .primary-btn:hover {
          background: var(--blue-dark);
          transform: translateY(-3px);
          box-shadow: 0 12px 36px rgba(0, 102, 255, 0.4);
        }

        .secondary-btn {
          display: inline-flex;
          align-items: center;
          gap: 0.75rem;
          padding: 1.5rem 3rem;
          background: white;
          color: var(--gray-900);
          border: 2px solid var(--gray-300);
          border-radius: 16px;
          font-weight: 600;
          font-size: 1.15rem;
          cursor: pointer;
          transition: all 0.3s ease;
          font-family: 'Sora', sans-serif;
        }

        .secondary-btn:hover {
          border-color: var(--blue);
          color: var(--blue);
          transform: translateY(-3px);
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
        }

        /* Stats Section */
        .stats {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
          gap: 2rem;
          max-width: 1200px;
          margin: 6rem auto;
          padding: 0 2rem;
        }

        .stat-card {
          text-align: center;
          padding: 2.5rem 2rem;
          background: var(--white);
          border-radius: 24px;
          border: 2px solid var(--gray-100);
          transition: all 0.4s ease;
        }

        .stat-card:hover {
          transform: translateY(-10px);
          border-color: var(--blue);
          box-shadow: 0 20px 50px rgba(0, 102, 255, 0.15);
        }

        .stat-value {
          font-family: 'Clash Display', sans-serif;
          font-size: 4rem;
          font-weight: 700;
          background: linear-gradient(135deg, var(--blue), var(--cyan));
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          line-height: 1;
          margin-bottom: 0.75rem;
        }

        .stat-label {
          font-size: 1.1rem;
          font-weight: 600;
          color: var(--gray-900);
          margin-bottom: 0.35rem;
        }

        .stat-suffix {
          font-size: 0.9rem;
          color: var(--gray-600);
        }

        /* Features Section */
        .features-section {
          padding: 8rem 2rem;
          background: var(--gray-50);
          position: relative;
        }

        .section-header {
          text-align: center;
          max-width: 900px;
          margin: 0 auto 5rem;
        }

        .section-tag {
          display: inline-block;
          padding: 0.6rem 1.25rem;
          background: var(--gold-light);
          color: var(--gold);
          border-radius: 50px;
          font-size: 0.85rem;
          font-weight: 700;
          margin-bottom: 1.5rem;
          letter-spacing: 1px;
          text-transform: uppercase;
        }

        .section-title {
          font-family: 'Clash Display', sans-serif;
          font-size: clamp(2.5rem, 5vw, 4.5rem);
          font-weight: 700;
          margin-bottom: 1.5rem;
          color: var(--gray-900);
          line-height: 1.15;
        }

        .section-description {
          font-size: 1.25rem;
          color: var(--gray-600);
          line-height: 1.75;
        }

        .features-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
          gap: 2rem;
          max-width: 1400px;
          margin: 0 auto;
        }

        .feature-card {
          background: white;
          padding: 3rem;
          border-radius: 24px;
          transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
          border: 2px solid transparent;
          position: relative;
          overflow: hidden;
        }

        .feature-card.large {
          grid-column: span 1;
        }

        .feature-card::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 4px;
          background: linear-gradient(90deg, var(--blue), var(--cyan));
          transform: scaleX(0);
          transform-origin: left;
          transition: transform 0.5s ease;
        }

        .feature-card:hover {
          transform: translateY(-12px);
          box-shadow: 0 24px 60px rgba(0, 0, 0, 0.12);
          border-color: var(--gray-100);
        }

        .feature-card:hover::before {
          transform: scaleX(1);
        }

        .feature-icon {
          width: 72px;
          height: 72px;
          border-radius: 18px;
          display: flex;
          align-items: center;
          justify-content: center;
          margin-bottom: 1.75rem;
          transition: all 0.4s ease;
        }

        .feature-card:hover .feature-icon {
          transform: scale(1.1) rotate(5deg);
        }

        .icon-cyan { background: var(--cyan-light); color: var(--cyan); }
        .icon-blue { background: var(--blue-light); color: var(--blue); }
        .icon-gold { background: var(--gold-light); color: var(--gold); }

        .feature-title {
          font-family: 'Clash Display', sans-serif;
          font-size: 1.65rem;
          font-weight: 600;
          margin-bottom: 1rem;
          color: var(--gray-900);
        }

        .feature-description {
          color: var(--gray-600);
          line-height: 1.75;
          font-size: 1.05rem;
        }

        /* Comparison Section */
        .comparison-section {
          padding: 8rem 2rem;
          max-width: 1200px;
          margin: 0 auto;
        }

        .comparison-table {
          background: white;
          border-radius: 24px;
          overflow: hidden;
          box-shadow: 0 8px 40px rgba(0, 0, 0, 0.08);
          margin-top: 3rem;
        }

        .comparison-header {
          display: grid;
          grid-template-columns: 2fr 1fr 1fr;
          gap: 2rem;
          padding: 2rem;
          background: var(--gray-50);
          font-weight: 700;
          font-size: 1.1rem;
          border-bottom: 2px solid var(--gray-200);
        }

        .comparison-row {
          display: grid;
          grid-template-columns: 2fr 1fr 1fr;
          gap: 2rem;
          padding: 2rem;
          border-bottom: 1px solid var(--gray-100);
          align-items: center;
          transition: background 0.2s ease;
        }

        .comparison-row:hover {
          background: var(--gray-50);
        }

        .comparison-row:last-child {
          border-bottom: none;
        }

        .comparison-aspect {
          font-weight: 600;
          color: var(--gray-900);
          font-size: 1.05rem;
        }

        .comparison-value {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          font-size: 0.95rem;
        }

        .comparison-value.manual {
          color: var(--gray-600);
        }

        .comparison-value.hiresight {
          color: var(--blue);
          font-weight: 600;
          background: var(--blue-light);
          padding: 0.75rem 1rem;
          border-radius: 12px;
        }

        .comparison-icon {
          flex-shrink: 0;
        }

        .comparison-icon.manual {
          color: var(--red);
        }

        .comparison-icon.hiresight {
          color: var(--green);
        }

        /* Testimonials Section */
        .testimonials-section {
          padding: 8rem 2rem;
          background: var(--white);
        }

        .testimonials-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
          gap: 2.5rem;
          max-width: 1400px;
          margin: 0 auto;
        }

        .testimonial-card {
          background: var(--white);
          padding: 3rem;
          border-radius: 24px;
          border: 2px solid var(--gray-200);
          transition: all 0.4s ease;
          position: relative;
        }

        .testimonial-card:hover {
          transform: translateY(-8px);
          border-color: var(--blue);
          box-shadow: 0 20px 50px rgba(0, 0, 0, 0.1);
        }

        .quote-icon {
          position: absolute;
          top: 2rem;
          left: 2rem;
          color: var(--gold);
          opacity: 0.3;
        }

        .company-logo {
          width: 56px;
          height: 56px;
          background: linear-gradient(135deg, var(--blue), var(--cyan));
          border-radius: 14px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: 700;
          font-size: 1.1rem;
          margin-bottom: 1.5rem;
          font-family: 'Clash Display', sans-serif;
        }

        .testimonial-quote {
          font-size: 1.1rem;
          line-height: 1.75;
          color: var(--gray-700);
          margin-bottom: 1.5rem;
          font-style: italic;
        }

        .testimonial-rating {
          display: flex;
          gap: 0.25rem;
          margin-bottom: 1.5rem;
        }

        .star {
          color: var(--gold);
        }

        .testimonial-author {
          display: flex;
          align-items: center;
          gap: 1rem;
          padding-top: 1.5rem;
          border-top: 1px solid var(--gray-200);
        }

        .author-avatar {
          width: 48px;
          height: 48px;
          border-radius: 12px;
          background: linear-gradient(135deg, var(--gold), var(--orange));
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: 600;
          font-size: 1rem;
        }

        .author-info {
          flex: 1;
        }

        .author-name {
          font-weight: 600;
          color: var(--gray-900);
          margin-bottom: 0.25rem;
        }

        .author-role {
          font-size: 0.9rem;
          color: var(--gray-600);
        }

        /* CTA Section */
        .cta-section {
          padding: 8rem 2rem;
          background: linear-gradient(135deg, var(--blue) 0%, var(--cyan) 100%);
          position: relative;
          overflow: hidden;
        }

        .cta-section::before {
          content: '';
          position: absolute;
          top: -50%;
          right: -20%;
          width: 800px;
          height: 800px;
          background: radial-gradient(circle, rgba(255, 255, 255, 0.15) 0%, transparent 70%);
          border-radius: 50%;
          animation: float 20s infinite ease-in-out;
        }

        .cta-content {
          max-width: 900px;
          margin: 0 auto;
          text-align: center;
          position: relative;
          z-index: 1;
        }

        .cta-content h2 {
          font-family: 'Clash Display', sans-serif;
          font-size: clamp(2.5rem, 5vw, 4.5rem);
          font-weight: 700;
          color: white;
          margin-bottom: 1.5rem;
          line-height: 1.15;
        }

        .cta-content p {
          font-size: 1.35rem;
          color: rgba(255, 255, 255, 0.95);
          margin-bottom: 3rem;
          line-height: 1.7;
        }

        .cta-buttons {
          display: flex;
          gap: 1.5rem;
          justify-content: center;
          flex-wrap: wrap;
        }

        .cta-primary {
          padding: 1.5rem 3rem;
          background: white;
          color: var(--blue);
          border: none;
          border-radius: 16px;
          font-weight: 600;
          font-size: 1.15rem;
          cursor: pointer;
          transition: all 0.3s ease;
          box-shadow: 0 8px 28px rgba(0, 0, 0, 0.2);
          font-family: 'Sora', sans-serif;
        }

        .cta-primary:hover {
          transform: translateY(-3px);
          box-shadow: 0 12px 36px rgba(0, 0, 0, 0.3);
        }

        .cta-secondary {
          padding: 1.5rem 3rem;
          background: transparent;
          color: white;
          border: 2px solid white;
          border-radius: 16px;
          font-weight: 600;
          font-size: 1.15rem;
          cursor: pointer;
          transition: all 0.3s ease;
          font-family: 'Sora', sans-serif;
        }

        .cta-secondary:hover {
          background: white;
          color: var(--blue);
          transform: translateY(-3px);
        }

        /* Footer */
        .footer {
          padding: 4rem 2rem 2rem;
          background: var(--gray-900);
          color: white;
        }

        .footer-content {
          max-width: 1200px;
          margin: 0 auto;
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 3rem;
          margin-bottom: 3rem;
        }

        .footer-section h4 {
          font-family: 'Clash Display', sans-serif;
          font-size: 1.25rem;
          margin-bottom: 1.5rem;
        }

        .footer-copy {
          color: rgba(255, 255, 255, 0.7);
          line-height: 1.7;
          margin-top: 1rem;
        }

        .footer-links {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }

        .footer-link {
          color: rgba(255, 255, 255, 0.7);
          text-decoration: none;
          transition: color 0.3s ease;
        }

        .footer-link:hover {
          color: var(--cyan);
        }

        .footer-bottom {
          max-width: 1200px;
          margin: 0 auto;
          padding-top: 2rem;
          border-top: 1px solid rgba(255, 255, 255, 0.1);
          text-align: center;
          color: rgba(255, 255, 255, 0.5);
        }

        /* Auth Modal */
        .auth-modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(10, 14, 20, 0.7);
          backdrop-filter: blur(8px);
          z-index: 1000;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 2rem;
          animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        .auth-modal {
          background: white;
          border-radius: 24px;
          padding: 3rem;
          max-width: 480px;
          width: 100%;
          position: relative;
          box-shadow: 0 24px 80px rgba(0, 0, 0, 0.3);
          animation: modalSlideUp 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }

        @keyframes modalSlideUp {
          from {
            opacity: 0;
            transform: translateY(20px) scale(0.95);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }

        .modal-close {
          position: absolute;
          top: 1.5rem;
          right: 1.5rem;
          width: 40px;
          height: 40px;
          border-radius: 10px;
          background: var(--gray-100);
          border: none;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.2s ease;
          color: var(--gray-700);
        }

        .modal-close:hover {
          background: var(--gray-200);
          color: var(--gray-900);
        }

        .modal-logo {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          margin-bottom: 2rem;
          justify-content: center;
        }

        .modal-logo-icon {
          width: 48px;
          height: 48px;
          background: linear-gradient(135deg, var(--blue), var(--cyan));
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: 700;
          font-size: 1.5rem;
        }

        .modal-logo-text {
          font-family: 'Clash Display', sans-serif;
          font-size: 1.75rem;
          font-weight: 700;
          color: var(--gray-900);
        }

        .auth-toggle {
          display: flex;
          gap: 1rem;
          margin-bottom: 2rem;
          background: var(--gray-100);
          padding: 0.5rem;
          border-radius: 12px;
        }

        .auth-toggle-btn {
          flex: 1;
          padding: 0.75rem;
          background: transparent;
          border: none;
          border-radius: 8px;
          font-weight: 600;
          font-size: 0.95rem;
          cursor: pointer;
          transition: all 0.2s ease;
          color: var(--gray-600);
          font-family: 'Sora', sans-serif;
        }

        .auth-toggle-btn.active {
          background: white;
          color: var(--blue);
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        }

        .auth-form {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .auth-form input {
          padding: 1rem 1.25rem;
          border: 2px solid var(--gray-300);
          border-radius: 12px;
          font-size: 1rem;
          font-family: 'Sora', sans-serif;
          transition: all 0.2s ease;
        }

        .auth-form input:focus {
          outline: none;
          border-color: var(--blue);
          box-shadow: 0 0 0 3px var(--blue-light);
        }

        .role-selector {
          display: flex;
          gap: 0.5rem;
          margin: 0.25rem 0 0;
        }

        .role-pill {
          flex: 1;
          border-radius: 999px;
          border: 1px solid rgba(15, 23, 42, 0.2);
          background: transparent;
          padding: 0.7rem 0.75rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .role-pill.active {
          background: var(--blue);
          border-color: var(--blue);
          color: white;
        }

        .role-pill:hover {
          border-color: var(--blue);
        }

        .auth-form input.error {
          border-color: var(--red);
          animation: shake 0.4s ease;
        }

        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-10px); }
          75% { transform: translateX(10px); }
        }

        .auth-error {
          color: var(--red);
          font-size: 0.9rem;
          padding: 0.75rem;
          background: var(--red-light);
          border-radius: 8px;
          margin: 0;
        }

        .auth-submit {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.75rem;
          padding: 1.25rem;
          background: var(--blue);
          color: white;
          border: none;
          border-radius: 12px;
          font-weight: 600;
          font-size: 1.05rem;
          cursor: pointer;
          transition: all 0.3s ease;
          margin-top: 0.5rem;
          font-family: 'Sora', sans-serif;
        }

        .auth-submit:hover:not(:disabled) {
          background: var(--blue-dark);
          transform: translateY(-2px);
          box-shadow: 0 6px 20px rgba(0, 102, 255, 0.3);
        }

        .auth-submit:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        /* Responsive */
        @media (max-width: 768px) {
          .nav {
            display: none;
          }

          .hero {
            padding: 6rem 1.5rem 3rem;
          }

          .hero-cta {
            flex-direction: column;
          }

          .stats {
            grid-template-columns: 1fr;
          }

          .features-grid {
            grid-template-columns: 1fr;
          }

          .feature-card.large {
            grid-column: span 1;
          }

          .comparison-header,
          .comparison-row {
            grid-template-columns: 1fr;
            gap: 1rem;
          }

          .comparison-header {
            display: none;
          }

          .comparison-aspect {
            font-size: 1rem;
            margin-bottom: 0.5rem;
          }

          .testimonials-grid {
            grid-template-columns: 1fr;
          }

          .auth-modal {
            padding: 2rem;
          }
        }
      `}</style>

      {/* Animated Background */}
      <div className="bg-gradient">
        <div className="gradient-orb orb-1"></div>
        <div className="gradient-orb orb-2"></div>
        <div className="gradient-orb orb-3"></div>
      </div>

      {/* Header */}
      <header className={`header ${scrollY > 50 ? 'scrolled' : ''}`}>
        <a href="#" className="logo">
          <div className="logo-icon">H</div>
          <span>HireSight</span>
        </a>
        <nav className="nav">
          <a href="#features" className="nav-link">
            Features
          </a>
          <a href="#testimonials" className="nav-link">
            Testimonials
          </a>
          <a href="#comparison" className="nav-link">
            Why HireSight
          </a>
          <a href="https://github.com/yourusername/HireSight" className="nav-link">
            GitHub
          </a>
          <button
            type="button"
            className="header-cta"
            onClick={() => openAuthModal('signin')}
          >
            Get Started
          </button>
        </nav>
      </header>

      {/* Hero Section */}
      <section className="hero">
        <div className="hero-content">
          <div className="badge">
            <Sparkles size={18} />
            <span>Open Source AI Resume Screener</span>
          </div>
          <h1 className="hero-title">Stop Drowning in Resumes</h1>
          <p className="hero-subtitle">
            Transform your recruitment with AI-powered intelligence. Parse, analyze, and rank
            candidates in seconds—reducing bias, saving hours, and finding the perfect fit every
            time.
          </p>
          <div className="hero-cta">
            <button
              className="primary-btn"
              onClick={() => openAuthModal('signup')}
            >
              <span>Start Screening Free</span>
              <ArrowRight size={22} />
            </button>
            <button className="secondary-btn">
              <span>Watch Demo</span>
            </button>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="stats">
        {stats.map((stat, index) => (
          <div
            key={stat.label}
            className="stat-card"
            style={{
              animationDelay: `${index * 0.1}s`,
              opacity: isVisible ? 1 : 0,
              animation: isVisible ? 'fadeInUp 0.8s ease forwards' : 'none'
            }}
          >
            <div className="stat-value">{stat.value}</div>
            <div className="stat-label">{stat.label}</div>
            <div className="stat-suffix">{stat.suffix}</div>
          </div>
        ))}
      </section>

      {/* Features Section */}
      <section id="features" className="features-section">
        <div className="section-header">
          <span className="section-tag">POWERFUL FEATURES</span>
          <h2 className="section-title">Everything You Need to Hire Smarter</h2>
          <p className="section-description">
            Built with cutting-edge NLP and machine learning, HireSight automates the most
            time-consuming parts of recruitment while maintaining fairness and transparency.
          </p>
        </div>
        <div className="features-grid">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <div key={index} className={`feature-card ${feature.size}`}>
                <div className={`feature-icon icon-${feature.color}`}>
                  <Icon size={36} strokeWidth={2} />
                </div>
                <h3 className="feature-title">{feature.title}</h3>
                <p className="feature-description">{feature.description}</p>
              </div>
            );
          })}
        </div>
      </section>

      {/* Comparison Section */}
      <section id="comparison" className="comparison-section">
        <div className="section-header">
          <span className="section-tag">WHY HIRESIGHT</span>
          <h2 className="section-title">Manual Screening vs AI-Powered</h2>
          <p className="section-description">
            See how HireSight transforms the hiring process from tedious to intelligent.
          </p>
        </div>
        <div className="comparison-table">
          <div className="comparison-header">
            <div>Aspect</div>
            <div>Manual Screening</div>
            <div>HireSight</div>
          </div>
          {comparison.map((item, index) => {
            const ManualIcon = item.manualIcon;
            const HireSightIcon = item.hiresightIcon;
            return (
              <div key={index} className="comparison-row">
                <div className="comparison-aspect">{item.aspect}</div>
                <div className="comparison-value manual">
                  <ManualIcon size={20} className="comparison-icon manual" />
                  <span>{item.manual}</span>
                </div>
                <div className="comparison-value hiresight">
                  <HireSightIcon size={20} className="comparison-icon hiresight" />
                  <span>{item.hiresight}</span>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Testimonials Section */}
      <section id="testimonials" className="testimonials-section">
        <div className="section-header">
          <span className="section-tag">TESTIMONIALS</span>
          <h2 className="section-title">Loved by Recruiters Worldwide</h2>
          <p className="section-description">
            Join 500+ companies that have transformed their hiring process with HireSight.
          </p>
        </div>
        <div className="testimonials-grid">
          {testimonials.map((testimonial, index) => (
            <div key={index} className="testimonial-card">
              <Quote size={48} className="quote-icon" />
              <div className="company-logo">{testimonial.logo}</div>
              <p className="testimonial-quote">"{testimonial.quote}"</p>
              <div className="testimonial-rating">
                {[...Array(testimonial.rating)].map((_, i) => (
                  <Star key={i} size={18} fill="var(--gold)" className="star" />
                ))}
              </div>
              <div className="testimonial-author">
                <div className="author-avatar">{testimonial.avatar}</div>
                <div className="author-info">
                  <div className="author-name">{testimonial.author}</div>
                  <div className="author-role">{testimonial.role}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="cta-content">
          <h2>Ready to Transform Your Hiring?</h2>
          <p>
            Start screening smarter with HireSight's open-source AI platform. No credit card
            required, instant results, and total transparency.
          </p>
          <div className="cta-buttons">
            <button
              className="cta-primary"
              onClick={() => openAuthModal('signup')}
            >
              Get Started Free
            </button>
            <button className="cta-secondary">View on GitHub</button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-content">
          <div className="footer-section">
            <h4>HireSight</h4>
            <p className="footer-copy">
              AI-powered resume screening for modern recruiters. Open source, transparent, and
              bias-minimized.
            </p>
          </div>
          <div className="footer-section">
            <h4>Product</h4>
            <div className="footer-links">
              <a href="#features" className="footer-link">
                Features
              </a>
              <a href="#comparison" className="footer-link">
                Why HireSight
              </a>
              <a href="#testimonials" className="footer-link">
                Testimonials
              </a>
              <a href="#" className="footer-link">
                Documentation
              </a>
            </div>
          </div>
          <div className="footer-section">
            <h4>Resources</h4>
            <div className="footer-links">
              <a href="#" className="footer-link">
                GitHub
              </a>
              <a href="#" className="footer-link">
                API Docs
              </a>
              <a href="#" className="footer-link">
                Contributing
              </a>
              <a href="#" className="footer-link">
                License
              </a>
            </div>
          </div>
          <div className="footer-section">
            <h4>Community</h4>
            <div className="footer-links">
              <a href="#" className="footer-link">
                Discord
              </a>
              <a href="#" className="footer-link">
                Twitter
              </a>
              <a href="#" className="footer-link">
                Blog
              </a>
            </div>
          </div>
        </div>
        <div className="footer-bottom">
          <p>© 2026 HireSight. MIT License. Built with ❤️ for better hiring.</p>
        </div>
      </footer>

      {/* Auth Modal */}
      {showAuthModal && (
        <div className="auth-modal-overlay" onClick={() => setShowAuthModal(false)}>
          <div className="auth-modal" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setShowAuthModal(false)}>
              <X size={20} />
            </button>

            <div className="modal-logo">
              <div className="modal-logo-icon">H</div>
              <span className="modal-logo-text">HireSight</span>
            </div>

            <div className="auth-toggle">
              <button
                className={authMode === 'signin' ? 'auth-toggle-btn active' : 'auth-toggle-btn'}
                onClick={() => setAuthMode('signin')}
              >
                Sign In
              </button>
              <button
                className={authMode === 'signup' ? 'auth-toggle-btn active' : 'auth-toggle-btn'}
                onClick={() => setAuthMode('signup')}
              >
                Sign Up
              </button>
            </div>

            <form onSubmit={handleSubmit} className="auth-form">
              {authMode === 'signup' && (
                <input
                  type="text"
                  placeholder="Full name"
                  value={formData.fullName}
                  onChange={handleChange('fullName')}
                  required
                  maxLength={72}
                  className={authError ? 'error' : ''}
                />
              )}
              <input
                type="email"
                placeholder="Email address"
                value={formData.email}
                onChange={handleChange('email')}
                required
                className={authError ? 'error' : ''}
              />
              <input
                type="password"
                placeholder="Password"
                value={formData.password}
                onChange={handleChange('password')}
                required
                minLength={8}
                maxLength={72}
                className={authError ? 'error' : ''}
              />
              {authMode === 'signup' && (
                <div className="role-selector">
                  <button
                    type="button"
                    className={`role-pill ${formData.role === 'job_seeker' ? 'active' : ''}`}
                    onClick={() => handleRoleChange('job_seeker')}
                  >
                    Job Seeker
                  </button>
                  <button
                    type="button"
                    className={`role-pill ${formData.role === 'company' ? 'active' : ''}`}
                    onClick={() => handleRoleChange('company')}
                  >
                    Company
                  </button>
                </div>
              )}
              {authMode === 'signup' && formData.role === 'company' && (
                <input
                  type="text"
                  placeholder="Company / Business name"
                  value={formData.companyName}
                  onChange={handleChange('companyName')}
                  required
                  className={authError ? 'error' : ''}
                />
              )}
              {authError && <p className="auth-error">{authError}</p>}
              <button type="submit" className="auth-submit" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader size={20} className="spin" />
                    <span>Processing...</span>
                  </>
                ) : (
                  <>
                    {authMode === 'signin' ? <Zap size={20} /> : <ArrowRight size={20} />}
                    <span>{authMode === 'signin' ? 'Access Dashboard' : 'Create Account'}</span>
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
