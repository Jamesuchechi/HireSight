# Assessment API Reference

All assessment endpoints live under `/assessments/` and are behind authentication (`LoginRequiredMixin`). Use these URLs for front-end integrations or automation.

| Endpoint | Method | Description | Payload |
| --- | --- | --- | --- |
| `/assessments/browse/` | GET | Lists available tests with `tests_data` including best scores and badge flags. Supports query params (`skill`, `difficulty`, `test_type`, `sort_by`). | N/A |
| `/assessments/test/<slug>/` | GET | Returns test metadata, historical attempts, best score, and badge status. Suitable for preview modals. | N/A |
| `/assessments/start/<uuid:test_id>/` | POST | Creates or resumes an attempt; returns redirect to `/assessments/take/<attempt_id>/`. | `test_id` in URL |
| `/assessments/take/<uuid:attempt_id>/` | GET/POST | Renders the timer + questions; POST submits answers. | Form fields named `question_<id>` for each question. |
| `/assessments/save-progress/<uuid:attempt_id>/` | POST | Auto-save endpoint for AJAX—provides `question_id` + `answer`. | JSON or form data (named keys) |
| `/assessments/results/<uuid:attempt_id>/` | GET | Displays results, percentile, and badge/certificate links. | N/A |
| `/assessments/certificate/<uuid:attempt_id>/` | GET | Generates and returns the PDF certificate (Buddy ensures badge exists). | N/A |
| `/assessments/my-badges/` | GET | Collection of earned badges with pagination. | query params: `page` |
| `/assessments/verify/<code>/` | GET | Public badge verification page with OG/Twitter metadata for sharing. | N/A |

### Recommendation & analytics hooks
- The `SkillProficiencyDashboard` at `/analytics/skill-proficiency/` consumes `get_skill_proficiency_data`, `get_assessment_trends`, and `generate_assessment_report_for_user` for Chart.js visuals.
- `CompanyCandidateInsights` uses `apps.assessments.analytics_helpers.get_company_candidate_insights` to surface badge counts, skill distribution, and top skills to employer dashboards.

### Security & reliability
1. CSRF is enforced on all forms. Auto-save endpoints expect CSRF tokens with AJAX headers.
2. Rate limiting (via `django-ratelimit`) guards submission endpoints—monitor logs when `W001` warns about Redis backend compatibility.
3. Celery tasks (`cleanup_expired_attempts`, `send_test_recommendation_emails`) are scheduled through `CELERY_BEAT_SCHEDULE` to enforce retention and nudges.
