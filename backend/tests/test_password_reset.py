from datetime import datetime, timedelta

from app import crud, models
from app.utils.security import get_password_hash


def test_password_reset_token_lifecycle(db_session):
    user = models.User(
        email='reset@example.com',
        password_hash=get_password_hash('StrongP@ss1'),
        account_type='personal'
    )
    db_session.add(user)
    db_session.commit()

    expires = datetime.utcnow() + timedelta(hours=1)
    token = crud.create_password_reset_token(db_session, user.id, expires)
    assert token.user_id == user.id
    assert token.expires_at == expires

    fetched = crud.get_password_reset_token(db_session, token.token)
    assert fetched is not None
    assert fetched.token == token.token

    crud.delete_password_reset_token(db_session, token.id)
    assert crud.get_password_reset_token(db_session, token.token) is None
