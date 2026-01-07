# OAuth2 vs OpenID Connect (OIDC) - Quick Guide

Practical guide for choosing and configuring OAuth2 vs OIDC providers in django-allauth.

## Quick Decision

**Test your provider**: `https://your-provider.com/.well-known/openid-configuration`
- ✅ Returns JSON → **Use OIDC**
- ❌ Returns 404 → **Use OAuth2**

```
Has .well-known/openid-configuration?
│
├── YES → Use openid_connect provider
│   └── Auth0, Okta, Keycloak, Azure AD
│
└── NO → Use OAuth2 provider
    ├── Built-in? → Use it (google, github, etc.)
    └── Custom? → Create OAuth2 provider
```

---

## Comparison

| Aspect | OAuth2 | OIDC |
|--------|--------|------|
| **Purpose** | Authorization | Authentication + Authorization |
| **User Identity** | Separate API call | Included in ID token |
| **Configuration** | Manual URLs | Auto-discovery |
| **User Data** | Provider-specific | Standardized claims |
| **User ID** | Varies | Standard `sub` |
| **Use Cases** | Social logins | Enterprise SSO |

---

## When to Use Each

### OAuth2
- Social platforms (Google, GitHub, Facebook, LinkedIn)
- No OIDC support
- Built-in provider available (127+ providers)
- Provider-specific features

### OIDC
- Enterprise SSO (Auth0, Okta, Keycloak, Azure AD)
- Multiple similar providers
- Standardized user data
- Auto-discovery

---

## OIDC Configuration

### Basic Setup

```python
INSTALLED_APPS = ['allauth.socialaccount.providers.openid_connect']

SOCIALACCOUNT_PROVIDERS = {
    'openid_connect': {
        'APPS': [
            {
                'provider_id': 'keycloak',
                'name': 'Keycloak',
                'client_id': 'your-client-id',
                'secret': 'your-client-secret',
                'settings': {
                    'server_url': 'https://keycloak.example.com/realms/master/.well-known/openid-configuration',
                },
            }
        ]
    }
}
```

### Multiple Providers

```python
'openid_connect': {
    'APPS': [
        {
            'provider_id': 'auth0',
            'name': 'Auth0',
            'client_id': 'auth0-client-id',
            'secret': 'auth0-secret',
            'settings': {'server_url': 'https://tenant.auth0.com/.well-known/openid-configuration'},
        },
        {
            'provider_id': 'okta',
            'name': 'Okta',
            'client_id': 'okta-client-id',
            'secret': 'okta-secret',
            'settings': {'server_url': 'https://org.okta.com/.well-known/openid-configuration'},
        },
    ]
}
```

---

## Discovery Endpoint

### server_url Options

**Full URL (recommended)**:
```python
'server_url': 'https://provider.com/.well-known/openid-configuration'
```

**Base URL** (auto-appends `/.well-known/openid-configuration`):
```python
'server_url': 'https://provider.com'
```

### What Gets Auto-Discovered

- Authorization endpoint (login page)
- Token endpoint (exchange code for tokens)
- Userinfo endpoint (user profile)
- JWKS URI (token verification)
- Supported auth methods

**No manual URL configuration needed!**

---

## Advanced Settings

```python
{
    'provider_id': 'custom-oidc',
    'name': 'Custom OIDC',
    'client_id': 'client-id',
    'secret': 'client-secret',
    'settings': {
        'server_url': 'https://provider.com/.well-known/openid-configuration',
        'uid_field': 'sub',  # Default user ID field
        'token_auth_method': 'client_secret_post',  # or client_secret_basic
        'fetch_userinfo': True,  # Get userinfo endpoint data
        'oauth_pkce_enabled': True,  # Enable PKCE
    },
}
```

---

## PKCE Configuration

### What is PKCE?

Security enhancement for authorization code flow. Recommended for mobile apps, SPAs, and public clients.

### Enable PKCE

**OAuth2**:
```python
SOCIALACCOUNT_PROVIDERS = {
    'github': {
        'OAUTH_PKCE_ENABLED': True,
    }
}
```

**OIDC**:
```python
'settings': {
    'oauth_pkce_enabled': True,
}
```

### When to Use

| Client Type | Use PKCE? |
|------------|-----------|
| Server-side web app | Optional |
| Mobile app | ✅ Yes |
| SPA | ✅ Yes |
| Public client | ✅ Yes |

---

## Provider Selection

### Common OIDC Providers

- **Auth0**: `https://{tenant}.auth0.com/.well-known/openid-configuration`
- **Okta**: `https://{org}.okta.com/.well-known/openid-configuration`
- **Keycloak**: `https://{host}/realms/{realm}/.well-known/openid-configuration`
- **Azure AD**: `https://login.microsoftonline.com/{tenant}/v2.0/.well-known/openid-configuration`

### Built-in OAuth2 Providers

Use these for: `google`, `github`, `facebook`, `linkedin_oauth2`, `twitter_oauth2`

---

## Scopes

**OAuth2** - Provider-specific:
```python
'google': {'SCOPE': ['profile', 'email']}
'github': {'SCOPE': ['user:email', 'read:user']}
```

**OIDC** - Standardized: `['openid', 'profile', 'email']`
- `openid` - Required
- `profile` - name, given_name, family_name, picture
- `email` - email, email_verified

---

## Troubleshooting

### OIDC Not Working?

1. Test discovery URL returns JSON: `https://provider.com/.well-known/openid-configuration`
2. Check client credentials are correct
3. Verify redirect URI: `http://localhost:8000/accounts/openid_connect/{provider_id}/login/callback/`
4. Ensure `openid` scope is included

### OAuth2 Not Working?

1. Verify endpoints are accessible
2. Check callback URL matches provider
3. Ensure necessary scopes included
4. Enable token storage if needed: `SOCIALACCOUNT_STORE_TOKENS = True`

---

## Quick Reference

### Decision Matrix

| Scenario | Use |
|----------|-----|
| Social login | Built-in OAuth2 provider |
| Enterprise SSO | OpenID Connect |
| Custom OIDC provider | OpenID Connect |
| Custom non-OIDC provider | Custom OAuth2 |
| Multiple similar IdPs | OpenID Connect |
| Standardized user data | OpenID Connect |
| Provider-specific features | OAuth2 |

### Configuration Comparison

| Feature | OAuth2 | OIDC |
|---------|--------|------|
| Auto-discovery | ❌ | ✅ |
| Manual endpoints | ✅ | ❌ |
| PKCE | `OAUTH_PKCE_ENABLED` | `oauth_pkce_enabled` |
| Default scopes | Provider-specific | `openid, profile, email` |
| User ID field | Varies | `sub` |

---

## Related Documentation

- [Social Providers Guide](./social-providers.md)
- [Callback URL Debugging](./callback-url-debugging.md)
- [Security Best Practices](./security.md)
