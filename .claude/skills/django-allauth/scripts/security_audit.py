#!/usr/bin/env python
"""
Django-Allauth Security Audit Script

Performs comprehensive security checks on django-allauth configuration.
Identifies potential security vulnerabilities and provides remediation guidance.

Usage:
    python security_audit.py
    python security_audit.py --json > audit.json
    python security_audit.py --fail-on critical
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Any


class SecurityFinding:
    """Represents a security finding with severity and remediation."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

    def __init__(self, severity: str, title: str, description: str, remediation: str, setting: str = None):
        self.severity = severity
        self.title = title
        self.description = description
        self.remediation = remediation
        self.setting = setting

    def to_dict(self) -> Dict[str, str]:
        """Convert finding to dictionary."""
        result = {
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "remediation": self.remediation
        }
        if self.setting:
            result["setting"] = self.setting
        return result


class SecurityAuditor:
    """Performs security audit on django-allauth settings."""

    def __init__(self, settings_module: str = None):
        self.findings: List[SecurityFinding] = []
        self.settings = {}
        self.settings_module = settings_module or os.getenv('DJANGO_SETTINGS_MODULE')
        self._load_settings()

    def _load_settings(self):
        """Load Django settings for analysis."""
        if not self.settings_module:
            print("Warning: DJANGO_SETTINGS_MODULE not set. Using default checks only.")
            return

        try:
            # Add current directory to path
            sys.path.insert(0, os.getcwd())

            # Import Django and settings
            import django
            from django.conf import settings as django_settings

            if not django_settings.configured:
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', self.settings_module)
                django.setup()

            # Extract relevant settings
            self.settings = {
                # Account settings
                'ACCOUNT_PREVENT_ENUMERATION': getattr(django_settings, 'ACCOUNT_PREVENT_ENUMERATION', None),
                'ACCOUNT_EMAIL_UNKNOWN_ACCOUNTS': getattr(django_settings, 'ACCOUNT_EMAIL_UNKNOWN_ACCOUNTS', True),
                'ACCOUNT_LOGIN_ATTEMPTS_LIMIT': getattr(django_settings, 'ACCOUNT_LOGIN_ATTEMPTS_LIMIT', None),
                'ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT': getattr(django_settings, 'ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT', None),
                'ACCOUNT_RATE_LIMITS': getattr(django_settings, 'ACCOUNT_RATE_LIMITS', None),
                'ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE': getattr(django_settings, 'ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE', True),
                'ACCOUNT_REAUTHENTICATION_REQUIRED': getattr(django_settings, 'ACCOUNT_REAUTHENTICATION_REQUIRED', True),

                # Session settings
                'SESSION_COOKIE_SECURE': getattr(django_settings, 'SESSION_COOKIE_SECURE', False),
                'SESSION_COOKIE_HTTPONLY': getattr(django_settings, 'SESSION_COOKIE_HTTPONLY', True),
                'SESSION_COOKIE_SAMESITE': getattr(django_settings, 'SESSION_COOKIE_SAMESITE', 'Lax'),
                'CSRF_COOKIE_SECURE': getattr(django_settings, 'CSRF_COOKIE_SECURE', False),
                'CSRF_COOKIE_HTTPONLY': getattr(django_settings, 'CSRF_COOKIE_HTTPONLY', False),
                'CSRF_COOKIE_SAMESITE': getattr(django_settings, 'CSRF_COOKIE_SAMESITE', 'Lax'),

                # Password settings
                'AUTH_PASSWORD_VALIDATORS': getattr(django_settings, 'AUTH_PASSWORD_VALIDATORS', []),
                'PASSWORD_RESET_TIMEOUT': getattr(django_settings, 'PASSWORD_RESET_TIMEOUT', 259200),

                # Social auth settings
                'SOCIALACCOUNT_STORE_TOKENS': getattr(django_settings, 'SOCIALACCOUNT_STORE_TOKENS', False),
                'SOCIALACCOUNT_EMAIL_AUTHENTICATION': getattr(django_settings, 'SOCIALACCOUNT_EMAIL_AUTHENTICATION', False),
                'SOCIALACCOUNT_PROVIDERS': getattr(django_settings, 'SOCIALACCOUNT_PROVIDERS', {}),

                # MFA settings
                'MFA_ENABLED': 'allauth.mfa' in getattr(django_settings, 'INSTALLED_APPS', []),
                'MFA_TOTP_ISSUER': getattr(django_settings, 'MFA_TOTP_ISSUER', None),
                'MFA_PASSKEY_LOGIN_ENABLED': getattr(django_settings, 'MFA_PASSKEY_LOGIN_ENABLED', False),

                # General settings
                'DEBUG': getattr(django_settings, 'DEBUG', False),
                'ALLOWED_HOSTS': getattr(django_settings, 'ALLOWED_HOSTS', []),
            }
        except Exception as e:
            print(f"Warning: Could not load Django settings: {e}")

    def audit_account_security(self):
        """Check account-related security settings."""
        # PREVENT_ENUMERATION check
        prevent_enum = self.settings.get('ACCOUNT_PREVENT_ENUMERATION')
        if prevent_enum is None or prevent_enum is False:
            self.findings.append(SecurityFinding(
                SecurityFinding.HIGH,
                "Account Enumeration Not Prevented",
                "ACCOUNT_PREVENT_ENUMERATION is not enabled. Attackers can enumerate valid accounts.",
                "Set ACCOUNT_PREVENT_ENUMERATION = True in settings.py",
                "ACCOUNT_PREVENT_ENUMERATION"
            ))

        # EMAIL_UNKNOWN_ACCOUNTS check
        if self.settings.get('ACCOUNT_EMAIL_UNKNOWN_ACCOUNTS', True):
            self.findings.append(SecurityFinding(
                SecurityFinding.MEDIUM,
                "Email Sent to Unknown Accounts",
                "ACCOUNT_EMAIL_UNKNOWN_ACCOUNTS is True. This can leak information about valid accounts.",
                "Set ACCOUNT_EMAIL_UNKNOWN_ACCOUNTS = False to prevent account enumeration",
                "ACCOUNT_EMAIL_UNKNOWN_ACCOUNTS"
            ))

        # Login attempt limits
        login_limit = self.settings.get('ACCOUNT_LOGIN_ATTEMPTS_LIMIT')
        if login_limit is None:
            self.findings.append(SecurityFinding(
                SecurityFinding.HIGH,
                "No Login Attempt Limits",
                "ACCOUNT_LOGIN_ATTEMPTS_LIMIT is not set. Brute force attacks are not throttled.",
                "Set ACCOUNT_LOGIN_ATTEMPTS_LIMIT to a reasonable value (e.g., 5)",
                "ACCOUNT_LOGIN_ATTEMPTS_LIMIT"
            ))
        elif login_limit > 10:
            self.findings.append(SecurityFinding(
                SecurityFinding.MEDIUM,
                "Login Attempt Limit Too High",
                f"ACCOUNT_LOGIN_ATTEMPTS_LIMIT is {login_limit}, which may be too permissive.",
                "Consider lowering ACCOUNT_LOGIN_ATTEMPTS_LIMIT to 5 or less",
                "ACCOUNT_LOGIN_ATTEMPTS_LIMIT"
            ))

        # Rate limiting
        rate_limits = self.settings.get('ACCOUNT_RATE_LIMITS')
        if not rate_limits:
            self.findings.append(SecurityFinding(
                SecurityFinding.MEDIUM,
                "No Rate Limiting Configured",
                "ACCOUNT_RATE_LIMITS is not configured. API endpoints may be vulnerable to abuse.",
                "Configure ACCOUNT_RATE_LIMITS with appropriate limits for login, signup, etc.",
                "ACCOUNT_RATE_LIMITS"
            ))

        # Logout on password change
        if not self.settings.get('ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE', True):
            self.findings.append(SecurityFinding(
                SecurityFinding.MEDIUM,
                "No Logout on Password Change",
                "ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE is False. Active sessions remain after password change.",
                "Set ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True to invalidate sessions on password change",
                "ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE"
            ))

        # Reauthentication
        if not self.settings.get('ACCOUNT_REAUTHENTICATION_REQUIRED', True):
            self.findings.append(SecurityFinding(
                SecurityFinding.LOW,
                "Reauthentication Not Required",
                "ACCOUNT_REAUTHENTICATION_REQUIRED is False. Sensitive operations don't require password confirmation.",
                "Set ACCOUNT_REAUTHENTICATION_REQUIRED = True for better security",
                "ACCOUNT_REAUTHENTICATION_REQUIRED"
            ))

    def audit_session_security(self):
        """Check session-related security settings."""
        # SESSION_COOKIE_SECURE
        if not self.settings.get('SESSION_COOKIE_SECURE', False):
            self.findings.append(SecurityFinding(
                SecurityFinding.CRITICAL,
                "Session Cookies Not Secure",
                "SESSION_COOKIE_SECURE is False. Session cookies can be intercepted over HTTP.",
                "Set SESSION_COOKIE_SECURE = True in production (requires HTTPS)",
                "SESSION_COOKIE_SECURE"
            ))

        # SESSION_COOKIE_HTTPONLY
        if not self.settings.get('SESSION_COOKIE_HTTPONLY', True):
            self.findings.append(SecurityFinding(
                SecurityFinding.HIGH,
                "Session Cookies Accessible via JavaScript",
                "SESSION_COOKIE_HTTPONLY is False. XSS attacks can steal session cookies.",
                "Set SESSION_COOKIE_HTTPONLY = True to prevent JavaScript access",
                "SESSION_COOKIE_HTTPONLY"
            ))

        # SESSION_COOKIE_SAMESITE
        samesite = self.settings.get('SESSION_COOKIE_SAMESITE', 'Lax')
        if samesite not in ['Strict', 'Lax']:
            self.findings.append(SecurityFinding(
                SecurityFinding.HIGH,
                "Session Cookie SameSite Not Configured",
                f"SESSION_COOKIE_SAMESITE is '{samesite}'. CSRF protection may be weak.",
                "Set SESSION_COOKIE_SAMESITE = 'Strict' or 'Lax' for CSRF protection",
                "SESSION_COOKIE_SAMESITE"
            ))

        # CSRF_COOKIE_SECURE
        if not self.settings.get('CSRF_COOKIE_SECURE', False):
            self.findings.append(SecurityFinding(
                SecurityFinding.HIGH,
                "CSRF Cookies Not Secure",
                "CSRF_COOKIE_SECURE is False. CSRF tokens can be intercepted over HTTP.",
                "Set CSRF_COOKIE_SECURE = True in production (requires HTTPS)",
                "CSRF_COOKIE_SECURE"
            ))

    def audit_password_security(self):
        """Check password-related security settings."""
        validators = self.settings.get('AUTH_PASSWORD_VALIDATORS', [])

        if not validators:
            self.findings.append(SecurityFinding(
                SecurityFinding.CRITICAL,
                "No Password Validators Configured",
                "AUTH_PASSWORD_VALIDATORS is empty. Weak passwords are allowed.",
                "Configure AUTH_PASSWORD_VALIDATORS with UserAttributeSimilarityValidator, MinimumLengthValidator, CommonPasswordValidator, and NumericPasswordValidator",
                "AUTH_PASSWORD_VALIDATORS"
            ))
        else:
            # Check for specific validators
            validator_names = [v.get('NAME', '') for v in validators]

            if not any('MinimumLength' in name for name in validator_names):
                self.findings.append(SecurityFinding(
                    SecurityFinding.HIGH,
                    "No Minimum Password Length",
                    "MinimumLengthValidator not found. Short passwords are allowed.",
                    "Add MinimumLengthValidator to AUTH_PASSWORD_VALIDATORS",
                    "AUTH_PASSWORD_VALIDATORS"
                ))

            if not any('CommonPassword' in name for name in validator_names):
                self.findings.append(SecurityFinding(
                    SecurityFinding.MEDIUM,
                    "Common Passwords Not Blocked",
                    "CommonPasswordValidator not found. Common passwords are allowed.",
                    "Add CommonPasswordValidator to AUTH_PASSWORD_VALIDATORS",
                    "AUTH_PASSWORD_VALIDATORS"
                ))

        # Password reset timeout
        reset_timeout = self.settings.get('PASSWORD_RESET_TIMEOUT', 259200)
        if reset_timeout > 86400:  # More than 24 hours
            self.findings.append(SecurityFinding(
                SecurityFinding.LOW,
                "Password Reset Timeout Too Long",
                f"PASSWORD_RESET_TIMEOUT is {reset_timeout} seconds ({reset_timeout // 3600} hours). Long-lived tokens increase risk.",
                "Consider reducing PASSWORD_RESET_TIMEOUT to 3600-86400 seconds (1-24 hours)",
                "PASSWORD_RESET_TIMEOUT"
            ))

    def audit_social_auth_security(self):
        """Check social authentication security settings."""
        # STORE_TOKENS check
        if self.settings.get('SOCIALACCOUNT_STORE_TOKENS', False):
            self.findings.append(SecurityFinding(
                SecurityFinding.CRITICAL,
                "Social Auth Tokens Stored in Plaintext",
                "SOCIALACCOUNT_STORE_TOKENS is True. OAuth tokens are stored unencrypted in the database.",
                "Set SOCIALACCOUNT_STORE_TOKENS = False unless absolutely necessary. If needed, implement encryption.",
                "SOCIALACCOUNT_STORE_TOKENS"
            ))

        # EMAIL_AUTHENTICATION check
        if self.settings.get('SOCIALACCOUNT_EMAIL_AUTHENTICATION', False):
            self.findings.append(SecurityFinding(
                SecurityFinding.CRITICAL,
                "Email-Based Social Account Takeover Risk",
                "SOCIALACCOUNT_EMAIL_AUTHENTICATION is True. Users can take over accounts by verifying email.",
                "Set SOCIALACCOUNT_EMAIL_AUTHENTICATION = False to prevent account takeover",
                "SOCIALACCOUNT_EMAIL_AUTHENTICATION"
            ))

        # PKCE check for OAuth providers
        providers = self.settings.get('SOCIALACCOUNT_PROVIDERS', {})
        for provider_name, provider_config in providers.items():
            pkce_enabled = provider_config.get('PKCE_ENABLED', False)
            if not pkce_enabled and provider_name.lower() in ['google', 'github', 'gitlab']:
                self.findings.append(SecurityFinding(
                    SecurityFinding.MEDIUM,
                    f"PKCE Not Enabled for {provider_name}",
                    f"PKCE is not enabled for {provider_name}. Authorization code interception is possible.",
                    f"Enable PKCE in SOCIALACCOUNT_PROVIDERS['{provider_name}']['PKCE_ENABLED'] = True",
                    f"SOCIALACCOUNT_PROVIDERS.{provider_name}.PKCE_ENABLED"
                ))

    def audit_mfa_security(self):
        """Check MFA-related security settings."""
        if not self.settings.get('MFA_ENABLED', False):
            self.findings.append(SecurityFinding(
                SecurityFinding.INFO,
                "MFA Not Enabled",
                "Multi-factor authentication is not enabled in INSTALLED_APPS.",
                "Consider enabling 'allauth.mfa' for enhanced security",
                "INSTALLED_APPS"
            ))
            return

        # TOTP plaintext warning
        self.findings.append(SecurityFinding(
            SecurityFinding.HIGH,
            "TOTP Secrets Stored in Database",
            "Django-allauth stores TOTP secrets in the database. Consider field-level encryption.",
            "Implement database field encryption for TOTP secrets using django-fernet-fields or similar",
            "MFA_TOTP"
        ))

        # Passkey recommendation
        if not self.settings.get('MFA_PASSKEY_LOGIN_ENABLED', False):
            self.findings.append(SecurityFinding(
                SecurityFinding.INFO,
                "Passkeys Not Enabled",
                "Passkey authentication (WebAuthn) is not enabled. Consider enabling for phishing resistance.",
                "Set MFA_PASSKEY_LOGIN_ENABLED = True to enable passkey authentication",
                "MFA_PASSKEY_LOGIN_ENABLED"
            ))

    def audit_general_security(self):
        """Check general Django security settings."""
        # DEBUG mode check
        if self.settings.get('DEBUG', False):
            self.findings.append(SecurityFinding(
                SecurityFinding.CRITICAL,
                "DEBUG Mode Enabled",
                "DEBUG = True in production exposes sensitive information and stack traces.",
                "Set DEBUG = False in production settings",
                "DEBUG"
            ))

        # ALLOWED_HOSTS check
        allowed_hosts = self.settings.get('ALLOWED_HOSTS', [])
        if not allowed_hosts or '*' in allowed_hosts:
            self.findings.append(SecurityFinding(
                SecurityFinding.HIGH,
                "ALLOWED_HOSTS Not Properly Configured",
                "ALLOWED_HOSTS is empty or contains '*'. Host header attacks are possible.",
                "Configure ALLOWED_HOSTS with specific domain names",
                "ALLOWED_HOSTS"
            ))

    def calculate_score(self) -> int:
        """Calculate security score (0-100) based on findings."""
        if not self.findings:
            return 100

        # Severity weights
        weights = {
            SecurityFinding.CRITICAL: 20,
            SecurityFinding.HIGH: 10,
            SecurityFinding.MEDIUM: 5,
            SecurityFinding.LOW: 2,
            SecurityFinding.INFO: 0
        }

        total_deductions = sum(weights.get(f.severity, 0) for f in self.findings)
        score = max(0, 100 - total_deductions)
        return score

    def run_audit(self) -> Dict[str, Any]:
        """Run all security audits and return results."""
        self.findings = []

        self.audit_account_security()
        self.audit_session_security()
        self.audit_password_security()
        self.audit_social_auth_security()
        self.audit_mfa_security()
        self.audit_general_security()

        # Organize findings by severity
        findings_by_severity = {
            SecurityFinding.CRITICAL: [],
            SecurityFinding.HIGH: [],
            SecurityFinding.MEDIUM: [],
            SecurityFinding.LOW: [],
            SecurityFinding.INFO: []
        }

        for finding in self.findings:
            findings_by_severity[finding.severity].append(finding)

        return {
            "score": self.calculate_score(),
            "total_findings": len(self.findings),
            "findings": findings_by_severity,
            "summary": {
                "critical": len(findings_by_severity[SecurityFinding.CRITICAL]),
                "high": len(findings_by_severity[SecurityFinding.HIGH]),
                "medium": len(findings_by_severity[SecurityFinding.MEDIUM]),
                "low": len(findings_by_severity[SecurityFinding.LOW]),
                "info": len(findings_by_severity[SecurityFinding.INFO])
            }
        }


