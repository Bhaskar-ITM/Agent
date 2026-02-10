from app.schemas.scan import ScanCreate

def validate_scan_request(scan: ScanCreate):
    if scan.mode not in ["AUTOMATED", "MANUAL"]:
        raise ValueError("Invalid scan mode")

    if scan.mode == "MANUAL":
        if not scan.selected_stages:
            raise ValueError("Manual scan requires selected stages")

        # Normalize stage names to lowercase for comparison
        stages = [s.lower() for s in scan.selected_stages]

        # Note: In a real app, we'd fetch the project to check for IP/URL.
        # This will be handled in the orchestrator or here if we pass the project.
        # For now, we follow the skeleton's logic but keep it extensible.
        return True

    return True

def validate_manual_targets(selected_stages: list[str], target_ip: str | None, target_url: str | None):
    stages = [s.lower() for s in selected_stages]

    if "nmap scan" in stages or "nmap" in stages:
        if not target_ip:
            raise ValueError("Nmap scan requires target IP")

    if "zap scan" in stages or "zap" in stages:
        if not target_url:
            raise ValueError("ZAP scan requires target URL")
