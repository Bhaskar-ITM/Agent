#!/usr/bin/env python3
"""
Test CVE title parsing logic in parser.py

Bug: CVE title shows "Description" instead of real title
Fix: Extract Description value, fall back to script name, skip metadata fields
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from parser import FindingDetector


class TestCveTitleParsing:
    """Test CVE title extraction logic"""

    def setup_method(self):
        """Set up test fixtures"""
        self.detector = FindingDetector()
        self.host_info = {
            'name': 'Test-Host',
            'ip': '192.168.1.1',
            'environment': 'Test'
        }
        self.scan_file = 'test_scan.txt'

    def test_cve_title_uses_description_value(self):
        """
        CVE title should use the Description value, not the field name.
        
        Example nmap output:
        | vuln:
        |   CVE-2021-1234: VULNERABLE
        |   Description: Remote code execution vulnerability
        |   References:
        |     https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2021-1234
        |_  Risk: High
        
        Expected title: "Remote code execution vulnerability"
        NOT: "Description"
        """
        content = """
80/tcp open  http
| vuln:
|   CVE-2021-1234: VULNERABLE
|   Description: Remote code execution vulnerability
|   References:
|     https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2021-1234
|_  Risk: High
"""
        # Clear findings from previous tests
        self.detector.findings = []
        self.detector.finding_counter = 0
        self.detector._seen = set()
        
        finding_ids = self.detector.detect_cve(content, self.host_info, self.scan_file)
        
        assert len(finding_ids) == 1, f"Expected 1 finding, got {len(finding_ids)}"
        
        finding = self.detector.findings[0]
        assert finding['title'] == "Remote code execution vulnerability", \
            f"Title should be description value, got: {finding['title']}"
        assert finding['cve'] == "CVE-2021-1234"
        assert "Remote code execution vulnerability" in finding['description']

    def test_cve_title_falls_back_to_script_name(self):
        """
        If no Description field exists, fall back to script name.
        
        Example nmap output:
        | http-slowloris:
        |   VULNERABLE
        |   CVE-2021-5678
        
        Expected title: "Http Slowloris" (from script name)
        """
        content = """
80/tcp open  http
| http-slowloris:
|   VULNERABLE
|   CVE-2021-5678
|_  Risk: Medium
"""
        self.detector.findings = []
        self.detector.finding_counter = 0
        self.detector._seen = set()
        
        finding_ids = self.detector.detect_cve(content, self.host_info, self.scan_file)
        
        assert len(finding_ids) == 1
        finding = self.detector.findings[0]
        assert finding['title'] == "Http Slowloris", \
            f"Title should fall back to script name, got: {finding['title']}"

    def test_cve_title_skips_metadata_fields(self):
        """
        Should skip metadata field names like 'References', 'Risk', 'CVSS'.
        
        Example nmap output without Description:
        | vuln:
        |   CVE-2021-9999: VULNERABLE
        |   References:
        |     https://example.com
        |_  Risk: High
        
        Expected title: "Vulnerability: CVE-2021-9999" (default)
        NOT: "References" or "Risk"
        """
        content = """
80/tcp open  http
| vuln:
|   CVE-2021-9999: VULNERABLE
|   References:
|     https://example.com
|_  Risk: High
"""
        self.detector.findings = []
        self.detector.finding_counter = 0
        self.detector._seen = set()
        
        finding_ids = self.detector.detect_cve(content, self.host_info, self.scan_file)
        
        assert len(finding_ids) == 1
        finding = self.detector.findings[0]
        # Should use default title, not "References" or "Risk"
        assert finding['title'] == "Vulnerability: CVE-2021-9999", \
            f"Title should be default when only metadata fields present, got: {finding['title']}"
        assert finding['title'] != "References"
        assert finding['title'] != "Risk"
        assert finding['title'] != "CVSS"

    def test_cve_title_skips_generic_script_names(self):
        """
        Should skip generic script names like 'vuln', 'exploit'.
        
        Example:
        | vuln:
        |   CVE-2021-1111: VULNERABLE
        
        Expected title: "Vulnerability: CVE-2021-1111" (default)
        NOT: "Vuln"
        """
        content = """
80/tcp open  http
| vuln:
|   CVE-2021-1111: VULNERABLE
|_  Risk: High
"""
        self.detector.findings = []
        self.detector.finding_counter = 0
        self.detector._seen = set()
        
        finding_ids = self.detector.detect_cve(content, self.host_info, self.scan_file)
        
        assert len(finding_ids) == 1
        finding = self.detector.findings[0]
        assert finding['title'] == "Vulnerability: CVE-2021-1111", \
            f"Title should skip generic 'vuln' script name, got: {finding['title']}"

    def test_cve_description_field_in_description_text(self):
        """
        When Description value is used for title, it should appear in description text.
        """
        content = """
80/tcp open  http
| vuln:
|   CVE-2021-2222: VULNERABLE
|   Description: SQL injection in login form
|_  Risk: High
"""
        self.detector.findings = []
        self.detector.finding_counter = 0
        self.detector._seen = set()
        
        finding_ids = self.detector.detect_cve(content, self.host_info, self.scan_file)
        
        assert len(finding_ids) == 1
        finding = self.detector.findings[0]
        assert finding['title'] == "SQL injection in login form"
        assert "SQL injection in login form" in finding['description']
        assert "CVE-2021-2222" in finding['description']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
