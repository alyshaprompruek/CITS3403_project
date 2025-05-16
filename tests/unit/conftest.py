import pytest
from app import application, db

@pytest.fixture
def app(tmp_path):
    # Use a fresh sqlite DB for each test session
    db_file = tmp_path / "test.db"
    application.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_file}",
        "WTF_CSRF_ENABLED": False,   # if you’re using CSRF in your forms
    })
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()
