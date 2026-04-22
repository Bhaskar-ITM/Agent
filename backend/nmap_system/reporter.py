#!/usr/bin/env python3
"""
BSOL Automated Penetration Testing System — Reporter
Generates PDF (client) and HTML (engineer) reports from findings.json
"""

import json
import sys
import argparse
import html
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from rich.console import Console

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT

console = Console()

# Color constants
DARK_BLUE = colors.HexColor("#1F3864")
MID_BLUE = colors.HexColor("#2E5FA3")
LIGHT_BLUE = colors.HexColor("#D6E4F7")
CYAN_ACCENT = colors.HexColor("#06B6D4")
RED_BG = colors.HexColor("#FEE2E2")
RED_ACCENT = colors.HexColor("#DC2626")
AMBER_BG = colors.HexColor("#FEF3C7")
AMBER_ACCENT = colors.HexColor("#F59E0B")
GREEN_BG = colors.HexColor("#E2EFDA")
GREEN_ACCENT = colors.HexColor("#10B981")
GREY_BG = colors.HexColor("#F2F2F2")
PURPLE_ACCENT = colors.HexColor("#8B5CF6")

# Scan type display names
SCAN_DISPLAY_NAMES = {
    "ssl": "SSL Cipher Enumeration",
    "brute": "Brute Force Test",
    "dos": "DoS Vulnerability Scan",
    "vuln": "Vulnerability & Exploit Scan",
    "slowloris": "HTTP Slowloris Check",
    "aggressive": "Aggressive Scan",
    "cert": "Certificate Expiry Check",
    "rdp": "RDP Vulnerability Check",
    "headers": "HTTP Security Headers",
    "methods": "HTTP Methods Check",
    "smtp": "SMTP Security Check",
    "ssh": "SSH Security Check",
    "smb": "SMB Security Check",
    "ftp": "FTP Security Check",
    "mysql": "MySQL Security Check",
    "mssql": "MSSQL Security Check",
    "discovery": "Service Discovery",
}

# Scan order for consistent dashboard rendering
SCAN_ORDER = [
    "discovery",
    "ssl",
    "brute",
    "dos",
    "vuln",
    "slowloris",
    "aggressive",
    "cert",
    "rdp",
    "headers",
    "methods",
    "smtp",
    "ssh",
    "smb",
    "ftp",
    "mysql",
    "mssql",
]

# Recommendation templates (used when AI is off)
# Order matters: more specific templates should appear before generic ones
# for proper keyword matching in get_recommendation()
RECOMMENDATION_TEMPLATES = {
    "SSL Certificate Expired": (
        "Renew the SSL certificate immediately. An expired certificate prevents "
        "secure connections and will trigger browser warnings for all users."
    ),
    "SSL Certificate Expiring": (
        "Plan to renew the SSL certificate before expiration. Set up monitoring "
        "to alert when certificates approach their expiry date."
    ),
    "Weak Diffie-Hellman": (
        "Reconfigure the server to use Diffie-Hellman parameters of at least "
        "2048 bits. Disable DHE cipher suites if DH upgrade is not possible."
    ),
    "Missing HTTP Security Headers": (
        "Configure the web server to include the missing HTTP security headers. "
        "These headers protect users from clickjacking, MIME sniffing, and "
        "cross-site scripting attacks."
    ),
    "Dangerous HTTP Methods": (
        "Disable unnecessary HTTP methods on the web server. Only GET, POST, "
        "HEAD and OPTIONS should be permitted for standard web applications."
    ),
    "SMTP Open Relay": (
        "Configure the mail server to reject unauthenticated relay attempts. "
        "Restrict relay to authenticated and authorized senders only."
    ),
    "SMTP STARTTLS": (
        "Enable STARTTLS on the SMTP server to encrypt email transmissions. "
        "This prevents eavesdropping on email communications."
    ),
    "RDP Vulnerability": (
        "Apply the relevant Microsoft security patch immediately. If patching "
        "is not possible, restrict RDP access to known IP addresses only."
    ),
    "HTTP Slowloris": (
        "Configure connection timeout settings on the web server to limit the "
        "impact of slow HTTP attacks. Consider using a reverse proxy."
    ),
    "JMX Console": (
        "Restrict access to the JMX console by enabling authentication and "
        "limiting access to trusted IP addresses only."
    ),
    "Unrecognized Service": (
        "Investigate the unrecognized service on the identified port. Disable "
        "or firewall the service if it is not required for business operations."
    ),
    "Weak SSH": (
        "Reconfigure SSH to disable weak cryptographic algorithms. Use only "
        "modern ciphers such as AES-GCM and ChaCha20."
    ),
    "SMB EternalBlue": (
        "Apply Microsoft security patches immediately and enable SMB signing. "
        "This is a critical remote code execution vulnerability."
    ),
    "SMB Signing": (
        "Enable SMB signing on the server to prevent potential man-in-the-middle "
        "attacks. Consider disabling SMBv1 if still in use."
    ),
    "SMB": (
        "Apply Microsoft security patches and enable SMB signing. Consider "
        "disabling SMBv1 if still in use."
    ),
    "FTP Anonymous": (
        "Disable anonymous FTP access if not required for business operations. "
        "Consider migrating to SFTP or FTPS for secure file transfers."
    ),
    "FTP Bounce": (
        "Disable FTP bounce attack vulnerability by configuring the FTP server "
        "to reject PORT commands that specify a different IP address."
    ),
    "FTP": (
        "Disable anonymous FTP access if not required. Consider migrating to "
        "SFTP or FTPS for secure file transfers."
    ),
    "MySQL Empty Password": (
        "Set a strong password for the MySQL root account immediately. An empty "
        "password allows unrestricted database access."
    ),
    "MySQL": (
        "Set strong passwords for all MySQL accounts. Disable remote root "
        "login and apply the principle of least privilege."
    ),
    "MSSQL Empty Password": (
        "Set a strong password for the MSSQL sa account immediately. An empty "
        "password allows unrestricted database access."
    ),
    "MSSQL": (
        "Set strong passwords for all MSSQL accounts. Apply Windows security "
        "updates and disable unnecessary SQL Server features."
    ),
}


class ReportDataLoader:
    """Loads all data sources needed for report generation"""

    def __init__(self, date_str: str, base_dir: Path):
        self.date_str = date_str
        self.base_dir = base_dir
        self.config: Optional[Dict] = None
        self.findings_data: Optional[Dict] = None
        self.scan_summary: Optional[Dict] = None

    def load_all(self) -> bool:
        """Load all data sources. Returns True if successful."""
        # Load targets.json (config)
        config_file = self.base_dir / "targets.json"
        if not config_file.exists():
            console.print("[bold red]❌ Error:[/bold red] targets.json not found")
            return False

        try:
            with open(config_file) as f:
                self.config = json.load(f)
        except json.JSONDecodeError as e:
            console.print(
                f"[bold red]❌ Error:[/bold red] Invalid JSON in targets.json: {e}"
            )
            return False

        # Load findings.json
        findings_file = self.base_dir / "scans" / self.date_str / "findings.json"
        if not findings_file.exists():
            console.print(
                f"[bold red]❌ Error:[/bold red] findings.json not found at {findings_file}"
            )
            return False

        try:
            with open(findings_file) as f:
                self.findings_data = json.load(f)
        except json.JSONDecodeError as e:
            console.print(
                f"[bold red]❌ Error:[/bold red] Invalid JSON in findings.json: {e}"
            )
            return False

        # Load scan_summary.json (optional)
        scan_summary_file = (
            self.base_dir / "scans" / self.date_str / "scan_summary.json"
        )
        if scan_summary_file.exists():
            try:
                with open(scan_summary_file) as f:
                    self.scan_summary = json.load(f)
            except json.JSONDecodeError:
                console.print(
                    "[yellow]⚠ Warning:[/yellow] Could not parse scan_summary.json"
                )
                self.scan_summary = None

        return True

    def get_recommendation(self, finding: Dict) -> str:
        """
        Get recommendation for a finding (AI-generated or template).
        Uses single-pass lookup through RECOMMENDATION_TEMPLATES dict.
        Order in dict matters: more specific templates appear first.
        """
        # Use AI-generated recommendation if available
        if finding.get("recommendation"):
            return finding["recommendation"]

        # Fall back to template based on title using single-pass dict lookup
        title = finding.get("title", "")
        title_lower = title.lower()

        # Single pass through priority-ordered dict items
        for keyword, template in RECOMMENDATION_TEMPLATES.items():
            if keyword.lower() in title_lower:
                return template

        # Default recommendation
        return (
            "Review and remediate this finding according to the vendor security "
            "advisory and your organization's patching policy."
        )


