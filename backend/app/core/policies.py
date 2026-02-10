from app.core.registry import SECURITY_STAGES, STAGE_NAME_TO_ID

class ValidationError(ValueError):
    pass

class ScanPolicy:
    def validate(self, payload: dict, project: dict):
        raise NotImplementedError

class AutomatedScanPolicy(ScanPolicy):
    def validate(self, payload: dict, project: dict):
        if payload.get("selected_stages"):
            raise ValidationError("Automated mode does not accept manual stage selection")

class ManualScanPolicy(ScanPolicy):
    def validate(self, payload: dict, project: dict):
        stages = payload.get("selected_stages", [])
        if not stages:
            raise ValidationError("Manual scan requires stage selection")

        for stage_name in stages:
            if stage_name not in STAGE_NAME_TO_ID:
                raise ValidationError(f"Invalid stage name: {stage_name}")

            stage_id = STAGE_NAME_TO_ID[stage_name]
            requirements = SECURITY_STAGES[stage_id]["requires"]

            for req in requirements:
                if not project.get(req):
                    raise ValidationError(f"{req} required for stage {stage_name}")

def get_policy(mode: str) -> ScanPolicy:
    if mode == "AUTOMATED":
        return AutomatedScanPolicy()
    elif mode == "MANUAL":
        return ManualScanPolicy()
    else:
        raise ValidationError(f"Invalid scan mode: {mode}")
