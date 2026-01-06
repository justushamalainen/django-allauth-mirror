# Django-AllAuth Skills Plan

## Executive Summary

Based on analysis of the django-allauth codebase (v65.14.0), this document outlines a comprehensive plan for creating Claude Skills to help developers use django-allauth efficiently and idiomatically.

---

## Codebase Analysis Summary

### Core Modules
| Module | Purpose | Key Extension Points |
|--------|---------|---------------------|
| `account` | Local authentication, signup, password management | AccountAdapter, signals, forms |
| `socialaccount` | OAuth/OIDC/SAML social login (127 providers) | SocialAccountAdapter, provider classes |
| `mfa` | Multi-factor authentication (TOTP, WebAuthn, recovery) | MFAAdapter |
| `headless` | JSON REST API for SPAs/mobile | HeadlessAdapter, JWT tokens |
| `idp` | Identity Provider (OIDC server) | OIDCAdapter |
| `usersessions` | Session tracking across devices | UserSessionsAdapter |

### Key Patterns
1. **Adapter Pattern** - Every module has an adapter for deep customization
2. **Signals** - Event-driven hooks (user_signed_up, email_confirmed, etc.)
3. **Form Overrides** - Custom form classes via settings
4. **Login Stages** - Multi-step authentication flows
5. **Provider System** - OAuth2/OIDC provider implementations

---

## Proposed Skills Structure

### Option A: Single Comprehensive Skill (Recommended for Start)

```
django-allauth/
├── SKILL.md                    # Main skill file (~400 lines)
└── reference/
    ├── setup-guide.md          # Installation & basic configuration
    ├── social-providers.md     # Social auth setup (Google, GitHub, etc.)
    ├── customization.md        # Adapters, signals, forms
    ├── mfa-setup.md            # Multi-factor authentication
    ├── headless-api.md         # API mode for SPAs
    ├── security.md             # Rate limiting, enumeration prevention
    ├── email-templates.md      # Custom email templates
    └── scripts/
        ├── check_allauth_setup.py    # Verify installation
        ├── add_social_provider.py    # Interactive provider setup
        └── generate_adapter.py       # Scaffold custom adapter
```

**Pros:**
- Single entry point for all allauth tasks
- Claude can understand context across features
- Easier to maintain one skill

**Cons:**
- Larger context load for simple tasks
- May exceed 500 lines if not careful

---

### Option B: Multiple Focused Skills

```
django-allauth-setup/
├── SKILL.md                    # Basic setup & configuration
└── reference/
    ├── installation.md
    └── basic-settings.md

django-allauth-social/
├── SKILL.md                    # Social authentication
└── reference/
    ├── provider-setup.md
    ├── google.md
    ├── github.md
    └── custom-provider.md

django-allauth-customize/
├── SKILL.md                    # Customization patterns
└── reference/
    ├── adapters.md
    ├── signals.md
    └── forms.md

django-allauth-mfa/
├── SKILL.md                    # Multi-factor authentication
└── reference/
    ├── totp.md
    └── webauthn.md

django-allauth-headless/
├── SKILL.md                    # Headless/API mode
└── reference/
    ├── jwt-setup.md
    └── spa-integration.md
```

**Pros:**
- Focused, smaller context per task
- User can install only what they need
- Better token efficiency

**Cons:**
- Multiple skills to manage
- Context split across skills

---

## Recommended Approach: Hybrid

Start with **Option A** (single comprehensive skill), then split into focused skills if the main skill grows too large.

---

## Skill Topics & Content Outline

### 1. Setup & Installation
**When to use:** New projects, adding allauth to existing project

**Content:**
- Installation command
- Required INSTALLED_APPS
- Middleware configuration
- URL configuration
- Database migrations
- Basic settings template

**Scripts:**
- `check_allauth_setup.py` - Verify correct installation

---

### 2. Social Authentication
**When to use:** Adding Google, GitHub, Facebook, or other OAuth login

**Content:**
- Provider configuration patterns
- OAuth2 flow explanation
- Database vs settings-based app config
- Common providers quick-start (Google, GitHub, Facebook, Microsoft)
- Handling email conflicts
- Auto-signup configuration

**Scripts:**
- `add_social_provider.py` - Interactive setup helper

**Key settings:**
```python
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
    }
}
```

---

### 3. Customization (Adapters, Signals, Forms)
**When to use:** Custom signup fields, redirect logic, email handling

**Content:**
- AccountAdapter methods reference
- SocialAccountAdapter methods reference
- Signal handlers (user_signed_up, email_confirmed, etc.)
- Form override patterns
- Custom username generation
- Custom redirect URLs

**Scripts:**
- `generate_adapter.py` - Scaffold custom adapter class

**Key patterns:**
```python
# Adapter example
class CustomAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        return '/dashboard/'

# Signal example
@receiver(user_signed_up)
def create_profile(sender, request, user, **kwargs):
    Profile.objects.create(user=user)
```

---

### 4. Multi-Factor Authentication (MFA)
**When to use:** Adding TOTP, WebAuthn/passkeys, recovery codes

