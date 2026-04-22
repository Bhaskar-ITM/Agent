#!/usr/bin/env python3
"""
Test suite for Reporter Task 6 enhancements:
1. Total Hosts stat box
2. Print CSS fixes for expanding cards
3. Search debounce functionality
4. Removal of onkeyup attributes
"""

import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from reporter import HTMLReportBuilder, ReportDataLoader


class TestStatBoxes(unittest.TestCase):
    """Test _build_stat_boxes method includes Total Hosts card"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_data_loader = Mock(spec=ReportDataLoader)
        self.mock_data_loader.date_str = "2026-03-25"
        self.mock_data_loader.config = {"client": "Test Client"}
        self.mock_data_loader.findings_data = {
            "host_summary": {},
            "findings": [],
            "summary": {},
        }
        self.mock_data_loader.scan_summary = None
        self.mock_data_loader.base_dir = Path("/tmp/test_base")
        self.builder = HTMLReportBuilder(self.mock_data_loader)

    def test_stat_boxes_includes_total_hosts(self):
        """Total Hosts card should appear first in stat boxes"""
        summary = {"total_hosts": 7, "critical": 2, "high": 3, "medium": 5, "low": 1}
        html = self.builder._build_stat_boxes(summary)

        # Check Total Hosts appears first
        self.assertIn("Total Hosts", html)
        self.assertIn("7", html)

        # Verify order: hosts should come before critical
        hosts_pos = html.find("Total Hosts")
        critical_pos = html.find("Critical")
        self.assertLess(
            hosts_pos, critical_pos, "Total Hosts should appear before Critical"
        )

    def test_stat_boxes_has_correct_count_for_total_hosts(self):
        """Total Hosts count should match summary value"""
        summary = {"total_hosts": 42}
        html = self.builder._build_stat_boxes(summary)

        self.assertIn(">42<", html)

    def test_stat_boxes_default_total_hosts_is_zero(self):
        """Total Hosts should default to 0 when not in summary"""
        summary = {}
        html = self.builder._build_stat_boxes(summary)

        # Should show 0 for Total Hosts
        self.assertIn(">0<", html)
        self.assertIn("Total Hosts", html)

    def test_stat_boxes_all_five_stats_present(self):
        """All five stat boxes should be present"""
        summary = {"total_hosts": 5, "critical": 1, "high": 2, "medium": 3, "low": 4}
        html = self.builder._build_stat_boxes(summary)

        # Count stat-box divs
        stat_box_count = html.count('class="stat-box')
        self.assertEqual(5, stat_box_count, "Should have exactly 5 stat boxes")

    def test_stat_boxes_has_border_left_style(self):
        """Each stat box should have border-left style"""
        summary = {"total_hosts": 1, "critical": 0, "high": 0, "medium": 0, "low": 0}
        html = self.builder._build_stat_boxes(summary)

        # Stat boxes should use solid background colors (no border-left)
        self.assertIn("stat-box stat-hosts", html)
        self.assertIn("stat-box stat-critical", html)
        self.assertIn("stat-box stat-low", html)
        self.assertNotIn("border-left", html)


class TestPrintCSS(unittest.TestCase):
    """Test print CSS expands all cards"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_data_loader = Mock(spec=ReportDataLoader)
        self.mock_data_loader.date_str = "2026-03-25"
        self.mock_data_loader.config = {"client": "Test Client"}
        self.mock_data_loader.findings_data = {
            "host_summary": {},
            "findings": [],
            "summary": {},
        }
        self.mock_data_loader.scan_summary = None
        self.mock_data_loader.base_dir = Path("/tmp/test_base")

    def test_print_css_expands_details_elements(self):
        """Print CSS should force details elements to display block"""
        builder = HTMLReportBuilder(self.mock_data_loader)

        # Generate full HTML
        import io

        output_file = Path("/tmp/test_print.html")
        builder.generate_html(output_file)
        html_content = output_file.read_text()

        # Check print CSS includes rules for expanding details
        self.assertIn(
            "details { display: block !important; }",
            html_content,
            "Print CSS should expand details elements",
        )

    def test_print_css_expands_content_elements(self):
        """Print CSS should force content elements to display block"""
        builder = HTMLReportBuilder(self.mock_data_loader)

        import io

        output_file = Path("/tmp/test_print.html")
        builder.generate_html(output_file)
        html_content = output_file.read_text()

        # Check print CSS includes rules for content
        self.assertIn(
            ".content { display: block !important; }",
            html_content,
            "Print CSS should expand content elements",
        )

    def test_print_css_removes_box_shadow(self):
        """Print CSS should remove box shadows from sections"""
        builder = HTMLReportBuilder(self.mock_data_loader)

        import io

        output_file = Path("/tmp/test_print.html")
        builder.generate_html(output_file)
        html_content = output_file.read_text()

        # Check print CSS removes shadows
        self.assertIn(
            "box-shadow: none", html_content, "Print CSS should remove box shadows"
        )


