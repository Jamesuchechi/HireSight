import datetime
import logging
import os

from django.core.exceptions import FieldDoesNotExist
from django.db.models import Prefetch, Q

from apps.applications.models import Application
from apps.assessments.models import SkillAssessmentAttempt
from apps.resumes.models import Resume
from apps.resumes.parsers import ResumeParser


logger = logging.getLogger(__name__)


class ApplicationDataService:
    """Service responsible for normalizing application+assessment payloads for screening."""

    @staticmethod
    def _serialize_value(value):
        """Convert datetimes to ISO strings so JSONField can persist them."""
        if isinstance(value, (datetime.datetime, datetime.date)):
            return value.isoformat()
        if isinstance(value, dict):
            return {k: ApplicationDataService._serialize_value(v) for k, v in value.items()}
        if isinstance(value, list):
            return [ApplicationDataService._serialize_value(v) for v in value]
        return value

    @classmethod
    def get_job_applications(cls, job_id):
        """Return applications for a job with optimized related loading.

        Args:
            job_id (UUID): Identifier of the job whose applications are required.

        Returns:
            QuerySet[Application]: Optimized queryset scoped to the job.
        """
        try:
            screening_answers_prefetch = Prefetch(
                'applicant__applications',
                queryset=Application.objects.only('screening_answers'),
                to_attr='prefetched_screening_answers'
            )

            queryset = Application.objects.filter(
                Q(job_id=job_id)
            ).select_related(
                'applicant',
                'applicant__personal_profile',
                'resume',
                'job'
            ).prefetch_related(screening_answers_prefetch)

            return queryset
        except Exception:
            logger.exception("Failed to load applications for job %s", job_id)
            return Application.objects.none()

    @classmethod
    def extract_resume_text(cls, resume):
        """Return resume text from stored or parsed sources, falling back to parsing.

        Args:
            resume (Resume): Resume whose text should be retrieved.

        Returns:
            str: Extracted resume text or empty string if unavailable.
        """
        if not resume:
            return ''

        try:
            parsed_data = getattr(resume, 'parsed_data', None) or {}
            extracted = parsed_data.get('extracted_text')
            if extracted:
                return extracted

            parsed_text = getattr(resume, 'parsed_text', '')
            if parsed_text:
                return parsed_text

            file_path = getattr(resume, 'file_path', None)
            if not file_path and getattr(resume, 'file', None):
                try:
                    file_path = resume.file.path
                except Exception:
                    file_path = resume.file.name

            if not file_path:
                return ''

            parser = ResumeParser()
            filename = getattr(resume, 'original_filename', os.path.basename(file_path))
            result = parser.parse_file(file_path, filename)
            return result.get('text') or result.get('parsed_text') or result.get('extracted_text') or ''

        except Exception as exc:
            logger.warning("Resume text extraction failed for resume %s: %s", getattr(resume, 'id', 'unknown'), exc)
            return ''

    @classmethod
    def get_application_screening_data(cls, application):
        """Compile a rich payload containing candidate info, answers, and assessments.

        Args:
            application (Application): Candidate application being screened.

        Returns:
            dict: Contains candidate_info, resume_text, screening_answers, assessment_results, and metadata.
        """
        try:
            applicant = application.applicant
            profile = getattr(applicant, 'personal_profile', None)

            candidate_info = {
                'name': (
                    profile.full_name if profile and profile.full_name
                    else applicant.get_full_name() or applicant.email
                ),
                'email': applicant.email,
                'phone': getattr(profile, 'phone', None) or '',
                'location': getattr(profile, 'location', None) or '',
            }

            resume = application.resume or Resume.objects.filter(user=applicant, is_primary=True).first()
            resume_text = cls.extract_resume_text(resume)

            raw_answers = application.screening_answers or []
            normalized_answers = []

            if isinstance(raw_answers, dict):
                # Some legacy applications store answers under nested keys.
                answers_payload = raw_answers.get('answers') or raw_answers.get('questions') or raw_answers
            else:
                answers_payload = raw_answers

            if isinstance(answers_payload, dict):
                answers_payload = list(answers_payload.values())

            for entry in answers_payload or []:
                if not isinstance(entry, dict):
                    continue
                normalized_answers.append({
                    'question': entry.get('question_text') or entry.get('question') or entry.get('label'),
                    'answer': entry.get('answer') or entry.get('response') or entry.get('value'),
                    'question_type': entry.get('type') or entry.get('question_type') or 'text'
                })

            assessment_results = []
            attempts = SkillAssessmentAttempt.objects.filter(
                user=applicant,
                status='COMPLETED'
            ).select_related('test').order_by('-completed_at')

            for attempt in attempts:
                # Include the associated test metadata alongside the attempt.
                assessment_results.append({
                    'test_name': attempt.test.title if attempt.test else 'Unknown Test',
                    'score': attempt.score,
                    'skills_validated': getattr(attempt.test, 'required_skills', []) if attempt.test else [],
                    'completed_at': ApplicationDataService._serialize_value(attempt.completed_at),
                })

            metadata = {
                'applied_at': ApplicationDataService._serialize_value(application.applied_at),
                'status': application.status,
                'source': application.source,
            }

            return {
                'application_id': str(application.id),
                'candidate_info': candidate_info,
                'resume_text': resume_text or '',
                'screening_answers': normalized_answers,
                'assessment_results': assessment_results,
                'application_metadata': metadata,
            }

        except Exception:
            logger.exception("Failed to build screening data for application %s", application.id)
            return {}

    @classmethod
    def get_bulk_application_data(cls, job_id):
        """Fetch screening data for all applicants under a job.

        Args:
            job_id (UUID): Job to aggregate application payloads for.

        Returns:
            list[dict]: List of application screening payloads.
        """
        results = []
        applications = cls.get_job_applications(job_id)

        for index, application in enumerate(applications, start=1):
            try:
                results.append(cls.get_application_screening_data(application))
            except Exception:
                logger.exception("Failed while processing application %s", application.id)
            finally:
                if index % 10 == 0:
                    logger.info("Processed %d/%d applications for job %s", index, applications.count(), job_id)

        return results

    @classmethod
    def get_assessment_results(cls, user, job=None):
        """Return assessment attempts for a user, optionally scoped to a job.

        Args:
            user (User): Candidate whose attempts should be aggregated.
            job (Job, optional): Job used to filter recommended assessments.

        Returns:
            list[dict]: Structured summaries of each completed attempt.
        """
        if not user:
            return []

        try:
            queryset = SkillAssessmentAttempt.objects.filter(
                user=user,
                status='COMPLETED'
            ).select_related('test').order_by('-completed_at')

            if job:
                test_model = SkillAssessmentAttempt._meta.get_field('test').related_model
                rec_field = None
                for candidate in ('recommended_for_jobs', 'recommended_jobs', 'jobs_recommended'):
                    try:
                        test_model._meta.get_field(candidate)
                        rec_field = candidate
                        break
                    except FieldDoesNotExist:
                        continue

                if rec_field:
                    queryset = queryset.filter(**{f'test__{rec_field}': job})

            results = []
            for attempt in queryset:
                test = attempt.test
                skills = []
                if test:
                    skills = getattr(test, 'skills_tested', None) or getattr(test, 'required_skills', None) or []
                if skills is None:
                    skills = []

                results.append({
                    'test_name': test.title if test else 'Unnamed Test',
                    'score': attempt.score,
                    'passed': attempt.passed,
                    'skills_validated': skills if isinstance(skills, list) else [skills],
                    'completed_at': attempt.completed_at,
                    'time_taken': getattr(attempt, 'time_taken_minutes', None) or getattr(attempt, 'time_taken', None),
                })

            return results

        except Exception:
            logger.exception("Failed to load assessment results for user %s", getattr(user, 'id', 'unknown'))
            return []
