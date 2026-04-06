"use client";

import { Document, Page, Text, View, StyleSheet, Font } from '@react-pdf/renderer';

// Register a clean font for professional look
Font.register({
    family: 'Inter',
    fonts: [
        { src: (typeof window !== 'undefined' ? window.location.origin : '') + '/fonts/Inter-Regular.ttf', fontWeight: 400 },
        { src: (typeof window !== 'undefined' ? window.location.origin : '') + '/fonts/Inter-Bold.ttf', fontWeight: 700 },
        { src: (typeof window !== 'undefined' ? window.location.origin : '') + '/fonts/Inter-Black.ttf', fontWeight: 900 },
        { src: (typeof window !== 'undefined' ? window.location.origin : '') + '/fonts/Inter-BlackItalic.ttf', fontWeight: 900, fontStyle: 'italic' },
    ]
});

const styles = StyleSheet.create({
    page: {
        padding: 40,
        fontFamily: 'Inter',
        color: '#18181b',
        lineHeight: 1.5,
    },
    header: {
        borderBottomWidth: 2,
        borderBottomColor: '#18181b',
        paddingBottom: 20,
        marginBottom: 20,
    },
    name: {
        fontSize: 32,
        fontWeight: 900,
        textTransform: 'uppercase',
        letterSpacing: -1,
    },
    contact: {
        flexDirection: 'row',
        marginTop: 10,
        fontSize: 9,
        fontWeight: 700,
        textTransform: 'uppercase',
        color: '#71717a',
        gap: 15,
    },
    sectionTitle: {
        fontSize: 10,
        fontWeight: 900,
        textTransform: 'uppercase',
        letterSpacing: 2,
        color: '#a1a1aa',
        marginBottom: 10,
        marginTop: 20,
    },
    summary: {
        fontSize: 11,
        color: '#3f3f46',
    },
    experienceItem: {
        marginBottom: 15,
    },
    expHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'baseline',
        marginBottom: 4,
    },
    company: {
        fontSize: 12,
        fontWeight: 900,
        textTransform: 'uppercase',
    },
    duration: {
        fontSize: 9,
        color: '#a1a1aa',
    },
    role: {
        fontSize: 10,
        fontWeight: 900,
        textTransform: 'uppercase',
        color: '#71717a',
        marginBottom: 8,
    },
    highlightRow: {
        flexDirection: 'row',
        marginBottom: 4,
    },
    bullet: {
        width: 10,
        fontSize: 10,
        color: '#d4d4d8',
    },
    highlightText: {
        flex: 1,
        fontSize: 10,
        color: '#52525b',
    },
    skillsContainer: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: 8,
    },
    skillBadge: {
        backgroundColor: '#f4f4f5',
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 4,
        fontSize: 8,
        fontWeight: 700,
        textTransform: 'uppercase',
        color: '#52525b',
    }
});

export const PDFTemplate = ({ data }: { data: any }) => (
    <Document title={`${data.fullName} - Resume`}>
        <Page size="A4" style={styles.page}>
            <View style={styles.header}>
                <Text style={styles.name}>{data.fullName}</Text>
                <View style={styles.contact}>
                    <Text>{data.contact?.email}</Text>
                    <Text>{data.contact?.phone}</Text>
                    <Text>{data.contact?.location}</Text>
                </View>
            </View>

            <View>
                <Text style={styles.sectionTitle}>Professional Synopsis</Text>
                <Text style={styles.summary}>{data.summary}</Text>
            </View>

            <View>
                <Text style={styles.sectionTitle}>Experience</Text>
                {data.experience?.map((exp: any, i: number) => (
                    <View key={i} style={styles.experienceItem}>
                        <View style={styles.expHeader}>
                            <Text style={styles.company}>{exp.company}</Text>
                            <Text style={styles.duration}>{exp.duration}</Text>
                        </View>
                        <Text style={styles.role}>{exp.role}</Text>
                        {exp.highlights?.map((h: string, j: number) => (
                            <View key={j} style={styles.highlightRow}>
                                <Text style={styles.bullet}>•</Text>
                                <Text style={styles.highlightText}>{h}</Text>
                            </View>
                        ))}
                    </View>
                ))}
            </View>

            <View>
                <Text style={styles.sectionTitle}>Education</Text>
                {data.education?.map((edu: any, i: number) => (
                    <View key={i} style={{ marginBottom: 10 }}>
                        <Text style={{ fontSize: 11, fontWeight: 900, textTransform: 'uppercase' }}>{edu.institution}</Text>
                        <Text style={{ fontSize: 9, color: '#71717a', marginTop: 2 }}>{edu.degree} — {edu.year}</Text>
                    </View>
                ))}
            </View>

            <View>
                <Text style={styles.sectionTitle}>Technical Arsenal</Text>
                <View style={styles.skillsContainer}>
                    {data.skills?.hard?.map((skill: string, i: number) => (
                        <View key={i} style={styles.skillBadge}>
                            <Text>{skill}</Text>
                        </View>
                    ))}
                </View>
            </View>
        </Page>
    </Document>
);
