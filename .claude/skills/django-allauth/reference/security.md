# Django-AllAuth Security Guide

Quick reference for security configuration and best practices.

## Table of Contents

1. [Account Enumeration Prevention](#account-enumeration-prevention)
2. [Rate Limiting](#rate-limiting)
3. [Session Security](#session-security)
4. [Password Security](#password-security)
5. [Email Verification Security](#email-verification-security)
6. [Social Authentication Security](#social-authentication-security)
7. [MFA Security Warnings](#mfa-security-warnings)
8. [Production Security Checklist](#production-security-checklist)

---

## Account Enumeration Prevention

Prevent attackers from determining if an email/username exists in your system.

### Critical Settings

```python
# settings.py
ACCOUNT_PREVENT_ENUMERATION = True  # Default - keeps it enabled
ACCOUNT_EMAIL_UNKNOWN_ACCOUNTS = False  # IMPORTANT: Prevent account existence leak
```

> **WARNING:** The default `ACCOUNT_EMAIL_UNKNOWN_ACCOUNTS = True` contradicts `PREVENT_ENUMERATION` by sending "No account found" emails. Set to `False` to prevent enumeration via password reset.

### Configuration Checklist

- [ ] `ACCOUNT_PREVENT_ENUMERATION = True` - Shows identical messages regardless of account existence
- [ ] `ACCOUNT_EMAIL_UNKNOWN_ACCOUNTS = False` - Don't reveal account existence in password reset
- [ ] Rate limiting configured for signup/login endpoints

**Note:** Signup page will still reveal if email/username exists (UX requirement). Use rate limiting to slow enumeration attacks.

---

## Rate Limiting

Built-in rate limiting prevents brute force, credential stuffing, and abuse.

### Configuration

```python
# settings.py
ACCOUNT_RATE_LIMITS = {
    "login": "30/m/ip",                      # Total login attempts
    "login_failed": "10/m/ip,5/5m/key",     # Failed attempts (key = username/email)
    "signup": "20/m/ip",
    "reset_password": "20/m/ip,5/m/key",    # Key = email address
    "reset_password_from_key": "20/m/ip",
    "change_password": "5/m/user",
    "manage_email": "10/m/user",
    "reauthenticate": "10/m/user",
    "confirm_email": "1/180s/key",          # One attempt per 3 minutes
    "verify_phone": "1/30s/key,3/m/ip",
    "change_phone": "1/m/user",
    "request_login_code": "20/m/ip,3/m/key",
}
```

### Format: `"amount/duration/scope"`

- **Duration units:** `s` (seconds), `m` (minutes), `h` (hours), `d` (days)
- **Scope types:** `ip` (IP address), `user` (authenticated user), `key` (email/username)
- **Multiple limits:** Comma-separated = ALL must be satisfied (AND condition)

### Redis for Distributed Systems

> **CRITICAL:** Django's default cache is per-process. Use Redis in production with multiple servers.

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

### Custom Rate Limits

```python
from allauth.core import ratelimit

def my_sensitive_view(request):
    resp = ratelimit.consume_or_429(
        request,
        action="my_custom_action",
        key=request.POST.get('email'),
    )
    if resp:
        return resp  # 429 Too Many Requests
    # Process request...
```

---

## Session Security

Proper cookie configuration is critical for preventing session hijacking.

### Required Settings

```python
# settings.py - REQUIRED in production
SESSION_COOKIE_SECURE = True        # HTTPS only
SESSION_COOKIE_HTTPONLY = True      # Prevent JavaScript access
SESSION_COOKIE_SAMESITE = 'Lax'     # CSRF protection

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
```

### Logout on Password Change

> **WARNING:** Default behavior allows stolen sessions to remain active after password change!

```python
# settings.py
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True  # Invalidate all other sessions
```

### Reauthentication

Force password re-entry before sensitive operations:

```python
# settings.py
ACCOUNT_REAUTHENTICATION_TIMEOUT = 300  # 5 minutes (default)
```

Customize via adapter:

```python
# adapters.py
from allauth.account.adapter import DefaultAccountAdapter

class MyAccountAdapter(DefaultAccountAdapter):
    def is_reauthentication_required(self, request, stage):
        """
        Stages: 'manage_email', 'change_password', or custom
        """
        if stage == "delete_account":
            return True
        return super().is_reauthentication_required(request, stage)
```

### Session Timeout

```python
# settings.py
SESSION_COOKIE_AGE = 1209600  # 2 weeks (default)
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Remember me checkbox
ACCOUNT_SESSION_REMEMBER = None  # Show checkbox (None/True/False)
```

---

## Password Security

### Django Password Validators

```python
# settings.py
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 12},  # Increase from default 8
    },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
```

### Password Reset Settings

```python
# settings.py
PASSWORD_RESET_TIMEOUT = 259200  # 3 days (Django setting)
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3  # Email verification expiration
```

### Code-Based Password Reset (More Secure)

```python
# settings.py
ACCOUNT_PASSWORD_RESET_BY_CODE_ENABLED = True
ACCOUNT_PASSWORD_RESET_BY_CODE_TIMEOUT = 180      # 3 minutes
ACCOUNT_PASSWORD_RESET_BY_CODE_MAX_ATTEMPTS = 3
```

**Benefits:** Short-lived (3 min vs 3 days), limited attempts, harder to phish.

---

## Email Verification Security

### HMAC Tokens (Recommended)

```python
# settings.py
ACCOUNT_EMAIL_CONFIRMATION_HMAC = True  # Default - stateless tokens
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3
```

### Code-Based Verification (More Secure)

```python
# settings.py
ACCOUNT_EMAIL_VERIFICATION_BY_CODE_ENABLED = True
ACCOUNT_EMAIL_VERIFICATION_BY_CODE_TIMEOUT = 900     # 15 minutes
ACCOUNT_EMAIL_VERIFICATION_BY_CODE_MAX_ATTEMPTS = 3
```

### CSRF Protection

```python
# settings.py
ACCOUNT_CONFIRM_EMAIL_ON_GET = False  # Require POST (recommended)
```

**Why:** `GET` requests can be triggered by prefetching or image tags. `POST` prevents CSRF.

---

## Social Authentication Security

### PKCE (OAuth 2.1 Security)

> **CRITICAL:** Enable PKCE for all OAuth2 providers to prevent authorization code interception.

```python
# settings.py
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {'client_id': '...', 'secret': '...'},
        'OAUTH_PKCE_ENABLED': True,  # REQUIRED
    },
    'github': {
        'APP': {'client_id': '...', 'secret': '...'},
        'OAUTH_PKCE_ENABLED': True,  # REQUIRED
    },
}
```

### Token Storage

> **WARNING:** OAuth tokens are stored in PLAINTEXT in the database!

```python
# settings.py
SOCIALACCOUNT_STORE_TOKENS = False  # Default - don't store tokens
```

**Only enable if:** You need to make API calls on behalf of users (Google Calendar, Facebook Graph, etc.).

**If enabled:** Encrypt database, limit access, use short-lived tokens with refresh rotation.

### Email Authentication (Account Takeover Risk!)

> **CRITICAL:** Do NOT enable unless you trust ALL providers completely!

```python
# settings.py
SOCIALACCOUNT_EMAIL_AUTHENTICATION = False  # KEEP THIS FALSE!
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = False
```

**Risk:** Malicious OAuth providers can claim any email address. If enabled, attacker can hijack accounts by creating a social account with victim's email.

**Only enable for:** Single fully-trusted corporate SSO providers.

---

## MFA Security Warnings

### TOTP Secrets in Plaintext

> **CRITICAL:** TOTP secrets are stored in PLAINTEXT by default!

**Mitigation:** Encrypt secrets with custom adapter:

```python
# adapters.py
from allauth.mfa.adapter import DefaultMFAAdapter
from cryptography.fernet import Fernet
from django.conf import settings

class SecureMFAAdapter(DefaultMFAAdapter):
    def encrypt(self, secret):
        fernet = Fernet(settings.TOTP_ENCRYPTION_KEY)
        return fernet.encrypt(secret.encode()).decode()

    def decrypt(self, encrypted_secret):
        fernet = Fernet(settings.TOTP_ENCRYPTION_KEY)
        return fernet.decrypt(encrypted_secret.encode()).decode()
```

```python
# settings.py
import os
from cryptography.fernet import Fernet

# Generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key())"
TOTP_ENCRYPTION_KEY = os.environ['TOTP_ENCRYPTION_KEY']
MFA_ADAPTER = 'myapp.adapters.SecureMFAAdapter'
```

### Trust Cookie Security

```python
# settings.py
from datetime import timedelta

MFA_TRUST_ENABLED = True
MFA_TRUST_COOKIE_AGE = timedelta(days=7)  # Default 14 is too long
MFA_TRUST_COOKIE_SECURE = True
MFA_TRUST_COOKIE_HTTPONLY = True
MFA_TRUST_COOKIE_SAMESITE = 'Strict'
```

### Development Bypass Code

> **CRITICAL:** Never use in production!

```python
# settings.py (DEVELOPMENT ONLY)
if DEBUG:
    MFA_TOTP_INSECURE_BYPASS_CODE = '123456'  # Raises error if DEBUG=False
```

### TOTP Tolerance

```python
# settings.py
MFA_TOTP_TOLERANCE = 0  # Accept only current time step (most secure)
# MFA_TOTP_TOLERANCE = 1  # Accept ±30 seconds (if users report issues)
```

### Recovery Codes

```python
# settings.py
MFA_RECOVERY_CODE_COUNT = 10   # Number of codes
MFA_RECOVERY_CODE_DIGITS = 8   # Digits per code
```

**Security gaps:** No rate limiting on recovery codes (uses `login_failed` limit), no usage notifications.

**Best practices:** Log recovery code usage, send email notifications, warn users to store securely.

---

## Production Security Checklist

### Account Security (5 items)

- [ ] `ACCOUNT_PREVENT_ENUMERATION = True` - Prevent username/email enumeration
- [ ] `ACCOUNT_EMAIL_UNKNOWN_ACCOUNTS = False` - Don't leak account existence
- [ ] `ACCOUNT_EMAIL_VERIFICATION = 'mandatory'` - Require email verification
- [ ] `ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True` - Invalidate stolen sessions
- [ ] `AUTH_PASSWORD_VALIDATORS` configured with 12+ character minimum

### Session Security (4 items)

- [ ] `SESSION_COOKIE_SECURE = True` - HTTPS only
- [ ] `SESSION_COOKIE_HTTPONLY = True` - Prevent XSS attacks
- [ ] `SESSION_COOKIE_SAMESITE = 'Lax'` - CSRF protection
- [ ] `CSRF_COOKIE_SECURE = True` - Secure CSRF cookies

### Rate Limiting (2 items)

- [ ] `ACCOUNT_RATE_LIMITS` configured (not disabled)
- [ ] Redis cache configured for distributed systems

### Social Authentication (3 items)

- [ ] `OAUTH_PKCE_ENABLED = True` for all OAuth2 providers
- [ ] `SOCIALACCOUNT_STORE_TOKENS = False` (unless API calls needed)
- [ ] `SOCIALACCOUNT_EMAIL_AUTHENTICATION = False` (unless single trusted provider)

### MFA Security (4 items)

- [ ] TOTP secrets encrypted (custom `MFAAdapter`)
- [ ] `MFA_TOTP_INSECURE_BYPASS_CODE` not set in production
- [ ] `MFA_TRUST_COOKIE_AGE = timedelta(days=7)` or less
- [ ] `MFA_TRUST_COOKIE_SECURE = True` and `HTTPONLY = True`

### Infrastructure (2 items)

- [ ] HTTPS enabled (Let's Encrypt, CloudFlare, load balancer)
- [ ] `SECRET_KEY` in environment variable (not version control)
- [ ] `DEBUG = False` in production

---

## Quick Reference: Critical Settings

```python
# settings.py - Production Security Baseline

# Account enumeration prevention
ACCOUNT_PREVENT_ENUMERATION = True
ACCOUNT_EMAIL_UNKNOWN_ACCOUNTS = False
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True

# Session security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True

# Email verification
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_CONFIRM_EMAIL_ON_GET = False

# Password security
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 12}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Rate limiting
ACCOUNT_RATE_LIMITS = {
    "login_failed": "10/m/ip,5/5m/key",
    "signup": "20/m/ip",
    "reset_password": "20/m/ip,5/m/key",
}

# Redis cache (distributed systems)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}

# Social auth security
SOCIALACCOUNT_STORE_TOKENS = False
SOCIALACCOUNT_EMAIL_AUTHENTICATION = False

# MFA security
MFA_ADAPTER = 'myapp.adapters.SecureMFAAdapter'  # Encrypt TOTP secrets
MFA_TRUST_COOKIE_AGE = timedelta(days=7)
MFA_TRUST_COOKIE_SECURE = True
MFA_TRUST_COOKIE_HTTPONLY = True
```

---

## Additional Resources

- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [Django Security Documentation](https://docs.djangoproject.com/en/stable/topics/security/)
- [Django-Allauth Documentation](https://docs.allauth.org/)

---

**Last Updated:** 2026-01-06
**Version:** 2.0 (Simplified)
