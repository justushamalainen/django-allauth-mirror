# Callback URL Debugging Guide

OAuth callback URLs are the #1 source of authentication errors in django-allauth. This guide helps you diagnose and fix callback URL issues quickly.

## How Callback URLs Work

### The OAuth Flow

1. User clicks "Login with Provider" - Django generates authorization URL with callback URL parameter
2. Provider redirects back - User authenticates, provider redirects to your callback URL with authorization code
3. Django processes callback - Exchanges code for access token, creates/updates user account

### Callback URL Format

```
{protocol}://{domain}{path}
```

**Examples:**
```
http://localhost:8000/accounts/google/login/callback/
https://example.com/accounts/github/login/callback/
https://myapp.com/accounts/facebook/login/callback/
```

**Critical Rule**: The callback URL sent to the provider MUST match the URL registered in the provider's console EXACTLY (protocol, domain, port, path, trailing slash).

## Top 5 Common Errors

### 1. Domain Mismatch (127.0.0.1 vs localhost)

**Error**: `redirect_uri_mismatch: The redirect URI in the request does not match`

**Cause**: Accessing via `localhost` but registered `127.0.0.1` (or vice versa).

**Fix - Update Site domain**:
```python
# In Django shell or admin:
from django.contrib.sites.models import Site
site = Site.objects.get_current()
site.domain = 'localhost:8000'  # Match your dev environment
site.save()
```

**Fix - Without Sites framework**:
```python
# settings.py - Access site consistently (pick ONE)
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
# Always use http://localhost:8000 OR http://127.0.0.1:8000
```

### 2. HTTPS vs HTTP

**Error**: Works locally but fails in production with `redirect_uri_mismatch`.

**Cause**: Django generates `http://` URLs in production, but provider expects `https://`.

**Fix - Force HTTPS**:
```python
# settings.py (production)
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'
```

**Fix - Behind reverse proxy**:
```python
# settings.py (with nginx/load balancer)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
```

### 3. Port Numbers

**Error**: Works in development (port 8000) but fails in production.

**Cause**: Callback URL includes port number when it shouldn't (or vice versa).

**Fix - Environment-specific configuration**:
```python
# settings.py
import os

if os.environ.get('ENVIRONMENT') == 'production':
    SITE_DOMAIN = 'example.com'  # No port
    ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'
else:
    SITE_DOMAIN = 'localhost:8000'  # Include port
    ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'http'
```

### 4. Trailing Slash Mismatch

**Error**: Provider expects `/callback/` but Django generates `/callback` (or vice versa).

**Cause**: Django's URL patterns include trailing slashes by default, but provider console doesn't.

**Fix**:
```python
# settings.py
APPEND_SLASH = True  # Default Django behavior

# Ensure provider console matches Django's URL:
# https://example.com/accounts/google/login/callback/
#                                                     ^ trailing slash
```

### 5. Wrong Callback Path

**Error**: Provider redirects to wrong URL path.

**Cause**: Custom URL configuration doesn't match provider console registration.

**Fix - Use default allauth URLs**:
```python
# urls.py
urlpatterns = [
    path('accounts/', include('allauth.urls')),  # Standard path
]

# Provider console should use:
# https://example.com/accounts/{provider}/login/callback/
```

## Quick Verification

**Check what callback URL Django generates**:
```bash
python manage.py shell -c "
from django.urls import reverse
from django.contrib.sites.models import Site
from django.conf import settings
protocol = getattr(settings, 'ACCOUNT_DEFAULT_HTTP_PROTOCOL', 'http')
site = Site.objects.get_current()
path = reverse('google_callback')
print(f'{protocol}://{site.domain}{path}')
"
```

**Compare with provider console**:
- Google: https://console.cloud.google.com/apis/credentials
- GitHub: https://github.com/settings/developers
- Facebook: https://developers.facebook.com/apps/

The URLs must match **character-by-character**.

## Pre-Production Checklist

Before deploying OAuth to production:

- [ ] HTTPS enabled: `ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'`
- [ ] Site domain correct (no port 8000): `Site.objects.get_current().domain`
- [ ] Reverse proxy headers set: `SECURE_PROXY_SSL_HEADER`, `USE_X_FORWARDED_HOST`
- [ ] Trailing slashes match between Django and provider console
- [ ] Test OAuth flow for each provider in production environment

## Debug Tips

**Enable debug logging**:
```python
# settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'loggers': {
        'allauth': {'handlers': ['console'], 'level': 'DEBUG'},
    },
}
```

**Check browser network tab**:
- Look for authorization redirect
- Find `redirect_uri` parameter in query string
- Copy and compare with provider console URL

**Common mistakes**:
- Mixed http/https between environments
- Hardcoded `localhost` or `127.0.0.1` in settings
- Port 8000 leaking into production URLs
- Missing trailing slash on provider console
- Using Sites framework but `SITE_ID` not set
