# Django-allauth Security Blunder Check

Quick reference for the most dangerous and unintuitive security mistakes. Check these when reviewing django-allauth configuration.

---

## Critical Blunders (Data Breach Risk)

### 1. TOTP Secrets Stored in PLAINTEXT
**Default behavior**: MFA TOTP secrets are stored unencrypted in database.
**Impact**: Database leak = all MFA bypassed instantly.
**Check**: Look for `MFAAdapter` with `encrypt()`/`decrypt()` overrides.

```python
# BAD: No encryption (default)
MFA_SUPPORTED_TYPES = ["totp"]  # Secrets stored as plaintext

# GOOD: Encrypted storage
class SecureMFAAdapter(DefaultMFAAdapter):
    def encrypt(self, text):
        from cryptography.fernet import Fernet
        return Fernet(settings.MFA_ENCRYPTION_KEY).encrypt(text.encode()).decode()

    def decrypt(self, encrypted):
        from cryptography.fernet import Fernet
        return Fernet(settings.MFA_ENCRYPTION_KEY).decrypt(encrypted.encode()).decode()

MFA_ADAPTER = "myapp.adapters.SecureMFAAdapter"
```

### 2. Sessions Survive Password Change
**Default behavior**: `ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = False`
**Impact**: Attacker with stolen session stays logged in after password reset.
**Check**: Must be explicitly set to `True`.

```python
# BAD: Default - attacker keeps access
# (no setting = False)

# GOOD: Invalidate all sessions on password change
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True
```

### 3. OAuth Tokens Stored in Plaintext
**Default behavior**: `SOCIALACCOUNT_STORE_TOKENS = True`
**Impact**: Database leak = access to users' Google/GitHub/etc accounts.
**Check**: Should be `False` unless tokens are actively used.

```python
# BAD: Default stores tokens
SOCIALACCOUNT_STORE_TOKENS = True

# GOOD: Don't store unless needed
SOCIALACCOUNT_STORE_TOKENS = False
```

### 4. Email Authentication Without Verification = Account Takeover
**Combination**: `ACCOUNT_EMAIL_AUTHENTICATION = True` + unverified emails
**Impact**: Attacker signs up with victim's email → social login auto-connects → takeover.
**Check**: Both settings must be coordinated.

```python
# BAD: Auto-connect by email without verification
ACCOUNT_EMAIL_AUTHENTICATION = True
ACCOUNT_EMAIL_VERIFICATION = "none"

# GOOD: Require verification before email-based matching
ACCOUNT_EMAIL_AUTHENTICATION = True
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
```

---

## High-Risk Blunders (Security Degradation)

### 5. Signed Cookies Session Backend
**Setting**: `SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"`
**Impact**: Email verification codes lost on redirect → verification fails.
**Check**: Must NOT use signed_cookies.

```python
# BAD: Loses verification state
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"

# GOOD: Server-side sessions
SESSION_ENGINE = "django.contrib.sessions.backends.db"  # or cached_db
```

### 6. Silent Email Failures
**Default behavior**: No `EMAIL_BACKEND` configured = emails silently discarded.
**Impact**: Password resets, email verification all fail without error.
**Check**: Must have explicit email backend.

```python
# BAD: No configuration (silent failure)
# EMAIL_BACKEND not set

# GOOD: At minimum, console for dev
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"  # Dev
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"     # Prod
```

### 7. No Rate Limiting
**Default behavior**: No rate limits configured.
**Impact**: Brute force attacks on login, password reset abuse.
**Check**: `ACCOUNT_RATE_LIMITS` should be configured.

```python
# BAD: No rate limiting (default)
# ACCOUNT_RATE_LIMITS not set

# GOOD: Configure limits
ACCOUNT_RATE_LIMITS = {
    "login_failed": "5/m/ip,10/h/ip",      # 5/min, 10/hour per IP
    "signup": "5/m/ip",                     # Prevent mass signup
    "reset_password": "5/m/ip,20/h/ip",    # Prevent reset abuse
    "change_password": "5/m/user",
}
```

