import React, { useState } from 'react';
import type { AuthUser } from '../types';
import Sidebar from './Sidebar';
import Topbar from './Topbar';
import Dashboard from './Dashboard';
import ResumeManager from './ResumeManager';
import JobManager from './JobManager';
import MyApplications from './MyApplications';
import ScreeningResults from './ScreeningResults';

type Props = {
  user: AuthUser;
  onSignOut: () => void;
};

export default function DashboardShell({ user, onSignOut }: Props) {
  const [route, setRoute] = useState<string>('overview');

  const renderContent = () => {
    switch (route) {
      case 'overview':
        return <Dashboard user={user} onSignOut={onSignOut} />;
      case 'resumes':
        return <ResumeManager />;
      case 'jobs':
        return user.account_type === 'company' ? <JobManager /> : <div style={{padding:20}}><h2>Job Discovery</h2><p>Search and discover jobs. (Placeholder)</p></div>;
      case 'applications':
        return <MyApplications />;
      case 'applicants':
        return <div style={{padding:20}}><h2>Applicants</h2><p>Applicants listing (Placeholder)</p></div>;
      case 'screening':
        return <ScreeningResults />;
      case 'analytics':
        return <div style={{padding:20}}><h2>Analytics</h2><p>Analytics dashboard (Placeholder)</p></div>;
      case 'profile':
        return <div style={{padding:20}}><h2>Profile</h2><p>Profile management (Placeholder)</p></div>;
      default:
        return <Dashboard user={user} onSignOut={onSignOut} />;
    }
  };

  return (
    <div style={{display: 'flex', minHeight: '100vh'}}>
      <Sidebar account_type={user.account_type} active={route} onNavigate={setRoute} />
      <div style={{flex: 1, display: 'flex', flexDirection: 'column'}}>
        <Topbar user={user} onSignOut={onSignOut} />
        <main style={{flex: 1}}>
          {renderContent()}
        </main>
      </div>
    </div>
  );
}
