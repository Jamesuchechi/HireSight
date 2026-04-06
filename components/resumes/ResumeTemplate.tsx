"use client";

import { ParsedResume } from "@/lib/ai/resume-parser";

interface ResumeTemplateProps {
    data: ParsedResume;
    theme?: 'modern' | 'classic' | 'minimal' | 'executive' | 'creative' | 'technical';
}

export default function ResumeTemplate({ data, theme = 'modern' }: ResumeTemplateProps) {
    if (!data) return null;

    if (theme === 'classic') {
        return (
            <div className="bg-white p-12 max-w-[21cm] mx-auto min-h-[29.7cm] font-serif text-zinc-900 border-t-[12px] border-zinc-900">
                <header className="text-center border-b border-zinc-200 pb-8 mb-10">
                    <h1 className="text-5xl font-black uppercase tracking-tight text-zinc-900 mb-4">{data.fullName}</h1>
                    <div className="flex justify-center space-x-6 text-[10px] font-bold uppercase tracking-widest text-zinc-500">
                        <span>{data.contact?.email}</span>
                        <span>•</span>
                        <span>{data.contact?.phone}</span>
                        <span>•</span>
                        <span>{data.contact?.location}</span>
                    </div>
                </header>

                <div className="grid grid-cols-1 gap-12">
                     <section>
                        <h3 className="text-sm font-black uppercase tracking-widest border-b-2 border-zinc-900 pb-1 mb-6">Professional Profile</h3>
                        <p className="text-sm leading-[1.8] text-zinc-800 italic">{data.summary}</p>
                    </section>

                    <section>
                        <h3 className="text-sm font-black uppercase tracking-widest border-b-2 border-zinc-900 pb-1 mb-8">Professional Experience</h3>
                        <div className="space-y-10">
                            {Array.isArray(data.experience) ? (data.experience as any[]).map((exp: any, i: number) => (
                                <div key={i} className="relative">
                                    <div className="flex justify-between items-baseline mb-3">
                                        <h4 className="font-black text-base uppercase">{exp.company}</h4>
                                        <span className="text-xs font-bold text-zinc-500 italic">{exp.duration}</span>
                                    </div>
                                    <p className="font-bold text-xs uppercase tracking-wider text-zinc-600 mb-4">{exp.role}</p>
                                    {typeof exp.highlights === 'string' ? (
                                        <p className="text-sm text-zinc-700 leading-relaxed italic pr-4 whitespace-pre-wrap">{exp.highlights}</p>
                                    ) : (
                                        <ul className="space-y-3 list-disc pl-5">
                                            {exp.highlights?.map((h: any, j: number) => (
                                                <li key={j} className="text-sm text-zinc-700 leading-relaxed">{h}</li>
                                            ))}
                                        </ul>
                                    )}
                                </div>
                            )) : (
                                <p className="text-sm text-zinc-700 leading-relaxed whitespace-pre-wrap">{data.experience as any}</p>
                            )}
                        </div>
                    </section>

                    <section className="grid grid-cols-2 gap-12">
                        <div>
                             <h3 className="text-base font-black uppercase tracking-widest border-b-2 border-zinc-900 pb-1 mb-6">Education</h3>
                             {data.education?.map((edu, i) => (
                                <div key={i} className="mb-4">
                                    <h4 className="font-black text-sm">{edu.institution}</h4>
                                    <p className="text-xs italic text-zinc-600">{edu.degree} — {edu.year}</p>
                                </div>
                            ))}
                        </div>
                        <div>
                            <h3 className="text-base font-black uppercase tracking-widest border-b-2 border-zinc-900 pb-1 mb-6">Expertise</h3>
                             <div className="flex flex-wrap gap-2">
                                {Array.isArray((data.skills as any)?.hard) ? (data.skills as any).hard.map((skill: any, i: number) => (
                                    <span key={i} className="px-3 py-1 bg-zinc-100 rounded text-[9px] font-bold uppercase text-zinc-700">
                                        {skill}
                                    </span>
                                )) : (
                                    <p className="text-[10px] text-zinc-700 leading-relaxed whitespace-pre-wrap italic">{data.skills as any}</p>
                                )}
                            </div>
                        </div>
                    </section>
                </div>
            </div>
        );
    }

    if (theme === 'minimal') {
        return (
            <div className="bg-white p-16 max-w-[21cm] mx-auto min-h-[29.7cm] font-sans text-zinc-600">
                 <h1 className="text-3xl font-light tracking-tight text-zinc-900 mb-2">{data.fullName}</h1>
                 <p className="text-xs font-medium tracking-tight text-zinc-400 mb-12">
                    {data.contact?.email} / {data.contact?.phone} / {data.contact?.location}
                 </p>

                 <div className="space-y-16">
                     <section className="grid grid-cols-3 gap-8">
                        <div className="text-[10px] font-black uppercase tracking-widest">About</div>
                        <div className="col-span-2 text-sm leading-relaxed">{data.summary}</div>
                     </section>

                     <section className="grid grid-cols-3 gap-8">
                        <div className="text-[10px] font-black uppercase tracking-widest">Experience</div>
                         <div className="col-span-2 space-y-12">
                             {Array.isArray(data.experience) ? data.experience.map((exp: any, i: number) => (
                                <div key={i}>
                                    <div className="flex justify-between items-baseline mb-4">
                                        <h4 className="font-bold text-zinc-900 text-sm">{exp.role}</h4>
                                        <span className="text-[10px] text-zinc-400">{exp.duration}</span>
                                    </div>
                                    <p className="text-[10px] uppercase tracking-widest font-black text-zinc-300 mb-4">{exp.company}</p>
                                    {typeof exp.highlights === 'string' ? (
                                        <p className="text-sm text-zinc-500 leading-relaxed whitespace-pre-wrap">{exp.highlights}</p>
                                    ) : (
                                        <ul className="space-y-4">
                                            {exp.highlights?.map((h: any, j: number) => (
                                                <li key={j} className="text-sm leading-relaxed text-zinc-500">• {h}</li>
                                            ))}
                                        </ul>
                                    )}
                                </div>
                            )) : (
                                <p className="text-sm text-zinc-500 leading-relaxed whitespace-pre-wrap">{data.experience as any}</p>
                            )}
                        </div>
                     </section>

                     <section className="grid grid-cols-3 gap-8">
                        <div className="text-[10px] font-black uppercase tracking-widest">Technical</div>
                        <div className="col-span-2 flex flex-wrap gap-4">
                            {Array.isArray((data.skills as any)?.hard) ? (data.skills as any).hard.map((s: any, i: number) => (
                                <span key={i} className="text-xs">{s}</span>
                            )) : (
                                <p className="text-xs text-zinc-400 leading-relaxed whitespace-pre-wrap">{data.skills as any}</p>
                            )}
                        </div>
                     </section>
                 </div>
            </div>
        );
    }

    if (theme === 'executive') {
        return (
            <div className="bg-white p-12 max-w-[21cm] mx-auto min-h-[29.7cm] font-serif text-zinc-900 border-[16px] border-double border-zinc-900 m-4 shadow-2xl">
                <header className="text-center mb-12 border-b-4 border-zinc-900 pb-8">
                    <h1 className="text-5xl font-black uppercase tracking-tighter text-zinc-900 mb-4">{data.fullName}</h1>
                    <div className="flex justify-center flex-wrap gap-x-8 gap-y-2 text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500">
                        <span>{data.contact?.email}</span>
                        <span>{data.contact?.phone}</span>
                        <span>{data.contact?.location}</span>
                    </div>
                </header>

                <div className="grid grid-cols-1 gap-12">
                     <section>
                        <h3 className="text-sm font-black uppercase tracking-[0.3em] border-b-2 border-zinc-900 pb-2 mb-6 flex justify-between items-center">
                            <span>Strategic Synopsis</span>
                            <div className="h-1 w-20 bg-zinc-900"></div>
                        </h3>
                        <p className="text-sm leading-[1.8] text-zinc-800 font-medium">{data.summary}</p>
                    </section>

                    <section>
                        <h3 className="text-sm font-black uppercase tracking-[0.3em] border-b-2 border-zinc-900 pb-2 mb-8 flex justify-between items-center">
                            <span>Executive Experience</span>
                            <div className="h-1 w-20 bg-zinc-900"></div>
                        </h3>
                        <div className="space-y-12">
                            {Array.isArray(data.experience) ? data.experience.map((exp: any, i: number) => (
                                <div key={i}>
                                    <div className="flex justify-between items-baseline mb-4">
                                        <h4 className="font-black text-lg uppercase tracking-tight">{exp.company}</h4>
                                        <span className="text-[10px] font-black text-zinc-400 uppercase tracking-widest">{exp.duration}</span>
                                    </div>
                                    <p className="font-bold text-xs uppercase tracking-[0.2em] text-zinc-500 mb-6 italic">{exp.role}</p>
                                    <ul className="space-y-4">
                                        {Array.isArray(exp.highlights) ? exp.highlights.map((h: any, j: number) => (
                                            <li key={j} className="text-sm text-zinc-700 leading-relaxed pl-6 relative">
                                                <span className="absolute left-0 top-2 w-1.5 h-1.5 bg-zinc-900"></span>
                                                {h}
                                            </li>
                                        )) : (
                                            <p className="text-sm text-zinc-700 leading-relaxed italic">{exp.highlights}</p>
                                        )}
                                    </ul>
                                </div>
                            )) : null}
                        </div>
                    </section>

                    <section className="grid grid-cols-2 gap-16 border-t-2 border-zinc-100 pt-12">
                        <div>
                            <h3 className="text-sm font-black uppercase tracking-[0.3em] mb-8">Board/Education</h3>
                            {data.education?.map((edu, i) => (
                                <div key={i} className="mb-6">
                                    <h4 className="font-black text-sm uppercase">{edu.institution}</h4>
                                    <p className="text-[10px] italic text-zinc-500 uppercase font-bold tracking-widest mt-1">{edu.degree} • {edu.year}</p>
                                </div>
                            ))}
                        </div>
                        <div>
                            <h3 className="text-sm font-black uppercase tracking-[0.3em] mb-8">Core Competency</h3>
                            <div className="grid grid-cols-2 gap-x-4 gap-y-3">
                                {data.skills?.hard?.map((skill: any, i: number) => (
                                    <div key={i} className="text-[10px] font-black uppercase tracking-widest text-zinc-600 border-l-2 border-zinc-900 pl-3">
                                        {skill}
                                    </div>
                                ))}
                            </div>
                        </div>
                    </section>
                </div>
            </div>
        );
    }

    if (theme === 'creative') {
        return (
            <div className="bg-zinc-900 p-8 max-w-[21cm] mx-auto min-h-[29.7cm] font-sans text-white overflow-hidden shadow-2xl m-4 flex">
                {/* Visual Sidebar */}
                <aside className="w-72 bg-zinc-800 p-10 flex flex-col shrink-0">
                    <div className="mb-20">
                        <h1 className="text-4xl font-black uppercase tracking-tighter leading-none mb-6">
                            {data.fullName.split(' ').map((n, i) => (
                                <span key={i} className={`${i === 1 ? 'text-primary block' : ''}`}>{n} </span>
                            ))}
                        </h1>
                        <div className="space-y-4 text-[9px] font-black uppercase tracking-widest text-zinc-400">
                             <div className="p-3 bg-zinc-900 rounded-xl border border-zinc-700">{data.contact?.email}</div>
                             <div className="p-3 bg-zinc-900 rounded-xl border border-zinc-700">{data.contact?.phone}</div>
                             <div className="p-3 bg-zinc-900 rounded-xl border border-zinc-700">{data.contact?.location}</div>
                        </div>
                    </div>

                    <div className="mt-auto">
                         <h3 className="text-[10px] font-black uppercase tracking-[0.3em] text-primary mb-8">Expertise DNA</h3>
                         <div className="flex flex-wrap gap-2">
                             {data.skills?.hard?.map((s, i) => (
                                 <span key={i} className="px-3 py-1.5 bg-zinc-700 rounded-full text-[8px] font-bold uppercase tracking-tighter">
                                     {s}
                                 </span>
                             ))}
                         </div>
                    </div>
                </aside>

                {/* Main Content */}
                <main className="flex-grow bg-white text-zinc-900 p-12 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full -translate-y-1/2 translate-x-1/2"></div>
                    
                    <section className="mb-16 relative">
                        <div className="w-12 h-1 bg-primary mb-6"></div>
                        <h3 className="text-[10px] font-black uppercase tracking-[0.4em] text-zinc-400 mb-6">Manifesto</h3>
                        <p className="text-base font-bold text-zinc-800 leading-relaxed italic">{data.summary}</p>
                    </section>

                    <section className="mb-16">
                        <h3 className="text-[10px] font-black uppercase tracking-[0.4em] text-zinc-400 mb-10">Journey</h3>
                        <div className="space-y-12">
                            {data.experience?.map((exp, i) => (
                                <div key={i} className="flex gap-8">
                                    <div className="w-24 shrink-0 text-[10px] font-black uppercase tracking-widest text-zinc-300 pt-1">
                                        {exp.duration}
                                    </div>
                                    <div className="flex-grow">
                                        <h4 className="text-lg font-black uppercase tracking-tight text-primary mb-1">{exp.role}</h4>
                                        <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400 mb-6">{exp.company}</p>
                                        <ul className="space-y-3">
                                            {exp.highlights?.map((h: any, j: number) => (
                                                <li key={j} className="text-xs font-medium text-zinc-600 border-l-2 border-zinc-100 pl-4">
                                                    {h}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </section>

                    <section>
                         <h3 className="text-[10px] font-black uppercase tracking-[0.4em] text-zinc-400 mb-8">Foundations</h3>
                         <div className="grid grid-cols-1 gap-6">
                             {data.education?.map((edu, i) => (
                                 <div key={i} className="flex justify-between items-center border-b border-zinc-50 pb-4">
                                     <div>
                                        <h4 className="font-black text-xs uppercase text-zinc-900">{edu.institution}</h4>
                                        <p className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">{edu.degree}</p>
                                     </div>
                                     <span className="text-[10px] font-black text-zinc-300">{edu.year}</span>
                                 </div>
                             ))}
                         </div>
                    </section>
                </main>
            </div>
        );
    }

    if (theme === 'technical') {
        return (
            <div className="bg-[#0a0a0a] p-10 max-w-[21cm] mx-auto min-h-[29.7cm] font-mono text-emerald-500 shadow-2xl m-4 border-t-8 border-emerald-500">
                <header className="mb-16 border-b border-emerald-500/20 pb-12">
                    <h1 className="text-4xl font-black uppercase tracking-tighter mb-4 text-white">&gt; {data.fullName}</h1>
                    <div className="flex flex-wrap gap-8 text-[10px]/relaxed opacity-70">
                        <span>[EMAIL]: {data.contact?.email}</span>
                        <span>[PHONE]: {data.contact?.phone}</span>
                        <span>[LOC]: {data.contact?.location}</span>
                    </div>
                </header>

                <div className="space-y-16">
                    <section>
                        <h3 className="text-[10px] font-black uppercase tracking-[0.3em] text-emerald-500/50 mb-6">/* ROOT_SUMMARY */</h3>
                        <p className="text-sm text-zinc-300 leading-relaxed border-l-2 border-emerald-500/10 pl-6 py-2">
                            {data.summary}
                        </p>
                    </section>

                    <section>
                        <h3 className="text-[10px] font-black uppercase tracking-[0.3em] text-emerald-500/50 mb-10">/* EXPERIENCE_LOG */</h3>
                        <div className="space-y-12">
                            {data.experience?.map((exp, i) => (
                                <div key={i} className="group">
                                    <div className="flex justify-between items-baseline mb-3">
                                        <h4 className="text-white font-bold text-base">&lt;{exp.company} /&gt;</h4>
                                        <span className="text-[10px] opacity-40">{exp.duration}</span>
                                    </div>
                                    <p className="text-emerald-400/80 text-[10px] font-bold mb-6 italic">{exp.role}</p>
                                    <div className="space-y-3">
                                        {exp.highlights?.map((h: any, j: number) => (
                                            <div key={j} className="text-xs text-zinc-400 flex items-start">
                                                <span className="mr-4 text-emerald-500 opacity-30">$</span>
                                                {h}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </section>

                    <div className="grid grid-cols-2 gap-16">
                        <section>
                            <h3 className="text-[10px] font-black uppercase tracking-[0.3em] text-emerald-500/50 mb-8">/* STACK_OVERVIEW */</h3>
                            <div className="flex flex-wrap gap-3">
                                {data.skills?.hard?.map((s, i) => (
                                    <span key={i} className="text-[10px] bg-emerald-500/5 px-2 py-1 border border-emerald-500/20 text-emerald-400">
                                        {s}
                                    </span>
                                ))}
                            </div>
                        </section>
                        <section>
                            <h3 className="text-[10px] font-black uppercase tracking-[0.3em] text-emerald-500/50 mb-8">/* EDUCATION_REF */</h3>
                             {data.education?.map((edu, i) => (
                                <div key={i} className="mb-4">
                                    <h4 className="text-white text-[10px] font-bold">{edu.institution}</h4>
                                    <p className="text-[10px] text-zinc-500 mt-1">{edu.degree} :: {edu.year}</p>
                                </div>
                            ))}
                        </section>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white p-8 max-w-[21cm] mx-auto min-h-[29.7cm] shadow-xs print:shadow-none print:p-0 font-sans text-zinc-900">
            {/* Header */}
            <header className="border-b-2 border-zinc-900 pb-6 mb-8 flex justify-between items-end">
                <div>
                    <h1 className="text-4xl font-black uppercase tracking-tighter italic">{data.fullName}</h1>
                    <div className="flex flex-wrap gap-4 mt-4 text-[10px] font-bold uppercase tracking-widest text-gray-500">
                        <span>{data.contact?.email}</span>
                        <span>{data.contact?.phone}</span>
                        <span>{data.contact?.location}</span>
                    </div>
                </div>
            </header>

            {/* Summary */}
            <section className="mb-8">
                <h3 className="text-xs font-black uppercase tracking-[0.3em] mb-3 text-zinc-400">Professional Synopsis</h3>
                <p className="text-sm leading-relaxed text-zinc-700">{data.summary}</p>
            </section>

            {/* Experience */}
            <section className="mb-8">
                <h3 className="text-xs font-black uppercase tracking-[0.3em] mb-6 text-zinc-400">Experience</h3>
                 <div className="space-y-6">
                    {Array.isArray(data.experience) ? data.experience.map((exp: any, i: number) => (
                        <div key={i}>
                            <div className="flex justify-between items-baseline mb-1">
                                <h4 className="font-black text-sm uppercase italic">{exp.company}</h4>
                                <span className="text-[10px] font-bold text-gray-400">{exp.duration}</span>
                            </div>
                            <p className="text-[10px] font-black uppercase tracking-widest text-zinc-500 mb-3">{exp.role}</p>
                            {typeof exp.highlights === 'string' ? (
                                <p className="text-xs text-zinc-600 leading-relaxed italic whitespace-pre-wrap">{exp.highlights}</p>
                            ) : (
                                <ul className="space-y-1.5">
                                    {exp.highlights?.map((h: any, j: number) => (
                                        <li key={j} className="text-xs text-zinc-600 flex items-start">
                                            <span className="mr-3 text-zinc-300">•</span>
                                            <span>{h}</span>
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </div>
                    )) : (
                        <p className="text-xs text-zinc-600 leading-relaxed whitespace-pre-wrap">{data.experience as any}</p>
                    )}
                </div>
            </section>

            {/* Education */}
            <section className="mb-8">
                <h3 className="text-xs font-black uppercase tracking-[0.3em] mb-4 text-zinc-400">Education</h3>
                <div className="grid grid-cols-2 gap-8">
                    {data.education?.map((edu, i) => (
                        <div key={i}>
                            <h4 className="font-black text-[10px] uppercase italic text-zinc-900">{edu.institution}</h4>
                            <p className="text-[10px] font-bold text-gray-500 mt-1">{edu.degree} — {edu.year}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* Skills */}
            <section>
                <h3 className="text-xs font-black uppercase tracking-[0.3em] mb-4 text-zinc-400">Technical Arsenal</h3>
                <div className="flex flex-wrap gap-2">
                    {Array.isArray((data.skills as any)?.hard) ? (data.skills as any).hard.map((skill: any, i: number) => (
                        <span key={i} className="px-3 py-1 bg-zinc-100 rounded text-[9px] font-bold uppercase tracking-widest text-zinc-600">
                            {skill}
                        </span>
                    )) : (
                        <p className="text-xs text-zinc-500 leading-relaxed italic whitespace-pre-wrap">{data.skills as any}</p>
                    )}
                </div>
            </section>

            {/* Print Styles */}
            <style jsx global>{`
                @media print {
                    @page { margin: 2cm; }
                    body { background: white; }
                    .no-print { display: none; }
                }
            `}</style>
        </div>
    );
}
