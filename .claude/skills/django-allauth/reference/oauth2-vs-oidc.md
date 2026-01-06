# OAuth2 vs OpenID Connect (OIDC) Guide

Understanding the difference between OAuth2 and OpenID Connect (OIDC) is crucial for choosing the right authentication provider in django-allauth.

## Table of Contents

- [Quick Decision Tree](#quick-decision-tree)
- [Key Differences Table](#key-differences-table)
- [When to Use Each](#when-to-use-each)
- [Using OpenID Connect Provider](#using-openid-connect-provider)
- [Provider Implementation Differences](#provider-implementation-differences)
- [Security Considerations](#security-considerations)
- [Migration Between OAuth2 and OIDC](#migration-between-oauth2-and-oidc)

---

## Quick Decision Tree

Follow this decision tree to choose the right approach:

```
Does your auth provider have a .well-known/openid-configuration endpoint?
│
├── YES → Use OIDC (openid_connect provider)
│   └── Examples: Auth0, Okta, Keycloak, Azure AD, Google Workspace
│
└── NO → Use provider-specific OAuth2 implementation
    │
    ├── Provider already implemented in django-allauth?
    │   ├── YES → Use the built-in provider (google, github, facebook, etc.)
    │   └── NO → Create custom OAuth2 provider
    │
    └── Examples: GitHub, Facebook, Twitter, LinkedIn
```

**Quick Test**: Try accessing `https://your-provider.com/.well-known/openid-configuration`
- If it returns JSON with `authorization_endpoint`, `token_endpoint`, etc. → Use OIDC
- If it returns 404 → Use OAuth2

---

## Key Differences Table

| Aspect | OAuth2 | OpenID Connect (OIDC) |
|--------|--------|----------------------|
| **Primary Purpose** | Authorization ("what can this app do?") | Authentication + Authorization ("who is this user?") |
| **User Identity** | Separate API call to provider's user endpoint | Included in ID token (JWT) |
| **User Info Format** | Provider-specific JSON structure | Standardized claims (sub, email, name, etc.) |
| **Setup Complexity** | Provider-specific configuration | Auto-discovery via `.well-known/openid-configuration` |
| **Endpoints** | Hardcoded authorize/token/userinfo URLs | Auto-discovered from server metadata |
| **Token Types** | Access token (opaque or JWT) | Access token + ID token (always JWT) |
| **User ID Field** | Provider-specific (id, user_id, etc.) | Standard `sub` claim |
| **Email Verification** | Provider-specific | Standard `email_verified` claim |
| **Built On** | OAuth2 protocol | OAuth2 + identity layer |
| **Typical Use Cases** | Social logins, API access | Enterprise SSO, federated identity |
| **Examples** | GitHub, Facebook, LinkedIn, Twitter | Auth0, Okta, Keycloak, Azure AD, Google (supports both) |

---

## When to Use Each

### Use OAuth2 Provider When:

1. **Social Authentication**: Integrating popular social platforms
   - Google, GitHub, Facebook, LinkedIn, Twitter
   - Provider-specific features (e.g., GitHub user:email scope)

2. **Provider Not OIDC-Compliant**: Legacy systems or providers without OIDC
   - No `.well-known/openid-configuration` endpoint
   - Custom authentication APIs

3. **Built-in Provider Available**: django-allauth has 127+ pre-configured providers
   - Less configuration required
   - Provider-specific optimizations
   - Community-tested implementations

### Use OpenID Connect Provider When:

1. **Enterprise Identity Providers**: Corporate SSO systems
   - Auth0, Okta, Keycloak, Azure AD, Google Workspace
   - SAML alternative with modern standards

2. **Multiple Similar Providers**: Configure multiple OIDC providers easily
   - Development, staging, production IdPs
   - Multi-tenant applications
   - Customer-specific identity providers

3. **Standardization Needed**: Consistent user data across providers
   - Standard claims (sub, email, email_verified, name)
   - Predictable data structure
   - Easier to maintain

4. **Advanced Features**: OIDC-specific capabilities
   - ID token verification
   - Token introspection
   - Discovery metadata

---

## Using OpenID Connect Provider

### Basic Configuration

```python
# settings.py
INSTALLED_APPS = [
    'allauth.socialaccount.providers.openid_connect',
    # ... other apps
]

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

### Multiple OIDC Providers

Configure multiple enterprise IdPs simultaneously:

```python
SOCIALACCOUNT_PROVIDERS = {
    'openid_connect': {
        'APPS': [
            {
                'provider_id': 'auth0',
                'name': 'Auth0',
                'client_id': 'auth0-client-id',
                'secret': 'auth0-secret',
                'settings': {
                    'server_url': 'https://your-tenant.auth0.com/.well-known/openid-configuration',
                },
            },
            {
                'provider_id': 'okta',
                'name': 'Okta',
                'client_id': 'okta-client-id',
                'secret': 'okta-secret',
                'settings': {
                    'server_url': 'https://your-org.okta.com/.well-known/openid-configuration',
                },
            },
        ]
    }
}
```

### server_url Setting

The `server_url` can point to:

1. **Discovery Document** (recommended):
   ```python
   'server_url': 'https://provider.com/.well-known/openid-configuration'
   ```

2. **Base URL** (auto-appends `.well-known/openid-configuration`):
   ```python
   'server_url': 'https://provider.com'  # Will add /.well-known/openid-configuration
   ```

### Auto-Discovery Process

When you configure an OIDC provider, django-allauth automatically:

1. **Fetches Discovery Document**:
   ```json
   GET https://provider.com/.well-known/openid-configuration
   {
     "issuer": "https://provider.com",
     "authorization_endpoint": "https://provider.com/oauth2/authorize",
     "token_endpoint": "https://provider.com/oauth2/token",
     "userinfo_endpoint": "https://provider.com/oauth2/userinfo",
     "jwks_uri": "https://provider.com/.well-known/jwks.json",
     "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"]
   }
   ```

2. **Configures Endpoints**: No need to manually specify authorize_url, token_url, etc.

3. **Determines Auth Method**: Automatically selects `client_secret_post` or `client_secret_basic`

### Customizing OIDC Behavior

```python
SOCIALACCOUNT_PROVIDERS = {
    'openid_connect': {
        'APPS': [
            {
                'provider_id': 'custom-oidc',
                'name': 'Custom OIDC',
                'client_id': 'client-id',
                'secret': 'client-secret',
                'settings': {
                    'server_url': 'https://provider.com/.well-known/openid-configuration',

                    # Custom UID field (default: 'sub')
                    'uid_field': 'sub',  # or 'user_id', 'email', etc.

                    # Token authentication method
                    'token_auth_method': 'client_secret_post',  # or 'client_secret_basic'

                    # Fetch userinfo endpoint (default: True)
                    'fetch_userinfo': True,  # Set False to only use ID token

                    # PKCE support
                    'oauth_pkce_enabled': True,
                },
            }
        ]
    }
}
```

---

## Provider Implementation Differences

### OAuth2Provider Class Structure

```python
# Example: GitHub provider
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter

class GitHubProvider(OAuth2Provider):
    id = "github"
    name = "GitHub"
    oauth2_adapter_class = GitHubOAuth2Adapter

    def get_default_scope(self):
        # Provider-specific scopes
        return ["user:email"]

    def extract_uid(self, data):
        # Provider-specific user ID field
        return str(data["id"])

    def extract_common_fields(self, data):
        # Provider-specific field mapping
        return dict(
            email=data.get("email"),
            username=data.get("login"),
            name=data.get("name"),
        )

    def extract_email_addresses(self, data):
        # Custom logic for multiple emails
        ret = []
        for email in data.get("emails", []):
            ret.append(EmailAddress(
                email=email["email"],
                primary=email["primary"],
                verified=email["verified"],
            ))
        return ret
```

**OAuth2 Adapter** must define:
```python
class GitHubOAuth2Adapter(OAuth2Adapter):
    provider_id = "github"

    # Hardcoded endpoints
    access_token_url = "https://github.com/login/oauth/access_token"
    authorize_url = "https://github.com/login/oauth/authorize"
    profile_url = "https://api.github.com/user"

    def complete_login(self, request, app, token, **kwargs):
        # Fetch user data from API
        headers = {"Authorization": f"token {token.token}"}
        resp = requests.get(self.profile_url, headers=headers)
        extra_data = resp.json()
        return self.get_provider().sociallogin_from_response(request, extra_data)
```

### OpenIDConnectProvider Class Structure

```python
# Generic OIDC provider - works with any OIDC-compliant IdP
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider
from allauth.socialaccount.providers.openid_connect.views import OpenIDConnectOAuth2Adapter

class OpenIDConnectProvider(OAuth2Provider):
    id = "openid_connect"
    name = "OpenID Connect"
    oauth2_adapter_class = OpenIDConnectOAuth2Adapter
    supports_token_authentication = True

    def get_default_scope(self):
        # Standard OIDC scopes
        return ["openid", "profile", "email"]

    def extract_uid(self, data):
        # Standard OIDC claim
        data = _pick_data(data)  # Prefer userinfo over id_token
        return str(data[self.app.settings.get("uid_field", "sub")])

    def extract_common_fields(self, data):
        # Standard OIDC claims
        data = _pick_data(data)
        return dict(
            email=data.get("email"),
            username=data.get("preferred_username"),
            name=data.get("name"),
            first_name=data.get("given_name"),
            last_name=data.get("family_name"),
            picture=data.get("picture"),
        )

    def extract_email_addresses(self, data):
        # Standard email verification
        data = _pick_data(data)
        addresses = []
        email = data.get("email")
        if email:
            addresses.append(EmailAddress(
                email=email,
                verified=data.get("email_verified", False),
                primary=True,
            ))
        return addresses
```

**OIDC Adapter** auto-discovers endpoints:
```python
class OpenIDConnectOAuth2Adapter(OAuth2Adapter):
    @property
    def openid_config(self):
        # Fetch discovery document
        server_url = self.get_provider().server_url
        resp = requests.get(server_url)
        return resp.json()

    @property
    def access_token_url(self):
        return self.openid_config["token_endpoint"]  # Auto-discovered

    @property
    def authorize_url(self):
        return self.openid_config["authorization_endpoint"]  # Auto-discovered

    @property
    def profile_url(self):
        return self.openid_config["userinfo_endpoint"]  # Auto-discovered

    def complete_login(self, request, app, token: SocialToken, **kwargs):
        id_token_str = kwargs["response"].get("id_token")
        data = {}

        # Fetch userinfo (optional)
        if app.settings.get("fetch_userinfo", True):
            data["userinfo"] = self._fetch_user_info(token.token)

        # Decode and verify ID token
        if id_token_str:
            data["id_token"] = self._decode_id_token(app, id_token_str)

        return self.get_provider().sociallogin_from_response(request, data)

    def _decode_id_token(self, app, id_token):
        # Verify JWT signature using JWKS
        return jwtkit.verify_and_decode(
            credential=id_token,
            keys_url=self.openid_config["jwks_uri"],
            issuer=self.openid_config["issuer"],
            audience=app.client_id,
            lookup_kid=jwtkit.lookup_kid_jwk,
        )
```

### How ID Token is Handled

#### OAuth2 (Traditional)
```
User → Authorize → Access Token → UserInfo API → User Data
                                   (separate HTTP call)
```

Example: GitHub OAuth2 flow
```python
# 1. Get access token from OAuth2 flow
token = "gho_abc123..."

# 2. Make separate API call to get user data
headers = {"Authorization": f"token {token}"}
response = requests.get("https://api.github.com/user", headers=headers)
user_data = response.json()
# {"id": 12345, "login": "octocat", "email": "octocat@github.com"}
```

#### OIDC (Modern)
```
User → Authorize → Access Token + ID Token (JWT)
                   ↓
                   ID Token contains user data (no extra call needed)
                   Optionally fetch userinfo endpoint for more data
```

Example: OIDC flow
```python
# 1. Get tokens from OAuth2 flow
access_token = "eyJhbGc..."
id_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY..."

# 2. Decode ID token (JWT) - user data already inside!
decoded = jwt.decode(id_token, verify_signature=True)
# {
#   "sub": "12345",
#   "email": "user@example.com",
#   "email_verified": true,
#   "name": "John Doe",
#   "given_name": "John",
#   "family_name": "Doe"
# }

# 3. Optionally fetch userinfo endpoint for additional claims
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get("https://provider.com/userinfo", headers=headers)
userinfo = response.json()  # May have more detailed profile data
```

In django-allauth OIDC implementation:
```python
def _pick_data(data: dict) -> dict:
    """Prefer userinfo, it likely has more info compared to the ID token."""
    if userinfo := data.get("userinfo"):
        return userinfo  # More complete data
    elif id_token := data.get("id_token"):
        return id_token  # Fallback to ID token
    return data
```

---

## Security Considerations

### OAuth2 Security

1. **State Parameter**: CSRF protection
   ```python
   # Automatically handled by django-allauth
   state_id = self.stash_redirect_state(request, process, next_url, data)
   client.state = state_id
   ```

2. **PKCE Support**: Protection against authorization code interception
   ```python
   SOCIALACCOUNT_PROVIDERS = {
       'github': {
           'OAUTH_PKCE_ENABLED': True,  # Recommended for mobile/SPA
       }
   }
   ```

3. **Token Storage**: Access tokens stored in database (plaintext by default)
   ```python
   SOCIALACCOUNT_STORE_TOKENS = False  # Don't store unless needed
   ```

### OIDC Security Enhancements

1. **ID Token Verification**: JWT signature validation
   ```python
   # Automatically verified by django-allauth
   identity_data = jwtkit.verify_and_decode(
       credential=id_token,
       keys_url=openid_config["jwks_uri"],
       issuer=openid_config["issuer"],
       audience=[app.client_id],
       lookup_kid=jwtkit.lookup_kid_jwk,
   )
   ```

2. **Email Verification**: Built-in verification status
   ```python
   # OIDC provides standard email_verified claim
   if data.get("email_verified"):
       email_address.verified = True
   ```

3. **Issuer Validation**: Prevents token substitution attacks
   ```python
   # ID token must be issued by expected IdP
   assert decoded_token["iss"] == "https://expected-provider.com"
   ```

### Security Comparison

| Security Feature | OAuth2 | OIDC |
|-----------------|--------|------|
| CSRF Protection (State) | ✅ Yes | ✅ Yes |
| PKCE Support | ⚠️ Optional | ⚠️ Optional |
| Token Signature Verification | ❌ No (opaque tokens) | ✅ Yes (JWT) |
| Issuer Validation | ❌ No | ✅ Yes |
| Audience Validation | ❌ No | ✅ Yes |
| Email Verification Status | ⚠️ Provider-specific | ✅ Standard claim |
| Token Expiration | ⚠️ Opaque | ✅ Explicit exp claim |

---

## Migration Between OAuth2 and OIDC

### When Google Switched to OIDC Support

Google supports both OAuth2 and OIDC. Django-allauth's Google provider handles both:

```python
class GoogleProvider(OAuth2Provider):
    supports_token_authentication = True  # OIDC-style token auth

    def extract_uid(self, data):
        # Handle both OAuth2 and OIDC responses
        if "sub" in data:  # OIDC ID token
            return data["sub"]
        return data["id"]  # OAuth2 userinfo

    def extract_email_addresses(self, data):
        email = data.get("email")
        if email:
            # Handle both naming conventions
            verified = bool(
                data.get("email_verified") or  # OIDC
                data.get("verified_email")     # OAuth2
            )
            return [EmailAddress(email=email, verified=verified, primary=True)]
```

### Migrating from OAuth2 to Generic OIDC

If your provider adds OIDC support, you can migrate:

**Before (Custom OAuth2 Provider)**:
```python
SOCIALACCOUNT_PROVIDERS = {
    'custom_oauth2': {
        'AUTHORIZE_URL': 'https://provider.com/oauth/authorize',
        'ACCESS_TOKEN_URL': 'https://provider.com/oauth/token',
        'PROFILE_URL': 'https://provider.com/api/user',
    }
}
```

**After (Generic OIDC Provider)**:
```python
SOCIALACCOUNT_PROVIDERS = {
    'openid_connect': {
        'APPS': [
            {
                'provider_id': 'custom_oidc',
                'name': 'Custom Provider',
                'client_id': 'same-client-id',
                'secret': 'same-secret',
                'settings': {
                    'server_url': 'https://provider.com/.well-known/openid-configuration',
                },
            }
        ]
    }
}
```

**Benefits**:
- Auto-discovery of endpoints
- Standard claims (no custom field mapping)
- ID token verification
- Easier to maintain

---

## Quick Reference

### Choosing Between OAuth2 and OIDC

| If You Need... | Use |
|---------------|-----|
| Social login (Google, GitHub, Facebook) | Built-in OAuth2 providers |
| Enterprise SSO (Auth0, Okta, Keycloak) | OpenID Connect |
| Custom provider with `.well-known/openid-configuration` | OpenID Connect |
| Custom provider without OIDC support | Custom OAuth2 provider |
| Multiple similar enterprise IdPs | OpenID Connect (easy multi-tenant) |
| Standardized user data structure | OpenID Connect |
| Provider-specific features | OAuth2 provider |

### Default Scopes

**OAuth2 (varies by provider)**:
- Google: `['profile', 'email']`
- GitHub: `['user:email']` (if QUERY_EMAIL=True)
- Facebook: `['email']`

**OIDC (standardized)**:
- Default: `['openid', 'profile', 'email']`
- `openid`: Required for OIDC
- `profile`: name, given_name, family_name, picture
- `email`: email, email_verified

---

## Related Documentation

- [Social Providers Guide](./social-providers.md) - Top 5 social providers setup
- [Callback URL Debugging](./callback-url-debugging.md) - Common OAuth/OIDC callback errors
- [Security Best Practices](./security.md) - OAuth2/OIDC security settings
- [Customization Guide](./customization.md) - Customize OAuth2/OIDC behavior