class PDFReportBuilder:
    """Builds professional PDF report for client delivery"""

    def __init__(self, data_loader: ReportDataLoader):
        self.data_loader = data_loader
        self.config = data_loader.config
        self.findings_data = data_loader.findings_data
        self.scan_summary = data_loader.scan_summary
        self.date_str = data_loader.date_str
        self.styles = getSampleStyleSheet()

    def add_page_header_footer(self, canvas, doc):
        """Add header and footer to PDF pages"""
        canvas.saveState()

        # Header on pages 2+ (skip cover page)
        if doc.page > 1:
            canvas.setFillColor(DARK_BLUE)
            canvas.setFont("Helvetica", 8)
            canvas.drawString(
                0.75 * inch,
                letter[1] - 0.5 * inch,
                f"BSOL Systems  |  {doc.title}  |  Penetration Test Report",
            )
            # Header line
            canvas.setStrokeColor(MID_BLUE)
            canvas.setLineWidth(0.5)
            canvas.line(
                0.75 * inch,
                letter[1] - 0.55 * inch,
                letter[0] - 0.75 * inch,
                letter[1] - 0.55 * inch,
            )

        # Footer on all pages
        canvas.setFillColor(colors.HexColor("#595959"))
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(letter[0] - 0.75 * inch, 0.4 * inch, f"Page {doc.page}")
        canvas.drawString(
            0.75 * inch, 0.4 * inch, "CONFIDENTIAL — BSOL Systems Pvt Ltd"
        )

        canvas.restoreState()

    def build_cover_page(self) -> List:
        """Build PDF cover page elements"""
        elements = []

        title_style = ParagraphStyle(
            "CustomTitle",
            parent=self.styles["Heading1"],
            fontSize=28,
            textColor=DARK_BLUE,
            spaceAfter=30,
            alignment=TA_CENTER,
        )

        client_style = ParagraphStyle(
            "ClientName",
            parent=self.styles["Heading1"],
            fontSize=22,
            textColor=RED_ACCENT,
            spaceAfter=20,
            alignment=TA_CENTER,
        )

        date_style = ParagraphStyle(
            "Date",
            parent=self.styles["Normal"],
            fontSize=12,
            textColor=colors.HexColor("#595959"),
            spaceAfter=40,
            alignment=TA_CENTER,
        )

        client_name = self.config.get("client", "Client")

        elements.append(Spacer(1, 2.0 * inch))
        elements.append(Paragraph("BSOL Systems Pvt Ltd", self.styles["Heading2"]))
        elements.append(Spacer(1, 0.3 * inch))
        elements.append(Paragraph("Penetration Test Report", title_style))
        elements.append(Paragraph(client_name, client_style))
        elements.append(Spacer(1, 0.2 * inch))
        elements.append(Paragraph(f"Release Date: {self.date_str}", date_style))

        notice_style = ParagraphStyle(
            "Notice",
            parent=self.styles["Normal"],
            fontSize=10,
            textColor=colors.darkgrey,
            alignment=TA_CENTER,
            leftIndent=0.5 * inch,
            rightIndent=0.5 * inch,
        )
        elements.append(
            Paragraph(
                "This document contains confidential information from BSOL Systems Pvt Ltd "
                "intended for the private use of the client. Do not copy, disclose, or distribute "
                "without written permission.",
                notice_style,
            )
        )

        elements.append(PageBreak())
        return elements

    def build_executive_summary(self) -> List:
        """Build executive summary elements"""
        elements = []
        summary = self.findings_data.get("summary", {})

        elements.append(Paragraph("Executive Summary", self.styles["Heading1"]))
        elements.append(Spacer(1, 0.3 * inch))

        body_style = ParagraphStyle(
            "Body",
            parent=self.styles["Normal"],
            fontSize=10,
            alignment=TA_JUSTIFY,
            spaceAfter=12,
        )

        # Get summary values FIRST (before if/else)
        total_hosts = summary.get("total_hosts", 0)
        total_findings = summary.get("total_findings", 0)
        critical = summary.get("critical", 0)
        high = summary.get("high", 0)
        medium = summary.get("medium", 0)
        low = summary.get("low", 0)

        # Use AI-generated summary if available
        if self.findings_data.get("executive_summary"):
            summary_text = self.findings_data["executive_summary"]
        else:
            if total_findings == 0:
                summary_text = (
                    f"This report presents the results of the monthly penetration test "
                    f"conducted against {self.config.get('client', 'the client')} infrastructure "
                    f"on {self.date_str}. A total of {total_hosts} hosts were assessed across "
                    f"Production, UAT, and Test environments using multiple scan types. "
                    f"No security findings were identified during this assessment."
                )
            else:
                crit_text = f"{critical} critical, " if critical > 0 else ""
                finding_word = "finding" if total_findings == 1 else "findings"
                summary_text = (
                    f"This report presents the results of the monthly penetration test "
                    f"conducted against {self.config.get('client', 'the client')} infrastructure "
                    f"on {self.date_str}. A total of {total_hosts} hosts were assessed across "
                    f"Production, UAT, and Test environments using multiple scan types including "
                    f"SSL cipher analysis, brute force testing, vulnerability scanning, and "
                    f"denial-of-service checks. "
                    f"The assessment identified {total_findings} security {finding_word}: "
                    f"{crit_text}{high} high severity, {medium} medium severity, and {low} low severity "
                    f"issues requiring attention. "
                    f"Immediate review is recommended for critical and high severity findings."
                )

        elements.append(Paragraph(summary_text, body_style))
        elements.append(Spacer(1, 0.3 * inch))

        # Issue 32: Add notice for unvalidated findings
        findings_list = self.findings_data.get("findings", [])
        unvalidated_count = len(
            [f for f in findings_list if f.get("confirmed") is None]
        )
        if unvalidated_count > 0:
            notice_style = ParagraphStyle(
                "Notice",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.darkgrey,
                spaceAfter=8,
            )
            elements.append(
                Paragraph(
                    f"<b>Note:</b> {unvalidated_count} finding(s) could not be AI-validated and require manual review.",
                    notice_style,
                )
            )
            elements.append(Spacer(1, 0.2 * inch))

        # Summary counts table
        table_data = [
            ["Total Hosts", "Total Findings", "Critical", "High", "Medium", "Low"],
            [
                str(total_hosts),
                str(total_findings),
                str(critical),
                str(high),
                str(medium),
                str(low),
            ],
        ]
        table = Table(table_data, colWidths=[1.0 * inch] * 6)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BLUE),
                    ("TEXTCOLOR", (0, 0), (-1, 0), DARK_BLUE),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    (
                        "BACKGROUND",
                        (2, 1),
                        (2, 1),
                        RED_BG if critical > 0 else colors.white,
                    ),
                    (
                        "BACKGROUND",
                        (3, 1),
                        (3, 1),
                        RED_BG if high > 0 else colors.white,
                    ),
                    (
                        "BACKGROUND",
                        (4, 1),
                        (4, 1),
                        AMBER_BG if medium > 0 else colors.white,
                    ),
                    (
                        "BACKGROUND",
                        (5, 1),
                        (5, 1),
                        GREEN_BG if low > 0 else colors.white,
                    ),
                ]
            )
        )
        elements.append(table)
        elements.append(PageBreak())
        return elements

    def build_scope_methodology(self) -> List:
        """Build scope and methodology section"""
        elements = []

        elements.append(Paragraph("Scope and Methodology", self.styles["Heading1"]))
        elements.append(Spacer(1, 0.3 * inch))

        # Table headers
        table_data = [
            ["Host Name", "IP Address", "Environment", "Ports Found", "Scans Run"]
        ]

        host_summary = self.findings_data.get("host_summary", {})

        for host_name, host_data in host_summary.items():
            # Get ports from discovery or open_ports
            open_ports = host_data.get("open_ports", [])
            ports_str = ", ".join(map(str, open_ports)) if open_ports else "N/A"

            # Get scans that actually ran
            scans_run = host_data.get("scans_run", [])
            scans_str = (
                ", ".join([SCAN_DISPLAY_NAMES.get(s, s) for s in scans_run])
                if scans_run
                else "None"
            )

            table_data.append(
                [
                    host_name,
                    host_data.get("ip", "Unknown"),
                    host_data.get("environment", "Unknown"),
                    ports_str,
                    scans_str,
                ]
            )

        table = Table(
            table_data,
            colWidths=[1.3 * inch, 1.1 * inch, 1.0 * inch, 1.0 * inch, 2.6 * inch],
            style=[
                ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BLUE),
                ("TEXTCOLOR", (0, 0), (-1, 0), DARK_BLUE),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#FAFAFA")],
                ),
            ],
        )

        elements.append(table)
        elements.append(PageBreak())
        return elements

    def build_risk_dashboard(self) -> List:
        """Build risk summary dashboard with only scans that ran"""
        elements = []

        elements.append(Paragraph("Risk Summary Dashboard", self.styles["Heading1"]))
        elements.append(Spacer(1, 0.2 * inch))

        # Table headers
        table_data = [
            ["Environment", "Host", "IP", "Scan Type", "Status", "Finding", "Details"]
        ]
        table_styles = [
            ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), DARK_BLUE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]

        host_summary = self.findings_data.get("host_summary", {})
        findings_list = self.findings_data.get("findings", [])

        row_idx = 1
        for host_name, host_data in sorted(host_summary.items()):
            # Get scans that actually ran for this host
            scans_dict = host_data.get("scans", {})

            for scan_id, scan_status in scans_dict.items():
                # Skip if scan didn't run
                if scan_status is None:
                    continue

                # Determine display values based on status
                if scan_status == "finding":
                    status_text = "VULNERABLE"
                    bg_color = RED_BG
                    # Issue 30: Collect ALL matching finding titles for this scan
                    finding_titles = []
                    finding_descriptions = []
                    for f in findings_list:
                        if (
                            f.get("host") == host_name
                            and f.get("severity") in ["Critical", "High"]
                            and f.get("scan_type", "")
                            == SCAN_DISPLAY_NAMES.get(scan_id, scan_id)
                        ):
                            finding_titles.append(f["title"][:60])
                            finding_descriptions.append(f.get("description", "")[:80])
                    # Fallback: if no scan_type match, just use host+severity match
                    if not finding_titles:
                        for f in findings_list:
                            if f.get("host") == host_name and f.get("severity") in [
                                "Critical",
                                "High",
                            ]:
                                finding_titles.append(f["title"][:60])
                                finding_descriptions.append(
                                    f.get("description", "")[:80]
                                )
                    # Join all titles or show count
                    if len(finding_titles) > 1:
                        finding_title = (
                            f"{finding_titles[0]}... (+{len(finding_titles) - 1} more)"
                        )
                        finding_comment = f"{finding_descriptions[0]}... (+{len(finding_descriptions) - 1} more)"
                    elif finding_titles:
                        finding_title = finding_titles[0]
                        finding_comment = (
                            finding_descriptions[0] if finding_descriptions else ""
                        )
                    else:
                        finding_title = ""
                        finding_comment = ""
                elif scan_status == "warning":
                    status_text = "WARNING"
                    bg_color = AMBER_BG
                    # Issue 30: Collect ALL matching finding titles for this scan
                    finding_titles = []
                    finding_descriptions = []
                    for f in findings_list:
                        if (
                            f.get("host") == host_name
                            and f.get("severity") in ["Medium", "Low"]
                            and f.get("scan_type", "")
                            == SCAN_DISPLAY_NAMES.get(scan_id, scan_id)
                        ):
                            finding_titles.append(f["title"][:60])
                            finding_descriptions.append(f.get("description", "")[:80])
                    # Fallback: if no scan_type match, just use host+severity match
                    if not finding_titles:
                        for f in findings_list:
                            if f.get("host") == host_name and f.get("severity") in [
                                "Medium",
                                "Low",
                            ]:
                                finding_titles.append(f["title"][:60])
                                finding_descriptions.append(
                                    f.get("description", "")[:80]
                                )
                    # Join all titles or show count
                    if len(finding_titles) > 1:
                        finding_title = (
                            f"{finding_titles[0]}... (+{len(finding_titles) - 1} more)"
                        )
                        finding_comment = f"{finding_descriptions[0]}... (+{len(finding_descriptions) - 1} more)"
                    elif finding_titles:
                        finding_title = finding_titles[0]
                        finding_comment = (
                            finding_descriptions[0] if finding_descriptions else ""
                        )
                    else:
                        finding_title = ""
                        finding_comment = ""
                elif scan_status == "clean":
                    status_text = "CLEAN"
                    bg_color = GREEN_BG
                    finding_title = ""
                    finding_comment = ""
                else:
                    continue  # Skip unknown statuses

                table_data.append(
                    [
                        host_data.get("environment", "Unknown"),
                        host_name,
                        host_data.get("ip", "Unknown"),
                        SCAN_DISPLAY_NAMES.get(scan_id, scan_id),
                        status_text,
                        finding_title,
                        finding_comment,
                    ]
                )

                table_styles.append(
                    ("BACKGROUND", (0, row_idx), (-1, row_idx), bg_color)
                )
                row_idx += 1

        table = Table(
            table_data,
            colWidths=[
                0.9 * inch,
                1.0 * inch,
                0.9 * inch,
                1.1 * inch,
                0.7 * inch,
                1.3 * inch,
                1.6 * inch,
            ],
        )
        table.setStyle(TableStyle(table_styles))
        elements.append(table)
        elements.append(PageBreak())
        return elements

    def build_findings_detail(self) -> List:
        """Build detailed findings section (one section per finding)"""
        elements = []
        findings_list = self.findings_data.get("findings", [])

        if not findings_list:
            elements.append(
                Paragraph(
                    "No security findings were identified.", self.styles["Normal"]
                )
            )
            elements.append(PageBreak())
            return elements

        # Severity colors for badges
        severity_colors = {
            "Critical": "#C00000",
            "High": "#C55A11",
            "Medium": "#F0A500",
            "Low": "#1E7145",
        }

        for finding in findings_list:
            # Finding header
            severity = finding.get("severity", "Unknown")
            cve = finding.get("cve")
            severity_color = severity_colors.get(severity, "#666666")

            # Build finding content as a list of elements
            finding_content = []

            # Title with finding ID
            finding_content.append(
                Paragraph(
                    f"Finding {finding.get('id', 'F-UNK')} — {finding.get('title', 'Unknown')}",
                    self.styles["Heading2"],
                )
            )

            # Severity badge with colored text
            cve_text = f" | CVE: {cve}" if cve else ""
            finding_content.append(
                Paragraph(
                    f"<b>Severity:</b> <font color='{severity_color}' size='12'><b>{severity}</b></font>{cve_text}",
                    self.styles["Normal"],
                )
            )

            # AI validated status badge
            ai_status = ""
            if finding.get("ai_validated"):
                if finding.get("false_positive"):
                    ai_status = ' | <font color="#5B9BD5">AI False Positive</font>'
                elif finding.get("confirmed") == True:
                    ai_status = ' | <font color="#1E7145">AI Confirmed</font>'
            elif finding.get("confirmed") is None:
                ai_status = ' | <font color="#999999">Unvalidated</font>'

            finding_content.append(
                Paragraph(
                    f"<b>Host:</b> {finding.get('host', 'Unknown')} ({finding.get('ip', 'Unknown')}:{finding.get('port', 'Unknown')}){ai_status}",
                    self.styles["Normal"],
                )
            )
            finding_content.append(
                Paragraph(
                    f"<b>Service:</b> {finding.get('service', 'N/A')}",
                    self.styles["Normal"],
                )
            )
            finding_content.append(
                Paragraph(
                    f"<b>Environment:</b> {finding.get('environment', 'Unknown')}",
                    self.styles["Normal"],
                )
            )

            finding_content.append(Spacer(1, 0.1 * inch))

            # Description
            finding_content.append(
                Paragraph("<b>Description:</b>", self.styles["Heading3"])
            )
            desc_style = ParagraphStyle(
                "Description",
                parent=self.styles["Normal"],
                fontSize=9,
                alignment=TA_JUSTIFY,
                spaceAfter=8,
            )
            finding_content.append(
                Paragraph(
                    finding.get("description", "No description available."), desc_style
                )
            )

            # Recommendation
            finding_content.append(Spacer(1, 0.1 * inch))
            finding_content.append(
                Paragraph("<b>Recommendation:</b>", self.styles["Heading3"])
            )
            recommendation = self.data_loader.get_recommendation(finding)
            finding_content.append(Paragraph(recommendation, desc_style))

            # Raw Evidence preview (truncated to 5 lines)
            finding_content.append(Spacer(1, 0.1 * inch))
            finding_content.append(
                Paragraph("<b>Raw Evidence:</b>", self.styles["Heading3"])
            )
            raw_evidence = finding.get("raw_evidence", "")
            if raw_evidence:
                lines = raw_evidence.split("\n")
                if len(lines) > 5:
                    preview = (
                        "\n".join(lines[:5]) + "\n... (see HTML report for full output)"
                    )
                else:
                    preview = raw_evidence
                # Escape special characters for PDF
                preview = (
                    preview.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                )
                pre_style = ParagraphStyle(
                    "Preformatted",
                    parent=self.styles["Normal"],
                    fontSize=8,
                    fontName="Courier",
                    textColor=colors.HexColor("#333333"),
                    leftIndent=10,
                    rightIndent=10,
                    spaceAfter=8,
                )
                finding_content.append(Paragraph(preview, pre_style))

            # Wrap content in bordered table
            bordered_table = Table([finding_content], colWidths=[6.5 * inch])
            bordered_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F9F9F9")),
                        ("LEFTPADDING", (0, 0), (-1, 0), 12),
                        ("RIGHTPADDING", (0, 0), (-1, 0), 12),
                        ("TOPPADDING", (0, 0), (-1, 0), 12),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BOX", (0, 0), (-1, 0), 0.5, colors.grey),
                        (
                            "LINEABOVE",
                            (0, 0),
                            (-1, 0),
                            2,
                            colors.HexColor(severity_color),
                        ),
                    ]
                )
            )
            elements.append(KeepTogether([bordered_table, Spacer(1, 12)]))

        # Issue 29: Add false positive section
        false_positives = [f for f in findings_list if f.get("false_positive") == True]
        if false_positives:
            elements.append(
                Paragraph("AI-Flagged False Positives", self.styles["Heading1"])
            )
            elements.append(Spacer(1, 0.2 * inch))
            fp_notice = ParagraphStyle(
                "FPNotice",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.darkgrey,
                spaceAfter=8,
            )
            elements.append(
                Paragraph(
                    "The following findings were flagged by AI analysis as potential false positives "
                    "and should be reviewed manually before remediation efforts are prioritized.",
                    fp_notice,
                )
            )
            elements.append(Spacer(1, 0.2 * inch))

            for fp in false_positives:
                fp_style = ParagraphStyle(
                    "FPItem",
                    parent=self.styles["Normal"],
                    fontSize=9,
                    spaceAfter=6,
                    leftIndent=20,
                )
                fp_reason = fp.get("false_positive_reason", "No reason provided")
                elements.append(
                    Paragraph(
                        f"<b>{fp.get('id', 'F-UNK')}: {fp.get('title', 'Unknown')}</b> on {fp.get('host', 'Unknown')} — {fp_reason}",
                        fp_style,
                    )
                )
            elements.append(Spacer(1, 0.2 * inch))

        elements.append(PageBreak())
        return elements

    def build_appendix(self) -> List:
        """Build appendix with scan coverage summary"""
        elements = []

        elements.append(
            Paragraph("Appendix A — Scan Coverage Summary", self.styles["Heading1"])
        )
        elements.append(Spacer(1, 0.3 * inch))

        # Table headers
        table_data = [["Host", "Scan", "Status", "Skip Reason"]]

        host_summary = self.findings_data.get("host_summary", {})

        # Get skip reasons from scan_summary if available
        skip_reasons = {}
        # Fix: scanner writes 'targets' not 'hosts'
        if self.scan_summary and "targets" in self.scan_summary:
            for host_name, host_data in self.scan_summary.get("targets", {}).items():
                for scan_id, reason in host_data.get("skip_reasons", {}).items():
                    skip_reasons[(host_name, scan_id)] = reason

        # Build table with row colors for RAN/SKIPPED status
        table_styles = [
            ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), DARK_BLUE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]

        row_idx = 1
        for host_name, host_data in sorted(host_summary.items()):
            scans_dict = host_data.get("scans", {})
            scans_run = host_data.get("scans_run", [])

            # Show all scans in SCAN_ORDER
            for scan_id in SCAN_ORDER:
                if scan_id in scans_dict:
                    status = "RAN"
                    skip_reason = ""
                    # Add green background for RAN
                    table_styles.append(
                        ("BACKGROUND", (0, row_idx), (-1, row_idx), GREEN_BG)
                    )
                else:
                    status = "SKIPPED"
                    skip_reason = skip_reasons.get(
                        (host_name, scan_id), "Service not found"
                    )
                    # Add grey background for SKIPPED
                    table_styles.append(
                        ("BACKGROUND", (0, row_idx), (-1, row_idx), GREY_BG)
                    )

                table_data.append(
                    [
                        host_name,
                        SCAN_DISPLAY_NAMES.get(scan_id, scan_id),
                        status,
                        skip_reason,
                    ]
                )
                row_idx += 1

        table = Table(
            table_data,
            colWidths=[1.2 * inch, 2.0 * inch, 1.0 * inch, 2.8 * inch],
            style=table_styles,
        )

        elements.append(table)
        return elements

    def generate_pdf(self, output_file: Path):
        """Generate complete PDF report"""
        doc = SimpleDocTemplate(
            str(output_file),
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=1 * inch,
            bottomMargin=0.75 * inch,
            title=self.config.get("client", "Penetration Test Report"),
        )

        all_elements = []

        # Build all sections
        all_elements += self.build_cover_page()
        all_elements += self.build_executive_summary()
        all_elements += self.build_scope_methodology()
        all_elements += self.build_risk_dashboard()
        all_elements += self.build_findings_detail()
        all_elements += self.build_appendix()

        # Build document with header/footer
        doc.build(
            all_elements,
            onFirstPage=self.add_page_header_footer,
            onLaterPages=self.add_page_header_footer,
        )


