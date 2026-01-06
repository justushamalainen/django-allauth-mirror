# Social Providers Guide

Complete reference for integrating social authentication providers with django-allauth.

## Provider Setup Checklist

Follow these steps for any social provider integration:

### 1. Add Provider to INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    # ... Django apps ...
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',  # Add your provider here
    'allauth.socialaccount.providers.github',
    # ... other providers ...
]
```

### 2. Run Migrations

```bash
python manage.py migrate
```

### 3. Configure Social App

Choose one approach:

**Option A: Admin Interface (Recommended for development)**
- Navigate to `/admin/socialaccount/socialapp/`
- Create new SocialApp entry
- Provider: Select from dropdown
- Name: Display name (e.g., "Google Login")
- Client ID: From provider's developer console
- Secret key: From provider's developer console
- Sites: Select your site

**Option B: Settings File (Recommended for production)**
```python
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': '123-abc.apps.googleusercontent.com',
            'secret': 'YOUR-SECRET-KEY',
            'key': ''  # Leave empty for most providers
        }
    }
}
```

### 4. Set Callback URL in Provider Console

Each provider requires you to register the OAuth callback URL:

**Format:** `https://yourdomain.com/accounts/{provider}/login/callback/`

**Examples:**
- Google: `https://yourdomain.com/accounts/google/login/callback/`
- GitHub: `https://yourdomain.com/accounts/github/login/callback/`
- Facebook: `https://yourdomain.com/accounts/facebook/login/callback/`

**Common Issues:**
- Must use exact domain (including subdomain)
- HTTPS required in production (most providers)
- Port number matters in development (`localhost:8000` ≠ `localhost`)
- Trailing slash required for some providers

### 5. Add Login Button

```html
<!-- In your template -->
{% load socialaccount %}

<a href="{% provider_login_url 'google' %}">Login with Google</a>
<a href="{% provider_login_url 'github' %}">Login with GitHub</a>
```

---

## Top 5 Providers Quick-Start

### Google

**1. Get Credentials:**
- Console: https://console.cloud.google.com/apis/credentials
- Create OAuth 2.0 Client ID
- Application type: Web application
- Authorized redirect URIs: `https://yourdomain.com/accounts/google/login/callback/`

**2. Install:**
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
            'client_id': 'YOUR-CLIENT-ID.apps.googleusercontent.com',
            'secret': 'YOUR-SECRET-KEY',
            'key': ''
        }
    }
}
```

**Advanced Scopes:**
```python
'SCOPE': [
    'profile',
    'email',
    'openid',  # For OIDC support
    # Optional scopes:
    # 'https://www.googleapis.com/auth/userinfo.profile',
    # 'https://www.googleapis.com/auth/calendar.readonly',
]
```

**Callback URL:** `https://yourdomain.com/accounts/google/login/callback/`

---

### GitHub

**1. Get Credentials:**
- Console: https://github.com/settings/developers
- Create OAuth App
- Homepage URL: `https://yourdomain.com`
- Authorization callback URL: `https://yourdomain.com/accounts/github/login/callback/`

**2. Install:**
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
            'user:email',  # Access user email addresses
            # Optional scopes:
            # 'read:user',  # Read all user profile data
            # 'user:follow',  # Access followers
        ],
        'APP': {
            'client_id': 'YOUR-CLIENT-ID',
            'secret': 'YOUR-SECRET-KEY',
        }
    }
}
```

**Callback URL:** `https://yourdomain.com/accounts/github/login/callback/`

**Note:** GitHub may provide multiple email addresses. django-allauth will use the primary verified email.

---

### Facebook

**1. Get Credentials:**
- Console: https://developers.facebook.com/apps/
- Create App > Consumer
- Settings > Basic: Get App ID and App Secret
- Add Facebook Login product
- Valid OAuth Redirect URIs: `https://yourdomain.com/accounts/facebook/login/callback/`

**2. Install:**
```python
INSTALLED_APPS = [
    # ...
    'allauth.socialaccount.providers.facebook',
]
```

**3. Configure:**
```python
SOCIALACCOUNT_PROVIDERS = {
    'facebook': {
        'METHOD': 'oauth2',  # or 'js_sdk' for JavaScript SDK
        'SCOPE': [
            'email',
            'public_profile',
        ],
        'AUTH_PARAMS': {
            'auth_type': 'reauthenticate'  # Force re-auth
        },
        'INIT_PARAMS': {'cookie': True},
        'FIELDS': [
            'id',
            'first_name',
            'last_name',
            'email',
            'name',
            'picture',
        ],
        'VERIFIED_EMAIL': False,  # Facebook emails not always verified
        'VERSION': 'v18.0',  # Graph API version
        'APP': {
            'client_id': 'YOUR-APP-ID',
            'secret': 'YOUR-APP-SECRET',
        }
    }
}
```

