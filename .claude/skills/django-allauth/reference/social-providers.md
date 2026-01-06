# Social Providers Guide

django-allauth supports 127+ social authentication providers including Google, GitHub, Facebook, Microsoft, Apple, Twitter, LinkedIn, Discord, Slack, and many more.

## Quick Setup (Any Provider)

### 1. Add Provider to INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    'django.contrib.sites',  # Required
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',  # Add provider(s) here
    'allauth.socialaccount.providers.github',
]

SITE_ID = 1
```

### 2. Run Migrations

```bash
python manage.py migrate
```

### 3. Configure Credentials

Choose one approach:

**Settings-based (Recommended):**
```python
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.environ['GOOGLE_CLIENT_ID'],
            'secret': os.environ['GOOGLE_SECRET'],
            'key': ''  # Leave empty for most providers
        }
    }
}
```

**Admin-based:** Configure at `/admin/socialaccount/socialapp/`

### 4. Set Callback URL in Provider Console

**Format:** `https://yourdomain.com/accounts/{provider}/login/callback/`

**Examples:**
- Google: `https://yourdomain.com/accounts/google/login/callback/`
- GitHub: `https://yourdomain.com/accounts/github/login/callback/`

**Important:**
- Must match exact domain (including subdomain)
- HTTPS required in production
- Port matters in development (`localhost:8000` ≠ `localhost`)
- Trailing slash required

### 5. Add Login Button

```html
{% load socialaccount %}
<a href="{% provider_login_url 'google' %}">Login with Google</a>
<a href="{% provider_login_url 'github' %}">Login with GitHub</a>
```

---

## Google (Full Setup)

**1. Create OAuth Credentials:**
- Go to: https://console.cloud.google.com/apis/credentials
- Create OAuth 2.0 Client ID
- Application type: Web application
- Authorized redirect URIs: `https://yourdomain.com/accounts/google/login/callback/`

**2. Install Provider:**
```python
INSTALLED_APPS = [
    # ...
    'allauth.socialaccount.providers.google',
]
```

**3. Configure:**
```python
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,  # Recommended for security
        'APP': {
            'client_id': os.environ.get('GOOGLE_CLIENT_ID'),  # YOUR-CLIENT-ID.apps.googleusercontent.com
            'secret': os.environ.get('GOOGLE_SECRET'),
            'key': ''
        }
    }
}
```

**4. Environment Variables:**
```bash
# .env file (never commit this!)
GOOGLE_CLIENT_ID=YOUR-CLIENT-ID.apps.googleusercontent.com
GOOGLE_SECRET=YOUR-SECRET-KEY
```

**Optional - Request Additional Scopes:**
```python
'SCOPE': [
    'profile',
    'email',
    'openid',  # For OIDC support
    # 'https://www.googleapis.com/auth/calendar.readonly',
    # 'https://www.googleapis.com/auth/userinfo.profile',
]
```

**Callback URL:** `https://yourdomain.com/accounts/google/login/callback/`

---

## GitHub (Full Setup)

**1. Create OAuth App:**
- Go to: https://github.com/settings/developers
- Click "New OAuth App"
- Homepage URL: `https://yourdomain.com`
- Authorization callback URL: `https://yourdomain.com/accounts/github/login/callback/`

**2. Install Provider:**
```python
INSTALLED_APPS = [
    # ...
    'allauth.socialaccount.providers.github',
]
```

**3. Configure:**
```python
SOCIALACCOUNT_PROVIDERS = {
    'github': {
        'SCOPE': [
            'user:email',  # Access user email addresses (required)
        ],
        'APP': {
            'client_id': os.environ.get('GITHUB_CLIENT_ID'),
            'secret': os.environ.get('GITHUB_SECRET'),
        }
    }
}
```

**4. Environment Variables:**
```bash
# .env file (never commit this!)
GITHUB_CLIENT_ID=YOUR-CLIENT-ID
GITHUB_SECRET=YOUR-SECRET-KEY
```

