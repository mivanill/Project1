KEYWORD_RULES = {
    "vpn": {
        "possible_system": "Authentication / Network",
        "recommended_check": "Check VPN service status and MFA logs",
        "interpretation": "VPN failures often point to authentication issues, access policy changes, or network instability",
        "confidence": "high",
    },
    "outlook": {
        "possible_system": "Email System",
        "recommended_check": "Check Outlook connectivity, mailbox service health, and client sync status",
        "interpretation": "Email issues may indicate a client-side problem or a broader mail platform disruption",
        "confidence": "high",
    },
    "zoom": {
        "possible_system": "Collaboration / Meetings",
        "recommended_check": "Check Zoom service status, meeting access, and endpoint connectivity",
        "interpretation": "Meeting failures can reflect collaboration platform degradation or user network problems",
        "confidence": "high",
    },
    "printer": {
        "possible_system": "Printing / Endpoint",
        "recommended_check": "Check printer queue, print server health, and device connectivity",
        "interpretation": "Printing issues may stem from endpoint configuration, spooler failures, or print service outages",
        "confidence": "medium",
    },
    "login": {
        "possible_system": "Identity / Access",
        "recommended_check": "Check sign-in service status, authentication logs, and recent access policy changes",
        "interpretation": "Login failures often indicate an authentication, directory, or access-control issue",
        "confidence": "medium",
    },
    "password": {
        "possible_system": "Identity / Access",
        "recommended_check": "Check password reset workflows, lockout events, and identity provider health",
        "interpretation": "Password-related tickets may indicate account lockouts, expired credentials, or identity system issues",
        "confidence": "medium",
    },
    "mfa": {
        "possible_system": "Identity / Access",
        "recommended_check": "Check MFA provider health, challenge logs, and user enrollment status",
        "interpretation": "MFA issues may point to identity provider disruption or user enrollment problems",
        "confidence": "high",
    },
    "laptop": {
        "possible_system": "Endpoint / Device Performance",
        "recommended_check": "Check device health, recent updates, and endpoint management alerts",
        "interpretation": "Laptop incidents often reflect local device degradation, failed updates, or hardware constraints",
        "confidence": "medium",
    },
}


def enrich_issue_text(title: str, description: str) -> dict:
    normalized_text = f"{title} {description}".lower().strip()

    for keyword, result in KEYWORD_RULES.items():
        if keyword in normalized_text:
            return result.copy()

    return {
        "possible_system": "Unknown",
        "recommended_check": "Review the issue details and identify the affected service",
        "interpretation": "No known keyword was detected in the issue text",
        "confidence": "low",
    }