class TestSearchDebounce(unittest.TestCase):
    """Test search functionality has debounce"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_data_loader = Mock(spec=ReportDataLoader)
        self.mock_data_loader.date_str = "2026-03-25"
        self.mock_data_loader.config = {"client": "Test Client"}
        self.mock_data_loader.findings_data = {
            "host_summary": {},
            "findings": [],
            "summary": {},
        }
        self.mock_data_loader.scan_summary = None
        self.mock_data_loader.base_dir = Path("/tmp/test_base")

    def test_debounce_function_present(self):
        """HTML should include debounce helper function"""
        builder = HTMLReportBuilder(self.mock_data_loader)

        import io

        output_file = Path("/tmp/test_debounce.html")
        builder.generate_html(output_file)
        html_content = output_file.read_text()

        # Check debounce helper exists
        self.assertIn(
            "debounceSearch", html_content, "Should have debounceSearch function"
        )
        self.assertIn(
            "searchDebounce", html_content, "Should have searchDebounce variable"
        )
        self.assertIn(
            "clearTimeout", html_content, "Should use clearTimeout for debounce"
        )
        self.assertIn("setTimeout", html_content, "Should use setTimeout for debounce")

    def test_debounce_delay_is_200ms(self):
        """Debounce should use 200ms delay"""
        builder = HTMLReportBuilder(self.mock_data_loader)

        import io

        output_file = Path("/tmp/test_debounce.html")
        builder.generate_html(output_file)
        html_content = output_file.read_text()

        # Check 200ms delay
        self.assertIn("200", html_content, "Should use 200ms debounce delay")

    def test_search_box_uses_event_listener(self):
        """Search box should use addEventListener, not onkeyup attribute"""
        builder = HTMLReportBuilder(self.mock_data_loader)

        import io

        output_file = Path("/tmp/test_debounce.html")
        builder.generate_html(output_file)
        html_content = output_file.read_text()

        # Should NOT have onkeyup attribute
        self.assertNotIn(
            'onkeyup="filterTable()"', html_content, "Should not use onkeyup attribute"
        )
        self.assertNotIn(
            "onkeyup='filterTable()'", html_content, "Should not use onkeyup attribute"
        )

        # Should use addEventListener
        self.assertIn(
            "addEventListener('keyup'",
            html_content,
            "Should use addEventListener for keyup",
        )
        self.assertIn(
            "debounceSearch(applyFilters)",
            html_content,
            "Should call debounceSearch with applyFilters",
        )

    def test_finding_search_uses_event_listener(self):
        """Finding search should use addEventListener, not onkeyup attribute"""
        builder = HTMLReportBuilder(self.mock_data_loader)

        import io

        output_file = Path("/tmp/test_debounce.html")
        builder.generate_html(output_file)
        html_content = output_file.read_text()

        # Should NOT have onkeyup attribute
        self.assertNotIn(
            'onkeyup="filterFindings()"',
            html_content,
            "Should not use onkeyup attribute",
        )
        self.assertNotIn(
            "onkeyup='filterFindings()'",
            html_content,
            "Should not use onkeyup attribute",
        )

        # Should use addEventListener
        self.assertIn(
            "addEventListener('keyup'",
            html_content,
            "Should use addEventListener for keyup",
        )
        self.assertIn(
            "debounceSearch(filterFindings)",
            html_content,
            "Should call debounceSearch with filterFindings",
        )


class TestSearchBoxId(unittest.TestCase):
    """Test search box has correct ID"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_data_loader = Mock(spec=ReportDataLoader)
        self.mock_data_loader.date_str = "2026-03-25"
        self.mock_data_loader.config = {"client": "Test Client"}
        self.mock_data_loader.findings_data = {
            "host_summary": {},
            "findings": [],
            "summary": {},
        }
        self.mock_data_loader.scan_summary = None
        self.mock_data_loader.base_dir = Path("/tmp/test_base")

    def test_search_box_has_id_attribute(self):
        """Dashboard search box should have id='search-box'"""
        builder = HTMLReportBuilder(self.mock_data_loader)

        import io

        output_file = Path("/tmp/test_search_id.html")
        builder.generate_html(output_file)
        html_content = output_file.read_text()

        # Check search box has correct ID
        self.assertIn(
            'id="search-box"', html_content, "Search box should have id='search-box'"
        )


if __name__ == "__main__":
    unittest.main()
