import React from 'react';
import type { AccountType } from '../types';

type Props = {
  account_type: AccountType;
  active: string;
  onNavigate: (route: string) => void;
};

export default function Sidebar({ account_type, active, onNavigate }: Props) {
  const personalNav = [
    { id: 'overview', label: 'Overview' },
    { id: 'resumes', label: 'Resume Manager' },
    { id: 'jobs', label: 'Job Discovery' },
    { id: 'applications', label: 'My Applications' },
    { id: 'profile', label: 'Profile' },
  ];

  const companyNav = [
    { id: 'overview', label: 'Overview' },
    { id: 'jobs', label: 'Job Manager' },
    { id: 'applicants', label: 'Applicants' },
    { id: 'screening', label: 'Screening Results' },
    { id: 'analytics', label: 'Analytics' },
    { id: 'profile', label: 'Profile' },
  ];

  const nav = account_type === 'company' ? companyNav : personalNav;

  return (
    <aside className={`sidebar ${active ? '' : ''}`} style={{width: 260, padding: 16}}>
      <div style={{marginBottom: 16, fontWeight: 700}}>HireSight</div>
      <nav>
        {nav.map((item) => (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            style={{
              display: 'block',
              width: '100%',
              textAlign: 'left',
              padding: '10px 12px',
              marginBottom: 8,
              borderRadius: 8,
              background: item.id === active ? '#E6F0FF' : 'transparent',
              border: 'none',
              cursor: 'pointer'
            }}
          >
            {item.label}
          </button>
        ))}
      </nav>
    </aside>
  );
}
