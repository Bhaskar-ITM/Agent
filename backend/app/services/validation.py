from app.schemas.scan import ScanCreate

VALID_STAGES = {
    "git_checkout",
    "sonar_scanner",
    "sonar_quality_gate",
    "npm_pip_install",
    "dependency_check",
    "trivy_fs_scan",
    "docker_build",
    "docker_push",
    "trivy_image_scan",
    "nmap_scan",
    "zap_scan"
}

def validate_scan_request(scan: ScanCreate):
    if scan.scan_mode not in ["automated", "manual"]:
        raise ValueError("scan_mode must be 'automated' or 'manual'")

    if scan.scan_mode == "automated":
        if scan.selected_stages is not None:
            raise ValueError("selected_stages must NOT be provided for automated scans")

    if scan.scan_mode == "manual":
        if not scan.selected_stages:
            raise ValueError("selected_stages is required and cannot be empty for manual scans")

        # Check for duplicates
        if len(scan.selected_stages) != len(set(scan.selected_stages)):
            raise ValueError("Duplicate stages are not allowed")

        # Check for valid stage identifiers
        for stage in scan.selected_stages:
            if stage not in VALID_STAGES:
                raise ValueError(f"Invalid stage identifier: {stage}")

    return True

# validate_manual_targets is removed as per Phase 3 rules (validation happens later)
