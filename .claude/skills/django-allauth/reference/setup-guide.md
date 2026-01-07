# Django-Allauth Setup Guide

Quick reference for installing and configuring django-allauth.

---

## Prerequisites

- **Python 3.8+**
- **Django 4.2+**
- **Database:** File-based or server-based (NOT `:memory:`)

```python
# ❌ This will NOT work
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# ✅ This works
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

---

## Installation

### Core Package

```bash
pip install django-allauth
```

### Optional Modules

```bash
# Social authentication (Google, GitHub, Facebook, etc.)
pip install "django-allauth[socialaccount]"

# Multi-Factor Authentication (TOTP, WebAuthn, recovery codes)
pip install "django-allauth[mfa]"

# REST API endpoints for SPAs/mobile apps
pip install "django-allauth[headless]"

# SAML 2.0 authentication
pip install "django-allauth[saml]"

# Install multiple modules
pip install "django-allauth[socialaccount,mfa]"
```

---

## INSTALLED_APPS Configuration

**CRITICAL: Order matters!** `django.contrib.auth` must come before `allauth`.

### Minimal (Account Only)

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',        # Must be before allauth
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',       # Required

    # Django-allauth
    'allauth',
    'allauth.account',

    # Your apps
]
```

### With Social Authentication

```python
INSTALLED_APPS = [
    # ... Django core apps ...
    'django.contrib.sites',

    # Django-allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',

    # Providers (add only what you need)
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.github',

    # Your apps
]
```

### With MFA

```python
INSTALLED_APPS = [
    # ... Django core apps ...
    'django.contrib.sites',

    # Django-allauth
    'allauth',
    'allauth.account',
    'allauth.mfa',  # Multi-Factor Authentication

    # Your apps
]
```

---

## Middleware Configuration

Add `AccountMiddleware` **after** `AuthenticationMiddleware`:

```python
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
```

---

## Authentication Backends

**Both backends required:**

```python
AUTHENTICATION_BACKENDS = [
    # Django's default (required for admin)
    'django.contrib.auth.backends.ModelBackend',

    # Allauth's backend (enables email login, social auth)
    'allauth.account.auth_backends.AuthenticationBackend',
]
```

---

## Email Backend Configuration

**⚠️ CRITICAL:** Emails will fail silently if not configured.

### Development

```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

Emails print to console where `runserver` is running.

### Production

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'noreply@yourdomain.com'
```

---

## Django Sites Framework

### Configuration

```python
# settings.py
SITE_ID = 1
```

### Update Site Domain

**CRITICAL:** Change from default `example.com` or email links will break.

```bash
# Via Django shell
python manage.py shell -c "
from django.contrib.sites.models import Site
site = Site.objects.get_current()
site.domain = '127.0.0.1:8000'  # or 'yourdomain.com' for production
site.name = 'My Site'
site.save()
"
```

Or via Django admin: `/admin/sites/site/1/change/`

---

## Session Engine Warning

**⚠️ CRITICAL:** Cannot use `signed_cookies` session engine.

```python
# ❌ DO NOT USE
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
```

Verification codes and multi-step flows require server-side sessions.

### Supported Engines

```python
# ✅ Any of these work
SESSION_ENGINE = 'django.contrib.sessions.backends.db'          # Default
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'       # Fast
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'   # Best
SESSION_ENGINE = 'django.contrib.sessions.backends.file'        # Works
```

---

## Custom User Model Integration

If using Django's default `User` model, **skip this section**.

### Configuration Settings

```python
# For standard custom user model
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'username'
ACCOUNT_USER_MODEL_EMAIL_FIELD = 'email'
```

### Email-Only Authentication (No Username)

```python
# models.py
class CustomUser(AbstractBaseUser):
    email = models.EmailField(unique=True)
    USERNAME_FIELD = 'email'

# settings.py
AUTH_USER_MODEL = 'accounts.CustomUser'
ACCOUNT_USER_MODEL_USERNAME_FIELD = None  # No username field
ACCOUNT_USER_MODEL_EMAIL_FIELD = 'email'
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
```

### Different Field Names

```python
# models.py
class CustomUser(AbstractBaseUser):
    user_name = models.CharField(max_length=150, unique=True)
    email_address = models.EmailField(unique=True)
    USERNAME_FIELD = 'user_name'

# settings.py
AUTH_USER_MODEL = 'accounts.CustomUser'
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'user_name'
ACCOUNT_USER_MODEL_EMAIL_FIELD = 'email_address'
```

---

## Complete Settings Template

Copy this into your `settings.py`:

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

# INSTALLED_APPS
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

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

# ============================================================================
# ALLAUTH SETTINGS
# ============================================================================

# Authentication
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = True

# Email verification
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'  # 'mandatory', 'optional', or 'none'

# Signup
ACCOUNT_SIGNUP_EMAIL_ENTER_TWICE = False
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True

# Login/Logout
LOGIN_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_ON_GET = False  # Require POST (more secure)

# Session
ACCOUNT_SESSION_REMEMBER = None  # Ask user "Remember me?"

# Custom user model (uncomment if applicable)
# ACCOUNT_USER_MODEL_USERNAME_FIELD = 'username'
# ACCOUNT_USER_MODEL_EMAIL_FIELD = 'email'
```

---

## URLs Configuration

Add to your project's `urls.py`:

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
]
```

Provides:
- `/accounts/login/` - Login
- `/accounts/signup/` - Signup
- `/accounts/logout/` - Logout
- `/accounts/password/reset/` - Password reset
- `/accounts/email/` - Email management

---

## Post-Installation Checklist

```bash
# 1. Run migrations
python manage.py migrate

# 2. Update site domain
python manage.py shell -c "
from django.contrib.sites.models import Site
site = Site.objects.get_current()
site.domain = '127.0.0.1:8000'
site.name = 'My Site'
site.save()
"

# 3. Create superuser (if needed)
python manage.py createsuperuser

# 4. Start server
python manage.py runserver

# 5. Test login page
# Visit: http://127.0.0.1:8000/accounts/login/
```

---

## Common Issues

### "No Site matches the given query"

```bash
python manage.py migrate sites
```

Then update site domain via admin or shell.

### Email links point to "example.com"

Update site domain (see Django Sites Framework section).

### Emails not being sent

**Development:**
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

**Production:** Configure SMTP settings (see Email Backend Configuration).

### "AccountMiddleware must be installed"

Add `allauth.account.middleware.AccountMiddleware` to `MIDDLEWARE`.

### Cannot login by email

Add both backends to `AUTHENTICATION_BACKENDS`.

### Verification codes not working

Change `SESSION_ENGINE` from `signed_cookies` to database or cache-backed.

---

**Version:** 1.0
**Last updated:** 2026-01-06
**Compatible with:** django-allauth 0.57+, Django 4.2+, Python 3.8+
