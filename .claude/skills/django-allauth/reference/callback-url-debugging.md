# Callback URL Debugging Guide

OAuth callback URLs are the #1 source of authentication errors in django-allauth. This guide helps you diagnose and fix callback URL issues quickly.

## How Callback URLs Work

### The Flow

1. **User clicks "Login with Provider"**
   - Django generates the authorization URL
   - Includes a callback URL parameter

2. **Provider redirects back**
   - User authenticates on provider's site
   - Provider redirects to your callback URL with authorization code

3. **Django processes callback**
   - Exchanges code for access token
   - Creates/updates user account

### URL Generation in django-allauth

```python
# Step 1: Generate the path
path = reverse('provider_callback', kwargs={'provider': 'google'})
# Returns: '/accounts/google/login/callback/'

# Step 2: Build full URL
callback_url = build_absolute_uri(request, path)
# Returns: 'http://localhost:8000/accounts/google/login/callback/'
```

**Critical Rule**: The callback URL sent to the provider MUST match the URL registered in the provider's console EXACTLY.

## Common Errors and Fixes

### 1. Domain Mismatch (127.0.0.1 vs localhost)

**Error Message**:
```
redirect_uri_mismatch: The redirect URI in the request does not match
```

**Cause**: You're accessing via `localhost` but registered `127.0.0.1` (or vice versa).

**Debug Steps**:
```bash
# Check what URL Django is generating
python manage.py shell
>>> from django.contrib.sites.models import Site
>>> Site.objects.get_current()
<Site: example.com>

# This should match how you access the site!
```

**Fix**:
```python
# In settings.py or Django admin, set SITE correctly
SITE_ID = 1

# In Django shell or admin:
from django.contrib.sites.models import Site
site = Site.objects.get_current()
site.domain = 'localhost:8000'  # Match your dev environment
site.name = 'Local Dev'
site.save()
```

**Alternative Fix** (without Sites framework):
```python
# settings.py
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Access site consistently - pick ONE:
# - Always use http://localhost:8000
# - Always use http://127.0.0.1:8000
```

### 2. HTTPS vs HTTP

**Error**: Works locally but fails in production with `redirect_uri_mismatch`.

**Cause**: Django generates `http://` URLs in production, but provider expects `https://`.

**Debug**:
```bash
# Check current protocol generation
python manage.py shell
>>> from allauth.account.adapter import get_adapter
>>> from allauth.utils import build_absolute_uri
>>> adapter = get_adapter()
>>> print(adapter.get_email_confirmation_url(None))
# Look for http:// vs https://
```

**Fix Option 1** - Force HTTPS in allauth:
```python
# settings.py
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'
```

**Fix Option 2** - Use Django's secure settings:
```python
# settings.py (production only)
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
```

**Fix Option 3** - Nginx/Reverse Proxy:
```nginx
# nginx.conf
location / {
    proxy_set_header X-Forwarded-Proto https;
    proxy_set_header X-Forwarded-Host $host;
    proxy_pass http://127.0.0.1:8000;
}
```

### 3. Port Numbers

**Error**: Works in development (port 8000) but fails in production (port 80/443).

**Cause**: Callback URL includes port number when it shouldn't (or vice versa).

**Debug**:
```bash
# Check if port is being included
python manage.py shell
>>> from django.contrib.sites.models import Site
>>> site = Site.objects.get_current()
>>> print(f"Domain: {site.domain}")
# Should be 'example.com' NOT 'example.com:8000' in production
```

**Fix** - Environment-specific configuration:
```python
# settings.py
import os

if os.environ.get('ENVIRONMENT') == 'production':
    SITE_DOMAIN = 'example.com'
    ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'
else:
    SITE_DOMAIN = 'localhost:8000'
    ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'http'

# Update site domain
from django.contrib.sites.models import Site
Site.objects.update_or_create(
    id=1,
    defaults={'domain': SITE_DOMAIN, 'name': SITE_DOMAIN}
)
```

### 4. Trailing Slash Mismatch

**Error**: Subtle mismatch between registered URL and generated URL.

