"""
Pytest configuration and fixtures for backend tests.
"""
import os
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set test environment variables before importing app modules
os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JENKINS_BASE_URL", "http://localhost:8080")
os.environ.setdefault("JENKINS_TOKEN", "test-jenkins-token")
os.environ.setdefault("STORAGE_PATH", "./storage/test")
os.environ.setdefault("SCAN_TIMEOUT", "120")
os.environ.setdefault("LOG_LEVEL", "DEBUG")
os.environ.setdefault("CALLBACK_TOKEN", "test-callback-token-12345678901234567890")
os.environ.setdefault("API_KEY", "test-api-key-123456789012345678901234")

# Mock the scan recovery task before importing app
mock_recovery = patch('app.services.scan_recovery.run_recovery_task')
mock_recovery.start()

# Mock Celery tasks to prevent Redis connection errors
mock_celery = patch('app.tasks.jenkins_tasks.trigger_jenkins_scan_async')
mock_celery_task = mock_celery.start()

from app.core.db import Base, get_db
from app.main import app


# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency overridden."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()
    # Drop all tables after test
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True, scope="session")
def cleanup():
    """Cleanup mock patches after all tests."""
    yield
    mock_recovery.stop()
    mock_celery.stop()
