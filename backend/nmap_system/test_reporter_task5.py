#!/usr/bin/env python3
"""
Test suite for Reporter Task 5: Appendix RAN/SKIPPED Colors + Fix Key Bug

Tests:
1. scan_summary key is 'targets' not 'hosts'
2. RAN rows have green background (#E2EFDA)
3. SKIPPED rows have grey background (#F2F2F2)
4. Skip reasons are displayed when available
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from reporter import PDFReportBuilder, SCAN_ORDER


class TestBuildAppendixTask5(unittest.TestCase):
    """Test cases for Task 5 appendix enhancements"""

    def setUp(self):
        """Set up test fixtures"""
        # Create mock data loader
        self.mock_data_loader = MagicMock()
        self.mock_data_loader.config = {'client': 'Test Client'}
        self.mock_data_loader.findings_data = {
            'host_summary': {
                'host1.example.com': {
                    'ip': '192.168.1.1',
                    'scans': {
                        'ssl': {'status': 'completed'},
                        'vuln': {'status': 'completed'},
                    },
                    'scans_run': ['ssl', 'vuln']
                },
                'host2.example.com': {
                    'ip': '192.168.1.2',
                    'scans': {
                        'ssl': {'status': 'completed'},
                    },
                    'scans_run': ['ssl']
                }
            }
        }
        # Scanner writes 'targets' not 'hosts'
        self.mock_data_loader.scan_summary = {
            'targets': {
                'host2.example.com': {
                    'skip_reasons': {
                        'vuln': 'Service not found (port 80 closed)',
                        'dos': 'Port 80 not open'
                    }
                }
            }
        }
        self.mock_data_loader.date_str = '2026-03-25'

        self.builder = PDFReportBuilder(self.mock_data_loader)

    def test_scan_summary_uses_targets_key(self):
        """Test that build_appendix reads 'targets' key from scan_summary"""
        # Call build_appendix
        elements = self.builder.build_appendix()
        
        # Verify elements were created
        self.assertTrue(len(elements) > 0)
        
        # The method should not raise KeyError for 'hosts'
        # and should successfully process 'targets' data
        # Elements: [Paragraph, Spacer, Table]
        table = elements[2]  # Third element should be the table
        
        # Verify table has data rows (header + at least some scan rows)
        # Use _cellvalues for data access
        self.assertGreater(len(table._cellvalues), 1, "Table should have header and data rows")

    def test_ran_rows_have_green_background(self):
        """Test that RAN rows have green background color (#E2EFDA)"""
        elements = self.builder.build_appendix()
        table = elements[2]  # Third element is the table
        
        # Extract table background styles from _bkgrndcmds
        bg_cmds = table._bkgrndcmds
        
        # Should have green background for RAN rows
        green_found = False
        for cmd in bg_cmds:
            # cmd format: ('BACKGROUND', (col1, row1), (col2, row2), color)
            if len(cmd) >= 4:
                color = cmd[3]
                # Check if it's the green color (#E2EFDA) using hexval()
                if hasattr(color, 'hexval'):
                    hex_val = color.hexval()  # Returns string like '0xe2efda'
                    # '0xe2efda' is the green color
                    if hex_val == '0xe2efda':
                        green_found = True
                        break
        
        self.assertTrue(green_found, "RAN rows should have green background (#E2EFDA)")

    def test_skipped_rows_have_grey_background(self):
        """Test that SKIPPED rows have grey background color (#F2F2F2)"""
        elements = self.builder.build_appendix()
        table = elements[2]  # Third element is the table
        
        # Extract table background styles from _bkgrndcmds
        bg_cmds = table._bkgrndcmds
        
        # Should have grey background for SKIPPED rows
        grey_found = False
        for cmd in bg_cmds:
            if len(cmd) >= 4:
                color = cmd[3]
                # Use hexval() to get the hex value (returns string like '0xf2f2f2')
                if hasattr(color, 'hexval'):
                    hex_val = color.hexval()
                    # '0xf2f2f2' is the grey color
                    if hex_val == '0xf2f2f2':
                        grey_found = True
                        break
        
        self.assertTrue(grey_found, "SKIPPED rows should have grey background (#F2F2F2)")

    def test_skip_reasons_displayed(self):
        """Test that skip reasons are displayed for SKIPPED scans"""
        elements = self.builder.build_appendix()
        table = elements[2]  # Third element is the table
        
        # Table data format: [Host, Scan, Status, Skip Reason]
        data = table._cellvalues
        
        # Find rows for host2.example.com (which has skip reasons)
        skip_reason_found = False
        for row in data[1:]:  # Skip header
            if len(row) >= 4:
                host = row[0]
                status = row[2]
                skip_reason = row[3]
                
                if host == 'host2.example.com' and status == 'SKIPPED':
                    if skip_reason and skip_reason != 'Service not found':
                        skip_reason_found = True
                        break
        
        self.assertTrue(skip_reason_found, "Skip reasons from scan_summary should be displayed")


if __name__ == '__main__':
    unittest.main()
