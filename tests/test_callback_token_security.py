"""
Test for callback token security - ensures no hardcoded tokens exist.
"""
import re
from pathlib import Path


def test_jenkinsfile_no_hardcoded_callback_token():
    """
    Security test: Verify Jenkinsfile does not contain hardcoded callback token.
    
    The CALLBACK_TOKEN must be loaded from environment variables only.
    Hardcoded tokens are a security vulnerability allowing forged scan results.
    """
    jenkinsfile_path = Path(__file__).parent.parent / "Jenkinsfile"
    content = jenkinsfile_path.read_text()
    
    # Pattern to match CALLBACK_TOKEN definition with fallback/default value
    # Matches: CALLBACK_TOKEN = "${env.CALLBACK_TOKEN ?: '...'}"
    # or: CALLBACK_TOKEN = "${env.CALLBACK_TOKEN ?: "..." }"
    hardcoded_token_pattern = r'CALLBACK_TOKEN\s*=\s*"\$\{env\.CALLBACK_TOKEN\s*\?:\s*[\'"][^\'"]+[\'"]\s*\}"'
    
    matches = re.findall(hardcoded_token_pattern, content)
    
    assert len(matches) == 0, (
        f"Hardcoded callback token fallback found in Jenkinsfile ({len(matches)} occurrence(s)). "
        "Remove the default fallback token to prevent security vulnerabilities. "
        "Use: CALLBACK_TOKEN = \"${env.CALLBACK_TOKEN}\""
    )


def test_jenkinsfile_callback_token_uses_env_only():
    """
    Security test: Verify CALLBACK_TOKEN uses environment variable without fallback.
    """
    jenkinsfile_path = Path(__file__).parent.parent / "Jenkinsfile"
    content = jenkinsfile_path.read_text()
    
    # Find the CALLBACK_TOKEN environment definition line
    callback_token_line = None
    for line in content.split('\n'):
        if 'CALLBACK_TOKEN' in line and 'env.CALLBACK_TOKEN' in line:
            callback_token_line = line
            break
    
    assert callback_token_line is not None, (
        "CALLBACK_TOKEN environment variable definition not found in Jenkinsfile"
    )
    
    # Verify no fallback operator (?:) is present
    assert '?:' not in callback_token_line, (
        f"CALLBACK_TOKEN should not have a fallback value. "
        f"Found: {callback_token_line.strip()}"
    )
    
    # Verify it's a clean environment variable reference
    expected_pattern = r'CALLBACK_TOKEN\s*=\s*"\$\{env\.CALLBACK_TOKEN\}"'
    assert re.search(expected_pattern, callback_token_line), (
        f"CALLBACK_TOKEN should use clean environment variable syntax. "
        f"Found: {callback_token_line.strip()}"
    )
