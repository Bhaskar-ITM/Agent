#!/usr/bin/env python3
"""
Tests for Reporter Enhancements - Task 3
Dashboard Sort + Icon Column + Critical/High Split Filter
"""

import json
import sys
from pathlib import Path
from io import StringIO

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from reporter import HTMLReportBuilder, ReportDataLoader


class TestFilterButtons:
    """Test that filter buttons include All/Critical/High/Medium/Low/Clean"""

    def test_filter_buttons_exist(self, tmp_path):
        """Verify filter buttons HTML contains all required severity filters"""
        # Create minimal test data
        test_data = {
            "summary": {
                "total_hosts": 1,
                "total_findings": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
            },
            "host_summary": {},
            "findings": [],
        }

        # Create temp files
        scans_dir = tmp_path / "scans" / "2026-03-25"
        scans_dir.mkdir(parents=True)
        (scans_dir / "findings.json").write_text(json.dumps(test_data))
        (tmp_path / "targets.json").write_text(json.dumps({"client": "Test Client"}))

        # Build HTML
        output_file = tmp_path / "test_report.html"
        data_loader = ReportDataLoader("2026-03-25", tmp_path)
        data_loader.load_all()
        builder = HTMLReportBuilder(data_loader)
        builder.generate_html(output_file)

        # Read generated HTML
        html_content = output_file.read_text()

        # Verify all filter buttons exist
        assert 'data-filter="all"' in html_content, "Missing 'All' filter button"
        assert 'data-filter="critical"' in html_content, (
            "Missing 'Critical' filter button"
        )
        assert 'data-filter="high"' in html_content, "Missing 'High' filter button"
        assert 'data-filter="medium"' in html_content, "Missing 'Medium' filter button"
        assert 'data-filter="low"' in html_content, "Missing 'Low' filter button"
        assert 'data-filter="clean"' in html_content, "Missing 'Clean' filter button"

        # Verify old filter buttons don't exist
        assert 'data-filter="finding"' not in html_content, (
            "Old 'Findings' filter should be removed"
        )
        assert 'data-filter="warning"' not in html_content, (
            "Old 'Warnings' filter should be removed"
        )

        print("✓ Filter buttons test passed")


class TestIconColumn:
    """Test that dashboard rows include status icon column"""

    def test_icon_column_in_rows(self, tmp_path):
        """Verify dashboard rows include icon column with ✓/⚠/✗"""
        # Create test data with different severity findings
        test_data = {
            "summary": {
                "total_hosts": 1,
                "total_findings": 1,
                "critical": 1,
                "high": 0,
                "medium": 0,
                "low": 0,
            },
            "host_summary": {
                "Test-Host": {
                    "ip": "192.168.1.1",
                    "environment": "Test",
                    "scans": {"ssl": "finding", "headers": "clean"},
                    "scans_run": ["ssl", "headers"],
                    "open_ports": [443],
                }
            },
            "findings": [
                {
                    "id": "F001",
                    "title": "SSL Certificate Expired",
                    "host": "Test-Host",
                    "ip": "192.168.1.1",
                    "port": 443,
                    "severity": "Critical",
                    "scan_type": "ssl",
                    "description": "Test finding",
                    "recommendation": "Test recommendation",
                }
            ],
        }

        # Create temp files
        scans_dir = tmp_path / "scans" / "2026-03-25"
        scans_dir.mkdir(parents=True)
        (scans_dir / "findings.json").write_text(json.dumps(test_data))
        (tmp_path / "targets.json").write_text(json.dumps({"client": "Test Client"}))

        # Build HTML
        output_file = tmp_path / "test_report.html"
        data_loader = ReportDataLoader("2026-03-25", tmp_path)
        data_loader.load_all()
        builder = HTMLReportBuilder(data_loader)
        builder.generate_html(output_file)

        # Read generated HTML
        html_content = output_file.read_text()

        # Verify Status column exists in table header
        assert (
            'onclick="sortTable(4)">Status</th>' in html_content
            or ">Status</th>" in html_content
        ), "Missing Status column header"

        # Verify icons are present in rows
        # Finding row should have ✗ icon
        assert "✗" in html_content or "✖" in html_content, (
            "Missing '✗' icon for finding rows"
        )

        # Clean row should have ✓ icon
        assert "✓" in html_content or "✔" in html_content, (
            "Missing '✓' icon for clean rows"
        )

        # Warning should have ⚠ icon
        assert "⚠" in html_content, "Missing '⚠' icon for warning rows"

        print("✓ Icon column test passed")


