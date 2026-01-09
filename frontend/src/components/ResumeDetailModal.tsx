import { useState } from 'react';
import { X, Copy, Briefcase, GraduationCap, Code } from 'lucide-react';
import type { ResumeOut } from '../types';

interface ResumeDetailModalProps {
    resume: ResumeOut | null;
    onClose: () => void;
    onAutoFill?: () => void;
    isLoading?: boolean;
}

export default function ResumeDetailModal({
    resume,
    onClose,
    onAutoFill,
    isLoading = false
}: ResumeDetailModalProps) {
    const [copied, setCopied] = useState<string | null>(null);

    if (!resume) return null;

    const parsedData = resume.parsed_data || {};
    const name = parsedData.name as string | undefined;
    const email = parsedData.email as string | undefined;
    const phone = parsedData.phone as string | undefined;
    const location = parsedData.location as string | undefined;
    const skills = (parsedData.skills as string[]) || [];
    const experience = (parsedData.experience as Array<{ company?: string; role?: string; start_date?: string; end_date?: string; description?: string }>) || [];
    const education = (parsedData.education as Array<{ institution?: string; degree?: string; graduation_date?: string; gpa?: string }>) || [];

    const copyToClipboard = (text: string, label: string) => {
        navigator.clipboard.writeText(text);
        setCopied(label);
        setTimeout(() => setCopied(null), 2000);
    };

    return (
        <>
            {/* Backdrop */}
            <div
                className="fixed inset-0 bg-black bg-opacity-50 z-50"
                onClick={onClose}
            />

            {/* Modal */}
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                    {/* Header */}
                    <div className="sticky top-0 bg-white border-b border-gray-200 p-6 flex items-center justify-between">
                        <div>
                            <h2 className="text-2xl font-bold text-gray-900">Resume Details</h2>
                            <p className="text-sm text-gray-600 mt-1">{resume.filename}</p>
                        </div>
                        <button
                            onClick={onClose}
                            className="p-2 hover:bg-gray-100 rounded-lg transition"
                            type="button"
                        >
                            <X size={24} className="text-gray-600" />
                        </button>
                    </div>

                    {/* Body */}
                    <div className="p-6 space-y-6">
                        {/* Contact Information */}
                        <div className="bg-gray-50 rounded-lg p-4">
                            <h3 className="font-semibold text-gray-900 mb-3">Contact Information</h3>
                            <div className="space-y-2">
                                {name && (
                                    <div className="flex items-center justify-between">
                                        <span className="text-gray-600">Name:</span>
                                        <span className="font-medium">{name}</span>
                                    </div>
                                )}
                                {email && (
                                    <div className="flex items-center justify-between">
                                        <span className="text-gray-600">Email:</span>
                                        <div className="flex items-center gap-2">
                                            <span className="font-medium">{email}</span>
                                            <button
                                                onClick={() => copyToClipboard(email, 'email')}
                                                className="p-1 hover:bg-gray-200 rounded transition"
                                                type="button"
                                                title="Copy email"
                                            >
                                                <Copy size={16} className="text-gray-500" />
                                            </button>
                                        </div>
                                    </div>
                                )}
                                {phone && (
                                    <div className="flex items-center justify-between">
                                        <span className="text-gray-600">Phone:</span>
                                        <span className="font-medium">{phone}</span>
                                    </div>
                                )}
                                {location && (
                                    <div className="flex items-center justify-between">
                                        <span className="text-gray-600">Location:</span>
                                        <span className="font-medium">{location}</span>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Skills */}
                        {skills.length > 0 && (
                            <div>
                                <div className="flex items-center gap-2 mb-3">
                                    <Code size={20} className="text-blue-600" />
                                    <h3 className="font-semibold text-gray-900">Skills</h3>
                                </div>
                                <div className="flex flex-wrap gap-2">
                                    {skills.map((skill, idx) => (
                                        <span
                                            key={idx}
                                            className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium"
                                        >
                                            {skill}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Experience */}
                        {experience.length > 0 && (
                            <div>
                                <div className="flex items-center gap-2 mb-3">
                                    <Briefcase size={20} className="text-green-600" />
                                    <h3 className="font-semibold text-gray-900">Experience</h3>
                                </div>
                                <div className="space-y-3">
                                    {experience.map((exp, idx) => (
                                        <div key={idx} className="pl-4 border-l-2 border-green-200">
                                            <div className="flex items-start justify-between">
                                                <div>
                                                    <p className="font-medium text-gray-900">{exp.role || 'Position'}</p>
                                                    <p className="text-sm text-gray-600">{exp.company || 'Company'}</p>
                                                </div>
                                                <p className="text-xs text-gray-500">
                                                    {exp.start_date} {exp.end_date && `- ${exp.end_date}`}
                                                </p>
                                            </div>
                                            {exp.description && (
                                                <p className="text-sm text-gray-600 mt-1">{exp.description}</p>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Education */}
                        {education.length > 0 && (
                            <div>
                                <div className="flex items-center gap-2 mb-3">
                                    <GraduationCap size={20} className="text-purple-600" />
                                    <h3 className="font-semibold text-gray-900">Education</h3>
                                </div>
                                <div className="space-y-3">
                                    {education.map((edu, idx) => (
                                        <div key={idx} className="pl-4 border-l-2 border-purple-200">
                                            <div className="flex items-start justify-between">
                                                <div>
                                                    <p className="font-medium text-gray-900">{edu.degree || 'Degree'}</p>
                                                    <p className="text-sm text-gray-600">{edu.institution || 'Institution'}</p>
                                                </div>
                                                <p className="text-xs text-gray-500">{edu.graduation_date}</p>
                                            </div>
                                            {edu.gpa && (
                                                <p className="text-sm text-gray-600 mt-1">GPA: {edu.gpa}</p>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Footer */}
                    {onAutoFill && (
                        <div className="sticky bottom-0 bg-white border-t border-gray-200 p-6 flex gap-3">
                            <button
                                onClick={onClose}
                                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50 transition"
                                type="button"
                            >
                                Close
                            </button>
                            <button
                                onClick={onAutoFill}
                                disabled={isLoading}
                                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                                type="button"
                            >
                                {isLoading ? 'Filling Profile...' : 'Auto-fill Profile'}
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </>
    );
}