**Content:**
- MFA installation and setup
- TOTP configuration
- WebAuthn/FIDO2 setup
- Recovery codes
- "Trust this device" feature
- MFA enforcement

**Key settings:**
```python
MFA_SUPPORTED_TYPES = ["recovery_codes", "totp", "webauthn"]
MFA_TOTP_ISSUER = "MyApp"
MFA_PASSKEY_LOGIN_ENABLED = True
```

---

### 5. Headless/API Mode
**When to use:** SPAs, React/Vue/mobile apps, API-only authentication

**Content:**
- Headless mode setup
- JWT token configuration
- Session vs JWT strategy
- API endpoints reference
- Frontend integration patterns
- CORS configuration

**Key settings:**
```python
HEADLESS_ONLY = True  # Disable traditional views
HEADLESS_TOKEN_STRATEGY = "allauth.headless.tokens.strategies.jwt.JWTTokenStrategy"
```

---

### 6. Email Configuration
**When to use:** Custom email templates, verification workflows

**Content:**
- Email verification modes (mandatory/optional/none)
- Code-based vs link-based verification
- Custom email templates
- Email subject customization
- Sending custom emails via adapter

**Template locations:**
```
templates/account/email/
├── email_confirmation_message.txt
├── email_confirmation_subject.txt
├── password_reset_key_message.txt
└── password_reset_key_subject.txt
```

---

### 7. Security Best Practices
**When to use:** Hardening authentication, rate limiting

**Content:**
- Rate limiting configuration
- Account enumeration prevention
- Reauthentication for sensitive actions
- Login attempt throttling
- Secure password reset flows

**Key settings:**
```python
ACCOUNT_PREVENT_ENUMERATION = True
ACCOUNT_RATE_LIMITS = {
    "login_failed": "10/m/ip,5/5m/key",
    "signup": "20/m/ip",
}
ACCOUNT_REAUTHENTICATION_REQUIRED = True
```

---

### 8. Custom Social Provider
**When to use:** Adding unsupported OAuth2/OIDC provider

**Content:**
- Provider class structure
- OAuth2Adapter implementation
- URL configuration
- Required methods (extract_uid, extract_common_fields)
- Testing custom providers

**Template:**
```python
class CustomProvider(OAuth2Provider):
    id = "custom"
    name = "Custom Provider"

    def extract_uid(self, data):
        return str(data["id"])
```

---

## Helper Scripts to Create

### 1. `check_allauth_setup.py`
**Purpose:** Verify django-allauth installation and configuration

**Checks:**
- Required apps in INSTALLED_APPS
- Middleware configuration
- Authentication backends
- URL patterns
- Database migrations status
- Common misconfigurations

### 2. `add_social_provider.py`
**Purpose:** Guide through adding a social provider

**Features:**
- Provider selection menu
- Configuration template generation
- Required settings output
- URL configuration snippet
- Admin setup instructions

### 3. `generate_adapter.py`
**Purpose:** Scaffold custom adapter classes

**Features:**
- Select adapter type (Account/Social/MFA)
- Choose methods to override
- Generate boilerplate code
- Add to settings snippet

### 4. `generate_email_templates.py`
**Purpose:** Create custom email template files

**Features:**
- List available email types
- Generate template structure
- Include context variables documentation

---

## Implementation Priority

### Phase 1: Core Skills
1. Main SKILL.md with overview
2. Setup guide reference
3. Social providers reference
4. `check_allauth_setup.py` script

### Phase 2: Customization
5. Customization reference (adapters, signals, forms)
6. `generate_adapter.py` script

### Phase 3: Advanced Features
7. MFA reference
8. Headless API reference
9. Security reference
10. Email templates reference

### Phase 4: Provider Development
11. Custom provider guide
12. `add_social_provider.py` script

---

## Key Design Decisions

### 1. Script Philosophy
Scripts should **solve problems**, not just output instructions:
- `check_allauth_setup.py` should fix common issues automatically
- `add_social_provider.py` should generate ready-to-use code
- All scripts should have clear error messages

### 2. Reference File Organization
- Each reference file < 200 lines
- Table of contents for files > 100 lines
- No nested references (all from SKILL.md)
- Concrete examples, not abstract patterns

### 3. When-To-Use Descriptions
Every skill/section should clearly state:
- What task it helps with
- Specific scenarios/triggers
- Prerequisites

### 4. Code Examples
All code examples should be:
- Complete and runnable
- Include imports
- Show both simple and advanced usage
- Use actual django-allauth class names

---

## Success Metrics

A successful skill set should enable Claude to:

1. **Setup Tasks**
   - Install and configure allauth in < 5 messages
   - Add any of the 127 social providers correctly

2. **Customization Tasks**
   - Create custom adapters with correct method signatures
   - Add signal handlers for common events
   - Override forms properly

3. **Debugging Tasks**
   - Diagnose configuration issues
   - Identify missing settings
   - Suggest fixes for common errors

4. **Advanced Tasks**
   - Set up MFA with TOTP
   - Configure headless mode for SPAs
   - Create custom OAuth2 providers