def format_text_output(results: Dict[str, Any]) -> str:
    """Format audit results as text."""
    output = []
    output.append("=" * 70)
    output.append("Django-Allauth Security Audit Report")
    output.append("=" * 70)
    output.append(f"\nSecurity Score: {results['score']}/100")
    output.append(f"Total Findings: {results['total_findings']}\n")

    summary = results['summary']
    output.append("Summary:")
    output.append(f"  Critical: {summary['critical']}")
    output.append(f"  High:     {summary['high']}")
    output.append(f"  Medium:   {summary['medium']}")
    output.append(f"  Low:      {summary['low']}")
    output.append(f"  Info:     {summary['info']}")
    output.append("\n" + "=" * 70)

    # Print findings by severity
    severity_order = [
        SecurityFinding.CRITICAL,
        SecurityFinding.HIGH,
        SecurityFinding.MEDIUM,
        SecurityFinding.LOW,
        SecurityFinding.INFO
    ]

    for severity in severity_order:
        findings = results['findings'][severity]
        if findings:
            output.append(f"\n{severity.upper()} Severity Findings:\n")
            for i, finding in enumerate(findings, 1):
                output.append(f"{i}. {finding.title}")
                if finding.setting:
                    output.append(f"   Setting: {finding.setting}")
                output.append(f"   Description: {finding.description}")
                output.append(f"   Remediation: {finding.remediation}")
                output.append("")

    output.append("=" * 70)
    return "\n".join(output)


