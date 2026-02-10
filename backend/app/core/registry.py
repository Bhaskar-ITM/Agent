SECURITY_STAGES = {
    1: {"name": "Git Checkout", "requires": []},
    2: {"name": "Sonar Scanner", "requires": []},
    3: {"name": "Sonar Quality Gate", "requires": []},
    4: {"name": "NPM / PIP Install", "requires": []},
    5: {"name": "Dependency Check", "requires": []},
    6: {"name": "Trivy FS Scan", "requires": []},
    7: {"name": "Docker Build", "requires": []},
    8: {"name": "Docker Push", "requires": []},
    9: {"name": "Trivy Image Scan", "requires": []},
    10: {"name": "Nmap Scan", "requires": ["target_ip"]},
    11: {"name": "ZAP Scan", "requires": ["target_url"]}
}

STAGE_NAME_TO_ID = {v["name"]: k for k, v in SECURITY_STAGES.items()}
