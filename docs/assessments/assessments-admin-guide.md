# Managing Questions and Tests

## Question Pool hygiene
1. Use the `QuestionPool` admin to review AI-generated entries. The list view shows success rate, usage counters, and verification status.
2. Bulk actions allow you to:
   - `Verify selected unverified questions` to batch approve or `Activate/Deactivate` content for use in dynamic tests.
   - Use `Mark verified/unverified` when editing question quality.

## AI-assisted question generation
1. Select one or more `SkillTest` records and run `Generate questions with AI` to invoke `QuestionGenerator` (Mistral AI). The generator respects test difficulty, question type, and filters.
2. Newly generated entries land in `QuestionPool` marked `is_verified=False` so you can vet them manually before enabling.
3. Need bulk work from the command line? `python manage.py generate_ai_questions --skill Python --difficulty ADVANCED --count 30` writes questions directly to `QuestionPool`; add `--verify` to bypass manual review.

## Test management
1. The `SkillTest` admin surface shows pass rates, attempts, and completion time with color-coded badges.
2. Use `Activate/Deactivate`, `Feature/Unfeature`, or `Duplicate` to manage availability quickly.
3. `Export question bank to CSV` downloads all pool entries matching the selected tests (includes JSON-encoded options/explanations).

## Invitations & reporting
1. `Send test invitations` emails personalized invite links to personal accounts whose profile skills align with the test skill (up to five per test).
2. Monitor admin logs for `AI generation` success/failures and vaccine actions in the standard log output (`logger` under `apps.assessments.admin`).

## Monitoring & troubleshooting
1. Check `logging` (`apps.assessments.views`, `ai_utils`, `analytics_helpers`) for assessment completion scores, certificate downloads, and failed submissions.
2. Celery beat tasks (`cleanup_expired_attempts`, `send_test_recommendation_emails`) live in `hiresight/settings.py`; ensure workers are running to keep badges and reminders synchronized.
