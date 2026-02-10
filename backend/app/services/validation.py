from app.schemas.scan import ScanCreate
from app.core.policies import get_policy, ValidationError

def validate_scan_request(scan: ScanCreate, project: dict):
    """
    Validates a scan request using the appropriate policy.
    """
    try:
        policy = get_policy(scan.mode)
        # Convert ScanCreate to dict for validation
        payload = scan.model_dump()
        policy.validate(payload, project)
        return True
    except ValidationError as e:
        raise ValueError(str(e))

# We can keep validate_manual_targets but it's now redundant with policy.validate
def validate_manual_targets(selected_stages: list[str], target_ip: str | None, target_url: str | None):
    # This remains for legacy compatibility or simpler use cases,
    # but the policy object is the new standard.
    from app.core.policies import ManualScanPolicy
    policy = ManualScanPolicy()
    project = {"target_ip": target_ip, "target_url": target_url}
    policy.validate({"selected_stages": selected_stages}, project)
