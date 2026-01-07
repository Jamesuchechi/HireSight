import { useState } from 'react';
import {
    User,
    Mail,
    Building,
    Edit,
    Save,
    X,
    Camera,
    Shield,
    Bell,
    Key
} from 'lucide-react';
import type { AuthUser } from '../types';

type ProfileProps = {
    user: AuthUser & {
        avatar?: string;
        company_name?: string;
        created_at?: string;
    };
    onUpdateProfile?: (data: Partial<AuthUser>) => void;
    onNavigate?: (route: string) => void;
    isLoading?: boolean;
};

export default function Profile({
    user,
    onUpdateProfile,
    onNavigate,
    isLoading = false
}: ProfileProps) {
    const [isEditing, setIsEditing] = useState(false);
    const [formData, setFormData] = useState({
        full_name: user.full_name,
        email: user.email,
        company_name: user.company_name || ''
    });

    const handleSave = () => {
        if (onUpdateProfile) {
            onUpdateProfile(formData);
        }
        setIsEditing(false);
    };

    const handleCancel = () => {
        setFormData({
            full_name: user.full_name,
            email: user.email,
            company_name: user.company_name || ''
        });
        setIsEditing(false);
    };

    return (
        <div className="profile-page">
            <style>{`
        .profile-page {
          padding: 2rem;
          max-width: 800px;
          margin: 0 auto;
        }

        .profile-header {
          display: flex;
          align-items: center;
          gap: 2rem;
          margin-bottom: 3rem;
          padding-bottom: 2rem;
          border-bottom: 1px solid #e5e7eb;
        }

        .profile-avatar {
          width: 120px;
          height: 120px;
          border-radius: 50%;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-size: 3rem;
          font-weight: bold;
          position: relative;
        }

        .avatar-edit {
          position: absolute;
          bottom: 0;
          right: 0;
          width: 32px;
          height: 32px;
          border-radius: 50%;
          background: #0066ff;
          border: 3px solid white;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          opacity: 0;
          transition: opacity 0.2s ease;
        }

        .profile-avatar:hover .avatar-edit {
          opacity: 1;
        }

        .profile-info h1 {
          font-size: 2.5rem;
          font-weight: 700;
          color: #111827;
          margin-bottom: 0.5rem;
        }

        .profile-role {
          font-size: 1.1rem;
          color: #6b7280;
          margin-bottom: 1rem;
        }

        .profile-stats {
          display: flex;
          gap: 2rem;
        }

        .stat-item {
          text-align: center;
        }

        .stat-value {
          font-size: 1.5rem;
          font-weight: 700;
          color: #111827;
        }

        .stat-label {
          font-size: 0.9rem;
          color: #6b7280;
        }

        .profile-content {
          display: grid;
          grid-template-columns: 1fr 300px;
          gap: 3rem;
        }

        .profile-form {
          background: white;
          border-radius: 12px;
          padding: 2rem;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .form-section {
          margin-bottom: 2rem;
        }

        .form-section:last-child {
          margin-bottom: 0;
        }

        .section-title {
          font-size: 1.25rem;
          font-weight: 600;
          color: #111827;
          margin-bottom: 1.5rem;
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .form-group {
          margin-bottom: 1.5rem;
        }

        .form-group:last-child {
          margin-bottom: 0;
        }

        .form-label {
          display: block;
          font-size: 0.9rem;
          font-weight: 500;
          color: #374151;
          margin-bottom: 0.5rem;
        }

        .form-input {
          width: 100%;
          padding: 0.75rem 1rem;
          border: 1px solid #d1d5db;
          border-radius: 8px;
          font-size: 1rem;
          transition: border-color 0.2s ease;
        }

        .form-input:focus {
          outline: none;
          border-color: #0066ff;
          box-shadow: 0 0 0 3px rgba(0, 102, 255, 0.1);
        }

        .form-input:disabled {
          background: #f9fafb;
          cursor: not-allowed;
        }

        .form-actions {
          display: flex;
          gap: 1rem;
          margin-top: 2rem;
        }

        .btn {
          padding: 0.75rem 1.5rem;
          border-radius: 8px;
          font-weight: 500;
          font-size: 0.95rem;
          cursor: pointer;
          transition: all 0.2s ease;
          border: none;
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .btn-primary {
          background: #0066ff;
          color: white;
        }

        .btn-primary:hover {
          background: #0052cc;
        }

        .btn-secondary {
          background: #f3f4f6;
          color: #374151;
        }

        .btn-secondary:hover {
          background: #e5e7eb;
        }

        .profile-sidebar {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }

        .sidebar-card {
          background: white;
          border-radius: 12px;
          padding: 1.5rem;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .sidebar-card h3 {
          font-size: 1.1rem;
          font-weight: 600;
          color: #111827;
          margin-bottom: 1rem;
        }

        .account-info {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .info-item {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 0.75rem;
          background: #f9fafb;
          border-radius: 8px;
        }

        .info-icon {
          width: 40px;
          height: 40px;
          border-radius: 8px;
          background: #e0f2fe;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #0066ff;
        }

        .info-content h4 {
          font-size: 0.9rem;
          font-weight: 500;
          color: #111827;
          margin-bottom: 0.25rem;
        }

        .info-content p {
          font-size: 0.8rem;
          color: #6b7280;
        }

        .quick-actions {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }

        .quick-action {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 0.75rem;
          border-radius: 8px;
          cursor: pointer;
          transition: background 0.2s ease;
        }

        .quick-action:hover {
          background: #f3f4f6;
        }

        .quick-action-icon {
          width: 36px;
          height: 36px;
          border-radius: 6px;
          background: #f3f4f6;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #6b7280;
        }

        .quick-action-text {
          flex: 1;
        }

        .quick-action-title {
          font-size: 0.9rem;
          font-weight: 500;
          color: #111827;
        }

        .quick-action-desc {
          font-size: 0.8rem;
          color: #6b7280;
        }

        @media (max-width: 768px) {
          .profile-page {
            padding: 1rem;
          }

          .profile-header {
            flex-direction: column;
            text-align: center;
            gap: 1.5rem;
          }

          .profile-content {
            grid-template-columns: 1fr;
            gap: 2rem;
          }

          .profile-stats {
            justify-content: center;
          }
        }
      `}</style>

            <div className="profile-header">
                <div className="profile-avatar">
                    {user.avatar || user.full_name.split(' ').map(n => n[0]).join('').toUpperCase()}
                    <div className="avatar-edit">
                        <Camera size={16} />
                    </div>
                </div>
                <div className="profile-info">
                    <h1>{user.full_name}</h1>
                    <p className="profile-role">
                        {user.role === 'company' ? 'Company Partner' : 'Talent Seeker'}
                    </p>
                    <div className="profile-stats">
                        <div className="stat-item">
                            <div className="stat-value">12</div>
                            <div className="stat-label">Jobs Posted</div>
                        </div>
                        <div className="stat-item">
                            <div className="stat-value">48</div>
                            <div className="stat-label">Candidates</div>
                        </div>
                        <div className="stat-item">
                            <div className="stat-value">95%</div>
                            <div className="stat-label">Match Rate</div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="profile-content">
                <div className="profile-form">
                    <div className="form-section">
                        <h2 className="section-title">
                            <User size={20} />
                            Personal Information
                        </h2>

                        <div className="form-group">
                            <label className="form-label">Full Name</label>
                            <input
                                type="text"
                                className="form-input"
                                value={formData.full_name}
                                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                                disabled={!isEditing}
                            />
                        </div>

                        <div className="form-group">
                            <label className="form-label">Email Address</label>
                            <input
                                type="email"
                                className="form-input"
                                value={formData.email}
                                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                disabled={!isEditing}
                            />
                        </div>

                        {user.role === 'company' && (
                            <div className="form-group">
                                <label className="form-label">Company Name</label>
                                <input
                                    type="text"
                                    className="form-input"
                                    value={formData.company_name}
                                    onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                                    disabled={!isEditing}
                                />
                            </div>
                        )}
                    </div>

                    <div className="form-actions">
                        {!isEditing ? (
                            <button
                                className="btn btn-primary"
                                onClick={() => setIsEditing(true)}
                            >
                                <Edit size={16} />
                                Edit Profile
                            </button>
                        ) : (
                            <>
                                <button
                                    className="btn btn-primary"
                                    onClick={handleSave}
                                    disabled={isLoading}
                                >
                                    <Save size={16} />
                                    Save Changes
                                </button>
                                <button
                                    className="btn btn-secondary"
                                    onClick={handleCancel}
                                >
                                    <X size={16} />
                                    Cancel
                                </button>
                            </>
                        )}
                    </div>
                </div>

                <div className="profile-sidebar">
                    <div className="sidebar-card">
                        <h3>Account Information</h3>
                        <div className="account-info">
                            <div className="info-item">
                                <div className="info-icon">
                                    <Mail size={20} />
                                </div>
                                <div className="info-content">
                                    <h4>Email Verified</h4>
                                    <p>Your email is verified</p>
                                </div>
                            </div>

                            <div className="info-item">
                                <div className="info-icon">
                                    <Shield size={20} />
                                </div>
                                <div className="info-content">
                                    <h4>Account Security</h4>
                                    <p>Password last changed 30 days ago</p>
                                </div>
                            </div>

                            <div className="info-item">
                                <div className="info-icon">
                                    <User size={20} />
                                </div>
                                <div className="info-content">
                                    <h4>Member Since</h4>
                                    <p>{user.created_at ? new Date(user.created_at).toLocaleDateString() : 'Recently'}</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="sidebar-card">
                        <h3>Quick Actions</h3>
                        <div className="quick-actions">
                            <div className="quick-action">
                                <div className="quick-action-icon">
                                    <Key size={18} />
                                </div>
                                <div className="quick-action-text">
                                    <div className="quick-action-title">Change Password</div>
                                    <div className="quick-action-desc">Update your account password</div>
                                </div>
                            </div>

                            <div className="quick-action">
                                <div className="quick-action-icon">
                                    <Bell size={18} />
                                </div>
                                <div className="quick-action-text">
                                    <div className="quick-action-title">Notification Settings</div>
                                    <div className="quick-action-desc">Manage your preferences</div>
                                </div>
                            </div>

                            <div className="quick-action">
                                <div className="quick-action-icon">
                                    <Shield size={18} />
                                </div>
                                <div className="quick-action-text">
                                    <div className="quick-action-title">Privacy Settings</div>
                                    <div className="quick-action-desc">Control your data sharing</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}