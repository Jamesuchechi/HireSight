"use client";

import { jsPDF } from "jspdf";
import html2canvas from "html2canvas";

export async function downloadCertificate(badge: any, fullName: string) {
    const doc = new jsPDF({
        orientation: "landscape",
        unit: "mm",
        format: "a4"
    });

    const canvas = document.createElement("canvas");
    canvas.width = 1123; // A4 Landscape ratio
    canvas.height = 794;
    const ctx = canvas.getContext("2d")!;

    // --- DRAW CERTIFICATE ---

    // 1. Background
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // 2. Neural Border (Primary Color)
    ctx.strokeStyle = "#e11d48"; // primary-600
    ctx.lineWidth = 40;
    ctx.strokeRect(40, 40, canvas.width - 80, canvas.height - 80);

    // 3. Inner Accents
    ctx.strokeStyle = "#000000";
    ctx.lineWidth = 2;
    ctx.setLineDash([10, 10]);
    ctx.strokeRect(80, 80, canvas.width - 160, canvas.height - 160);
    ctx.setLineDash([]);

    // 4. Logo / Title
    ctx.fillStyle = "#000000";
    ctx.font = "italic black 48px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("HIRESIGHT", canvas.width / 2, 180);
    
    ctx.font = "bold 16px sans-serif";
    ctx.fillStyle = "#e11d48";
    ctx.fillText("NEURAL VERIFIED CREDENTIAL", canvas.width / 2, 210);

    // 5. Main Content
    ctx.fillStyle = "#52525b";
    ctx.font = "bold 24px sans-serif";
    ctx.fillText("This official technical node certifies that", canvas.width / 2, 300);

    ctx.fillStyle = "#000000";
    ctx.font = "italic black 64px sans-serif";
    ctx.fillText(fullName.toUpperCase(), canvas.width / 2, 380);

    ctx.fillStyle = "#52525b";
    ctx.font = "bold 24px sans-serif";
    ctx.fillText("has successfully navigated the vetting protocol and earned a", canvas.width / 2, 450);

    // 6. Achievement Tier
    ctx.fillStyle = "#e11d48";
    ctx.font = "italic black 56px sans-serif";
    ctx.fillText(`${badge.badge_level.toUpperCase()} NODE`, canvas.width / 2, 530);

    ctx.fillStyle = "#000000";
    ctx.font = "bold 32px sans-serif";
    ctx.fillText(badge.skill_name.toUpperCase(), canvas.width / 2, 580);

    // 7. Footer Details
    ctx.fillStyle = "#a1a1aa";
    ctx.font = "bold 14px sans-serif";
    ctx.textAlign = "left";
    ctx.fillText(`INDEXED SCORE: ${badge.score}%`, 140, 680);
    ctx.fillText(`ISSUANCE DATE: ${new Date(badge.issued_at).toLocaleDateString()}`, 140, 710);

    ctx.textAlign = "right";
    ctx.fillText(`VERIFICATION CODE: ${badge.verification_code}`, canvas.width - 140, 680);
    ctx.fillText(`SYSTEM ID: HS-V2-${badge.id.substring(0, 8)}`, canvas.width - 140, 710);

    // --- SAVE PDF ---
    const imgData = canvas.toDataURL("image/png");
    doc.addImage(imgData, "PNG", 0, 0, 297, 210);
    doc.save(`HireSight_Credential_${badge.skill_name.replace(/ /g, "_")}.pdf`);
}