**Callback URL:** `https://yourdomain.com/accounts/facebook/login/callback/`

**Security Note:** Facebook does not verify email addresses. Set `ACCOUNT_EMAIL_VERIFICATION = 'mandatory'` if email verification is critical.

---

### Microsoft

**1. Get Credentials:**
- Console: https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps
- Register new application
- Platform: Web
- Redirect URIs: `https://yourdomain.com/accounts/microsoft/login/callback/`
- Certificates & secrets: Create new client secret

**2. Install:**
```python
INSTALLED_APPS = [
    # ...
    'allauth.socialaccount.providers.microsoft',
]
```

**3. Configure:**
```python
SOCIALACCOUNT_PROVIDERS = {
    'microsoft': {
        'SCOPE': [
            'User.Read',  # Basic profile
            # Optional scopes:
            # 'Calendars.Read',
            # 'Mail.Read',
        ],
        'TENANT': 'common',  # 'common', 'organizations', 'consumers', or tenant ID
        'APP': {
            'client_id': 'YOUR-APPLICATION-CLIENT-ID',
            'secret': 'YOUR-CLIENT-SECRET',
        }
    }
}
```

**Callback URL:** `https://yourdomain.com/accounts/microsoft/login/callback/`

**Tenant Options:**
- `common`: Both personal Microsoft accounts and work/school accounts
- `organizations`: Only work/school accounts
- `consumers`: Only personal Microsoft accounts
- `<tenant-id>`: Specific organization only

---

### Apple

**1. Get Credentials:**
- Console: https://developer.apple.com/account/resources/identifiers/list/serviceId
- Create Services ID
- Configure Sign In with Apple
- Return URLs: `https://yourdomain.com/accounts/apple/login/callback/`
- Create Private Key for Sign In with Apple

**2. Install:**
```python
INSTALLED_APPS = [
    # ...
    'allauth.socialaccount.providers.apple',
]
```

**3. Configure:**
```python
SOCIALACCOUNT_PROVIDERS = {
    'apple': {
        'SCOPE': [
            'name',
            'email',
        ],
        'APP': {
            'client_id': 'com.yourcompany.yourserviceid',  # Services ID
            'secret': 'YOUR-TEAM-ID.YOUR-KEY-ID',  # Team ID + Key ID
            'key': 'YOUR-PRIVATE-KEY',  # Contents of .p8 file
            # OR use certificate:
            # 'certificate_key': '/path/to/key.p8',
        },
        'SETTINGS': {
            'team': 'YOUR-TEAM-ID',
            'key': 'YOUR-KEY-ID',
        }
    }
}
```

**Callback URL:** `https://yourdomain.com/accounts/apple/login/callback/`

**Important Notes:**
- Apple only provides name data on first sign-in
- Email may be private relay address (`@privaterelay.appleid.com`)
- Requires active Apple Developer Program membership

---

## Provider Configuration Pattern

All providers follow this configuration structure:

```python
SOCIALACCOUNT_PROVIDERS = {
    'provider_id': {
        # OAuth Scopes (permissions requested from user)
        'SCOPE': ['email', 'profile'],

        # Additional OAuth authorization parameters
        'AUTH_PARAMS': {
            'access_type': 'offline',  # Request refresh token
            'prompt': 'consent',        # Force consent screen
        },

        # App credentials (alternative to database configuration)
        'APP': {
            'client_id': 'YOUR-CLIENT-ID',
            'secret': 'YOUR-SECRET-KEY',
            'key': '',  # Some providers (Twitter, LinkedIn) need this
        },

        # Provider-specific settings
        'VERIFIED_EMAIL': True,    # Trust provider's email verification
        'VERSION': 'v2.0',          # API version (if applicable)
        'TENANT': 'common',         # Microsoft-specific
        'METHOD': 'oauth2',         # Facebook-specific
        # ... other provider-specific options ...
    }
}
```

### Common Configuration Options

| Option | Type | Description |
|--------|------|-------------|
| `SCOPE` | list | OAuth scopes/permissions to request |
| `AUTH_PARAMS` | dict | Additional parameters for authorization URL |
| `APP` | dict | Credentials (alternative to database storage) |
| `VERIFIED_EMAIL` | bool | Whether to trust provider's email verification |
| `OAUTH_PKCE_ENABLED` | bool | Enable PKCE for added security (OAuth 2.1) |

---

## Database vs Settings-Based Apps

### Database Configuration (via Admin)

