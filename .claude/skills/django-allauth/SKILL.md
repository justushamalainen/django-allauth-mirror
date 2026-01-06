# Django-AllAuth Skill

Use this skill when working with django-allauth for authentication, social login, MFA, or headless API. Helps with setup, configuration, customization via adapters/signals, and security hardening.

---

## Table of Contents

1. [When to Use This Skill](#when-to-use-this-skill)
2. [Core Concepts](#core-concepts)
3. [Setup & Installation](#setup--installation)
4. [Social Authentication](#social-authentication)
5. [Customization](#customization-adapters-signals-forms)
6. [Multi-Factor Authentication](#multi-factor-authentication)
7. [Headless/API Mode](#headlessapi-mode)
8. [Email Configuration](#email-configuration)
9. [Security Best Practices](#security-best-practices)
10. [Custom Providers](#custom-providers)
11. [Helper Scripts](#helper-scripts)
12. [Common Workflows](#common-workflows)

---

## When to Use This Skill

Invoke this skill when working with:

- **Setup**: Installing allauth, configuring INSTALLED_APPS, URL patterns, migrations
- **Social Auth**: Google, GitHub, Facebook OAuth; OAuth2/OIDC providers; callback URLs
- **Customization**: AccountAdapter, SocialAccountAdapter, signals (user_signed_up, email_confirmed), form overrides
- **MFA**: TOTP, WebAuthn, passkeys, recovery codes, enforcement
- **Headless**: JWT tokens, session auth, SPA/mobile integration, CORS
- **Email**: Verification workflows, custom templates, code vs link verification
- **Security**: Rate limiting, enumeration prevention, reauthentication, PKCE
- **Custom**: Building OAuth2/OIDC providers, extending auth flows

**Key Terms**: django-allauth, OAuth2, OIDC, social login, AccountAdapter, SocialAccountAdapter, MFA, TOTP, WebAuthn, JWT, headless, rate limiting

---

## Core Concepts

**Adapter Pattern**: Every module has an adapter for deep customization:
- `DefaultAccountAdapter` - Local authentication
- `DefaultSocialAccountAdapter` - Social authentication
- `DefaultMFAAdapter` - Multi-factor authentication
- `HeadlessAdapter` - API mode

Override adapter methods, then configure via settings:
```python
ACCOUNT_ADAPTER = 'myapp.adapters.CustomAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'myapp.adapters.CustomSocialAccountAdapter'
```

**Signals**: Event-driven hooks for user_signed_up, user_logged_in, email_confirmed, pre_social_login

**Multi-App Architecture**: account (local auth), socialaccount (OAuth), mfa, headless (APIs), usersessions

---

## Setup & Installation

**Quick Install:** `pip install django-allauth`

**Required Configuration:**
```python
INSTALLED_APPS = ['django.contrib.sites', 'allauth', 'allauth.account', 'allauth.socialaccount']
SITE_ID = 1
AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend',
                          'allauth.account.auth_backends.AuthenticationBackend']
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
```

**URLs:** `path('accounts/', include('allauth.urls'))`

**Critical Prerequisites:**
- Python 3.8+, Django 4.2+; Email backend configured (emails fail silently); `SESSION_ENGINE` cannot be `signed_cookies`; `SITE_ID = 1`

**Custom User Models:** Set `ACCOUNT_USER_MODEL_USERNAME_FIELD` and `ACCOUNT_USER_MODEL_EMAIL_FIELD`

**Reference**: `reference/setup-guide.md` for complete guide. Use `scripts/check_allauth_setup.py` to verify.

---

## Social Authentication

**Setup Process:**
1. Add provider app: `'allauth.socialaccount.providers.google'`
2. Configure provider settings
3. Add Social App in admin (Client ID, Secret)
4. Configure callback URL: `https://domain.com/accounts/google/login/callback/`

**Provider Configuration:**
```python
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'OAUTH_PKCE_ENABLED': True,  # Security enhancement
    }
}
```

**Auto-Signup & Email Conflicts:**
```python
SOCIALACCOUNT_AUTO_SIGNUP = True
ACCOUNT_EMAIL_AUTHENTICATION = True  # Match existing users by email
```

**Security Considerations:**
- Don't store tokens: `SOCIALACCOUNT_STORE_TOKENS = False`
- Enable PKCE for OAuth2 providers
- Verify email before account linking

**127+ Providers Supported**: Google, GitHub, Facebook, Microsoft, Apple, Twitter, LinkedIn, etc.

**Reference**: `reference/social-providers.md` for top 5 provider setup guides, `reference/callback-url-debugging.md` for common errors, `reference/oauth2-vs-oidc.md` for protocol differences.

---

## Customization (Adapters, Signals, Forms)

**AccountAdapter - Common Overrides:**
```python
class CustomAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        return '/dashboard/'
    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=False)
        # Add custom fields
        if commit: user.save()
        return user
```

**SocialAccountAdapter:** Override `pre_social_login()` to connect existing users, `is_auto_signup_allowed()` for access control

**Configure:** `ACCOUNT_ADAPTER = 'myapp.adapters.CustomAccountAdapter'`

**Signals:** `user_signed_up`, `email_confirmed`, `user_logged_in`, `pre_social_login`
```python
@receiver(user_signed_up)
def create_profile(sender, request, user, **kwargs):
    Profile.objects.create(user=user)
```

**Forms:** Override via `ACCOUNT_FORMS = {'signup': 'myapp.forms.CustomSignupForm'}`

**Reference**: `reference/customization.md` for 60+ adapter methods. Use `scripts/generate_adapter.py`.

---

## Multi-Factor Authentication

**Setup:**
```python
INSTALLED_APPS += ['allauth.mfa']
MFA_SUPPORTED_TYPES = ["recovery_codes", "totp", "webauthn"]
MFA_TOTP_ISSUER = "MyApp"
MFA_PASSKEY_LOGIN_ENABLED = True
```

**TOTP:** Configure via `MFA_TOTP_PERIOD` (30s default), `MFA_TOTP_TOLERANCE` (±30s drift)

**Security Warnings:**
- TOTP secrets stored PLAINTEXT by default - override `MFAAdapter.encrypt()/decrypt()`
- Never set `MFA_TOTP_INSECURE_BYPASS_CODE` in production

**WebAuthn:** Chrome 67+, Firefox 60+, Safari 13+. Supports hardware keys and platform authenticators.

**Enforcement:** Override `AccountAdapter.is_mfa_required(request, user)` to enforce for specific users

**Reference**: `reference/mfa-setup.md`, `reference/mfa-security.md` for encryption.

---

## Headless/API Mode

**Setup:**
```python
INSTALLED_APPS += ['allauth.headless']
HEADLESS_TOKEN_STRATEGY = "allauth.headless.tokens.SessionTokenStrategy"  # or JWT
HEADLESS_ONLY = True  # JSON only
```

**CORS:** Install `django-cors-headers`, set `CORS_ALLOWED_ORIGINS`, `CORS_ALLOW_CREDENTIALS = True`

**JWT:** Set strategy to `jwt.JWTTokenStrategy`, configure `SIMPLE_JWT` lifetimes

**Key Endpoints:** POST `/auth/signup/`, `/auth/login/`, `/auth/logout/`, GET `/auth/user/`, POST `/auth/token/refresh/`

**Frontend:**
```javascript
fetch('/accounts/auth/login/', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  credentials: 'include',
  body: JSON.stringify({username, password})
});
```

**Reference**: `reference/headless-api.md` (34 endpoints), `reference/headless-cors.md`, `reference/headless-jwt.md`.

---

## Email Configuration

**Verification Modes:** `ACCOUNT_EMAIL_VERIFICATION = 'mandatory'` (must verify), `'optional'` (encouraged), `'none'`

**Methods:** Link-based (default) or code-based via `ACCOUNT_EMAIL_VERIFICATION_BY_CODE_ENABLED = True`

**Custom Templates:** Create in `templates/account/email/` - `email_confirmation_subject.txt`, `email_confirmation_message.txt`, etc.

**Context Variables:** `{{ user }}`, `{{ activate_url }}`, `{{ key }}`, `{{ current_site }}`

**Backend:** Use `console.EmailBackend` for dev, `smtp.EmailBackend` for production with SMTP settings

**Reference**: `reference/email-templates.md` (40 templates), `reference/email-deliverability.md` (SPF/DKIM).

---

## Security Best Practices

**Rate Limiting:** Configure `ACCOUNT_RATE_LIMITS` dict with format `"10/m/ip,5/5m/key"` for login_failed, signup, reset_password, etc.

**Enumeration Prevention:** `ACCOUNT_PREVENT_ENUMERATION = True` (default, don't reveal accounts)

**Reauthentication:** `ACCOUNT_REAUTHENTICATION_REQUIRED = True` for sensitive actions

**Session Security:**
```python
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True  # Default False - security gap!
SESSION_COOKIE_SECURE = True  # HTTPS only
SESSION_COOKIE_HTTPONLY = True
```

**OAuth:** `SOCIALACCOUNT_STORE_TOKENS = False` (plaintext risk), enable `OAUTH_PKCE_ENABLED`

**Critical:** Never set `ACCOUNT_EMAIL_UNKNOWN_ACCOUNTS = True`. `LOGOUT_ON_PASSWORD_CHANGE` defaults False.

**Reference**: `reference/security.md`, `reference/security-checklist.md`, `scripts/security_audit.py`.

---

## Custom Providers

**Basic Provider:**
```python
class CustomProvider(OAuth2Provider):
    id = 'custom'
    name = 'Custom Provider'
    def extract_uid(self, data):
        return str(data['id'])
    def extract_common_fields(self, data):
        return dict(email=data.get('email'), username=data.get('username'))
```

**OAuth2 Adapter:** Extend `OAuth2Adapter`, set `access_token_url`, `authorize_url`, `profile_url`, implement `complete_login()`

**Reference**: `reference/custom-provider.md` for complete guide with URL configuration and testing.

---

## Helper Scripts

**check_allauth_setup.py** - Verifies installation and auto-fixes issues
- Checks: Django/Python versions, INSTALLED_APPS, AUTHENTICATION_BACKENDS, SESSION_ENGINE, EMAIL_BACKEND, SITE_ID, migrations
- Usage: `python scripts/check_allauth_setup.py`

**add_social_provider.py** - Interactive provider setup wizard
- Features: Provider selection, settings generation, callback URL format, admin instructions
- Usage: `python scripts/add_social_provider.py`

**generate_adapter.py** - Scaffolds custom adapters
- Features: Adapter type selection, method override menu by category, boilerplate code generation
- Usage: `python scripts/generate_adapter.py`

---

## Common Workflows

**1. Add Google OAuth:**
- Add `'allauth.socialaccount.providers.google'` to INSTALLED_APPS
- Create Social App in admin (Client ID, Secret)
- Configure callback: `https://domain.com/accounts/google/login/callback/`

**2. Customize Signup:**
- Create custom `AccountAdapter` with `save_user()` override
- Set `ACCOUNT_ADAPTER = 'myapp.adapters.CustomAccountAdapter'`
- Add `@receiver(user_signed_up)` signal for post-signup tasks

**3. Headless API with JWT:**
- Install: `pip install djangorestframework-simplejwt django-cors-headers`
- Add `'allauth.headless'` to INSTALLED_APPS
- Set `HEADLESS_TOKEN_STRATEGY` to JWT
- Configure CORS with `CORS_ALLOW_CREDENTIALS = True`

**4. Enable MFA:**
- Add `'allauth.mfa'` to INSTALLED_APPS
- Set `MFA_SUPPORTED_TYPES = ["recovery_codes", "totp"]`
- Run `migrate allauth.mfa`
- Users configure at `/accounts/mfa/`

**5. Custom Email Templates:**
- Create `templates/account/email/`
- Copy templates (subject.txt, message.txt)
- Use `{{ user }}`, `{{ activate_url }}`, `{{ key }}`

---

## Reference Files

All detailed documentation in `reference/`:

- `setup-guide.md` - Complete installation and troubleshooting
- `social-providers.md` - Google, GitHub, Facebook, Microsoft, Apple setup
- `customization.md` - 60+ adapter methods, signals, forms
- `mfa-setup.md` - Multi-factor configuration and enforcement
- `headless-api.md` - Complete API documentation (34 endpoints)
- `email-templates.md` - All 40 templates with context variables
- `security.md` - Comprehensive security guide and attack mitigations
- `custom-provider.md` - OAuth2/OIDC provider development

Scripts in `scripts/`: check_allauth_setup.py, add_social_provider.py, generate_adapter.py
