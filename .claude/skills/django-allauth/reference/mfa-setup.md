# Multi-Factor Authentication (MFA) Setup Guide

Quick setup guide for configuring MFA in django-allauth with critical security warnings.

---

## Installation & Setup

### 1. Install MFA Dependencies

```bash
pip install django-allauth[mfa]
```

### 2. Add to INSTALLED_APPS

Order matters! Add `allauth.mfa` BEFORE `allauth.account`:

```python
# settings.py
INSTALLED_APPS = [
    # ... django apps ...
    'allauth',
    'allauth.account',
    'allauth.mfa',  # BEFORE allauth.account
    'allauth.socialaccount',
]
```

### 3. URL Configuration

```python
# urls.py
urlpatterns = [
    path('accounts/', include('allauth.urls')),  # MFA URLs included automatically
]
```

### 4. Run Migrations

```bash
python manage.py migrate
```

---

## TOTP Configuration

### Settings

```python
# settings.py

# Required: Display name in authenticator apps
MFA_TOTP_ISSUER = "MyApp"

# Optional: Time window for code validity
MFA_TOTP_PERIOD = 30  # Default: 30 seconds (standard)
MFA_TOTP_DIGITS = 6   # Default: 6 (standard)

# Optional: Tolerance for clock drift
MFA_TOTP_TOLERANCE = 0  # Default: 0 (strict, recommended)
```

### Tolerance Levels

```python
# TOLERANCE = 0 (Recommended) - Only current 30s window
# TOLERANCE = 1 (Balanced) - 90s total window (previous, current, next)
# TOLERANCE = 2 (Not Recommended) - 150s window, major security degradation
```

If users report "code expired" errors:
1. Check server NTP sync: `timedatectl status`
2. Tell users to enable automatic time sync
3. Only increase TOLERANCE as last resort

---

## WebAuthn/Passkeys

WebAuthn enables hardware keys (YubiKey), device biometrics (Face ID, Touch ID), or passkeys.

**Browser Support:** Chrome 90+, Edge 90+, Safari 14+, Firefox 90+ on all major platforms. iOS 14+ and Android 9+ support biometric authentication.

### Configuration

```python
# settings.py

# Enable WebAuthn support
MFA_SUPPORTED_TYPES = ['recovery_codes', 'totp', 'webauthn']

# Allow passkey login/signup (without password)
MFA_PASSKEY_LOGIN_ENABLED = True   # Default: False
MFA_PASSKEY_SIGNUP_ENABLED = True  # Default: False

# DEVELOPMENT ONLY: Allow HTTP origins
MFA_WEBAUTHN_ALLOW_INSECURE_ORIGIN = True  # Default: False
```

**WARNING:** WebAuthn REQUIRES HTTPS in production! Set `MFA_WEBAUTHN_ALLOW_INSECURE_ORIGIN = False` for production.

---

## Recovery Codes

Single-use backup codes for account recovery.

```python
# settings.py
MFA_RECOVERY_CODE_COUNT = 10   # Default: 10
MFA_RECOVERY_CODE_DIGITS = 8   # Default: 8
```

**User Guidance:**
- Codes shown ONCE during setup - store securely
- Download to password manager or print and secure
- DO NOT email codes or store in unencrypted notes
- Regenerate at `/accounts/mfa/recovery-codes/` (invalidates old codes)

---

## Trust Device Feature

Allows users to skip MFA for a period after authentication.

```python
# settings.py
MFA_TRUST_ENABLED = True  # Default: False
MFA_TRUST_COOKIE_AGE = timedelta(days=7)  # Default: 14 (reduce to 7 or less)

# Cookie security (CRITICAL for production)
MFA_TRUST_COOKIE_SECURE = True      # HTTPS only
MFA_TRUST_COOKIE_HTTPONLY = True    # Prevent JavaScript access
MFA_TRUST_COOKIE_SAMESITE = "Strict"
```

**WARNING:** Trust device reduces MFA security! Risks include stolen devices, cookie theft, and shared computers. Disable for high-security applications.

---

## CRITICAL SECURITY WARNINGS

### 1. TOTP Secrets Stored in PLAINTEXT

**DANGER:** By default, TOTP secrets are stored unencrypted!

If database is compromised, attackers can generate valid TOTP codes and bypass MFA completely.

**Solution: Implement encryption**

```python
# settings.py
MFA_ADAPTER = "myapp.adapters.SecureMFAAdapter"

# myapp/adapters.py
from allauth.mfa.adapter import DefaultMFAAdapter
from cryptography.fernet import Fernet
from django.conf import settings

class SecureMFAAdapter(DefaultMFAAdapter):
    def __init__(self):
        super().__init__()
        key = settings.MFA_ENCRYPTION_KEY.encode()
        self.cipher = Fernet(key)

    def encrypt(self, text: str) -> str:
        encrypted = self.cipher.encrypt(text.encode())
        return encrypted.decode('utf-8')

    def decrypt(self, encrypted_text: str) -> str:
        decrypted = self.cipher.decrypt(encrypted_text.encode())
        return decrypted.decode('utf-8')
```

**Generate encryption key:**

```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())  # Store in environment variable
```

```bash
# .env file (DO NOT COMMIT)
MFA_ENCRYPTION_KEY=your-generated-key-here
```

### 2. MFA_TOTP_INSECURE_BYPASS_CODE

**DANGER:** Bypass code allows authentication without valid TOTP!

```python
# NEVER IN PRODUCTION
MFA_TOTP_INSECURE_BYPASS_CODE = "123456"
```

Use ONLY for development, testing, and CI/CD. Django raises error if `DEBUG=False` and this is set.

### 3. Trust Cookie Age

Default 14-day trust period is too long! Reduce to 7 days or less:

```python
MFA_TRUST_COOKIE_AGE = timedelta(days=7)   # Recommended
MFA_TRUST_COOKIE_AGE = timedelta(days=3)   # More secure
MFA_TRUST_ENABLED = False                  # Most secure
```

---

## MFA Enforcement

**CRITICAL:** django-allauth does NOT enforce MFA by default! Users can skip setup entirely. You must implement enforcement.

### Enforcement via Middleware

```python
# myapp/middleware.py
from django.shortcuts import redirect
from django.urls import reverse
from allauth.mfa.adapter import get_adapter as get_mfa_adapter

class MFAEnforcementMiddleware:
    """Require all staff users to enable MFA."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            exempt_paths = [
                reverse('mfa_activate_totp'),
                reverse('mfa_activate_webauthn'),
                reverse('account_logout'),
            ]

            if request.path not in exempt_paths and request.user.is_staff:
                adapter = get_mfa_adapter()
                if not adapter.is_mfa_enabled(request.user):
                    return redirect('mfa_activate_totp')

        return self.get_response(request)

# settings.py
MIDDLEWARE = [
    # ... other middleware ...
    'myapp.middleware.MFAEnforcementMiddleware',
]
```

---

## Summary

**Essential security requirements:**

1. **Encrypt TOTP secrets** - Override `encrypt()`/`decrypt()` methods
2. **Never use bypass code in production**
3. **Keep TOTP_TOLERANCE=0** unless users report issues
4. **Reduce trust cookie age** to 7 days or less (or disable)
5. **Enforce MFA** via middleware (not automatic)
6. **Use HTTPS** for WebAuthn in production
7. **Educate users** on recovery code storage
