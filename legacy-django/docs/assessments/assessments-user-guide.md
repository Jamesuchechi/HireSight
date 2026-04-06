# How to Take Assessments

## 1. Discovering the right test
1. Visit **Assessment Spotlight** on your personal dashboard to review recommended tests, recent badges, and links to the assessment catalog.
2. Browse the full catalog at `/assessments/browse/`, filter by skill level, difficulty, and format, and use the built-in search to narrow down fast.

## 2. Starting an assessment
1. Selecting a test spins up a **dynamic question set** within seconds—each attempt pulls from the question pool and is locked for the duration of the attempt.
2. The timer in the top-right counts down in real time. Questions are auto-saved every 2 seconds so you can refresh or recover from interruptions.

## 3. During the test
- Answer questions sequentially; your answers are saved automatically to the server.
- Use the “Save Progress” AJAX endpoint when toggling between devices to ensure every response persists.
- The progress bar reflects answered vs remaining questions so you always know how much is left.

## 4. Submitting & results
1. When the timer ends or you click "Submit", the system calculates your score, awards points, and stores question-level results.
2. Badge progress and analytics are displayed on your **Skill Proficiency** page (Chart.js visualizations) and the personal dashboard widget.
3. Earned badges include verification codes for third-party sharing, and certificates are downloadable from the results page.

## 5. Badge verification & sharing
- Every badge has a public verification page (`/assessments/verify/<code>/`) with Open Graph/Twitter/LinkedIn metadata, share links, and download buttons.
- Link certificates to your profile, export PDFs, or share via social media using the CTA buttons on the badge detail page.

## 6. Recommended follow-up
- Use the **Test Recommendation Engine** to see which areas need reinforcement. The engine considers profile, applications, and unfinished attempts.
- Keep your profile skills current so recommendations stay relevant.

## 7. Email notifications
- Automatic emails notify you when you earn a badge, when new tests are recommended, and when reminders are required.
- Check the responsive templates under `templates/assessments/emails/` for the latest CTA links and branding.
