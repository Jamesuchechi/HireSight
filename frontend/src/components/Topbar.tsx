import React from 'react';
import type { AuthUser } from '../types';

type Props = {
  user: AuthUser;
  onSignOut: () => void;
};

export default function Topbar({ user, onSignOut }: Props) {
  return (
    <header style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 20px', borderBottom: '1px solid #eee'}}>
      <div style={{fontWeight: 700}}>Hello, {user.full_name || user.company_name || user.email}</div>
      <div>
        <button onClick={onSignOut} style={{padding: '8px 12px', borderRadius: 6}}>Sign out</button>
      </div>
    </header>
  );
}
