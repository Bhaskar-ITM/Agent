import os
from typing import Optional, List


def get_sonar_url() -> str:
    """Lazy load SONARQUBE_URL to avoid import errors"""
    from app.core.config import settings
    return settings.SONARQUBE_URL


def get_sonar_dashboard_link(sonar_key: str) -> str:
    """
    Generate SonarQube dashboard link from project key.
    Uses SONARQUBE_URL from environment.
    """
    sonar_url = get_sonar_url()
    return f"https://{sonar_url}/dashboard?id={sonar_key}"


def create_sonar_report_link(sonar_key: Optional[str]) -> Optional[str]:
    """Create SonarQube report entry (returns link only, no parsing)"""
    if not sonar_key:
        return None
    return get_sonar_dashboard_link(sonar_key)


def get_sonar_issues_link(sonar_key: str) -> str:
    """Generate SonarQube issues page link"""
    sonar_url = get_sonar_url()
    return f"https://{sonar_url}/project/issues?id={sonar_key}&resolved=false"