### 8. Account Enumeration Enabled
**Setting**: `ACCOUNT_PREVENT_ENUMERATION = False`
**Impact**: Attackers can discover valid email addresses.
**Check**: Should be `True` (which is the default, but verify).

```python
# BAD: Reveals which accounts exist
ACCOUNT_PREVENT_ENUMERATION = False

# GOOD: Default, but verify it's not overridden
ACCOUNT_PREVENT_ENUMERATION = True
```

---

## Medium-Risk Blunders (Best Practice Violations)

### 9. PKCE Not Enabled for OAuth
**Default behavior**: PKCE disabled for OAuth2 providers.
**Impact**: Vulnerable to authorization code interception.
**Check**: Enable for each provider.

```python
# BAD: No PKCE
SOCIALACCOUNT_PROVIDERS = {
    "google": {"SCOPE": ["profile", "email"]}
}

# GOOD: PKCE enabled
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "OAUTH_PKCE_ENABLED": True,
    }
}
```

### 10. MFA Bypass Code in Production
**Setting**: `MFA_TOTP_INSECURE_BYPASS_CODE`
**Impact**: Hardcoded code bypasses all MFA.
**Check**: Must NEVER be set in production.

```python
# CRITICAL: Never in production
MFA_TOTP_INSECURE_BYPASS_CODE = "123456"  # DELETE THIS
```

### 11. SITE_ID Mismatch
**Issue**: `SITE_ID` doesn't match Site object in database.
**Impact**: Email verification links have wrong domain.
**Check**: Verify Site.objects.get(pk=SITE_ID).domain matches actual domain.

```python
# Verify in Django shell:
from django.contrib.sites.models import Site
from django.conf import settings
site = Site.objects.get(pk=settings.SITE_ID)
print(f"Domain: {site.domain}")  # Must match your actual domain
```

### 12. Missing Session Security Headers
**Check**: Production cookie settings.

```python
# Required for production
SESSION_COOKIE_SECURE = True      # HTTPS only
SESSION_COOKIE_HTTPONLY = True    # No JavaScript access
CSRF_COOKIE_SECURE = True         # HTTPS only
```

---

## Quick Audit Checklist

Run through this list when auditing django-allauth security:

```
[ ] TOTP secrets encrypted? (MFAAdapter.encrypt/decrypt)
[ ] ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True?
[ ] SOCIALACCOUNT_STORE_TOKENS = False?
[ ] EMAIL_BACKEND explicitly configured?
[ ] SESSION_ENGINE != signed_cookies?
[ ] ACCOUNT_RATE_LIMITS configured?
[ ] ACCOUNT_PREVENT_ENUMERATION = True? (default)
[ ] OAUTH_PKCE_ENABLED for OAuth2 providers?
[ ] No MFA_TOTP_INSECURE_BYPASS_CODE in production?
[ ] SITE_ID matches actual domain?
[ ] SESSION_COOKIE_SECURE = True in production?
[ ] If ACCOUNT_EMAIL_AUTHENTICATION = True, also ACCOUNT_EMAIL_VERIFICATION = "mandatory"?
```

---

## Settings to Grep For

Quick grep patterns to find potential issues:

```bash
# Find dangerous settings
grep -r "LOGOUT_ON_PASSWORD_CHANGE" .          # Should be True
grep -r "STORE_TOKENS" .                        # Should be False
grep -r "signed_cookies" .                      # Should not exist
grep -r "INSECURE_BYPASS" .                     # Should not exist
grep -r "EMAIL_UNKNOWN_ACCOUNTS.*True" .        # Should not exist
grep -r "PREVENT_ENUMERATION.*False" .          # Should not exist
grep -r "EMAIL_VERIFICATION.*none" .            # Verify intentional
```
