# Django-AllAuth Security Guide

Comprehensive security best practices, attack mitigations, and configuration hardening for django-allauth.

## Table of Contents

1. [Account Enumeration Prevention](#account-enumeration-prevention)
2. [Rate Limiting](#rate-limiting)
3. [Session Security](#session-security)
4. [Password Security](#password-security)
5. [Email Verification Security](#email-verification-security)
6. [Social Authentication Security](#social-authentication-security)
7. [MFA Security Warnings](#mfa-security-warnings)
8. [Attack Mitigations](#attack-mitigations)
9. [Security Checklist](#security-checklist)

---

## Account Enumeration Prevention

Account enumeration allows attackers to determine if an email/username exists in your system. Django-allauth provides protection but requires proper configuration.

### PREVENT_ENUMERATION Setting

**Default:** `True`

When enabled, django-allauth prevents attackers from determining if an account exists by:
- Showing identical success messages regardless of account existence
- Performing "pretend" password checks for non-existent accounts (timing attack mitigation)
- Returning generic error messages during login

```python
# settings.py
ACCOUNT_PREVENT_ENUMERATION = True  # Recommended
```

### How Pretend Login Works

When a login fails for a non-existent user, allauth still performs a password hash operation to prevent timing attacks:

```python
# From allauth/account/auth_backends.py
def _mitigate_timing_attack(self, password):
    get_user_model()().set_password(password)
```

This ensures that failed logins for non-existent accounts take the same time as failed logins for existing accounts.

### EMAIL_UNKNOWN_ACCOUNTS Setting

**Default:** `True` (SECURITY GAP!)

**WARNING:** This setting contradicts `PREVENT_ENUMERATION`!

When `True`, password reset emails are sent even if the account doesn't exist, saying "No account found." This **leaks account existence**.

```python
# Secure configuration
ACCOUNT_EMAIL_UNKNOWN_ACCOUNTS = False  # Don't leak account existence
ACCOUNT_PREVENT_ENUMERATION = True
```

**Recommended behavior:** Always show a success message like "If an account exists, we've sent a password reset email."

### Account Enumeration Attack Vectors

**Login page timing attacks:**
- Mitigated by pretend password checks
- Ensure `PREVENT_ENUMERATION = True`

**Password reset page:**
- Set `EMAIL_UNKNOWN_ACCOUNTS = False`
- Use generic success messages

**Signup page:**
- Returns error if email/username already exists (unavoidable UX tradeoff)
- Use rate limiting to slow enumeration attacks

---

## Rate Limiting

Django-allauth includes comprehensive rate limiting to prevent abuse, credential stuffing, and brute force attacks.

### Configuration Overview

```python
# settings.py
ACCOUNT_RATE_LIMITS = {
    # Format: "amount/duration/per"
    # amount: number of requests
    # duration: time period (s=seconds, m=minutes, h=hours, d=days)
    # per: scope (ip, user, key)

    "login": "30/m/ip",                          # 30 login attempts per minute per IP
    "login_failed": "10/m/ip,5/5m/key",         # Complex rate limit (see below)
    "signup": "20/m/ip",                         # 20 signups per minute per IP
    "reset_password": "20/m/ip,5/m/key",        # Password reset requests
    "reset_password_from_key": "20/m/ip",       # Password reset form submissions
    "change_password": "5/m/user",               # Password changes (logged in)
    "manage_email": "10/m/user",                 # Email management actions
    "reauthenticate": "10/m/user",               # Reauthentication prompts
    "confirm_email": "1/180s/key",               # Email verification attempts
    "verify_phone": "1/30s/key,3/m/ip",         # Phone verification
    "change_phone": "1/m/user",                  # Phone number changes
    "request_login_code": "20/m/ip,3/m/key",    # Login code requests
}

# Disable all rate limiting (NOT RECOMMENDED)
ACCOUNT_RATE_LIMITS = False
```

### Rate Limit Format Syntax

**Single rate limit:**
```python
"10/m/ip"  # 10 requests per minute per IP address
```

**Multiple rate limits (ALL must be satisfied):**
```python
"10/m/ip,5/5m/key"
# AND condition:
# - 10 requests per minute per IP
# - 5 requests per 5 minutes per key
```

**Duration units:**
- `s` = seconds
- `m` = minutes
- `h` = hours
- `d` = days

**Scope types:**
- `ip` = Per client IP address
- `user` = Per authenticated user (user.pk)
- `key` = Per custom key (e.g., email address, username)

### All Available Rate Limit Actions

From `/home/user/django-allauth-mirror/allauth/account/app_settings.py`:

| Action | Default | Purpose |
|--------|---------|---------|
| `login` | `30/m/ip` | Login attempts (successful or failed) |
| `login_failed` | `10/m/ip,5/5m/key` | Failed login tracking (key = username/email) |
| `signup` | `20/m/ip` | Account creation |
| `reset_password` | `20/m/ip,5/m/key` | Password reset requests (key = email) |
| `reset_password_from_key` | `20/m/ip` | Password reset form submission |
| `change_password` | `5/m/user` | Password changes (logged in users) |
| `manage_email` | `10/m/user` | Email add/remove/change primary |
| `reauthenticate` | `10/m/user` | Reauthentication for sensitive actions |
| `confirm_email` | `1/180s/key` | Email verification (key = email) |
| `verify_phone` | `1/30s/key,3/m/ip` | Phone verification (key = phone number) |
| `change_phone` | `1/m/user` | Phone number changes |
| `request_login_code` | `20/m/ip,3/m/key` | Email-based login code requests |

### Custom Rate Limits in Views

Add rate limiting to your own views:

```python
from allauth.core import ratelimit

def my_sensitive_view(request):
    # Check rate limit
    resp = ratelimit.consume_or_429(
        request,
        action="my_custom_action",
        key=request.POST.get('email'),
    )
    if resp:
        return resp  # Return 429 Too Many Requests

    # Process request
    return HttpResponse("Success")
```

### Redis for Distributed Systems

**WARNING:** Django's default cache backend uses in-memory storage (per-process). In distributed systems (multiple servers/processes), rate limits won't work correctly.

**Solution:** Use Redis for shared cache:

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### Rate Limiting Implementation Notes

From `/home/user/django-allauth-mirror/allauth/core/internal/ratelimit.py`:

**Race condition warning:** Rate limiting uses non-atomic cache operations. In high-concurrency scenarios, you may occasionally see slight overruns (e.g., 11-12 requests when the limit is 10). This is acceptable for most use cases.

---

## Session Security

Django-allauth relies on Django's session framework. Proper cookie configuration is critical.

### Cookie Security Settings

**Always set these in production:**

```python
# settings.py
SESSION_COOKIE_SECURE = True        # Only send over HTTPS
SESSION_COOKIE_HTTPONLY = True      # Prevent JavaScript access
SESSION_COOKIE_SAMESITE = 'Lax'     # CSRF protection ('Strict' or 'Lax')

# Additional security
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
```

**Explanation:**
- `SECURE = True`: Prevents session cookies from being sent over HTTP (man-in-the-middle protection)
- `HTTPONLY = True`: Prevents XSS attacks from stealing session cookies
- `SAMESITE = 'Lax'`: Prevents CSRF attacks by blocking cross-site cookie sending

**SameSite options:**
- `'Strict'`: Never send cookies cross-site (breaks OAuth flows!)
- `'Lax'`: Send cookies on top-level navigation (recommended for allauth)
- `'None'`: Send cookies everywhere (requires `SECURE = True`)

### LOGOUT_ON_PASSWORD_CHANGE

**Default:** `False` (SECURITY GAP!)

**WARNING:** When a user changes their password, existing sessions remain active by default. If an attacker has stolen a session cookie, they can continue accessing the account even after password change.

```python
# Secure configuration
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True  # Invalidate all sessions on password change
```

**Behavior:**
- User changes password
- All other sessions are terminated
- User remains logged in on current device
- Prevents session fixation attacks

### Reauthentication for Sensitive Actions

Force users to re-enter their password before sensitive operations:

```python
# settings.py
ACCOUNT_REAUTHENTICATION_REQUIRED = False  # Global setting
ACCOUNT_REAUTHENTICATION_TIMEOUT = 300     # 5 minutes (default)
```

**Adapter method to require reauthentication:**

```python
# adapters.py
from allauth.account.adapter import DefaultAccountAdapter
from django.utils import timezone

class MyAccountAdapter(DefaultAccountAdapter):
    def is_reauthentication_required(self, request, stage):
        """
        Require reauthentication for specific stages:
        - 'manage_email': Adding/removing email addresses
        - 'change_password': Changing password
        - 'delete_account': Account deletion (custom)
        """
        if stage == "delete_account":
            return True
        return super().is_reauthentication_required(request, stage)
```

### Session Timeout Configuration

```python
# settings.py
SESSION_COOKIE_AGE = 1209600  # 2 weeks (default)

# Session expiration on browser close
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Default

# Remember me functionality
ACCOUNT_SESSION_REMEMBER = None  # Ask user (shows "Remember me" checkbox)
# ACCOUNT_SESSION_REMEMBER = True   # Always remember
# ACCOUNT_SESSION_REMEMBER = False  # Never remember
```

---

## Password Security

Django-allauth integrates with Django's password validation framework.

### Django Password Validators

Configure in `settings.py`:

```python
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,  # Increase from default 8
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
```

**If no validators are configured, django-allauth falls back to:**
```python
ACCOUNT_PASSWORD_MIN_LENGTH = 6  # Weak! Use Django validators instead.
```

### Password Reset Token Security

**Token expiration:**

```python
# settings.py
PASSWORD_RESET_TIMEOUT = 259200  # 3 days (Django default)
# Or: PASSWORD_RESET_TIMEOUT_DAYS = 3  (deprecated)

# Allauth-specific setting
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3  # Email confirmation links
```

**Token generator:**

Django-allauth uses `EmailAwarePasswordResetTokenGenerator` by default, which includes the user's email in the token hash. This means:
- Changing email invalidates password reset tokens
- Prevents token reuse after email change

**Custom token generator:**

```python
# settings.py
ACCOUNT_PASSWORD_RESET_TOKEN_GENERATOR = 'myapp.tokens.MyTokenGenerator'
```

### Password Reset by Code

**Alternative to token links:** Use verification codes instead.

```python
# settings.py
ACCOUNT_PASSWORD_RESET_BY_CODE_ENABLED = True
ACCOUNT_PASSWORD_RESET_BY_CODE_TIMEOUT = 180      # 3 minutes
ACCOUNT_PASSWORD_RESET_BY_CODE_MAX_ATTEMPTS = 3   # Maximum attempts
```

**Security benefits:**
- Short-lived codes (3 minutes vs 3 days)
- Limited attempts
- Harder to phish (user must type code)

### Timing Attack Mitigations

Django-allauth mitigates timing attacks during authentication:

```python
# From allauth/account/auth_backends.py
def _mitigate_timing_attack(self, password):
    """
    For non-existent users, still perform a password hash operation
    to prevent timing analysis.
    """
    get_user_model()().set_password(password)
```

**What this prevents:**
- Attacker measures response time for login attempts
- Failed login for existing user: ~100ms (password hash)
- Failed login for non-existent user: ~1ms (no hash) **← timing leak!**
- With mitigation: Both take ~100ms

---

## Email Verification Security

Email verification tokens can be vulnerable if not configured properly.

### HMAC vs Database Tokens

**Default:** HMAC-based tokens (recommended)

```python
# settings.py
ACCOUNT_EMAIL_CONFIRMATION_HMAC = True  # Default, recommended
```

**HMAC (recommended):**
- No database storage required
- Stateless token generation
- Tokens include expiration timestamp
- Cannot be revoked (except by changing `SECRET_KEY`)

**Database tokens (`HMAC = False`):**
- Stored in `EmailConfirmation` table
- Can be manually revoked
- Requires database queries
- Slower for high-traffic sites

### Email Verification Expiration

```python
# settings.py
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3  # Default
```

**Security considerations:**
- Shorter expiration = more secure (reduces attack window)
- Too short = poor UX (users miss emails)
- **Recommendation:** 3 days for user signups, 1 day for email changes

### Code-Based Verification

**More secure than link-based verification:**

```python
# settings.py
ACCOUNT_EMAIL_VERIFICATION_BY_CODE_ENABLED = True
ACCOUNT_EMAIL_VERIFICATION_BY_CODE_TIMEOUT = 900     # 15 minutes
ACCOUNT_EMAIL_VERIFICATION_BY_CODE_MAX_ATTEMPTS = 3  # Max attempts
```

**Security benefits:**
- Short-lived codes (15 minutes vs 3 days)
- Rate-limited attempts
- Resistant to email forwarding attacks
- Harder to phish

**User experience tradeoff:**
- Requires user to manually enter code
- No one-click verification

### CONFIRM_EMAIL_ON_GET

**Default:** `False` (recommended)

```python
# settings.py
ACCOUNT_CONFIRM_EMAIL_ON_GET = False  # Require POST (CSRF protection)
```

**Why this matters:**
- `GET` requests can be triggered by image tags, prefetching, etc.
- An attacker could verify an email by embedding the link in an image
- `POST` requirement prevents CSRF attacks

**When to enable (`True`):**
- One-click verification from email clients
- Tradeoff: Less secure but better UX

---

## Social Authentication Security

Social authentication introduces additional attack vectors. Proper configuration is critical.

### PKCE Support (OAuth 2.1)

**Proof Key for Code Exchange (PKCE)** prevents authorization code interception attacks.

```python
# settings.py
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': 'YOUR_CLIENT_ID',
            'secret': 'YOUR_SECRET',
        },
        'OAUTH_PKCE_ENABLED': True,  # Recommended for all providers!
    },
    'github': {
        'APP': {'client_id': '...', 'secret': '...'},
        'OAUTH_PKCE_ENABLED': True,
    },
    # Enable for all OAuth2 providers
}
```

**What PKCE prevents:**
1. **Authorization code interception attack:**
   - Attacker intercepts authorization code in redirect
   - Without PKCE: Attacker can exchange code for access token
   - With PKCE: Code exchange requires code verifier (known only to client)

**PKCE is especially important for:**
- Mobile apps (can't securely store client secrets)
- Single-page applications (SPAs)
- Public clients

### State Parameter CSRF Protection

Django-allauth automatically generates a `state` parameter for OAuth flows. This prevents CSRF attacks where an attacker tricks a user into logging in with the attacker's social account.

**How it works:**
1. User clicks "Login with Google"
2. Allauth generates random `state` token, stores in session
3. Redirects to Google with `state` parameter
4. Google redirects back with same `state`
5. Allauth verifies `state` matches session value

**No configuration needed** - this is automatic.

### Token Storage Security

**Default:** `STORE_TOKENS = False` (recommended)

```python
# settings.py
SOCIALACCOUNT_STORE_TOKENS = False  # Don't store tokens in database
```

**WARNING:** If enabled, OAuth access tokens and refresh tokens are stored in **PLAINTEXT** in the `SocialToken` table.

**When to enable:**
- You need to make API calls on behalf of the user
- You're calling Google Calendar, Facebook Graph API, etc.

**If you must store tokens:**
1. Encrypt the database
2. Limit database access
3. Use short-lived tokens with refresh token rotation
4. Consider storing tokens in Redis with TTL instead

### EMAIL_AUTHENTICATION Risk (Account Takeover!)

**Default:** `False` (DO NOT ENABLE unless you trust all providers)

```python
# settings.py
SOCIALACCOUNT_EMAIL_AUTHENTICATION = False  # KEEP THIS FALSE!
```

**What this does:**
- User signs up with email `user@example.com`
- Attacker creates a social account with a malicious OAuth provider
- Attacker's OAuth provider claims email is `user@example.com` (verified)
- If `EMAIL_AUTHENTICATION = True`: **Attacker can now log into the user's account!**

**Only enable if:**
- You're using a single, fully-trusted OAuth provider (e.g., corporate SSO)
- The provider rigorously verifies email ownership

### EMAIL_AUTHENTICATION_AUTO_CONNECT

**Default:** `False`

```python
# settings.py
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = False
```

**If `EMAIL_AUTHENTICATION = True`, this controls whether the social account is permanently linked.**

**Behavior:**
- `False`: Social account is NOT saved; login is ephemeral
- `True`: Social account is added to user's connected accounts

**Security implication:**
- `True` is more dangerous: If attacker gains temporary access via email match, the malicious social account remains connected even after email change

---

## MFA Security Warnings

Django-allauth's MFA implementation has critical security gaps that require attention.

### TOTP Secrets Stored in PLAINTEXT

**CRITICAL SECURITY ISSUE:**

By default, TOTP secrets are stored in **PLAINTEXT** in the `Authenticator` table. If your database is compromised, attackers can generate valid TOTP codes.

**Mitigation:** Encrypt TOTP secrets

```python
# adapters.py
from allauth.mfa.adapter import DefaultMFAAdapter
from cryptography.fernet import Fernet
from django.conf import settings

class SecureMFAAdapter(DefaultMFAAdapter):
    def encrypt(self, secret):
        """Encrypt TOTP secret before database storage."""
        fernet = Fernet(settings.TOTP_ENCRYPTION_KEY)
        return fernet.encrypt(secret.encode()).decode()

    def decrypt(self, encrypted_secret):
        """Decrypt TOTP secret from database."""
        fernet = Fernet(settings.TOTP_ENCRYPTION_KEY)
        return fernet.decrypt(encrypted_secret.encode()).decode()
```

```python
# settings.py
import os
from cryptography.fernet import Fernet

# Generate once: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key())"
TOTP_ENCRYPTION_KEY = os.environ['TOTP_ENCRYPTION_KEY']  # Store in environment variable
MFA_ADAPTER = 'myapp.adapters.SecureMFAAdapter'
```

### Trust Cookie Age (14 Days is Too Long!)

**Default:** 14 days

```python
# settings.py
from datetime import timedelta

MFA_TRUST_ENABLED = True
MFA_TRUST_COOKIE_AGE = timedelta(days=14)  # Too long!
```

**Security risk:**
- User enables "Trust this device"
- Device is stolen/compromised within 14 days
- Attacker bypasses MFA

**Recommended configuration:**

```python
MFA_TRUST_COOKIE_AGE = timedelta(days=7)    # Or even shorter: 3 days
MFA_TRUST_COOKIE_SECURE = True              # HTTPS only
MFA_TRUST_COOKIE_HTTPONLY = True            # Prevent JavaScript access
MFA_TRUST_COOKIE_SAMESITE = 'Strict'        # Strict same-site policy
```

### TOTP_INSECURE_BYPASS_CODE

**CRITICAL:** Never use in production!

```python
# settings.py (DEVELOPMENT ONLY!)
if DEBUG:
    MFA_TOTP_INSECURE_BYPASS_CODE = '123456'  # Development/testing only
```

**What this does:**
- Accepts a hardcoded TOTP code
- Bypasses all MFA security
- **Raises `ImproperlyConfigured` if `DEBUG = False`**

### TOTP_TOLERANCE

**Default:** `0` (most secure)

```python
# settings.py
MFA_TOTP_TOLERANCE = 0  # Accept only current time step
# MFA_TOTP_TOLERANCE = 1  # Accept ±30 seconds (1 step before/after)
```

**Tradeoffs:**
- `0`: Most secure, but clock drift can cause false failures
- `1`: Accepts codes from previous/next 30-second window
- `2`: Accepts codes from ±60 seconds (too lenient)

**Recommendation:** Start with `0`. Increase to `1` only if users report frequent failures.

### Recovery Codes

**Limited security controls:**

```python
# settings.py
MFA_RECOVERY_CODE_COUNT = 10   # Number of codes generated
MFA_RECOVERY_CODE_DIGITS = 8   # Digits per code
```

**Security gaps:**
- No rate limiting on recovery code attempts (rely on `login_failed` rate limit)
- No notification when recovery codes are used
- Users may store recovery codes insecurely

**Best practices:**
- Warn users to store recovery codes securely (password manager, printed copy)
- Send email notification when recovery code is used
- Log recovery code usage for audit trails

---

## Attack Mitigations

How django-allauth protects against common authentication attacks.

### Credential Stuffing

**Attack:** Attacker uses leaked username/password pairs from other breaches.

**Mitigation:**

1. **Rate limiting on login attempts:**
```python
ACCOUNT_RATE_LIMITS = {
    "login_failed": "10/m/ip,5/5m/key",  # 5 failures per 5 min per username/email
}
```

2. **Account lockout (via adapter):**
```python
from allauth.account.adapter import DefaultAccountAdapter
from django.core.cache import cache

class MyAccountAdapter(DefaultAccountAdapter):
    def is_safe_url(self, url):
        return super().is_safe_url(url)

    def get_login_redirect_url(self, request):
        # Check for suspicious login patterns
        failed_attempts = cache.get(f"failed_login:{request.user.pk}", 0)
        if failed_attempts > 10:
            # Send security alert email
            self.send_mail('account/email/security_alert', request.user.email, {})
        return super().get_login_redirect_url(request)
```

3. **Monitor for multiple simultaneous sessions:**
```python
# Custom middleware to detect multiple concurrent sessions
```

### Session Hijacking

**Attack:** Attacker steals session cookie via XSS, network sniffing, or physical access.

**Mitigation:**

1. **Secure cookie flags (required):**
```python
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
```

2. **Logout on password change:**
```python
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True
```

3. **Session rotation on privilege escalation:**
```python
# Django automatically rotates session key on login
# Ensure you're using Django's SessionMiddleware
```

4. **IP address monitoring (via adapter):**
```python
from allauth.account.adapter import DefaultAccountAdapter

class MyAccountAdapter(DefaultAccountAdapter):
    def get_client_ip(self, request):
        # Get IP from request
        ip = super().get_client_ip(request)

        # Store IP in session on login
        if request.user.is_authenticated:
            session_ip = request.session.get('login_ip')
            if session_ip and session_ip != ip:
                # IP changed - potential session hijacking
                # Force re-authentication
                from django.contrib.auth import logout
                logout(request)
        return ip
```

### Password Reset Vulnerabilities

**Attack:** Attacker requests password reset for victim's account.

**Mitigation:**

1. **Token expiration:**
```python
PASSWORD_RESET_TIMEOUT = 259200  # 3 days (Django setting)
```

2. **Rate limiting:**
```python
ACCOUNT_RATE_LIMITS = {
    "reset_password": "20/m/ip,5/m/key",  # Max 5 resets per email per minute
}
```

3. **Email notifications:**
```python
ACCOUNT_EMAIL_NOTIFICATIONS = True  # Notify user of password changes
```

4. **Generic success message (prevent enumeration):**
```python
ACCOUNT_EMAIL_UNKNOWN_ACCOUNTS = False
# Always show: "If an account exists, we've sent an email."
```

### Brute Force Attacks

**Attack:** Attacker tries many passwords for a single account.

**Mitigation:**

1. **Account-specific rate limiting:**
```python
ACCOUNT_RATE_LIMITS = {
    "login_failed": "10/m/ip,5/5m/key",  # "key" = username/email
}
```

2. **Progressive delays (via adapter):**
```python
import time
from allauth.account.adapter import DefaultAccountAdapter
from django.core.cache import cache

class MyAccountAdapter(DefaultAccountAdapter):
    def authentication_failed(self, request, **kwargs):
        username = kwargs.get('username', '')
        cache_key = f"login_attempts:{username}"
        attempts = cache.get(cache_key, 0) + 1
        cache.set(cache_key, attempts, timeout=3600)

        if attempts > 3:
            delay = min(2 ** (attempts - 3), 30)  # Exponential backoff, max 30s
            time.sleep(delay)

        return super().authentication_failed(request, **kwargs)
```

### OAuth State Tampering

**Attack:** Attacker manipulates OAuth state parameter to perform CSRF.

**Mitigation:**

- Django-allauth automatically generates and validates state parameter
- State is stored in session and verified on callback
- No configuration needed (automatic protection)

### Email Verification Bypass

**Attack:** Attacker attempts to use the platform without verifying email.

**Mitigation:**

1. **Require email verification:**
```python
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'  # Block login until verified
```

2. **Short expiration for verification links:**
```python
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 1  # More secure than 3 days
```

3. **Rate limit verification resends:**
```python
ACCOUNT_RATE_LIMITS = {
    "confirm_email": "1/180s/key",  # One attempt per 3 minutes
}
```

---

## Security Checklist

Use this checklist before deploying django-allauth to production.

### Account Security

- [ ] `ACCOUNT_PREVENT_ENUMERATION = True` (default)
- [ ] `ACCOUNT_EMAIL_UNKNOWN_ACCOUNTS = False` (prevents account enumeration)
- [ ] `ACCOUNT_EMAIL_VERIFICATION = 'mandatory'` (require email verification)
- [ ] `ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True` (invalidate other sessions)
- [ ] `ACCOUNT_UNIQUE_EMAIL = True` (default - prevent duplicate emails)
- [ ] `ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3` (or less)
- [ ] `ACCOUNT_CONFIRM_EMAIL_ON_GET = False` (CSRF protection)
- [ ] `AUTH_PASSWORD_VALIDATORS` configured with minimum 12 characters

### Session Security

- [ ] `SESSION_COOKIE_SECURE = True` (HTTPS only)
- [ ] `SESSION_COOKIE_HTTPONLY = True` (prevent XSS)
- [ ] `SESSION_COOKIE_SAMESITE = 'Lax'` or `'Strict'` (CSRF protection)
- [ ] `CSRF_COOKIE_SECURE = True`
- [ ] `CSRF_COOKIE_HTTPONLY = True`
- [ ] `SESSION_COOKIE_AGE` set to reasonable duration (default 2 weeks)

### Rate Limiting

- [ ] Rate limiting enabled (`ACCOUNT_RATE_LIMITS != False`)
- [ ] Redis cache configured for distributed systems
- [ ] Custom rate limits for sensitive endpoints
- [ ] `"login_failed"` rate limit includes per-key limiting

### Social Authentication

- [ ] `OAUTH_PKCE_ENABLED = True` for all OAuth2 providers
- [ ] `SOCIALACCOUNT_STORE_TOKENS = False` (unless needed)
- [ ] `SOCIALACCOUNT_EMAIL_AUTHENTICATION = False` (unless single trusted provider)
- [ ] Provider credentials stored in environment variables (not `settings.py`)
- [ ] Callback URLs use HTTPS in production
- [ ] State parameter validation enabled (automatic)

### MFA Security

- [ ] TOTP secrets encrypted (custom `MFAAdapter.encrypt/decrypt`)
- [ ] `MFA_TOTP_INSECURE_BYPASS_CODE` not set (or only in development)
- [ ] `MFA_TRUST_COOKIE_AGE` set to 7 days or less (if trust enabled)
- [ ] `MFA_TRUST_COOKIE_SECURE = True`
- [ ] `MFA_TRUST_COOKIE_HTTPONLY = True`
- [ ] `MFA_TOTP_TOLERANCE = 0` or `1` (not higher)
- [ ] Recovery code usage logged and monitored

### Password Security

- [ ] Django password validators configured
- [ ] Minimum password length ≥ 12 characters
- [ ] `PASSWORD_RESET_TIMEOUT` set to 3 days or less
- [ ] Password reset emails sent asynchronously (Celery/RQ)
- [ ] `ACCOUNT_EMAIL_NOTIFICATIONS = True` (notify on password change)

### Email Verification

- [ ] `ACCOUNT_EMAIL_CONFIRMATION_HMAC = True` (default)
- [ ] Verification codes preferred over links (`EMAIL_VERIFICATION_BY_CODE_ENABLED`)
- [ ] Short timeout for verification codes (15 minutes)
- [ ] Email backend configured correctly (not console in production!)

### Infrastructure

- [ ] HTTPS enabled (Let's Encrypt, CloudFlare, load balancer)
- [ ] `ALLOWED_HOSTS` configured
- [ ] `SECRET_KEY` stored in environment variable (not version control)
- [ ] `DEBUG = False` in production
- [ ] Security middleware enabled (`SecurityMiddleware`)
- [ ] Database encrypted at rest (for TOTP secrets, tokens)
- [ ] Application logs reviewed regularly for suspicious activity

### Monitoring

- [ ] Failed login attempts logged
- [ ] Successful logins from new IPs logged
- [ ] Password reset requests monitored for abuse
- [ ] Rate limit violations logged
- [ ] MFA bypass attempts logged
- [ ] Security alerts sent to administrators

---

## Additional Resources

- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [Django Security Documentation](https://docs.djangoproject.com/en/stable/topics/security/)
- [Django-Allauth Documentation](https://docs.allauth.org/)

---

**Last Updated:** 2026-01-06
**Version:** 1.0