**Use when:**
- Multiple environments share same codebase
- Non-technical staff need to manage credentials
- Different sites in a multi-tenant setup need different apps

**Pros:**
- No code changes to update credentials
- Manage via admin interface
- Different credentials per Django site

**Cons:**
- Requires database access to view/change
- Must be configured after deployment
- Not version controlled

**Setup:**
```python
# settings.py - No APP key needed
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        # No APP key - will use database
    }
}
```

Then configure via admin at `/admin/socialaccount/socialapp/`.

---

### Settings-Based Configuration

**Use when:**
- Credentials are environment variables
- Following 12-factor app principles
- Automating deployments
- Containers/serverless environments

**Pros:**
- Version controlled (with secrets encrypted)
- Environment-specific via env vars
- No manual admin setup needed

**Cons:**
- Requires code deployment to update
- Credentials in settings (use environment variables!)

**Setup:**
```python
# settings.py
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.environ.get('GOOGLE_CLIENT_ID'),
            'secret': os.environ.get('GOOGLE_SECRET'),
        }
    }
}
```

**Best Practice:** Use environment variables:
```bash
# .env file (never commit this!)
GOOGLE_CLIENT_ID=123-abc.apps.googleusercontent.com
GOOGLE_SECRET=your-secret-key
```

---

### Multi-Environment Handling

**Recommended Pattern:**
```python
# settings.py
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
    }
}

# Different files or environment-specific settings
if os.environ.get('DJANGO_ENV') == 'production':
    SOCIALACCOUNT_PROVIDERS['google']['APP'] = {
        'client_id': os.environ.get('GOOGLE_CLIENT_ID_PROD'),
        'secret': os.environ.get('GOOGLE_SECRET_PROD'),
    }
elif os.environ.get('DJANGO_ENV') == 'staging':
    SOCIALACCOUNT_PROVIDERS['google']['APP'] = {
        'client_id': os.environ.get('GOOGLE_CLIENT_ID_STAGING'),
        'secret': os.environ.get('GOOGLE_SECRET_STAGING'),
    }
# else: Use database configuration for development
```

---

## Provider Categories

django-allauth supports 127+ providers across different protocols:

### OAuth 2.0 Providers (Most Common)

| Provider | ID | Use Case | Verified Email |
|----------|----|-----------|--------------------|
| Google | `google` | General auth, Google services | Yes |
| GitHub | `github` | Developer tools, code platforms | Yes |
| Facebook | `facebook` | Social apps, general auth | No* |
| Microsoft | `microsoft` | Enterprise apps, Office 365 | Yes |
| Twitter | `twitter` | Social media integration | Limited |
| LinkedIn | `linkedin_oauth2` | Professional networks | Yes |
| Discord | `discord` | Gaming, communities | Yes |
| Slack | `slack` | Team collaboration | Yes |
| Spotify | `spotify` | Music apps | Yes |

*Facebook marks emails as verified, but they may not be actually verified by the user.

### OpenID Connect (OIDC) Providers

| Provider | ID | Use Case |
|----------|----|-----------|
| Generic OIDC | `openid_connect` | Any OIDC-compliant provider |
| Apple | `apple` | iOS apps, privacy-focused |
| Auth0 | `auth0` | Identity platform |
| Keycloak | `openid_connect` | Self-hosted identity |
| Okta | `okta` | Enterprise SSO |

**OIDC Configuration:**
```python
SOCIALACCOUNT_PROVIDERS = {
    'openid_connect': {
        'APPS': [
            {
                'provider_id': 'keycloak',
                'name': 'Keycloak SSO',
                'client_id': 'your-client-id',
                'secret': 'your-secret',
                'settings': {
                    'server_url': 'https://keycloak.example.com/realms/myrealm/.well-known/openid-configuration',
                }
            }
        ]
    }
}
```

### SAML 2.0 Providers

django-allauth has limited built-in SAML support. Use `djangosaml2` or `python3-saml` for SAML integration.

### Custom Protocol Providers

| Provider | Protocol | Use Case |
|----------|----------|----------|
| Persona | BrowserID | Deprecated |
| OpenID (legacy) | OpenID 1.0/2.0 | Mostly deprecated |

---

## Common Settings

Configure social account behavior globally:

### SOCIALACCOUNT_AUTO_SIGNUP

```python
SOCIALACCOUNT_AUTO_SIGNUP = True  # Default
```

**True:** Automatically create account if social login email doesn't exist
**False:** Show signup form even if email from social provider is available

**Use False when:**
- Need to collect additional fields (terms acceptance, phone number)
- Want explicit user consent before account creation
- Need custom validation logic

---

