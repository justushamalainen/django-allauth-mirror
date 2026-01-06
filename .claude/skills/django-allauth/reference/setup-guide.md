# Django-Allauth Setup Guide

A comprehensive guide to installing and configuring django-allauth in your Django project.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Steps](#installation-steps)
3. [INSTALLED_APPS Configuration](#installed_apps-configuration)
4. [Middleware Configuration](#middleware-configuration)
5. [Authentication Backends](#authentication-backends)
6. [Email Backend Configuration](#email-backend-configuration)
7. [Django Sites Framework](#django-sites-framework)
8. [Session Engine Warning](#session-engine-warning)
9. [Custom User Model Integration](#custom-user-model-integration)
10. [Basic Settings Template](#basic-settings-template)
11. [Post-Installation Checklist](#post-installation-checklist)

---

## Prerequisites

### Python Version

**Minimum Required: Python 3.8+**

Django-allauth requires Python 3.8 or higher. Check your Python version:

```bash
python --version
# or
python3 --version
```

If you're running an older version, upgrade Python before proceeding.

### Django Version

**Minimum Required: Django 4.2+**

Django-allauth requires Django 4.2 or higher. Check your Django version:

```bash
python -c "import django; print(django.get_version())"
```

### Database Requirements

**CRITICAL: Database must be configured (not `:memory:`)**

Django-allauth **will not work** with SQLite's in-memory database (`:memory:`). You must use a file-based database or another database backend (PostgreSQL, MySQL, etc.).

**Bad Configuration:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # ❌ This will NOT work with django-allauth
    }
}
```

**Good Configuration:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',  # ✅ File-based database works
    }
}
```

### Environment

- A working Django project
- Virtual environment (recommended)
- Git (recommended for version control)

---

## Installation Steps

### Core Installation

Install the base django-allauth package:

```bash
pip install django-allauth
```

This installs the core `allauth.account` module, which provides:
- User registration
- Login/logout
- Password reset
- Email verification
- Account management

### Optional Dependencies Matrix

Django-allauth is modular. Install only the features you need:

| Module | Install Command | Features Provided |
|--------|----------------|-------------------|
| **Social Account** | `pip install "django-allauth[socialaccount]"` | OAuth 1.0/2.0, OpenID Connect providers (Google, GitHub, Facebook, etc.) |
| **MFA** | `pip install "django-allauth[mfa]"` | Multi-Factor Authentication (TOTP, WebAuthn/FIDO2, Recovery Codes) |
| **Headless/API** | `pip install "django-allauth[headless]"` | REST API endpoints for SPAs and mobile apps (session + JWT tokens) |
| **SAML** | `pip install "django-allauth[saml]"` | SAML 2.0 authentication (enterprise SSO) |

### Installing Multiple Modules

To install multiple optional modules at once:

```bash
# Social authentication + MFA
pip install "django-allauth[socialaccount,mfa]"

# All features
pip install "django-allauth[socialaccount,mfa,headless,saml]"
```

### Development Installation

For development, install with all extras:

```bash
pip install "django-allauth[socialaccount,mfa,headless,saml]"
```

### Verifying Installation

Check that django-allauth is installed correctly:

```bash
python -c "import allauth; print(allauth.__version__)"
```

---

## INSTALLED_APPS Configuration

### Correct Application Order

**CRITICAL: The order matters!** Django's `django.contrib.auth` must come **before** `allauth`.

### Minimal Configuration (Account Only)

For basic account functionality (no social authentication):

```python
INSTALLED_APPS = [
    # Django core apps (must come first)
    'django.contrib.admin',
    'django.contrib.auth',        # ✅ Must be before allauth
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',       # Required by allauth

    # Django-allauth apps
    'allauth',
    'allauth.account',

    # Your apps
    'myapp',
]
```

### With Social Authentication

Add `allauth.socialaccount` and provider apps:

```python
INSTALLED_APPS = [
    # Django core apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # Django-allauth apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount',

    # Social providers (add only the ones you need)
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.github',
    'allauth.socialaccount.providers.facebook',

    # Your apps
    'myapp',
]
```

### With MFA

Add `allauth.mfa`:

```python
INSTALLED_APPS = [
    # Django core apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # Django-allauth apps
    'allauth',
    'allauth.account',
    'allauth.mfa',  # Multi-Factor Authentication

    # Optional: social authentication
    'allauth.socialaccount',

    # Your apps
    'myapp',
]
```

### With Headless API

Add `allauth.headless`:

```python
INSTALLED_APPS = [
    # Django core apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # Django-allauth apps
    'allauth',
    'allauth.account',
    'allauth.headless',  # API endpoints for SPAs/mobile

    # Optional: social + MFA
    'allauth.socialaccount',
    'allauth.mfa',

    # Your apps
    'myapp',
]
```

---

## Middleware Configuration

### AccountMiddleware Requirement

**REQUIRED:** Django-allauth needs its middleware to function properly.

Add `allauth.account.middleware.AccountMiddleware` to your `MIDDLEWARE` setting:

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Add allauth middleware AFTER AuthenticationMiddleware
    'allauth.account.middleware.AccountMiddleware',  # ✅ Add this
]
```

### Correct Order

The middleware **must** be placed **after** these Django core middlewares:
- `django.contrib.sessions.middleware.SessionMiddleware`
- `django.contrib.auth.middleware.AuthenticationMiddleware`
- `django.contrib.messages.middleware.MessageMiddleware`

**Why?** The middleware needs access to the request's session, authenticated user, and messages framework.

---

## Authentication Backends

### Both Backends Required

Django-allauth requires **two** authentication backends to function properly:

```python
AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by email
    'allauth.account.auth_backends.AuthenticationBackend',
]
```

### What Each Backend Does

| Backend | Purpose |
|---------|---------|
| `ModelBackend` | Django's default backend. Handles username-based authentication for Django admin and supports traditional login. |
| `AuthenticationBackend` | Allauth's backend. Enables email-based login, social authentication, and allauth-specific features. |

### Common Mistakes

**❌ Missing Django's ModelBackend:**
```python
AUTHENTICATION_BACKENDS = [
    # Missing ModelBackend
    'allauth.account.auth_backends.AuthenticationBackend',
]
```
**Result:** Django admin login may break, username authentication doesn't work.

**❌ Missing Allauth's Backend:**
```python
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    # Missing AuthenticationBackend
]
```
**Result:** Email-based login doesn't work, social authentication breaks.

**✅ Correct Configuration:**
```python
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
```

---

## Email Backend Configuration

### CRITICAL: Email Backend Must Be Configured

**⚠️ WARNING:** If you don't configure an email backend, **emails will fail silently** without error messages. Users won't receive verification emails, password reset emails, etc.

### Development: Console Backend

For local development, use Django's console email backend to print emails to the terminal:

```python
# settings.py (development)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

**How it works:**
- Emails are printed to the console/terminal where `runserver` is running
- No actual emails are sent
- Perfect for testing email flows during development
- No external SMTP server needed

### Production: SMTP Backend

For production, configure a real SMTP server:

```python
# settings.py (production)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'noreply@yourdomain.com'
```

### Common SMTP Providers

| Provider | HOST | PORT | TLS/SSL |
|----------|------|------|---------|
| **Gmail** | `smtp.gmail.com` | 587 | TLS |
| **SendGrid** | `smtp.sendgrid.net` | 587 | TLS |
| **Mailgun** | `smtp.mailgun.org` | 587 | TLS |
| **AWS SES** | `email-smtp.us-east-1.amazonaws.com` | 587 | TLS |
| **Office 365** | `smtp.office365.com` | 587 | TLS |

### Environment-Based Configuration

Use environment variables to switch between development and production:

```python
# settings.py
import os

if os.environ.get('DJANGO_ENV') == 'production':
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ.get('EMAIL_HOST')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
    EMAIL_USE_TLS = True
else:
    # Development
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

### Testing Email Configuration

Test your email backend:

```python
# In Django shell (python manage.py shell)
from django.core.mail import send_mail

send_mail(
    'Test Subject',
    'Test message.',
    'from@example.com',
    ['to@example.com'],
    fail_silently=False,
)
```

If using console backend, check your terminal. If using SMTP, check the recipient's inbox.

---

## Django Sites Framework

### Why Sites Framework is Required

Django-allauth **requires** the Django Sites framework because:

1. **Email verification links** need to know the domain name
2. **Password reset emails** contain absolute URLs
3. **Social authentication callbacks** need the correct domain
4. **Multi-site deployments** can have different OAuth credentials per site

Without proper configuration, email links will be broken or point to `example.com`.

### Basic Configuration

#### 1. Add to INSTALLED_APPS

Already covered in [INSTALLED_APPS Configuration](#installed_apps-configuration):

```python
INSTALLED_APPS = [
    # ...
    'django.contrib.sites',  # ✅ Required
    # ...
]
```

#### 2. Set SITE_ID

Add the `SITE_ID` setting:

```python
# settings.py
SITE_ID = 1
```

This tells Django which site in the database to use.

#### 3. Run Migrations

```bash
python manage.py migrate
```

This creates the `django_site` table.

#### 4. Update Site Domain

**CRITICAL:** Change the default site domain from `example.com`:

**Option A: Via Django Admin**
1. Go to http://127.0.0.1:8000/admin/
2. Navigate to "Sites"
3. Click on "example.com"
4. Change:
   - **Domain name:** `127.0.0.1:8000` (development) or `yourdomain.com` (production)
   - **Display name:** Your site name
5. Save

**Option B: Via Django Shell**

```python
# python manage.py shell
from django.contrib.sites.models import Site

site = Site.objects.get_current()
site.domain = '127.0.0.1:8000'  # or 'yourdomain.com' for production
site.name = 'My Site'
site.save()
```

**Option C: Via Management Command**

```bash
python manage.py shell -c "
from django.contrib.sites.models import Site
site = Site.objects.get_current()
site.domain = '127.0.0.1:8000'
site.name = 'My Site'
site.save()
"
```

### Multi-Site Setup

For projects serving multiple domains:

```python
# settings.py
SITE_ID = 1  # Default site

# In your code, you can switch sites dynamically
from django.contrib.sites.models import Site

# Get site by domain
site = Site.objects.get(domain='site1.com')

# Use different OAuth credentials per site via Django admin
# Each SocialApp can be associated with specific sites
```

### Common Issues

**Issue:** Email links point to `http://example.com`

**Solution:** You forgot to update the Site domain. See step 4 above.

**Issue:** `Site matching query does not exist`

**Solution:** Run migrations: `python manage.py migrate sites`

---

## Session Engine Warning

### Cannot Use Signed Cookies

**⚠️ CRITICAL:** Django-allauth **will not work** with the `signed_cookies` session engine.

**Bad Configuration:**
```python
# ❌ DO NOT USE THIS
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
```

**Why?** Verification codes, login codes, and multi-step authentication flows require server-side session storage. Signed cookies are client-side only and cannot store temporary authentication state.

### Supported Session Engines

Use any of these session engines:

**Database-backed (default):**
```python
SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # ✅ Default, works fine
```

**Cached sessions:**
```python
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'  # ✅ Fast, requires cache backend
```

**Cached database sessions:**
```python
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'  # ✅ Best of both worlds
```

**File-based sessions:**
```python
SESSION_ENGINE = 'django.contrib.sessions.backends.file'  # ✅ Works, but slower
```

### What Breaks Without Server-Side Sessions

If you use `signed_cookies`, these features will fail:
- Email verification codes
- Password reset codes
- Login by code (magic links)
- Multi-factor authentication codes
- Social authentication state (CSRF protection)
- Phone verification codes

### Recommendation

Use the default database-backed sessions or cached_db for better performance:

```python
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_CACHE_ALIAS = 'default'
```

---

## Custom User Model Integration

### Why This Matters

**~80% of Django projects use custom user models.** If you're using a custom user model, you **must** tell django-allauth which fields to use for username and email.

### Standard Django User Model

If you're using Django's default `User` model (`django.contrib.auth.models.User`), **skip this section**. No configuration needed.

### Identifying Your User Model

Check your `settings.py` for `AUTH_USER_MODEL`:

```python
# If you see this, you're using a custom user model
AUTH_USER_MODEL = 'accounts.CustomUser'
```

### Configuration Settings

Tell django-allauth which fields your custom user model uses:

```python
# settings.py
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'username'  # Field name for username
ACCOUNT_USER_MODEL_EMAIL_FIELD = 'email'       # Field name for email
```

### Common Custom User Model Scenarios

#### Scenario 1: Email-Only Authentication (No Username)

Your user model only has an email field, no username:

```python
# models.py
class CustomUser(AbstractBaseUser):
    email = models.EmailField(unique=True)
    # No username field

    USERNAME_FIELD = 'email'
```

**Configuration:**
```python
# settings.py
AUTH_USER_MODEL = 'accounts.CustomUser'
ACCOUNT_USER_MODEL_USERNAME_FIELD = None  # ✅ No username field
ACCOUNT_USER_MODEL_EMAIL_FIELD = 'email'

# Also configure login methods
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
```

#### Scenario 2: Different Field Names

Your user model uses different field names:

```python
# models.py
class CustomUser(AbstractBaseUser):
    user_name = models.CharField(max_length=150, unique=True)  # Not 'username'
    email_address = models.EmailField(unique=True)             # Not 'email'

    USERNAME_FIELD = 'user_name'
```

**Configuration:**
```python
# settings.py
AUTH_USER_MODEL = 'accounts.CustomUser'
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'user_name'      # ✅ Match your model
ACCOUNT_USER_MODEL_EMAIL_FIELD = 'email_address'    # ✅ Match your model
```

#### Scenario 3: Phone-Based Authentication

Your user model uses phone number for login:

```python
# models.py
class CustomUser(AbstractBaseUser):
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True)

    USERNAME_FIELD = 'phone'
```

**Configuration:**
```python
# settings.py
AUTH_USER_MODEL = 'accounts.CustomUser'
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'phone'
ACCOUNT_USER_MODEL_EMAIL_FIELD = 'email'

# Configure for phone authentication
ACCOUNT_AUTHENTICATION_METHOD = 'email'  # Will use phone via adapter override
```

### Migration for Existing Users

If you're adding django-allauth to an existing project with users:

1. **Run migrations first:**
   ```bash
   python manage.py migrate
   ```

2. **No data migration needed** - django-allauth works with existing users automatically.

3. **EmailAddress records** - Allauth will create `EmailAddress` records when users log in:
   ```python
   # Optional: Pre-populate EmailAddress records for existing users
   from django.contrib.auth import get_user_model
   from allauth.account.models import EmailAddress

   User = get_user_model()
   for user in User.objects.all():
       EmailAddress.objects.get_or_create(
           user=user,
           email=user.email,
           defaults={'verified': True, 'primary': True}
       )
   ```

---

## Basic Settings Template

### Complete Working Example

Copy this into your `settings.py` as a starting point:

```python
# ============================================================================
# DJANGO-ALLAUTH CONFIGURATION
# ============================================================================

# Sites framework
SITE_ID = 1

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Email backend (change for production)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# INSTALLED_APPS (add these)
INSTALLED_APPS = [
    # Django core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # Django-allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',  # Optional: remove if not using social auth

    # Your apps
]

# Middleware (add AccountMiddleware)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',  # Add this
]

# ============================================================================
# ALLAUTH SETTINGS
# ============================================================================

# Authentication
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'  # Allow login with username or email
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = True

# Email verification
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'  # Options: 'mandatory', 'optional', 'none'

# Signup
ACCOUNT_SIGNUP_EMAIL_ENTER_TWICE = False
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True

# Login/Logout
LOGIN_REDIRECT_URL = '/'  # Where to redirect after login
ACCOUNT_LOGOUT_REDIRECT_URL = '/'  # Where to redirect after logout
ACCOUNT_LOGOUT_ON_GET = False  # Require POST to logout (more secure)

# Session
ACCOUNT_SESSION_REMEMBER = None  # Ask user "Remember me?"

# Custom user model (if applicable)
# ACCOUNT_USER_MODEL_USERNAME_FIELD = 'username'
# ACCOUNT_USER_MODEL_EMAIL_FIELD = 'email'

# ============================================================================
# URLS CONFIGURATION (add to urls.py)
# ============================================================================
# from django.urls import path, include
#
# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('accounts/', include('allauth.urls')),  # Add this
# ]
```

### URLs Configuration

Add django-allauth URLs to your project's `urls.py`:

```python
# urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),  # ✅ Add this line

    # Your other URLs
]
```

This provides these URL patterns:
- `/accounts/login/` - Login page
- `/accounts/signup/` - Signup page
- `/accounts/logout/` - Logout page
- `/accounts/password/reset/` - Password reset
- `/accounts/email/` - Email management
- And many more...

---

## Post-Installation Checklist

### 1. Run Migrations

```bash
python manage.py migrate
```

**Expected output:** Migrations for `account`, `socialaccount` (if installed), `sites`, etc.

### 2. Update Site Domain

See [Django Sites Framework](#django-sites-framework) section.

```bash
python manage.py shell -c "
from django.contrib.sites.models import Site
site = Site.objects.get_current()
site.domain = '127.0.0.1:8000'
site.name = 'My Site'
site.save()
print(f'Site updated: {site.domain}')
"
```

### 3. Create Superuser (if needed)

```bash
python manage.py createsuperuser
```

### 4. Start Development Server

```bash
python manage.py runserver
```

### 5. Verify Login Page Loads

Open your browser and navigate to:

```
http://127.0.0.1:8000/accounts/login/
```

**Expected:** Login form should display without errors.

**If you see errors:**
- Check that all migrations have run
- Verify `INSTALLED_APPS` includes all required apps
- Check that middleware is correctly configured

### 6. Test Signup Flow

1. Go to `http://127.0.0.1:8000/accounts/signup/`
2. Fill in the signup form
3. Submit

**If EMAIL_VERIFICATION is 'mandatory':**
- Check your console/terminal for the verification email
- Copy the verification URL and paste it in your browser

**If EMAIL_VERIFICATION is 'optional' or 'none':**
- You should be logged in immediately after signup

### 7. Verify Email Backend

Check your terminal/console for email output if using console backend:

```
Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit
Subject: [example.com] Please Confirm Your Email Address
From: webmaster@localhost
To: user@example.com
Date: Mon, 06 Jan 2025 12:00:00 -0000
Message-ID: <...>

Hello from example.com!

You're receiving this email because...
```

### 8. Check Django Admin

1. Go to `http://127.0.0.1:8000/admin/`
2. Login with your superuser credentials
3. Verify these sections appear:
   - **Sites** - Check the domain is correct
   - **Email addresses** - Verify your user's email
   - **Social accounts** (if installed)
   - **Social applications** (if installed)

### 9. Validate SITE_ID Configuration

```bash
python manage.py shell
```

```python
from django.contrib.sites.models import Site
site = Site.objects.get_current()
print(f"Domain: {site.domain}")
print(f"Name: {site.name}")

# Domain should NOT be "example.com" for development
# Should be "127.0.0.1:8000" or your actual domain
```

### 10. Test Account Functions

Verify these core functions work:

- [ ] Signup with email verification
- [ ] Login with username
- [ ] Login with email
- [ ] Password reset
- [ ] Logout
- [ ] Email management (if applicable)

---

## Troubleshooting

### Issue: "No Site matches the given query"

**Cause:** Sites framework not configured or migrations not run.

**Solution:**
```bash
python manage.py migrate sites
```

Then update the site domain via admin or shell.

### Issue: Email verification links point to "example.com"

**Cause:** Site domain not updated from default.

**Solution:** See [Django Sites Framework](#django-sites-framework) section, step 4.

### Issue: Emails not being sent/received

**Cause:** Email backend not configured.

**Solution:**
- Development: Set `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'`
- Production: Configure SMTP settings (see [Email Backend Configuration](#email-backend-configuration))

### Issue: "AccountMiddleware must be installed"

**Cause:** Forgot to add `AccountMiddleware` to `MIDDLEWARE`.

**Solution:** See [Middleware Configuration](#middleware-configuration).

### Issue: Cannot login by email

**Cause:** Missing authentication backend.

**Solution:** Add both backends to `AUTHENTICATION_BACKENDS` (see [Authentication Backends](#authentication-backends)).

### Issue: Verification codes not working

**Cause:** Using `SESSION_ENGINE = 'signed_cookies'`.

**Solution:** Change to database or cache-backed sessions (see [Session Engine Warning](#session-engine-warning)).

### Issue: Custom user model fields not recognized

**Cause:** Didn't configure `ACCOUNT_USER_MODEL_*_FIELD` settings.

**Solution:** See [Custom User Model Integration](#custom-user-model-integration).

---

## Next Steps

Now that django-allauth is installed and configured:

1. **Customize Templates** - Override default templates to match your site's design
2. **Configure Settings** - Fine-tune authentication behavior (see settings reference)
3. **Add Social Providers** - Enable login with Google, GitHub, Facebook, etc.
4. **Implement MFA** - Add two-factor authentication for enhanced security
5. **Create Adapters** - Customize authentication flow logic
6. **Setup Rate Limiting** - Configure rate limits for security

---

## Additional Resources

- **Official Documentation:** https://docs.allauth.org/
- **Settings Reference:** See `reference/settings-reference.md` (if available)
- **Social Providers:** See `reference/social-providers.md` (if available)
- **Customization Guide:** See `reference/customization.md` (if available)
- **GitHub Issues:** https://codeberg.org/allauth/django-allauth/issues

---

**Setup guide version:** 1.0
**Last updated:** 2026-01-06
**Compatible with:** django-allauth 0.57+, Django 4.2+, Python 3.8+