**Optional - Request Additional Scopes:**
```python
'SCOPE': [
    'user:email',
    'read:user',    # Read all user profile data
    'user:follow',  # Access followers
]
```

**Callback URL:** `https://yourdomain.com/accounts/github/login/callback/`

**Note:** GitHub may provide multiple email addresses. django-allauth uses the primary verified email.

---

## Other Common Providers

### Facebook

```python
INSTALLED_APPS = ['allauth.socialaccount.providers.facebook']

SOCIALACCOUNT_PROVIDERS = {
    'facebook': {
        'METHOD': 'oauth2',
        'SCOPE': ['email', 'public_profile'],
        'VERSION': 'v18.0',
        'APP': {
            'client_id': os.environ['FACEBOOK_APP_ID'],
            'secret': os.environ['FACEBOOK_APP_SECRET'],
        }
    }
}
```

**Callback URL:** `https://yourdomain.com/accounts/facebook/login/callback/`

**Setup:** https://developers.facebook.com/apps/ (Create App > Consumer > Add Facebook Login product)

**Note:** Facebook emails are not always verified. Consider requiring email verification if critical.

---

### Microsoft

```python
INSTALLED_APPS = ['allauth.socialaccount.providers.microsoft']

SOCIALACCOUNT_PROVIDERS = {
    'microsoft': {
        'TENANT': 'common',  # 'common', 'organizations', 'consumers', or tenant ID
        'APP': {
            'client_id': os.environ['MICROSOFT_CLIENT_ID'],
            'secret': os.environ['MICROSOFT_SECRET'],
        }
    }
}
```

**Callback URL:** `https://yourdomain.com/accounts/microsoft/login/callback/`

**Setup:** https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps (Register new application > Add redirect URI)

---

### Apple

```python
INSTALLED_APPS = ['allauth.socialaccount.providers.apple']

SOCIALACCOUNT_PROVIDERS = {
    'apple': {
        'APP': {
            'client_id': 'com.yourcompany.serviceid',  # Services ID
            'secret': 'YOUR-TEAM-ID.YOUR-KEY-ID',
            'key': 'YOUR-PRIVATE-KEY',  # Contents of .p8 file
        }
    }
}
```

**Callback URL:** `https://yourdomain.com/accounts/apple/login/callback/`

**Setup:** https://developer.apple.com/account/resources/identifiers/list/serviceId (Create Services ID > Configure Sign In with Apple)

**Note:** Apple only provides name/email on first sign-in. Email may be private relay address.

---

### Twitter (X)

```python
INSTALLED_APPS = ['allauth.socialaccount.providers.twitter']

SOCIALACCOUNT_PROVIDERS = {
    'twitter': {
        'APP': {
            'client_id': os.environ['TWITTER_CLIENT_ID'],
            'secret': os.environ['TWITTER_SECRET'],
        }
    }
}
```

**Callback URL:** `https://yourdomain.com/accounts/twitter/login/callback/`

**Setup:** https://developer.twitter.com/en/portal/projects-and-apps

---

### LinkedIn

```python
INSTALLED_APPS = ['allauth.socialaccount.providers.linkedin_oauth2']

SOCIALACCOUNT_PROVIDERS = {
    'linkedin_oauth2': {
        'SCOPE': ['r_liteprofile', 'r_emailaddress'],
        'APP': {
            'client_id': os.environ['LINKEDIN_CLIENT_ID'],
            'secret': os.environ['LINKEDIN_SECRET'],
        }
    }
}
```

**Callback URL:** `https://yourdomain.com/accounts/linkedin_oauth2/login/callback/`

**Setup:** https://www.linkedin.com/developers/apps

---

### Discord

```python
INSTALLED_APPS = ['allauth.socialaccount.providers.discord']

SOCIALACCOUNT_PROVIDERS = {
    'discord': {
        'APP': {
            'client_id': os.environ['DISCORD_CLIENT_ID'],
            'secret': os.environ['DISCORD_SECRET'],
        }
    }
}
```

