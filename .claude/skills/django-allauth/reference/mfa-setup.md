# Multi-Factor Authentication (MFA) Setup Guide

Comprehensive guide for configuring and securing MFA in django-allauth.

---

## Table of Contents

1. [Installation & Setup](#installation--setup)
2. [TOTP Configuration](#totp-configuration)
3. [WebAuthn/Passkeys](#webauthnpasskeys)
4. [Recovery Codes](#recovery-codes)
5. [Trust Device Feature](#trust-device-feature)
6. [CRITICAL SECURITY WARNINGS](#critical-security-warnings)
7. [MFA Enforcement](#mfa-enforcement)
8. [Customization](#customization)

---

## Installation & Setup

### 1. Install MFA Dependencies

```bash
# Install with MFA extras (includes qrcode, webauthn, cryptography)
pip install django-allauth[mfa]
```

This installs:
- `qrcode` - QR code generation for TOTP
- `webauthn` - WebAuthn/passkey support
- `cryptography` - Required for encryption

### 2. Add to INSTALLED_APPS

Order matters! Add `allauth.mfa` BEFORE `allauth.account`:

```python
# settings.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    'allauth',
    'allauth.account',
    'allauth.mfa',  # BEFORE allauth.account
    'allauth.socialaccount',
]
```

### 3. URL Configuration

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),  # MFA URLs included automatically
]
```

MFA endpoints included:
- `/accounts/mfa/activate/totp/` - TOTP setup
- `/accounts/mfa/activate/webauthn/` - Passkey setup
- `/accounts/mfa/authenticate/` - MFA challenge
- `/accounts/mfa/recovery-codes/` - View/regenerate codes
- `/accounts/mfa/deactivate/` - Disable MFA

### 4. Run Migrations

```bash
python manage.py migrate
```

Creates tables:
- `mfa_authenticator` - Stores TOTP/WebAuthn credentials
- `mfa_authenticatorcode` - Recovery codes

### 5. Verify Installation

```python
# Check if MFA is available
from allauth.mfa import app_settings

print(app_settings.SUPPORTED_TYPES)  # ['recovery_codes', 'totp']
```

---

## TOTP Configuration

Time-based One-Time Password (TOTP) is the most common MFA method. Users scan a QR code with Google Authenticator, Authy, or similar apps.

### Basic Settings

```python
# settings.py

# Required: Display name in authenticator apps
MFA_TOTP_ISSUER = "MyApp"  # Shows as "MyApp (user@example.com)"

# Optional: Time window for code validity
MFA_TOTP_PERIOD = 30  # Default: 30 seconds (standard)

# Optional: Number of digits in code
MFA_TOTP_DIGITS = 6  # Default: 6 (do not change unless required)

# Optional: Tolerance for clock drift
MFA_TOTP_TOLERANCE = 0  # Default: 0 (strict)
```

### Understanding MFA_TOTP_TOLERANCE

Critical setting for balancing security vs usability:

```python
# TOLERANCE = 0 (Most Secure - Recommended for Production)
MFA_TOTP_TOLERANCE = 0
# - Only accepts code from current 30s window
# - Pros: Maximum security against replay attacks
# - Cons: Fails if user's clock is off by >15 seconds
# - Use when: Security is paramount

# TOLERANCE = 1 (Balanced)
MFA_TOTP_TOLERANCE = 1
# - Accepts previous, current, and next 30s window (90s total)
# - Pros: Handles minor clock drift (~30-60s)
# - Cons: 3x larger attack window
# - Use when: Users report frequent "code expired" errors

# TOLERANCE = 2 (Lenient - Not Recommended)
MFA_TOTP_TOLERANCE = 2
# - Accepts 5 windows (150s total)
# - Pros: Works with significant clock drift
# - Cons: Major security degradation
# - Use when: Legacy devices with poor time sync
```

### Clock Drift Handling

If users report "code expired" errors:

1. **Check server time sync:**
```bash
# Verify NTP is running
timedatectl status
# Should show "System clock synchronized: yes"
```

2. **User troubleshooting:**
   - Tell users to sync their phone's time (Settings > Date & Time > Auto)
   - Test with multiple TOTP apps to isolate device issues
   - Check timezone settings on both server and client

3. **Before increasing TOLERANCE:**
   - Log failed attempts to identify patterns
   - Consider if clock issues affect other systems
   - Document the security tradeoff

### TOTP Period and Digits

```python
# Non-standard configuration (rare)
MFA_TOTP_PERIOD = 60  # 60-second codes (less secure, more usable)
MFA_TOTP_DIGITS = 8   # 8-digit codes (more secure, harder to type)
```

WARNING: Non-standard values may not work with all authenticator apps!
- Google Authenticator: Supports custom period/digits
- Authy: May not respect custom settings
- Microsoft Authenticator: Usually works

---

## WebAuthn/Passkeys

WebAuthn enables passwordless authentication using hardware keys (YubiKey), device biometrics (Face ID, Touch ID), or passkeys.

### Browser Compatibility Matrix

| Browser | Platform | Support | Notes |
|---------|----------|---------|-------|
| Chrome 90+ | All | Full | Best support |
| Edge 90+ | Windows/Mac | Full | Uses Windows Hello |
| Safari 14+ | macOS/iOS | Full | Face ID/Touch ID |
| Firefox 90+ | All | Full | U2F fallback |
| Chrome Android | Android 9+ | Full | Fingerprint/PIN |
| Safari iOS | iOS 14+ | Full | Face ID/Touch ID |
| IE 11 | Windows | None | Use TOTP fallback |
| Opera | All | Partial | Use Chrome engine version |

### Configuration

```python
# settings.py

# Enable WebAuthn support
MFA_SUPPORTED_TYPES = ['recovery_codes', 'totp', 'webauthn']

# Allow passkey login (without password)
MFA_PASSKEY_LOGIN_ENABLED = True  # Default: False

# Allow passkey during signup (skip password)
MFA_PASSKEY_SIGNUP_ENABLED = True  # Default: False

# DEVELOPMENT ONLY: Allow HTTP origins
MFA_WEBAUTHN_ALLOW_INSECURE_ORIGIN = True  # Default: False
```

### CRITICAL: MFA_WEBAUTHN_ALLOW_INSECURE_ORIGIN

```python
# DEVELOPMENT
MFA_WEBAUTHN_ALLOW_INSECURE_ORIGIN = True  # OK for localhost

# PRODUCTION
MFA_WEBAUTHN_ALLOW_INSECURE_ORIGIN = False  # MUST be False
```

WARNING: WebAuthn REQUIRES HTTPS in production!
- Browsers block WebAuthn on non-HTTPS sites
- Exception: `localhost` and `127.0.0.1` work on HTTP
- Do NOT use in production with HTTP

### Origin Validation

WebAuthn validates the origin (domain) to prevent phishing:

```python
# Correct setup
ALLOWED_HOSTS = ['example.com', 'www.example.com']
# WebAuthn origin: https://example.com
# Passkey registered to: example.com
# ✓ Login works
```

```python
# Incorrect setup (common error)
ALLOWED_HOSTS = ['example.com']
# User registers passkey at: https://example.com
# User tries to login at: https://www.example.com
# ✗ Origin mismatch error
```

Solution: Use consistent subdomain or register both origins.

### Passkey User Experience

When both login and signup are enabled:

```python
MFA_PASSKEY_LOGIN_ENABLED = True
MFA_PASSKEY_SIGNUP_ENABLED = True
```

1. **Signup Flow:**
   - User enters email (no password)
   - Browser prompts for biometric/PIN
   - Passkey created and stored
   - Account created without password

2. **Login Flow:**
   - User enters email
   - Browser prompts for biometric/PIN
   - Logged in (no password, no TOTP)

3. **Fallback:**
   - Users can still set a password later
   - TOTP available as backup

### Implementation Example

```python
# myapp/views.py
from django.contrib.auth.decorators import login_required
from allauth.mfa.adapter import get_adapter as get_mfa_adapter

@login_required
def profile(request):
    adapter = get_mfa_adapter()
    mfa_enabled = adapter.is_mfa_enabled(request.user)

    # Check if browser supports WebAuthn
    webauthn_supported = 'webauthn' in app_settings.SUPPORTED_TYPES

    return render(request, 'profile.html', {
        'mfa_enabled': mfa_enabled,
        'webauthn_supported': webauthn_supported,
    })
```

---

## Recovery Codes

Single-use backup codes for account recovery when users lose their TOTP device or passkey.

### Configuration

```python
# settings.py

# Number of recovery codes to generate
MFA_RECOVERY_CODE_COUNT = 10  # Default: 10

# Length of each code
MFA_RECOVERY_CODE_DIGITS = 8  # Default: 8 (e.g., "12345678")
```

### Code Format

```python
# With defaults (10 codes, 8 digits each)
MFA_RECOVERY_CODE_COUNT = 10
MFA_RECOVERY_CODE_DIGITS = 8

# Generated codes:
# 12345678
# 87654321
# 11223344
# ... (7 more)

# Alternative: Longer codes for higher security
MFA_RECOVERY_CODE_COUNT = 5
MFA_RECOVERY_CODE_DIGITS = 12

# Generated codes:
# 123456789012
# 987654321098
# ... (3 more)
```

Tradeoffs:
- **More codes:** Easier for users to lose/misplace
- **Fewer codes:** Higher risk of lockout
- **Longer codes:** Harder to type, more typos
- **Shorter codes:** Easier to brute force (but hashed)

### Storage Best Practices

Recovery codes are shown ONCE during MFA setup. Users must store them securely:

**Tell users to:**
1. Download codes as text file
2. Print and store in secure location (safe, locked drawer)
3. Use password manager's secure notes
4. Take photo and store in encrypted photo vault

**Warn users NOT to:**
- Email codes to themselves (email compromise = MFA bypass)
- Store in unencrypted notes app
- Share codes with anyone
- Post screenshots online

### Regeneration Guidance

Users can regenerate codes at `/accounts/mfa/recovery-codes/`:

```python
# Template: allauth/mfa/recovery_codes.html
# Shows:
# - Number of unused codes remaining
# - Option to generate new codes (invalidates old ones)
# - Warning about storing new codes
```

**When to regenerate:**
- Lost/used all codes
- Security breach (device compromise)
- Shared codes accidentally
- Regular rotation (e.g., yearly)

**Security consideration:**
```python
# Recovery codes are hashed in database (not plaintext)
from allauth.mfa.models import Authenticator

auth = Authenticator.objects.get(user=user, type=Authenticator.Type.RECOVERY_CODES)
# auth.data contains hashed codes (cannot be retrieved)
```

Users CANNOT view codes after generation - must regenerate!

---

## Trust Device Feature

Allows users to skip MFA for a period after successful authentication.

### Configuration

```python
# settings.py

# Enable device trust
MFA_TRUST_ENABLED = True  # Default: False

# How long to trust device (WARNING: Security risk!)
from datetime import timedelta
MFA_TRUST_COOKIE_AGE = timedelta(days=14)  # Default: 14 days

# Or specify in seconds
MFA_TRUST_COOKIE_AGE = 60 * 60 * 24 * 7  # 7 days (recommended max)

# Cookie name
MFA_TRUST_COOKIE_NAME = "mfa_trusted"  # Default

# Cookie domain (for multi-subdomain setups)
MFA_TRUST_COOKIE_DOMAIN = None  # Default: SESSION_COOKIE_DOMAIN

# Cookie path
MFA_TRUST_COOKIE_PATH = "/"  # Default: SESSION_COOKIE_PATH

# HttpOnly flag (prevent JavaScript access)
MFA_TRUST_COOKIE_HTTPONLY = True  # Default: SESSION_COOKIE_HTTPONLY

# Secure flag (HTTPS only)
MFA_TRUST_COOKIE_SECURE = True  # Default: SESSION_COOKIE_SECURE

# SameSite attribute
MFA_TRUST_COOKIE_SAMESITE = "Lax"  # Default: SESSION_COOKIE_SAMESITE
```

### Cookie Security Settings

CRITICAL: Trust cookies bypass MFA - secure them properly!

```python
# PRODUCTION (Secure)
MFA_TRUST_COOKIE_SECURE = True      # HTTPS only
MFA_TRUST_COOKIE_HTTPONLY = True    # No JavaScript access
MFA_TRUST_COOKIE_SAMESITE = "Strict"  # No cross-site requests
MFA_TRUST_COOKIE_AGE = timedelta(days=7)  # Shorter is safer

# DEVELOPMENT
MFA_TRUST_COOKIE_SECURE = False     # Allow HTTP localhost
MFA_TRUST_COOKIE_HTTPONLY = True    # Still block JavaScript
MFA_TRUST_COOKIE_SAMESITE = "Lax"
```

### Security Warnings

WARNING: Trust device feature significantly reduces MFA security!

**Risks:**
1. **Device theft:** Stolen laptop bypasses MFA for 14 days
2. **Shared computers:** Users forget to logout
3. **Cookie theft:** XSS vulnerabilities steal trust cookie
4. **Public computers:** Users trust library/cafe computers

**Mitigations:**
1. **Reduce cookie age:**
   ```python
   MFA_TRUST_COOKIE_AGE = timedelta(days=3)  # Instead of 14
   ```

2. **Implement device fingerprinting:**
   ```python
   # Custom adapter
   class MyMFAAdapter(DefaultMFAAdapter):
       def get_trust_cookie_value(self, request):
           # Include device fingerprint in cookie
           import hashlib
           fingerprint = f"{request.user.id}:{request.META.get('HTTP_USER_AGENT')}"
           return hashlib.sha256(fingerprint.encode()).hexdigest()
   ```

3. **Provide "logout all devices" functionality:**
   ```python
   # Rotate user's trust secret on security event
   from allauth.mfa.models import Authenticator
   Authenticator.objects.filter(user=request.user).delete()
   ```

4. **Only enable for low-risk applications**

**Best practice:** Do NOT enable for:
- Financial applications
- Healthcare systems
- Admin panels
- Systems handling PII

---

## CRITICAL SECURITY WARNINGS

### 1. TOTP Secrets Stored in PLAINTEXT

DANGER: By default, TOTP secrets are stored unencrypted in the database!

```python
# Default behavior (INSECURE)
from allauth.mfa.adapter import DefaultMFAAdapter

class DefaultMFAAdapter(BaseAdapter):
    def encrypt(self, text: str) -> str:
        return text  # NO ENCRYPTION!

    def decrypt(self, encrypted_text: str) -> str:
        return encrypted_text
```

**If database is compromised:**
- Attacker gets TOTP secrets
- Attacker can generate valid TOTP codes
- MFA is completely bypassed

**Solution: Override encrypt()/decrypt() methods**

```python
# settings.py
MFA_ADAPTER = "myapp.adapters.SecureMFAAdapter"

# myapp/adapters.py
from allauth.mfa.adapter import DefaultMFAAdapter
from cryptography.fernet import Fernet
from django.conf import settings

class SecureMFAAdapter(DefaultMFAAdapter):
    """MFA adapter with encrypted TOTP secret storage."""

    def __init__(self):
        super().__init__()
        # Store encryption key in environment variable!
        key = settings.MFA_ENCRYPTION_KEY.encode()
        self.cipher = Fernet(key)

    def encrypt(self, text: str) -> str:
        """Encrypt TOTP secret before database storage."""
        encrypted = self.cipher.encrypt(text.encode())
        return encrypted.decode('utf-8')

    def decrypt(self, encrypted_text: str) -> str:
        """Decrypt TOTP secret from database."""
        decrypted = self.cipher.decrypt(encrypted_text.encode())
        return decrypted.decode('utf-8')
```

**Generate encryption key:**

```python
# One-time key generation
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())  # Store in environment variable
```

**Environment variable setup:**

```bash
# .env file (DO NOT COMMIT)
MFA_ENCRYPTION_KEY=your-generated-key-here

# settings.py
import os
MFA_ENCRYPTION_KEY = os.environ['MFA_ENCRYPTION_KEY']
```

**Key rotation procedure:**

```python
# When rotating keys
class SecureMFAAdapter(DefaultMFAAdapter):
    def __init__(self):
        super().__init__()
        self.new_cipher = Fernet(settings.MFA_ENCRYPTION_KEY_NEW.encode())
        self.old_cipher = Fernet(settings.MFA_ENCRYPTION_KEY_OLD.encode())

    def decrypt(self, encrypted_text: str) -> str:
        try:
            # Try new key first
            return self.new_cipher.decrypt(encrypted_text.encode()).decode('utf-8')
        except:
            # Fall back to old key
            decrypted = self.old_cipher.decrypt(encrypted_text.encode()).decode('utf-8')
            # Re-encrypt with new key
            self.re_encrypt(encrypted_text)
            return decrypted
```

### 2. MFA_TOTP_INSECURE_BYPASS_CODE

DANGER: Bypass code allows MFA authentication without valid TOTP!

```python
# NEVER IN PRODUCTION
MFA_TOTP_INSECURE_BYPASS_CODE = "123456"  # Any TOTP challenge accepts this

# Django will raise ImproperlyConfigured if DEBUG=False
```

**Use cases (ONLY development/testing):**
- E2E test automation
- Local development without phone
- CI/CD pipeline tests

**Production impact if enabled:**
- Complete MFA bypass
- Attacker just needs to know the code
- Defeats entire purpose of MFA

**Mitigation:**
```python
# settings.py
if DEBUG:
    MFA_TOTP_INSECURE_BYPASS_CODE = os.environ.get('MFA_BYPASS_CODE')
# Never set in production settings
```

### 3. Trust Cookie Age Warning

WARNING: Default 14-day trust period is too long!

```python
# Default (HIGH RISK)
MFA_TRUST_COOKIE_AGE = timedelta(days=14)

# Recommended (MEDIUM RISK)
MFA_TRUST_COOKIE_AGE = timedelta(days=7)

# Secure (LOW RISK)
MFA_TRUST_COOKIE_AGE = timedelta(days=3)

# Very Secure (Consider not enabling trust at all)
MFA_TRUST_ENABLED = False
```

**Attack scenario:**
1. User enables "trust this device"
2. User's laptop is stolen 2 weeks later
3. Attacker has 12 days to access account without MFA
4. Attacker can change password, add MFA, lock out real user

---

## MFA Enforcement

CRITICAL: django-allauth does NOT enforce MFA by default!

### No Built-in Enforcement

Even with MFA configured, users can:
- Skip MFA setup completely
- Login without MFA
- Access all functionality

You MUST implement enforcement yourself.

### Enforcement Strategy 1: Middleware

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
            # Exempt specific URLs (avoid redirect loops)
            exempt_paths = [
                reverse('mfa_activate_totp'),
                reverse('mfa_activate_webauthn'),
                reverse('account_logout'),
            ]

            if request.path not in exempt_paths:
                # Check if MFA required but not enabled
                if request.user.is_staff:
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

### Enforcement Strategy 2: Signals

```python
# myapp/signals.py
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.shortcuts import redirect
from allauth.mfa.adapter import get_adapter as get_mfa_adapter

@receiver(user_logged_in)
def enforce_mfa_on_login(sender, request, user, **kwargs):
    """Redirect to MFA setup after login if not configured."""
    if user.is_staff:
        adapter = get_mfa_adapter()
        if not adapter.is_mfa_enabled(user):
            request.session['mfa_enforce_redirect'] = True

# myapp/views.py
def post_login_view(request):
    if request.session.pop('mfa_enforce_redirect', False):
        messages.info(request, "Staff accounts require MFA. Please set it up.")
        return redirect('mfa_activate_totp')
```

### Enforcement Strategy 3: Grace Period

```python
# myapp/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class MFAEnforcement(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    enforcement_date = models.DateTimeField()
    dismissed_count = models.IntegerField(default=0)

    @classmethod
    def should_enforce(cls, user):
        try:
            enforcement = cls.objects.get(user=user)
            return timezone.now() > enforcement.enforcement_date
        except cls.DoesNotExist:
            return False

# myapp/middleware.py
class GracePeriodMFAMiddleware:
    """Enforce MFA with grace period."""

    def __call__(self, request):
        if request.user.is_authenticated and request.user.is_staff:
            adapter = get_mfa_adapter()

            if not adapter.is_mfa_enabled(request.user):
                # Check if grace period expired
                if MFAEnforcement.should_enforce(request.user):
                    # Force MFA setup
                    return redirect('mfa_activate_totp')
                else:
                    # Show dismissible warning
                    enforcement, created = MFAEnforcement.objects.get_or_create(
                        user=request.user,
                        defaults={'enforcement_date': timezone.now() + timedelta(days=30)}
                    )
                    if created:
                        messages.warning(
                            request,
                            f"MFA will be required in 30 days. Please set it up."
                        )

        return self.get_response(request)
```

### Admin Bypass Patterns

```python
# myapp/middleware.py
class MFAEnforcementMiddleware:
    """Enforce MFA with admin override capability."""

    SUPERUSER_BYPASS_ENABLED = False  # Set to True for emergency access

    def __call__(self, request):
        if request.user.is_authenticated:
            # Emergency bypass for superuser (USE CAREFULLY)
            if self.SUPERUSER_BYPASS_ENABLED and request.user.is_superuser:
                return self.get_response(request)

            # Check MFA enforcement
            adapter = get_mfa_adapter()
            if request.user.is_staff and not adapter.is_mfa_enabled(request.user):
                return redirect('mfa_activate_totp')

        return self.get_response(request)
```

WARNING: Admin bypass should only be enabled temporarily for emergency access!

---

## Customization

### MFAAdapter Methods

Override adapter methods for custom behavior:

```python
# myapp/adapters.py
from allauth.mfa.adapter import DefaultMFAAdapter

class MyMFAAdapter(DefaultMFAAdapter):

    def get_totp_label(self, user) -> str:
        """Customize TOTP label in authenticator apps."""
        return f"{user.get_full_name()} ({user.email})"

    def get_totp_issuer(self) -> str:
        """Customize TOTP issuer name."""
        return "My Company Name"

    def can_delete_authenticator(self, authenticator) -> bool:
        """Prevent users from removing last authenticator."""
        from allauth.mfa.models import Authenticator
        count = Authenticator.objects.filter(user=authenticator.user).count()
        return count > 1  # Must keep at least one

    def generate_authenticator_name(self, user, type) -> str:
        """Custom authenticator naming."""
        if type == Authenticator.Type.TOTP:
            return f"{user.username}'s Authenticator"
        elif type == Authenticator.Type.WEBAUTHN:
            return f"{user.username}'s Security Key"
        return super().generate_authenticator_name(user, type)

# settings.py
MFA_ADAPTER = "myapp.adapters.MyMFAAdapter"
```

### Form Overrides

Customize MFA forms:

```python
# myapp/forms.py
from allauth.mfa.forms import ActivateTOTPForm

class CustomActivateTOTPForm(ActivateTOTPForm):
    def clean_code(self):
        code = super().clean_code()
        # Add custom validation
        if code.startswith('0'):
            raise forms.ValidationError("Invalid code format")
        return code

# settings.py
MFA_FORMS = {
    'activate_totp': 'myapp.forms.CustomActivateTOTPForm',
}
```

### Template Customization

Override MFA templates by creating files in your templates directory:

```
templates/
└── allauth/
    └── mfa/
        ├── activate_totp.html         # TOTP setup page
        ├── authenticate.html          # MFA challenge page
        ├── recovery_codes.html        # View/regenerate codes
        ├── deactivate.html           # Disable MFA
        └── activate_webauthn.html    # Passkey setup
```

### Custom MFA Challenge

```python
# myapp/views.py
from allauth.mfa.views import AuthenticateView

class CustomAuthenticateView(AuthenticateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add custom help text
        context['help_text'] = "Enter code from your authenticator app"
        return context

# urls.py
from myapp.views import CustomAuthenticateView

urlpatterns = [
    path('accounts/mfa/authenticate/', CustomAuthenticateView.as_view(), name='mfa_authenticate'),
    path('accounts/', include('allauth.urls')),
]
```

---

## Summary

Key takeaways for secure MFA implementation:

1. ALWAYS encrypt TOTP secrets (override encrypt()/decrypt())
2. NEVER use MFA_TOTP_INSECURE_BYPASS_CODE in production
3. Keep TOTP_TOLERANCE=0 unless users report issues
4. Reduce trust cookie age to 7 days or less
5. Enforce MFA via middleware/signals (not built-in)
6. Implement grace periods for user adoption
7. Provide admin bypass only for emergencies
8. Test WebAuthn across all target browsers
9. Educate users on recovery code storage
10. Monitor failed MFA attempts for security events
