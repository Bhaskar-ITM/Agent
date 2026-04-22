#!/usr/bin/env python3
"""
BSOL Penetration Testing AI Agent
Validates findings using local Ollama model
"""

import json
import re
import sys
import argparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import requests
from rich.console import Console

console = Console()


def check_ollama_running():
    """Check if Ollama is running"""
    try:
        requests.get("http://localhost:11434", timeout=3)
        return True
    except requests.exceptions.RequestException:
        return False


def call_ollama(prompt, model="mistral", max_attempts=2, base_delay=1.0):
    """
    Call Ollama API with retry and exponential backoff.

    Args:
        prompt: The prompt to send to Ollama
        model: The model to use (default: mistral)
        max_attempts: Total number of attempts (default: 2 = 1 initial + 1 retry)
        base_delay: Base delay in seconds for exponential backoff (default: 1.0)

    Returns:
        The response text or None on failure
    """
    last_error = None

    for attempt in range(max_attempts):
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=120
            )

            # Raise exception for non-2xx status codes
            response.raise_for_status()

            return response.json()["response"]

        except requests.exceptions.HTTPError as e:
            last_error = e
            console.print(f"[red]Ollama HTTP error (attempt {attempt + 1}/{max_attempts}): Status {response.status_code}[/red]")
        except requests.exceptions.RequestException as e:
            last_error = e
            console.print(f"[red]Ollama request error (attempt {attempt + 1}/{max_attempts}): {e}[/red]")
        except (KeyError, json.JSONDecodeError) as e:
            last_error = e
            console.print(f"[red]Ollama response parse error (attempt {attempt + 1}/{max_attempts}): {e}[/red]")

        # Exponential backoff before retry (not after last attempt)
        if attempt < max_attempts - 1:
            delay = base_delay * (2 ** attempt)
            console.print(f"[yellow]Retrying in {delay:.1f} seconds...[/yellow]")
            time.sleep(delay)

    console.print(f"[red]Ollama call failed after {max_attempts} attempts: {last_error}[/red]")
    return None