**Callback URL:** `https://yourdomain.com/accounts/discord/login/callback/`

**Setup:** https://discord.com/developers/applications

---

### Slack

```python
INSTALLED_APPS = ['allauth.socialaccount.providers.slack']

SOCIALACCOUNT_PROVIDERS = {
    'slack': {
        'APP': {
            'client_id': os.environ['SLACK_CLIENT_ID'],
            'secret': os.environ['SLACK_SECRET'],
        }
    }
}
```

**Callback URL:** `https://yourdomain.com/accounts/slack/login/callback/`

**Setup:** https://api.slack.com/apps

---

## Common Settings

```python
# Auto-create account on social login
SOCIALACCOUNT_AUTO_SIGNUP = True  # Default

# Require email from social provider
SOCIALACCOUNT_EMAIL_REQUIRED = True  # Default: False

# Store OAuth tokens in database (security risk - only if needed for API calls)
SOCIALACCOUNT_STORE_TOKENS = False  # Default

# Trust social provider's email to log into existing accounts (⚠️ security risk)
SOCIALACCOUNT_EMAIL_AUTHENTICATION = False  # Default - only enable for trusted providers

# Request email scope from providers
SOCIALACCOUNT_QUERY_EMAIL = True  # Default

# Redirect after social login
LOGIN_REDIRECT_URL = '/dashboard/'
```

### SOCIALACCOUNT_AUTO_SIGNUP

- `True`: Automatically create account if email doesn't exist
- `False`: Show signup form to collect additional fields

### SOCIALACCOUNT_STORE_TOKENS

**⚠️ WARNING:** Tokens stored in plaintext. Only enable if making API calls to provider.

### SOCIALACCOUNT_EMAIL_AUTHENTICATION

**⚠️ CRITICAL:** Only enable for fully trusted providers (Google, Microsoft). Risk of account hijacking with untrusted providers.

---

## Configuration Options Reference

All providers support this structure:

```python
SOCIALACCOUNT_PROVIDERS = {
    'provider_id': {
        'SCOPE': ['email', 'profile'],           # OAuth scopes
        'AUTH_PARAMS': {'access_type': 'online'}, # OAuth parameters
        'VERIFIED_EMAIL': True,                   # Trust provider's email verification
        'OAUTH_PKCE_ENABLED': True,               # Enable PKCE (recommended)
        'APP': {
            'client_id': 'YOUR-CLIENT-ID',
            'secret': 'YOUR-SECRET-KEY',
            'key': '',  # Required for some providers
        }
    }
}
```

---

## Troubleshooting

**Callback URL mismatch:**
- Verify exact URL in provider console (HTTPS vs HTTP, domain, port, trailing slash)

**Provider not showing in admin:**
- Add to INSTALLED_APPS
- Run `python manage.py migrate`
- Restart server

**Email not captured:**
- Add email to `SCOPE`
- Set `SOCIALACCOUNT_QUERY_EMAIL = True`

**Account not auto-created:**
- Set `SOCIALACCOUNT_AUTO_SIGNUP = True`
- Check email doesn't already exist

---

## Production Checklist

```python
# Minimal production-ready configuration
INSTALLED_APPS = [
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

SITE_ID = 1

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'OAUTH_PKCE_ENABLED': True,
        'APP': {
            'client_id': os.environ['GOOGLE_CLIENT_ID'],
            'secret': os.environ['GOOGLE_SECRET'],
        }
    }
}

# Security settings
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_STORE_TOKENS = False  # Only if needed
SOCIALACCOUNT_EMAIL_AUTHENTICATION = False  # Only for trusted providers
```

---

## See Also

- `/home/user/django-allauth-mirror/.claude/skills/django-allauth/reference/setup-guide.md` - Initial setup
- `/home/user/django-allauth-mirror/.claude/skills/django-allauth/reference/customization.md` - Adapters and signals
- `/home/user/django-allauth-mirror/.claude/skills/django-allauth/reference/security.md` - Security best practices