class TestSortableHeaders:
    """Test that table headers have onclick sort handlers"""

    def test_sortable_column_headers(self, tmp_path):
        """Verify table headers have onclick='sortTable(n)' attributes"""
        test_data = {
            "summary": {
                "total_hosts": 1,
                "total_findings": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
            },
            "host_summary": {},
            "findings": [],
        }

        scans_dir = tmp_path / "scans" / "2026-03-25"
        scans_dir.mkdir(parents=True)
        (scans_dir / "findings.json").write_text(json.dumps(test_data))
        (tmp_path / "targets.json").write_text(json.dumps({"client": "Test Client"}))

        output_file = tmp_path / "test_report.html"
        data_loader = ReportDataLoader("2026-03-25", tmp_path)
        data_loader.load_all()
        builder = HTMLReportBuilder(data_loader)
        builder.generate_html(output_file)

        html_content = output_file.read_text()

        # Verify sortable headers exist (6 columns: Environment, Host, IP, Scan Type, Status, Finding)
        assert 'onclick="sortTable(0)"' in html_content, (
            "Missing sort handler for column 0"
        )
        assert 'onclick="sortTable(1)"' in html_content, (
            "Missing sort handler for column 1"
        )
        assert 'onclick="sortTable(2)"' in html_content, (
            "Missing sort handler for column 2"
        )
        assert 'onclick="sortTable(3)"' in html_content, (
            "Missing sort handler for column 3"
        )
        assert 'onclick="sortTable(4)"' in html_content, (
            "Missing sort handler for column 4"
        )
        assert 'onclick="sortTable(5)"' in html_content, (
            "Missing sort handler for column 5"
        )
        # Column 6 removed — duplicate Status header was removed

        print("✓ Sortable headers test passed")


class TestSortTableFunction:
    """Test that sortTable JavaScript function exists"""

    def test_sorttable_function_exists(self, tmp_path):
        """Verify sortTable JavaScript function is defined"""
        test_data = {
            "summary": {
                "total_hosts": 1,
                "total_findings": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
            },
            "host_summary": {},
            "findings": [],
        }

        scans_dir = tmp_path / "scans" / "2026-03-25"
        scans_dir.mkdir(parents=True)
        (scans_dir / "findings.json").write_text(json.dumps(test_data))
        (tmp_path / "targets.json").write_text(json.dumps({"client": "Test Client"}))

        output_file = tmp_path / "test_report.html"
        data_loader = ReportDataLoader("2026-03-25", tmp_path)
        data_loader.load_all()
        builder = HTMLReportBuilder(data_loader)
        builder.generate_html(output_file)

        html_content = output_file.read_text()

        # Verify sortTable function exists
        assert "function sortTable" in html_content, "Missing sortTable function"
        assert "columnIndex" in html_content, (
            "sortTable should accept columnIndex parameter"
        )
        assert (
            "querySelectorAll('tr')" in html_content
            or 'querySelectorAll("tr")' in html_content
        ), "sortTable should sort table rows"

        print("✓ sortTable function test passed")