**Cause**: Provider expects `/callback/` but Django generates `/callback` (or vice versa).

**Debug**:
```bash
# Check Django's URL pattern
python manage.py shell
>>> from django.urls import reverse
>>> reverse('google_callback')
'/accounts/google/login/callback/'  # Has trailing slash

# Compare with provider console registration
```

**Fix**:
```python
# settings.py - Force trailing slashes
APPEND_SLASH = True  # Default Django behavior

# Or use django-allauth URL configuration
# The default patterns include trailing slashes
# Just ensure provider console matches: https://example.com/accounts/google/login/callback/
```

## Verification Script

Run this script to see exactly what callback URLs django-allauth will generate:

```python
# save as check_callbacks.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.urls import reverse
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from allauth.utils import build_absolute_uri

print("=== Callback URL Verification ===\n")

# Check site configuration
site = Site.objects.get_current()
print(f"Current Site: {site.domain}")
print(f"Site Name: {site.name}\n")

# Check protocol
from django.conf import settings
protocol = getattr(settings, 'ACCOUNT_DEFAULT_HTTP_PROTOCOL', 'http')
print(f"Protocol: {protocol}\n")

# Check each provider
print("Configured Providers:")
for app in SocialApp.objects.all():
    try:
        callback_path = reverse(f'{app.provider}_callback')
        callback_url = f"{protocol}://{site.domain}{callback_path}"
        print(f"\n{app.provider.upper()}:")
        print(f"  Callback Path: {callback_path}")
        print(f"  Full Callback URL: {callback_url}")
        print(f"  Client ID: {app.client_id[:20]}...")
    except Exception as e:
        print(f"\n{app.provider.upper()}: Error - {e}")
```

**Run it**:
```bash
python check_callbacks.py
```

## Pre-Production Checklist

Before deploying OAuth to production:

- [ ] **HTTPS Enabled**
  ```bash
  # Verify HTTPS works
  curl -I https://yourdomain.com
  # Should return 200, not redirect loop
  ```

- [ ] **Domain Matches Exactly**
  ```python
  # settings.py
  ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'

  # Check Site model
  python manage.py shell
  >>> Site.objects.get_current().domain
  'yourdomain.com'  # NOT 'yourdomain.com:8000'
  ```

- [ ] **No Hardcoded Ports**
  ```bash
  # Search for hardcoded ports in settings
  grep -r "8000" myproject/settings/
  grep -r "localhost" myproject/settings/
  ```

- [ ] **Trailing Slashes Match**
  - Check provider console
  - Run verification script above
  - Ensure both have (or don't have) trailing slash

- [ ] **Test Each Provider**
  ```bash
  # For each provider, test OAuth flow
  # Click "Login with Provider"
  # Check browser network tab for redirect_uri parameter
  # Verify it matches provider console
  ```

- [ ] **Check Reverse Proxy Headers**
  ```python
  # settings.py (if behind nginx/load balancer)
  SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
  USE_X_FORWARDED_HOST = True
  USE_X_FORWARDED_PORT = False
  ```

## Quick Debug Commands

```bash
# 1. Check what callback URL Django generates
python manage.py shell -c "
from django.urls import reverse
from django.contrib.sites.models import Site
from django.conf import settings
protocol = getattr(settings, 'ACCOUNT_DEFAULT_HTTP_PROTOCOL', 'http')
site = Site.objects.get_current()
path = reverse('google_callback')
print(f'{protocol}://{site.domain}{path}')
"

# 2. Check provider console URLs
# Google: https://console.cloud.google.com/apis/credentials
# GitHub: https://github.com/settings/developers
# Facebook: https://developers.facebook.com/apps/

# 3. Compare the two URLs character-by-character
# They must match EXACTLY
```

## Still Having Issues?

1. **Enable allauth debug logging**:
```python
# settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'loggers': {
        'allauth': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

2. **Check browser network tab**:
   - Look for the authorization redirect
   - Find the `redirect_uri` parameter
   - Copy and compare with provider console

3. **Use provider's testing tools**:
   - Google: OAuth Playground
   - GitHub: Test OAuth app feature
   - Most providers have callback URL validators