### SOCIALACCOUNT_EMAIL_REQUIRED

```python
SOCIALACCOUNT_EMAIL_REQUIRED = False  # Default (inferred from ACCOUNT_SIGNUP_FIELDS)
```

**True:** Require email address from social provider
**False:** Allow signup without email (if provider doesn't supply one)

**Note:** Automatically set to `True` if `ACCOUNT_SIGNUP_FIELDS` requires email.

---

### SOCIALACCOUNT_STORE_TOKENS

```python
SOCIALACCOUNT_STORE_TOKENS = False  # Default
```

**True:** Store OAuth access tokens in database
**False:** Discard tokens after authentication

**⚠️ SECURITY WARNING:**
- Tokens are stored in **PLAINTEXT** in the database
- Anyone with database access can use these tokens
- Tokens may grant access to user's social account data
- Only enable if you need token for API calls

**When to use True:**
- Making API calls to social provider on behalf of user
- Syncing data from social platform
- Implementing social features (post to Facebook, etc.)

**If enabled, protect tokens:**
```python
# Use database encryption at rest
# Limit database access strictly
# Rotate tokens regularly
# Monitor token usage
# Consider encrypt/decrypt in SocialAccountAdapter
```

---

### SOCIALACCOUNT_EMAIL_AUTHENTICATION

```python
SOCIALACCOUNT_EMAIL_AUTHENTICATION = False  # Default
```

**True:** If social login email matches existing account, log into that account
**False:** Require explicit social account connection

**⚠️ CRITICAL SECURITY WARNING:**
- **DO NOT** set to `True` with untrustworthy providers
- Malicious provider could fabricate verified email and hijack accounts
- **Only use with fully trusted providers** (Google, Microsoft, etc.)
- High risk of account takeover attacks

**Example Attack Scenario:**
1. Attacker creates malicious OAuth provider
2. User logs in with malicious provider
3. Malicious provider returns `victim@example.com` as verified email
4. If `EMAIL_AUTHENTICATION = True`, attacker gains access to victim's account

**Safe Usage:**
```python
# Only enable for specific trusted providers
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        # Can trust Google's email verification
        'EMAIL_AUTHENTICATION': True,
    },
    'facebook': {
        # Cannot trust Facebook's verification
        'EMAIL_AUTHENTICATION': False,  # Keep disabled
    }
}
```

---

### SOCIALACCOUNT_QUERY_EMAIL

```python
SOCIALACCOUNT_QUERY_EMAIL = True  # Default (if EMAIL_REQUIRED)
```

Controls whether to request email scope from providers.

**True:** Request email in OAuth scopes
**False:** Don't request email (user profile only)

---

### Additional Settings

```python
# Redirect after social login
LOGIN_REDIRECT_URL = '/dashboard/'

# Allow immediate social login (skip intermediate page)
SOCIALACCOUNT_LOGIN_ON_GET = False  # Default: False (security risk if True)

# Auto-connect social account when emails match
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = False  # Default
```

---

## Quick Reference: Configuration Checklist

```python
# Minimal production-ready configuration
INSTALLED_APPS = [
    'django.contrib.sites',  # Required!
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

SITE_ID = 1

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'OAUTH_PKCE_ENABLED': True,  # Security best practice
        'APP': {
            'client_id': os.environ['GOOGLE_CLIENT_ID'],
            'secret': os.environ['GOOGLE_SECRET'],
        }
    }
}

# Security settings
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_STORE_TOKENS = False  # Only enable if needed
SOCIALACCOUNT_EMAIL_AUTHENTICATION = False  # Only for trusted providers
```

---

## Troubleshooting

**Callback URL mismatch:**
- Verify exact URL in provider console
- Check HTTPS vs HTTP
- Ensure domain matches (including subdomain)
- Include/exclude trailing slash consistently

**Provider not showing in admin:**
- Check provider is in INSTALLED_APPS
- Run `python manage.py migrate`
- Restart development server

**Email not captured:**
- Check `SCOPE` includes email permission
- Verify `SOCIALACCOUNT_QUERY_EMAIL = True`
- Some providers require email scope approval

**Account not auto-created:**
- Check `SOCIALACCOUNT_AUTO_SIGNUP = True`
- Verify email doesn't already exist
- Check for signals preventing creation

---

## See Also

- `/home/user/django-allauth-mirror/.claude/skills/django-allauth/reference/setup-guide.md` - Initial setup
- `/home/user/django-allauth-mirror/.claude/skills/django-allauth/reference/customization.md` - Adapters and signals
- `/home/user/django-allauth-mirror/.claude/skills/django-allauth/reference/security.md` - Security best practices
