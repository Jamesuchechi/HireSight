# Screening Developer Guide

## Architecture Overview

- **ApplicationDataService** assembles job applicants by selecting related `Application`, `Resume`, and assessment attempts, normalizing screening answers, and returning a payload that includes `candidate_info`, `resume_text`, `screening_answers`, `assessment_results`, and metadata for `applied_at`, `status`, and `source`.
- **AI scoring** (`apps/screening/ai_matcher.py`) consumes the payload alongside job descriptions and criteria. If application data exists, it evaluates screening answers and assessments via `evaluate_screening_answers` and `evaluate_assessments`, then merges those scores with resume skills, experience, education, and semantic similarity to compute the final `match_score`.
- **Database relationships**: `Job → Application → Resume` (OneToOne per applicant) with `ScreeningResult` optionally linking to an `Application`. `ScreeningSession` aggregates multiple `ScreeningResult`s, `ScreeningCriteria` tie the weights, and `ProgressUpdate` tracks status. (Diagram: `Job` feeds `Applications` which feed `Resumes`, `ScreeningResult`s, and `Assessment` attempts, all converging in the AI scorer.)

## Adding New Data Sources

1. **Template**:
   - Extend `ApplicationDataService.get_application_screening_data` to collect the new source (e.g., `linkedin_profile_score`).
   - Ensure the payload adds `{ 'linkedin_score': value }` or similar for downstream use.
   - Add normalization logic in the AI matcher to interpret the new metric.

2. **Weights system**:
   - Add a new weight field to `ScreeningCriteria` (with validators and help text).
   - Update `validate_weights()` to include the new weight so the sum still rounds to 1.0.
   - Use hidden inputs/sliders + criteria form to expose the percentage to recruiters.

3. **Example – LinkedIn profile scores**:
   - Store the score on the `Application` (e.g., add `linkedin_score` JSON).
   - When `ApplicationDataService` builds the payload, include `linkedin_score`.
   - In `ai_matcher.calculate_match_score`, add a helper (e.g., `evaluate_linkedin_profile`) and incorporate the weighted result with the new weight field.

## Customizing Scoring Logic

- Modify `apps/screening/ai_matcher.py`:
  - Update `calculate_match_score` to ingest new `application_data` components and adjust the weight normalization logic.
  - Use the helper methods `evaluate_screening_answers` and `evaluate_assessments` as patterns; add new `evaluate_<component>` methods as needed.
- To add custom evaluators:
  - Build a method behind the new component (e.g., `evaluate_portfolio_quality`) and call it when `application_data` exists.
  - Return structured details for `match_details` so the admin UI can show the breakdown.
- Testing scoring:
  - Use `apps/screening/tests.py` to instantiate `AIScreener` and call `calculate_match_score` with canned resume text, job descriptions, and criteria.
  - Extend tests to cover edge cases (missing data, abnormal weights).

## Common Tasks

- **Re-screen existing applications**:
  - Use the admin action “Re-screen with latest data” or requeue `process_resume_screening` via Celery for completed results.
  - Ensure resumes and applications are still linked; run `migrate_old_screenings` if needed.

- **Adjust weights after screening**:
  - Edit the `ScreeningCriteria` (via the criteria setup UI or admin) and resubmit the session so future scores reflect updated sliders.
  - Existing results keep their previous weights; reprocessing requires re-running the task.

- **Export enhanced results**:
  - Use the `/screening/sessions/<id>/export/` endpoint to generate reports that include screening answers, assessments, and match breakdowns.

## Troubleshooting

| Issue | Check |
| --- | --- |
| Applications not showing in screening | Confirm resumes are uploaded and marked `is_primary`; verify `ApplicationDataService` is referencing the correct job. |
| Match scores seem wrong | Ensure `ScreeningCriteria.validate_weights` passes (weights sum ≈ 1.0); inspect match breakdown JSON for unexpected zero scores. |
| Assessments not included | Confirm `SkillAssessmentAttempt` is `COMPLETED` and linked to the applicant; review `ApplicationDataService.get_application_screening_data` for `assessment_results`. |

For additional guidance, review `templates/screening/job_application_screening.html` and the related views/tasks to understand how the UI, background jobs, and admin actions coordinate.
