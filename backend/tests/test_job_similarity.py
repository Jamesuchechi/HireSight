from app import crud, models
from app.schemas import JobCreate


def test_similar_jobs_returns_best_match(db_session):
    company = models.User(
        email='company@example.com',
        password_hash='hashed',
        account_type='company'
    )
    db_session.add(company)
    db_session.commit()

    job_data = JobCreate(
        title='Senior Backend Engineer',
        description='Build APIs',
        requirements={'skills': ['Python', 'Django', 'PostgreSQL']},
        status='active'
    )
    job_one = crud.create_job(db_session, company.id, job_data)

    job_two = crud.create_job(
        db_session,
        company.id,
        JobCreate(
            title='Python API Engineer',
            description='Design reliable backend systems',
            requirements={'skills': ['Python', 'FastAPI', 'PostgreSQL']},
            status='active'
        )
    )

    similar = crud.get_similar_jobs(db_session, job_one.id, limit=3)
    assert any(job.id == job_two.id for job in similar)
