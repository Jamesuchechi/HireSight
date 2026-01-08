from pathlib import Path

from fastapi.testclient import TestClient

from app import models
from app.main import app
from app.utils.security import (
    get_current_personal_user,
    get_current_verified_user,
    get_password_hash
)


def test_resume_parse_endpoint(monkeypatch, db_session):
    user = models.User(
        email='parser@example.com',
        password_hash=get_password_hash('StrongP@ss1'),
        account_type='personal',
        is_verified=True
    )
    db_session.add(user)
    db_session.commit()

    def fake_parser(path: str):
        return {
            'success': True,
            'filename': Path(path).name,
            'raw_text': 'dummy content'
        }

    monkeypatch.setattr('app.routes.parse_resume', fake_parser)
    app.dependency_overrides[get_current_personal_user] = lambda: user
    app.dependency_overrides[get_current_verified_user] = lambda: user

    client = TestClient(app)
    upload_data = {
        'file': ('sample.pdf', b'%PDF-1.4 Dummy resume', 'application/pdf')
    }
    response = client.post('/api/resumes/upload', files=upload_data)
    assert response.status_code == 200
    resume_id = response.json()['id']
    file_path = response.json()['file_url']

    parse_resp = client.post(f'/api/resumes/{resume_id}/parse')
    assert parse_resp.status_code == 200
    assert parse_resp.json()['id'] == resume_id

    Path(file_path).unlink(missing_ok=True)
    app.dependency_overrides.clear()