def main():
    """Main entry point for the security audit script."""
    parser = argparse.ArgumentParser(
        description="Django-Allauth Security Audit Script"
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results in JSON format'
    )
    parser.add_argument(
        '--fail-on',
        choices=['critical', 'high', 'medium', 'low'],
        help='Exit with non-zero status if findings of this severity or higher are found'
    )
    parser.add_argument(
        '--settings',
        help='Django settings module (default: DJANGO_SETTINGS_MODULE env var)'
    )

    args = parser.parse_args()

    # Run audit
    auditor = SecurityAuditor(settings_module=args.settings)
    results = auditor.run_audit()

    # Output results
    if args.json:
        # Convert findings to serializable format
        json_results = {
            "score": results["score"],
            "total_findings": results["total_findings"],
            "summary": results["summary"],
            "findings": {
                severity: [f.to_dict() for f in findings]
                for severity, findings in results["findings"].items()
            }
        }
        print(json.dumps(json_results, indent=2))
    else:
        print(format_text_output(results))

    # Check fail-on condition
    if args.fail_on:
        severity_levels = {
            'critical': [SecurityFinding.CRITICAL],
            'high': [SecurityFinding.CRITICAL, SecurityFinding.HIGH],
            'medium': [SecurityFinding.CRITICAL, SecurityFinding.HIGH, SecurityFinding.MEDIUM],
            'low': [SecurityFinding.CRITICAL, SecurityFinding.HIGH, SecurityFinding.MEDIUM, SecurityFinding.LOW]
        }

        relevant_severities = severity_levels[args.fail_on]
        has_findings = any(
            len(results['findings'][severity]) > 0
            for severity in relevant_severities
        )

        if has_findings:
            sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