class HTMLReportBuilder:
    """Builds self-contained HTML report for internal engineer use"""

    def __init__(self, data_loader: ReportDataLoader):
        self.data_loader = data_loader
        self.config = data_loader.config
        self.findings_data = data_loader.findings_data
        self.scan_summary = data_loader.scan_summary
        self.date_str = data_loader.date_str

    def generate_html(self, output_file: Path):
        """Generate complete self-contained HTML report"""
        host_summary = self.findings_data.get("host_summary", {})
        findings_list = self.findings_data.get("findings", [])
        summary = self.findings_data.get("summary", {})

        # Count unvalidated findings (confirmed=None and not false_positive)
        unvalidated_count = sum(
            1
            for f in findings_list
            if f.get("confirmed") is None and not f.get("false_positive", False)
        )

        # Build unvalidated banner
        unvalidated_banner = ""
        if unvalidated_count > 0:
            unvalidated_banner = f"""<div style="background:#FFF3CD;border:1px solid #FFC107;border-radius:4px;padding:1rem;margin-bottom:1rem;color:#856404">
        <strong>⚠ Notice:</strong> {unvalidated_count} finding(s) could not be AI-validated and require manual review.
    </div>
    """

        # Build all HTML sections
        dashboard_rows = self._build_dashboard_rows(host_summary, findings_list)
        findings_html = self._build_findings_html(findings_list)
        appendix_html = self._build_appendix_html(host_summary)
        scope_rows = self._build_scope_rows(host_summary)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Penetration Test Report - {self.config.get("client", "Client")}</title>
    <style>
        :root {{
            --dark-blue: #1F3864;
            --mid-blue: #2E5FA3;
            --light-blue: #D6E4F7;
            --red-bg: #FFDAD6;
            --amber-bg: #FCE4D6;
            --green-bg: #E2EFDA;
            --grey-bg: #F2F2F2;
            --stat-hosts: #1F3864;
            --stat-critical: #DC2626;
            --stat-high: #EA580C;
            --stat-medium: #F59E0B;
            --stat-low: #10B981;
            --gradient-start: #1F3864;
            --gradient-end: #2E5FA3;
            --accent-cyan: #06B6D4;
            --accent-purple: #8B5CF6;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            margin: 0;
            padding: 0;
            color: #1a1a1a;
            background: linear-gradient(135deg, #f0f4ff 0%, #f8f9fa 50%, #fef5f0 100%);
            min-height: 100vh;
        }}
        header {{
            background: linear-gradient(90deg, var(--gradient-start) 0%, var(--mid-blue) 50%, var(--gradient-end) 100%);
            color: white;
            padding: 0.6rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
            box-shadow: 0 4px 20px rgba(31, 56, 100, 0.3);
        }}
        header .header-left {{ flex: 1; }}
        header h1 {{ margin: 0 0 0.1rem 0; font-size: 1.25rem; }}
        header p {{ margin: 0; opacity: 0.7; font-size: 0.8rem; }}
        .print-button {{
            background: linear-gradient(135deg, rgba(255,255,255,0.15) 0%, rgba(255,255,255,0.05) 100%);
            color: rgba(255,255,255,0.9);
            border: 1px solid rgba(255,255,255,0.25);
            padding: 0.5rem 1rem;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.8rem;
            flex-shrink: 0;
            white-space: nowrap;
            transition: all 0.25s ease;
            backdrop-filter: blur(4px);
        }}
        .print-button:hover {{ 
            background: linear-gradient(135deg, rgba(255,255,255,0.25) 0%, rgba(255,255,255,0.15) 100%);
            border-color: rgba(255,255,255,0.5); 
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }}
        nav {{
            background: linear-gradient(90deg, var(--mid-blue) 0%, var(--accent-cyan) 50%, var(--mid-blue) 100%);
            background-size: 200% 100%;
            padding: 0;
            position: sticky;
            top: 0;
            z-index: 100;
            display: flex;
            justify-content: center;
            height: 45px;
            box-shadow: 0 4px 15px rgba(46, 95, 163, 0.25);
            animation: navShimmer 8s ease infinite;
        }}
        @keyframes navShimmer {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}
        nav a {{
            color: white;
            text-decoration: none;
            padding: 0 1.25rem;
            display: flex;
            align-items: center;
            font-weight: 500;
            font-size: 0.85rem;
            height: 100%;
            border-bottom: 3px solid transparent;
            transition: all 0.2s;
            position: relative;
        }}
        nav a:hover {{ 
            background: rgba(255,255,255,0.15);
            text-shadow: 0 0 10px rgba(255,255,255,0.5);
        }}
        nav a::after {{
            content: '';
            position: absolute;
            bottom: 0;
            left: 50%;
            width: 0;
            height: 2px;
            background: var(--accent-cyan);
            transition: all 0.2s ease;
            transform: translateX(-50%);
        }}
        nav a:hover::after {{ width: 80%; }}
        main {{
            padding: 2rem;
            max-width: 1400px;
            margin: 0 auto;
            min-height: 100vh;
        }}
        section {{
            margin-bottom: 2.5rem;
            background: white;
            border: 1px solid #e8e8e8;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            scroll-margin-top: 60px;
        }}
        section h2 {{
            background: linear-gradient(90deg, #f8fafc 0%, #ffffff 50%, #f0f9ff 100%);
            color: var(--dark-blue);
            padding: 1.25rem 1.75rem;
            margin: 0;
            font-size: 1.25rem;
            font-weight: 700;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: relative;
            overflow: hidden;
        }}
        section h2::before {{
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 4px;
            background: linear-gradient(180deg, var(--accent-cyan) 0%, var(--mid-blue) 100%);
        }}
        section h2::after {{
            content: '▼';
            font-size: 0.75rem;
            transition: transform 0.2s;
            opacity: 0.5;
        }}
        section h2.collapsed::after {{
            transform: rotate(-90deg);
        }}
        section .content {{ padding: 2rem; }}
        
        /* Metric Cards */
        .stats-container {{
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 1rem;
            margin: 1.5rem 0;
        }}
        .stat-box {{
            display: inline-flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 1.25rem 2rem;
            border-radius: 14px;
            background: white;
            border: 1px solid #e8e8e8;
            border-top: 4px solid var(--stat-color);
            box-shadow: 0 4px 15px rgba(0,0,0,0.08), 0 0 0 1px rgba(255,255,255,0.5) inset;
            min-width: 120px;
            transition: transform 0.25s ease, box-shadow 0.25s ease;
        }}
        .stat-box:hover {{ 
            transform: translateY(-4px) scale(1.02); 
            box-shadow: 0 12px 30px rgba(0,0,0,0.15), 0 0 20px rgba(var(--stat-color-rgb), 0.15);
        }}
        .stat-box .count {{
            font-size: 2.4rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--stat-color) 0%, var(--stat-color-light) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1;
        }}
        .stat-box .label {{
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            background: linear-gradient(90deg, #666 0%, #888 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-top: 0.5rem;
        }}
        .stat-hosts  {{ --stat-color: #1F3864; --stat-color-light: #3B69C4; --stat-color-rgb: 31, 56, 100; }}
        .stat-critical {{ --stat-color: #DC2626; --stat-color-light: #F87171; --stat-color-rgb: 220, 38, 38; }}
        .stat-high   {{ --stat-color: #EA580C; --stat-color-light: #FB923C; --stat-color-rgb: 234, 88, 12; }}
        .stat-medium {{ --stat-color: #F59E0B; --stat-color-light: #FCD34D; --stat-color-rgb: 245, 158, 11; }}
        .stat-low    {{ --stat-color: #10B981; --stat-color-light: #34D399; --stat-color-rgb: 16, 185, 129; }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
            table-layout: fixed;
        }}
        th, td {{
            border: 1px solid #eee;
            padding: 0.8rem 1rem;
            text-align: left;
            vertical-align: middle;
            word-wrap: break-word;
        }}
        th {{
            background: linear-gradient(180deg, #f1f5f9 0%, #e2e8f0 100%);
            color: var(--dark-blue);
            font-weight: 700;
            position: sticky;
            top: 45px;
            text-align: center;
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            z-index: 10;
            border-bottom: 2px solid var(--mid-blue);
        }}
        th:first-child, td:first-child {{ text-align: left; width: 10%; }}
        th:nth-child(2), td:nth-child(2) {{ text-align: left; width: 13%; }}
        th:nth-child(3), td:nth-child(3) {{ text-align: center; width: 13%; font-family: monospace; }}
        th:nth-child(4), td:nth-child(4) {{ text-align: left; width: 17%; }}
        th:nth-child(5), td:nth-child(5) {{ text-align: center; width: 13%; }}
        th:nth-child(6), td:nth-child(6) {{ text-align: left; width: 19%; font-weight: 500; }}
        th:nth-child(7), td:nth-child(7) {{ text-align: left; width: 15%; color: #6b7280; font-size: 0.8rem; }}

        .filters {{
            margin-bottom: 1.5rem;
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }}
        .filters button {{
            padding: 0.5rem 1.25rem;
            cursor: pointer;
            border: 1px solid #e5e7eb;
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            color: #4b5563;
            border-radius: 8px;
            font-size: 0.8rem;
            font-weight: 600;
            transition: all 0.25s ease;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }}
        .filters button:hover {{ 
            background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
            border-color: var(--mid-blue);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        .filters button.active {{
            background: linear-gradient(135deg, var(--mid-blue) 0%, var(--accent-cyan) 100%);
            color: white;
            border-color: var(--mid-blue);
            box-shadow: 0 4px 15px rgba(46, 95, 163, 0.3);
        }}
        #search-box, #finding-search {{
            width: 300px;
            padding: 0.7rem 1rem;
            margin-bottom: 1.5rem;
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            font-size: 0.9rem;
            outline: none;
            transition: all 0.25s ease;
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.04);
        }}
        #search-box:focus, #finding-search:focus {{ 
            border-color: var(--mid-blue);
            box-shadow: 0 0 0 3px rgba(46, 95, 163, 0.15), inset 0 2px 4px rgba(0,0,0,0.04);
        }}

        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 10px;
            font-weight: 700;
            color: white;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        .badge:hover {{ transform: scale(1.05); }}
        .badge-critical {{ 
            background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
            box-shadow: 0 2px 10px rgba(220, 38, 38, 0.4);
        }}
        .badge-high {{ 
            background: linear-gradient(135deg, #F97316 0%, #EA580C 100%);
            box-shadow: 0 2px 10px rgba(234, 88, 12, 0.4);
        }}
        .badge-medium {{ 
            background: linear-gradient(135deg, #FBBF24 0%, #F59E0B 100%);
            box-shadow: 0 2px 10px rgba(245, 158, 11, 0.4);
        }}
        .badge-low {{ 
            background: linear-gradient(135deg, #34D399 0%, #10B981 100%);
            box-shadow: 0 2px 10px rgba(16, 185, 129, 0.4);
        }}

        /* Finding Cards Improvements */
        .finding {{
            border-left: 5px solid #e5e7eb;
            margin: 1.5rem 0;
            padding: 1.5rem 2rem;
            background: #fff;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08), 0 0 30px rgba(0,0,0,0.03);
            border: 1px solid #f0f0f0;
            border-left-width: 6px;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        .finding:hover {{
            transform: translateX(4px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.12);
        }}
        .finding h3 {{ 
            margin-top: 0; 
            color: var(--dark-blue); 
            font-size: 1.2rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        .finding h3::before {{
            content: '⚠';
            font-size: 1rem;
        }}
        .finding-critical {{ 
            border-left-color: #DC2626; 
            background: linear-gradient(135deg, #fef2f2 0%, #fff 100%);
        }}
        .finding-critical h3::before {{ content: '🔴'; }}
        .finding-high     {{ 
            border-left-color: #EA580C; 
            background: linear-gradient(135deg, #fff7ed 0%, #fff 100%);
        }}
        .finding-high h3::before {{ content: '🟠'; }}
        .finding-medium   {{ 
            border-left-color: #F59E0B; 
            background: linear-gradient(135deg, #FFFBEB 0%, #fff 100%);
        }}
        .finding-medium h3::before {{ content: '🟡'; }}
        .finding-low      {{ 
            border-left-color: #10B981; 
            background: linear-gradient(135deg, #ECFDF5 0%, #fff 100%);
        }}
        .finding-low h3::before {{ content: '🟢'; }}

        pre-wrapper {{
            position: relative;
            margin-top: 1rem;
        }}
        pre {{
            margin: 0;
            max-height: 400px;
            overflow: auto;
            background: #1e293b;
            color: #cbd5e1;
            padding: 1.25rem;
            font-family: 'JetBrains Mono', 'Fira Code', monospace;
            font-size: 11px;
            line-height: 1.5;
            border-radius: 8px;
        }}
        pre-wrapper::after {{
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 40px;
            background: linear-gradient(transparent, rgba(30, 41, 59, 0.8));
            pointer-events: none;
            border-bottom-left-radius: 8px;
            border-bottom-right-radius: 8px;
        }}

        .collapsible {{
            cursor: pointer;
            padding: 1rem 1.5rem;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            width: 100%;
            text-align: left;
            font-weight: 600;
            font-size: 0.95rem;
            color: var(--dark-blue);
            border-radius: 8px;
            margin-bottom: 0.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .collapsible:hover {{ background: #f1f5f9; }}
        .collapsible::after {{ content: '▼'; font-size: 0.7rem; opacity: 0.5; transition: transform 0.2s; }}
        .collapsible.collapsed::after {{ transform: rotate(-90deg); }}

        #findings-empty, #dashboard-empty {{
            display: none;
            text-align: center;
            padding: 3rem;
            color: #94a3b8;
            font-style: italic;
            background: #f8fafc;
            border-radius: 8px;
            margin: 1rem 0;
        }}

        @media print {{
            * {{ -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}
            .no-print {{ display: none !important; }}
            nav {{ display: none !important; position: static !important; }}
            header {{ position: static !important; }}
            body {{ background: white !important; }}
            main {{ padding: 0.5rem !important; max-width: none !important; }}

            /* Fix stat box gradient text — falls back to solid color for PDF */
            .stat-box .count {{
                -webkit-text-fill-color: var(--stat-color) !important;
                background: none !important;
            }}
            .stat-box .label {{
                -webkit-text-fill-color: #555 !important;
                background: none !important;
            }}

            /* Sections: allow page breaks between sections */
            section {{
                box-shadow: none !important;
                border: 1px solid #ddd !important;
                page-break-inside: auto;
                break-inside: auto;
                margin-bottom: 1rem !important;
            }}

            /* Expand all details elements */
            details {{ display: block !important; }}
            details > * {{ display: block !important; }}
            details > summary {{
                display: block !important;
                page-break-after: avoid;
            }}

            /* Fix pre overflow/height */
            pre {{
                max-height: none !important;
                overflow: visible !important;
                white-space: pre-wrap !important;
                word-break: break-all !important;
                page-break-inside: auto;
                font-size: 9px !important;
                background: #f4f4f4 !important;
                color: #1a1a1a !important;
                border: 1px solid #ddd !important;
            }}

            /* Findings: avoid mid-card breaks */
            .finding {{
                page-break-inside: avoid !important;
                break-inside: avoid !important;
                box-shadow: none !important;
            }}

            /* Table: allow rows to paginate, freeze header per page */
            table {{ page-break-inside: auto; }}
            tr {{ page-break-inside: avoid; break-inside: avoid; }}
            thead {{ display: table-header-group; }}
            th {{ position: static !important; top: auto !important; }}

            /* Always show content (sections may be collapsed) */
            .content {{ display: block !important; }}

            /* Appendix host blocks */
            .appendix-host {{ page-break-inside: auto; break-inside: auto; }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="header-left">
            <h1>Penetration Test Report</h1>
            <p>Client: {self.config.get("client", "Unknown")} | Date: {self.date_str}</p>
        </div>
        <button class="print-button no-print" onclick="window.print()">🖨 Print Report</button>
    </header>

    <nav class="no-print">
        <a href="#summary">Summary</a>
        <a href="#dashboard">Dashboard</a>
        <a href="#findings">Findings</a>
        <a href="#scope">Scope</a>
        <a href="#appendix">Appendix</a>
    </nav>

    <main>
        <!-- Executive Summary -->
        <section id="summary">
            <h2 onclick="toggleSection(this)">📋 Executive Summary</h2>
            <div class="content">
                {self._build_executive_summary_html()}
                <div class="stats-container">
                    {self._build_stat_boxes(summary)}
                </div>
            </div>
        </section>

        <!-- Risk Dashboard -->
        <section id="dashboard">
            <h2 onclick="toggleSection(this)">🔍 Risk Dashboard</h2>
            <div class="content">
                <div class="filters no-print">
                    <button class="active" data-filter="all">All</button>
                    <button data-filter="critical">Critical</button>
                    <button data-filter="high">High</button>
                    <button data-filter="medium">Medium</button>
                    <button data-filter="low">Low</button>
                    <button data-filter="clean">Clean</button>
                </div>
                <input type="text" id="search-box" class="no-print" placeholder="Search hosts or scans...">
                <div id="dashboard-empty">No results match your filters.</div>
                <table id="dashboard-table">
                    <thead>
                        <tr>
                            <th onclick="sortTable(0)">Environment</th>
                            <th onclick="sortTable(1)">Host</th>
                            <th onclick="sortTable(2)">IP</th>
                            <th onclick="sortTable(3)">Scan Type</th>
                            <th onclick="sortTable(4)">Status</th>
                            <th onclick="sortTable(5)">Finding</th>
                            <th onclick="sortTable(6)">Details</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join(dashboard_rows)}
                    </tbody>
                </table>
            </div>
        </section>

        <!-- Findings Detail -->
        <section id="findings">
            <h2 onclick="toggleSection(this)">⚠️ Findings Detail</h2>
            <div class="content">
                <input type="text" id="finding-search" class="no-print" placeholder="Search by title, CVE, or description...">
                <div id="findings-empty">No findings match your search.</div>
                {unvalidated_banner}
                {"".join(findings_html)}
            </div>
        </section>

        <!-- Scope and Methodology -->
        <section id="scope">
            <h2 onclick="toggleSection(this)">🎯 Scope and Methodology</h2>
            <div class="content">
                <table>
                    <thead>
                        <tr>
                            <th>Host Name</th>
                            <th>IP</th>
                            <th>Environment</th>
                            <th>Ports Found</th>
                            <th>Scan Summary</th>
                        </tr>
                    </thead>
                    <tbody>
                        {"".join(scope_rows)}
                    </tbody>
                </table>
            </div>
        </section>

        <!-- Appendix -->
        <section id="appendix">
            <h2 onclick="toggleSection(this)">📄 Appendix — Raw Scan Output</h2>
            <div class="content">
                {"".join(appendix_html)}
            </div>
        </section>
    </main>

    <script>
        // Debounce helper
        let searchDebounce;
        function debounceSearch(callback) {{
            clearTimeout(searchDebounce);
            searchDebounce = setTimeout(callback, 200);
        }}

        // Dashboard filter buttons
        document.querySelectorAll('.filters button').forEach(btn => {{
            btn.addEventListener('click', function() {{
                document.querySelectorAll('.filters button').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                applyFilters();
            }});
        }});

        function sortTable(columnIndex) {{
            const table = document.getElementById('dashboard-table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));

            rows.sort((a, b) => {{
                const aText = a.querySelectorAll('td')[columnIndex].textContent.trim();
                const bText = b.querySelectorAll('td')[columnIndex].textContent.trim();
                return aText.localeCompare(bText, undefined, {{numeric: true, sensitivity: 'base'}});
            }});

            rows.forEach(row => tbody.appendChild(row));
        }}

        function applyFilters() {{
            const activeFilter = document.querySelector('.filters button.active').dataset.filter;
            const search = document.getElementById('search-box').value.toLowerCase();
            const rows = document.querySelectorAll('#dashboard-table tbody tr');
            let visibleCount = 0;

            rows.forEach(row => {{
                const severity = row.dataset.severity;
                const text = row.textContent.toLowerCase();
                const matchesFilter = activeFilter === 'all' || severity === activeFilter;
                const matchesSearch = text.includes(search);

                if (matchesFilter && matchesSearch) {{
                    row.style.display = '';
                    visibleCount++;
                }} else {{
                    row.style.display = 'none';
                }}
            }});

            document.getElementById('dashboard-empty').style.display = visibleCount === 0 ? 'block' : 'none';
            document.getElementById('dashboard-table').style.display = visibleCount === 0 ? 'none' : 'table';
        }}

        function filterFindings() {{
            const search = document.getElementById('finding-search').value.toLowerCase();
            const findings = document.querySelectorAll('.finding');
            let visibleCount = 0;

            findings.forEach(f => {{
                const text = f.textContent.toLowerCase();
                if (text.includes(search)) {{
                    f.style.display = '';
                    visibleCount++;
                }} else {{
                    f.style.display = 'none';
                }}
            }});
            
            document.getElementById('findings-empty').style.display = visibleCount === 0 ? 'block' : 'none';
        }}

        // Update event listeners to use debounce
        document.getElementById('search-box').addEventListener('keyup', () => debounceSearch(applyFilters));
        document.getElementById('finding-search').addEventListener('keyup', () => debounceSearch(filterFindings));

        function toggleSection(header) {{
            const content = header.nextElementSibling;
            if (!content) return;
            const isHidden = content.style.display === 'none' || content.style.display === '';
            // For section h2 elements, the content div starts visible (no inline display:none)
            // so we check computed style too
            const computed = window.getComputedStyle(content).display;
            if (computed === 'none') {{
                content.style.display = 'block';
                header.classList.remove('collapsed');
            }} else {{
                content.style.display = 'none';
                header.classList.add('collapsed');
            }}
        }}

        // Expand everything before printing so no content is hidden in PDF/print
        window.addEventListener('beforeprint', function() {{
            // Show all section content divs
            document.querySelectorAll('section .content').forEach(el => {{
                el.style.display = 'block';
            }});
            // Expand appendix collapsible host blocks
            document.querySelectorAll('.collapsible').forEach(btn => {{
                const next = btn.nextElementSibling;
                if (next) next.style.display = 'block';
                btn.classList.remove('collapsed');
            }});
            // Expand all <details> elements
            document.querySelectorAll('details').forEach(d => {{
                d.setAttribute('open', '');
            }});
            // Show all filtered-out table rows
            document.querySelectorAll('#dashboard-table tbody tr').forEach(r => {{
                r.style.display = '';
            }});
            // Remove section h2 collapsed state
            document.querySelectorAll('section h2.collapsed').forEach(h => {{
                h.classList.remove('collapsed');
            }});
        }});

        // Active Nav Highlight
        const sections = document.querySelectorAll('section[id]');
        const navLinks = document.querySelectorAll('nav a');
        window.addEventListener('scroll', () => {{
            let current = '';
            sections.forEach(s => {{
                if (window.scrollY >= s.offsetTop - 100) current = s.id;
            }});
            navLinks.forEach(a => {{
                a.style.borderBottom = a.getAttribute('href') === '#' + current 
                    ? '3px solid white' : '3px solid transparent';
                a.style.background = a.getAttribute('href') === '#' + current 
                    ? 'rgba(255,255,255,0.1)' : 'transparent';
            }});
        }});
    </script>
</body>
</html>"""

        output_file.write_text(html)

    def _build_dashboard_rows(self, host_summary, findings_list):
        """Build dashboard table rows"""
        rows = []
        for host_name, host_data in host_summary.items():
            scans_dict = host_data.get("scans", {})

            for scan_id, scan_status in scans_dict.items():
                if scan_status == "finding":
                    row_class = "row-finding"
                    # Find actual severity from findings (Critical takes precedence over High)
                    data_severity = "high"
                    for f in findings_list:
                        if (
                            f.get("host") == host_name
                            and f.get("severity") == "Critical"
                            and scan_id in f.get("scan_type", "").lower()
                        ):
                            data_severity = "critical"
                            break

                    status_cell = '<span style="background:#FEE2E2;color:#991B1B;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600">✗ VULNERABLE</span>'
                    # Collect finding titles and descriptions
                    finding_titles = []
                    finding_descs = []
                    for f in findings_list:
                        if f.get("host") == host_name and f.get("severity") in [
                            "Critical",
                            "High",
                        ]:
                            finding_titles.append(f["title"][:40])
                            finding_descs.append(f.get("description", "")[:80])
                    notes = ", ".join(finding_titles)
                    details = finding_descs[0] if finding_descs else ""
                elif scan_status == "warning":
                    row_class = "row-warning"
                    data_severity = "medium"
                    status_cell = '<span style="background:#FEF3C7;color:#92400E;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600">⚠ WARNING</span>'
                    finding_titles = []
                    finding_descs = []
                    for f in findings_list:
                        if f.get("host") == host_name and f.get("severity") in [
                            "Medium",
                            "Low",
                        ]:
                            finding_titles.append(f["title"][:40])
                            finding_descs.append(f.get("description", "")[:80])
                    notes = ", ".join(finding_titles)
                    details = finding_descs[0] if finding_descs else ""
                elif scan_status == "clean":
                    row_class = "row-clean"
                    data_severity = "clean"
                    status_cell = '<span style="background:#D1FAE5;color:#065F46;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600">✓ CLEAN</span>'
                    notes = ""
                    details = ""
                else:
                    continue

                rows.append(f'''<tr class="{row_class}" data-severity="{data_severity}">
                    <td>{host_data.get("environment", "Unknown")}</td>
                    <td>{host_name}</td>
                    <td>{host_data.get("ip", "Unknown")}</td>
                    <td>{SCAN_DISPLAY_NAMES.get(scan_id, scan_id)}</td>
                    <td style="text-align:center">{status_cell}</td>
                    <td title="{notes[:100]}">{notes[:50] if notes else ""}</td>
                    <td>{details}</td>
                </tr>''')

        return rows

    def _build_stat_boxes(self, summary):
        """Build colored stat boxes for summary"""
        html_out = ""
        stats = [
            ("hosts", summary.get("total_hosts", 0), "Total Hosts"),
            ("critical", summary.get("critical", 0), "Critical"),
            ("high", summary.get("high", 0), "High"),
            ("medium", summary.get("medium", 0), "Medium"),
            ("low", summary.get("low", 0), "Low"),
        ]
        for css_class, count, label in stats:
            html_out += f"""<div class="stat-box stat-{css_class}">
                <span class="count">{count}</span>
                <span class="label">{label}</span>
            </div>"""
        return html_out

    def _build_executive_summary_html(self):
        """Build executive summary paragraph"""
        if self.findings_data.get("executive_summary"):
            return f"<p>{self.findings_data['executive_summary']}</p>"

        summary = self.findings_data.get("summary", {})
        total_hosts = summary.get("total_hosts", 0)
        total_findings = summary.get("total_findings", 0)

        if total_findings == 0:
            return f"""<p>This report presents the results of the monthly penetration test
            conducted against {self.config.get("client", "the client")} infrastructure
            on {self.date_str}. A total of {total_hosts} hosts were assessed.
            No security findings were identified.</p>"""

        return f"""<p>This report presents the results of the monthly penetration test
        conducted against {self.config.get("client", "the client")} infrastructure
        on {self.date_str}. A total of {total_hosts} hosts were assessed across
        Production, UAT, and Test environments. The assessment identified
        {total_findings} security findings requiring attention.</p>"""

    def _build_findings_html(self, findings_list):
        """Build findings detail HTML"""
        SEVERITY_BADGE = {
            "Critical": '<span class="badge badge-critical">🔴 CRITICAL</span>',
            "High": '<span class="badge badge-high">🔴 HIGH</span>',
            "Medium": '<span class="badge badge-medium">🟡 MEDIUM</span>',
            "Low": '<span class="badge badge-low">🟢 LOW</span>',
        }

        html_parts = []
        for f in findings_list:
            severity = f.get("severity", "Unknown")
            sev_lower = severity.lower()
            badge = SEVERITY_BADGE.get(
                severity, f'<span class="badge">{severity}</span>'
            )
            cve = f.get("cve")
            cve_text = f" | CVE: {html.escape(str(cve))}" if cve else ""

            # AI validated, false positive, and unvalidated badges
            extra_badges = ""
            if f.get("false_positive"):
                extra_badges += (
                    ' <span class="badge" style="background:#999">False Positive</span>'
                )
                if f.get("false_positive_reason"):
                    extra_badges += f" ({html.escape(str(f['false_positive_reason']))})"
            elif f.get("confirmed") is None:
                extra_badges += ' <span class="badge" style="background:#FFC107;color:#000">Unvalidated</span>'
            elif f.get("ai_validated"):
                extra_badges += ' <span class="badge" style="background:#5B9BD5">AI Validated</span>'

            finding_id = html.escape(str(f.get("id", "unknown")))
            title = html.escape(str(f.get("title", "Unknown")))
            host = html.escape(str(f.get("host", "Unknown")))
            ip = html.escape(str(f.get("ip", "Unknown")))
            port = html.escape(str(f.get("port", "Unknown")))
            service = html.escape(str(f.get("service", "N/A")))
            description = html.escape(
                str(f.get("description", "No description available."))
            )

            # Fix Recommendation: None
            rec = f.get("recommendation") or self.data_loader.get_recommendation(f)
            recommendation = html.escape(str(rec))

            raw_evidence = html.escape(str(f.get("raw_evidence", "N/A")))

            html_parts.append(f'''<div class="finding finding-{sev_lower}" id="{finding_id}">
                <h3>{finding_id}: {title}</h3>
                <p><strong>Severity:</strong> {badge}{cve_text}{extra_badges}</p>
                <p><strong>Host:</strong> {host} ({ip}:{port})</p>
                <p><strong>Service:</strong> {service}</p>
                <p><strong>Description:</strong> {description}</p>
                <p><strong>Recommendation:</strong> {recommendation}</p>
                <details style="margin-top: 1rem">
                    <summary style="cursor:pointer;padding:0.5rem;background:#f0f0f0">Raw Evidence</summary>
                    <pre style="background:#1a1a1a;color:#e0e0e0;padding:1rem;overflow-x:auto;font-size:11px;line-height:1.4">{raw_evidence}</pre>
                </details>
            </div>''')

        return html_parts

    def _build_scope_rows(self, host_summary):
        """Build scope table rows"""
        rows = []
        all_scans = set(SCAN_DISPLAY_NAMES.keys())
        for host_name, host_data in host_summary.items():
            open_ports = host_data.get("open_ports", [])
            ports_str = ", ".join(map(str, open_ports)) if open_ports else "N/A"

            scans_run = host_data.get("scans_run", [])
            scans_run_count = len(scans_run)
            scans_skipped_count = len(all_scans - set(scans_run))

            scans_cell = f'<span style="color:#1E7145;font-weight:600">{scans_run_count} ran</span> / <span style="color:#888">{scans_skipped_count} skipped</span>'

            rows.append(f"""<tr>
                <td>{host_name}</td>
                <td>{host_data.get("ip", "Unknown")}</td>
                <td>{host_data.get("environment", "Unknown")}</td>
                <td>{ports_str}</td>
                <td>{scans_cell}</td>
            </tr>""")

        return rows

    def _build_appendix_html(self, host_summary):
        """Build appendix with raw scan output"""
        html_parts = []
        raw_dir = self.data_loader.base_dir / "scans" / self.date_str / "raw"

        for host_name, host_data in sorted(host_summary.items()):
            host_scans = []
            for scan_id in SCAN_ORDER:
                scan_file = raw_dir / f"{host_name}_{scan_id}.txt"
                if scan_file.exists():
                    try:
                        content = scan_file.read_text(
                            encoding="utf-8", errors="replace"
                        )
                        # Escape HTML
                        content = (
                            content.replace("&", "&amp;")
                            .replace("<", "&lt;")
                            .replace(">", "&gt;")
                        )
                        host_scans.append(f"""<details>
                            <summary style="cursor:pointer;padding:0.5rem;background:#f0f0f0">
                                {SCAN_DISPLAY_NAMES.get(scan_id, scan_id)}
                            </summary>
                            <pre>{content}</pre>
                        </details>""")
                    except Exception:
                        pass

            if host_scans:
                html_parts.append(f"""<div class="appendix-host">
                    <button class="collapsible collapsed" onclick="toggleSection(this)">{host_name}</button>
                    <div class="content" style="display:none;padding:1rem">
                        {"".join(host_scans)}
                    </div>
                </div>""")

        return html_parts


def main():
    """Main entry point for reporter"""
    parser = argparse.ArgumentParser(
        description="BSOL Penetration Testing Reporter — Generates PDF and HTML reports"
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Generate report for specific date (YYYY-MM-DD). Defaults to today.",
    )
    parser.add_argument(
        "--export-pdf",
        action="store_true",
        help="Also export the HTML report to a client-ready PDF using wkhtmltopdf",
    )
    parser.add_argument(
        "--html-only", action="store_true", help="Generate only HTML report"
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path("."),
        help="Base directory for scans folder (default: current directory)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory for reports (default: scans/{date}/reports/)",
    )
    args = parser.parse_args()

    # Determine date
    date_str = args.date or datetime.now().strftime("%Y-%m-%d")

    # Issue 34: Validate --date argument format
    if args.date:
        try:
            datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            console.print(
                "[bold red]Error:[/bold red] Invalid date format. Use YYYY-MM-DD"
            )
            sys.exit(1)

    console.print(f"[bold blue]════════════════════════════════════════[/bold blue]")
    console.print(f"[bold blue]  BSOL Reporter — {date_str}[/bold blue]")
    console.print(f"[bold blue]════════════════════════════════════════[/bold blue]\n")

    # Load all data
    data_loader = ReportDataLoader(date_str, args.base_dir)
    if not data_loader.load_all():
        sys.exit(1)

    # Determine output directory
    output_dir = args.output_dir or (args.base_dir / "scans" / date_str / "reports")

    # Issue 22: Add output directory validation before PDF generation begins
    try:
        output_dir.mkdir(parents=True, exist_ok=True)

        # Validate directory is writable by attempting to create a test file
        test_file = output_dir / ".write_test"
        test_file.touch()
        test_file.unlink()
    except PermissionError:
        console.print(
            f"[bold red]❌ Error:[/bold red] No write permission for output directory: {output_dir}"
        )
        sys.exit(1)
    except OSError as e:
        console.print(
            f"[bold red]❌ Error:[/bold red] Cannot create output directory {output_dir}: {e}"
        )
        sys.exit(1)

    console.print(f"[dim]Output directory validated:[/dim] {output_dir}\n")

    # Generate PDF
    if not args.html_only:
        pdf_file = output_dir / f"report_{date_str}.pdf"
        console.print(f"[bold]Generating PDF report...[/bold]")
        try:
            pdf_builder = PDFReportBuilder(data_loader)
            pdf_builder.generate_pdf(pdf_file)
            console.print(f"  [green]✓ PDF saved:[/green] {pdf_file}")
        except Exception as e:
            console.print(f"  [bold red]❌ Error generating PDF:[/bold red] {e}")
            if not args.pdf_only:
                console.print("  Continuing with HTML generation...")
            else:
                sys.exit(1)

    # Generate HTML
    if not args.pdf_only:
        html_file = output_dir / f"report_{date_str}.html"
        console.print(f"[bold]Generating HTML report...[/bold]")
        try:
            html_builder = HTMLReportBuilder(data_loader)
            html_builder.generate_html(html_file)
            console.print(f"  [green]✓ HTML saved:[/green] {html_file}")
        except Exception as e:
            console.print(f"  [bold red]❌ Error generating HTML:[/bold red] {e}")
            sys.exit(1)

    console.print(f"\n[green]✓ Report generation complete![/green]")
    console.print(f"  Output directory: {output_dir}")

    # Optional: export HTML → client PDF via wkhtmltopdf
    if getattr(args, "export_pdf", False) and not args.pdf_only:
        html_file = output_dir / f"report_{date_str}.html"
        client_pdf = output_dir / f"report_{date_str}_client.pdf"
        wkhtmltopdf_bin = shutil.which("wkhtmltopdf")
        if not wkhtmltopdf_bin:
            console.print(
                "[yellow]⚠ wkhtmltopdf not found — skipping HTML→PDF export.[/yellow]"
            )
        elif not html_file.exists():
            console.print(
                "[yellow]⚠ HTML report not found — skipping HTML→PDF export.[/yellow]"
            )
        else:
            console.print(f"[bold]Exporting HTML → client PDF...[/bold]")
            try:
                result = subprocess.run(
                    [
                        wkhtmltopdf_bin,
                        "--page-size", "A4",
                        "--margin-top", "15mm",
                        "--margin-bottom", "15mm",
                        "--margin-left", "12mm",
                        "--margin-right", "12mm",
                        "--enable-local-file-access",
                        "--javascript-delay", "800",
                        "--no-stop-slow-scripts",
                        "--load-error-handling", "ignore",
                        "--title", f"Penetration Test Report {date_str}",
                        str(html_file),
                        str(client_pdf),
                    ],
                    capture_output=True,
                    text=True,
                )
                if client_pdf.exists():
                    console.print(
                        f"  [green]✓ Client PDF saved:[/green] {client_pdf}"
                    )
                else:
                    console.print(
                        f"  [bold red]❌ PDF export failed:[/bold red] {result.stderr[:200]}"
                    )
            except Exception as e:
                console.print(f"  [bold red]❌ PDF export error:[/bold red] {e}")


if __name__ == "__main__":
    main()