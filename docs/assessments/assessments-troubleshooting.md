# Troubleshooting Guide

## 1. Question generation errors
- Check `logs` or Django logs for `AI generation failed` entries from `apps.assessments.admin` or `apps.assessments.ai_utils`.
- Ensure `MISTRAL_AI_API_KEY` and `MISTRAL_AI_MODEL` are set in environment/config; missing keys cause immediate failures logged as errors.
- Re-run the admin action for a single test to isolate which skill/difficulty is timing out.

## 2. Auto-save & completed attempts
- The `TakeTestView` logs errors on submission failures. Look for messages of form `Error submitting assessment for <email> on <test>: ...`.
- Verify the AJAX endpoint `/assessments/save-progress/<attempt_id>/` receives CSRF tokens and returns `success: true` plus answered counts.
- If the browser crashes, return to the dashboard—the auto-saved attempt will appear under “Resume” on the test detail page.

## 3. Certificate downloads
- Certificates require a passing attempt and an existing badge. The certificate view logs `Certificate downloaded by ...` on success and reports `Error generating certificate` on failure.
- Ensure badges are not expired (`SkillBadge.is_expired`) and that the attempt is marked `COMPLETED`.

## 4. Recommendation & emails
- The `TestRecommendationEngine` logs limited info; check personal dashboard widgets for empty recommendations and inspect profile skills.
- If email reminders fail, inspect Celery worker logs for `send_test_recommendation_emails` and confirm SMTP credentials are valid in settings.

## 5. Celery & scheduled tasks
- Celery beat tasks live under `hiresight/settings.py` (`cleanup-expired-attempts`, `send-test-recommendations`). Ensure workers respect UTC and that Redis is reachable.
- Check `celerybeat-schedule` file for next schedules and ensure the `apps.assessments.tasks` module imports the expected tasks.
- Reminder emails are sent hourly from `send_test_reminder_emails`; verify attempts that are `IN_PROGRESS` and near expiration trigger reminders and the cache key `assessment_reminder_sent_<attempt_id>` is set.

## 6. Logging & monitoring
- Key loggers:
  - `apps.assessments.ai_utils.QuestionGenerator` (AI question creation),
  - `apps.assessments.views.TakeTestView.post` (submission + completion info),
  - `apps.assessments.views.DownloadCertificateView` (certificate downloads),
  - `apps.assessments.admin` (admin actions).
- Use these logs for Sentry alerts or external monitoring integrations.