def parse_json_response(response_text):
    """Parse JSON from Ollama response, handling markdown code fences"""
    if not response_text:
        return None
    
    text = response_text.strip()
    if text.startswith('```'):
        lines = text.split('\n')
        text = '\n'.join(lines[1:-1]) if lines[-1].strip() == '```' else '\n'.join(lines[1:])
    
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        match = re.search(r'\{[^{}]+\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return None


def build_executive_summary_prompt(findings_data):
    """Build prompt for AI executive summary generation"""
    findings = findings_data['findings']
    summary = findings_data['summary']
    hosts = list(findings_data['host_summary'].keys())
    confirmed = [f for f in findings if f.get('confirmed') == True]

    confirmed_text = '\n'.join([
        f"- {f['title']} ({f['severity']}) on {f['host']}"
        for f in confirmed
    ]) if confirmed else "None"

    return f"""You are a senior penetration testing expert writing an executive summary.

Assessment details:
- Client: {findings_data['client']}
- Date: {findings_data['scan_date']}
- Hosts tested: {', '.join(hosts)}
- Total findings: {summary['total_findings']}
- Confirmed: {len(confirmed)}
- High: {summary['high']} | Medium: {summary['medium']} | Low: {summary['low']}

Confirmed findings:
{confirmed_text}

Write an executive summary for a non-technical manager with this exact structure:

Paragraph 1: Overall security posture in plain English (2 sentences)
Paragraph 2: Most critical findings summary (1-2 sentences, no CVE numbers, use plain names like "an expired SSL certificate" not "CVE-2015-4000")
Paragraph 3: Recommended immediate actions (1-2 sentences)

Requirements:
- Total: under 120 words
- Tone: professional, suitable for a non-technical manager
- No bullet points, no headers, plain paragraph text only
- Respond with only the paragraph text (3 paragraphs separated by blank lines)
"""


# Keyword-based context templates for AI validation prompts
# Each key is a tuple of keywords that must ALL appear in the title (case-insensitive)
FINDING_CONTEXT_TEMPLATES = {
    ('ssh', 'algorithm'): (
        "\nNote: This is an SSH weak algorithm finding. "
        "Consider if the algorithms listed are genuinely weak by modern standards.\n"
    ),
    ('ssh', 'weak'): (
        "\nNote: This is an SSH weak algorithm finding. "
        "Consider if the algorithms listed are genuinely weak by modern standards.\n"
    ),
    ('smb', 'eternalblue'): (
        "\nNote: This is an SMB EternalBlue vulnerability finding. "
        "This is a critical RCE vulnerability (CVE-2017-0144). "
        "Verify the VULNERABLE status is genuine.\n"
    ),
    ('ftp', 'anonymous'): (
        "\nNote: This is an FTP anonymous login finding. "
        "Consider if anonymous FTP is intentionally configured or a misconfiguration.\n"
    ),
    ('mysql', 'empty password'): (
        "\nNote: This is a database empty password finding. "
        "This is a critical authentication bypass. "
        "Verify the finding is from a real database service.\n"
    ),
    ('mssql', 'empty password'): (
        "\nNote: This is a database empty password finding. "
        "This is a critical authentication bypass. "
        "Verify the finding is from a real database service.\n"
    ),
    ('smb', 'signing'): (
        "\nNote: This is an SMB signing not required finding. "
        "This allows potential MITM attacks but is not as severe as EternalBlue.\n"
    ),
}


def build_validation_prompt(finding):
    """Build prompt for validating a finding"""
    title_lower = finding['title'].lower()
    finding_type_context = ""

    for keywords, context in FINDING_CONTEXT_TEMPLATES.items():
        if all(k in title_lower for k in keywords):
            finding_type_context = context
            break
    
    return f"""You are a senior penetration testing expert reviewing a security finding.

Finding: {finding['title']}
CVE: {finding.get('cve', 'N/A')}
Host: {finding['host']} ({finding['ip']})
Port: {finding.get('port', 'unknown')}
Environment: {finding['environment']}
Severity: {finding['severity']}
{finding_type_context}
Evidence:
{finding['raw_evidence']}

Is this a real vulnerability or false positive? Respond in JSON format only:
{{"confirmed": true/false, "false_positive": true/false, "false_positive_reason": "explanation or null", "confidence": "high/medium/low"}}
"""


def build_recommendation_prompt(finding):
    """Build prompt for remediation recommendation"""
    return f"""You are a senior penetration testing expert writing remediation recommendations.

Finding: {finding['title']}
CVE: {finding.get('cve', 'N/A')}
Host: {finding['host']}
Evidence: {finding['raw_evidence']}

Write a clear, specific remediation recommendation (max 4 sentences). Be specific to the technology. Respond with only the recommendation text.
"""


def validate_single_finding(finding, model):
    """
    Validate a single finding using Ollama.
    Designed to be called from ThreadPoolExecutor.
    Mutates the finding dict in-place; returns None.
    """
    title = finding.get('title', '')

    # Skip unknown service findings
    if title.startswith('Unrecognized Service on Port'):
        finding['confirmed'] = True
        finding['false_positive'] = False
        finding['ai_validated'] = True
        return

    validation_response = call_ollama(build_validation_prompt(finding), model)
    if validation_response:
        validation = parse_json_response(validation_response)
        if validation:
            finding['confirmed'] = validation.get('confirmed')
            finding['false_positive'] = validation.get('false_positive')
            finding['false_positive_reason'] = validation.get('false_positive_reason')
            finding['ai_validated'] = True

            # Handle confirmed=None explicitly
            if validation.get('confirmed') is None:
                console.print(f"  [yellow]⚠ Warning:[/yellow] AI returned confirmed=None for '{title}' on {finding['host']}")
            elif finding['confirmed'] is True:
                # Generate recommendation for confirmed findings
                recommendation = call_ollama(build_recommendation_prompt(finding), model)
                if recommendation:
                    finding['recommendation'] = recommendation

            # Ensure false_positive_reason is set when false_positive=true
            if finding.get('false_positive') and not finding.get('false_positive_reason'):
                finding['false_positive_reason'] = "Flagged as false positive by AI analysis — manual confirmation recommended"
        else:
            console.print(f"[yellow]  Could not parse AI response for '{title}'[/yellow]")
    else:
        console.print(f"[yellow]  Ollama call failed for '{title}'[/yellow]")


def run_ai_agent(config, findings_data, date_str):
    """Run AI validation on all findings using ThreadPoolExecutor for concurrency"""
    model = config.get('ai_model', 'mistral')

    # Issue 5: Add warning log when ai_model defaults to "mistral"
    if not config.get('ai_model'):
        console.print("[yellow]⚠ Warning:[/yellow] ai_model not specified in targets.json, defaulting to 'mistral'")

    findings = findings_data['findings']
    console.print(f"[bold]Running AI agent on {len(findings)} findings with {model} model...[/bold]")

    # Issue 6: Use ThreadPoolExecutor with limit of 3 workers for concurrent Ollama calls
    # Rich's Console is thread-safe by default, no lock needed

    with ThreadPoolExecutor(max_workers=3) as executor:
        # Submit all validation tasks
        future_to_finding = {
            executor.submit(validate_single_finding, finding, model): finding
            for finding in findings
        }

        # Collect results as they complete
        for future in as_completed(future_to_finding):
            finding = future_to_finding[future]
            try:
                future.result()  # finding already mutated in-place
                console.print(f"  Validated: {finding['title']} on {finding['host']}")
            except Exception as e:
                console.print(f"[red]  Error validating {finding['title']}: {e}[/red]")

    # Issue 4: Fix ai_confirmed summary count - use explicit == True check
    findings_data['summary']['ai_confirmed'] = len([
        f for f in findings_data['findings'] if f.get('confirmed') == True
    ])
    findings_data['summary']['ai_false_positives'] = len([
        f for f in findings_data['findings'] if f.get('false_positive') == True
    ])

    # Generate executive summary
    console.print("  Generating executive summary...")
    executive_summary = call_ollama(build_executive_summary_prompt(findings_data), model)
    if executive_summary:
        findings_data['executive_summary'] = executive_summary.strip()
        console.print("  Executive summary generated.")
    else:
        findings_data['executive_summary'] = None
        console.print("[yellow]  Could not generate executive summary[/yellow]")

    # Save updated findings
    output_file = Path(f"scans/{date_str}/findings.json")
    with open(output_file, 'w') as f:
        json.dump(findings_data, f, indent=2)

    console.print(f"[green]✅ AI agent complete. findings.json updated.[/green]")


def main():
    parser = argparse.ArgumentParser(description='BSOL Penetration Testing AI Agent')
    parser.add_argument('--date', type=str, help='Process specific date')
    args = parser.parse_args()
    
    config_file = Path('targets.json')
    if not config_file.exists():
        console.print("[bold red]❌ Error:[/bold red] targets.json not found.")
        sys.exit(1)
    
    with open(config_file) as f:
        config = json.load(f)
    
    if not config.get('ai_agent', False):
        console.print("[yellow]AI agent disabled in targets.json. Skipping.[/yellow]")
        sys.exit(0)
    
    if not check_ollama_running():
        console.print("[bold red]❌ Error:[/bold red] Ollama is not running. Start with: ollama serve")
        sys.exit(1)

    date_str = args.date or datetime.now().strftime('%Y-%m-%d')

    # Issue 34: Validate --date argument format
    if args.date:
        try:
            datetime.strptime(args.date, '%Y-%m-%d')
        except ValueError:
            console.print("[bold red]Error:[/bold red] Invalid date format. Use YYYY-MM-DD")
            sys.exit(1)

    findings_file = Path(f"scans/{date_str}/findings.json")
    
    if not findings_file.exists():
        console.print(f"[bold red]❌ Error:[/bold red] findings.json not found: {findings_file}")
        sys.exit(1)
    
    with open(findings_file) as f:
        findings_data = json.load(f)
    
    if not findings_data['findings']:
        console.print("No findings to validate.")
        sys.exit(0)
    
    console.print(f"[bold]Running AI agent on {len(findings_data['findings'])} findings...[/bold]")
    run_ai_agent(config, findings_data, date_str)


if __name__ == '__main__':
    main()