class TestFilterDashboardFunction:
    """Test that filterDashboard handles new severity filters"""

    def test_filterDashboard_handles_severities(self, tmp_path):
        """Verify filterDashboard function handles critical/high/medium/low/clean"""
        test_data = {
            "summary": {
                "total_hosts": 1,
                "total_findings": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
            },
            "host_summary": {},
            "findings": [],
        }

        scans_dir = tmp_path / "scans" / "2026-03-25"
        scans_dir.mkdir(parents=True)
        (scans_dir / "findings.json").write_text(json.dumps(test_data))
        (tmp_path / "targets.json").write_text(json.dumps({"client": "Test Client"}))

        output_file = tmp_path / "test_report.html"
        data_loader = ReportDataLoader("2026-03-25", tmp_path)
        data_loader.load_all()
        builder = HTMLReportBuilder(data_loader)
        builder.generate_html(output_file)

        html_content = output_file.read_text()

        # Verify applyFilters function handles new severities (filterDashboard was renamed)
        assert "function applyFilters" in html_content, "Missing applyFilters function"
        assert '"critical"' in html_content, (
            "applyFilters should handle 'critical' filter"
        )
        assert '"high"' in html_content, "applyFilters should handle 'high' filter"
        assert '"medium"' in html_content, "applyFilters should handle 'medium' filter"
        assert '"low"' in html_content, "applyFilters should handle 'low' filter"
        assert '"clean"' in html_content, "applyFilters should handle 'clean' filter"

        print("✓ filterDashboard function test passed")


class TestDataSeverityAttribute:
    """Test that rows have correct data-severity attribute for Critical/High distinction"""

    def test_data_severity_critical_high(self, tmp_path):
        """Verify data-severity attribute distinguishes Critical from High"""
        test_data = {
            "summary": {
                "total_hosts": 1,
                "total_findings": 2,
                "critical": 1,
                "high": 1,
                "medium": 0,
                "low": 0,
            },
            "host_summary": {
                "Test-Host": {
                    "ip": "192.168.1.1",
                    "environment": "Test",
                    "scans": {"ssl": "finding", "vuln": "finding"},
                    "scans_run": ["ssl", "vuln"],
                    "open_ports": [443],
                }
            },
            "findings": [
                {
                    "id": "F001",
                    "title": "SSL Certificate Expired",
                    "host": "Test-Host",
                    "ip": "192.168.1.1",
                    "port": 443,
                    "severity": "Critical",
                    "scan_type": "ssl",
                    "description": "Test finding",
                    "recommendation": "Test recommendation",
                },
                {
                    "id": "F002",
                    "title": "Weak Diffie-Hellman",
                    "host": "Test-Host",
                    "ip": "192.168.1.1",
                    "port": 443,
                    "severity": "High",
                    "scan_type": "vuln",
                    "description": "Test finding",
                    "recommendation": "Test recommendation",
                },
            ],
        }

        scans_dir = tmp_path / "scans" / "2026-03-25"
        scans_dir.mkdir(parents=True)
        (scans_dir / "findings.json").write_text(json.dumps(test_data))
        (tmp_path / "targets.json").write_text(json.dumps({"client": "Test Client"}))

        output_file = tmp_path / "test_report.html"
        data_loader = ReportDataLoader("2026-03-25", tmp_path)
        data_loader.load_all()
        builder = HTMLReportBuilder(data_loader)
        builder.generate_html(output_file)

        html_content = output_file.read_text()

        # Verify data-severity attributes exist for filtering
        # Should have 'critical' for SSL scan (Critical finding)
        assert 'data-severity="critical"' in html_content, (
            "Missing data-severity='critical' attribute"
        )
        # Should have 'high' for vuln scan (High finding)
        assert 'data-severity="high"' in html_content, (
            "Missing data-severity='high' attribute"
        )

        print("✓ data-severity attribute test passed")


def run_tests():
    """Run all tests"""
    import tempfile
    import shutil

    tests = [
        TestFilterButtons(),
        TestIconColumn(),
        TestSortableHeaders(),
        TestSortTableFunction(),
        TestFilterDashboardFunction(),
        TestDataSeverityAttribute(),
    ]

    passed = 0
    failed = 0

    for test_class in tests:
        for method_name in dir(test_class):
            if method_name.startswith("test_"):
                test_method = getattr(test_class, method_name)
                with tempfile.TemporaryDirectory() as tmp_dir:
                    tmp_path = Path(tmp_dir)
                    try:
                        test_method(tmp_path)
                        passed += 1
                    except AssertionError as e:
                        print(f"✗ {method_name} FAILED: {e}")
                        failed += 1
                    except Exception as e:
                        print(f"✗ {method_name} ERROR: {e}")
                        failed += 1

    print(f"\n{'=' * 50}")
    print(f"Tests: {passed + failed} | Passed: {passed} | Failed: {failed}")

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
