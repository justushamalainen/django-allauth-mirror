# Custom Provider Implementation Guide

This guide demonstrates how to create a custom OAuth2 provider for django-allauth. This is an advanced feature for edge cases where you need to integrate with a provider not already supported.

## Directory Structure

```
myapp/providers/custom/
├── __init__.py
├── provider.py      # Provider and Account classes
├── views.py         # Adapter class
└── urls.py          # URL patterns
```

## Required Classes and Methods

### Classes

- **OAuth2Provider** - Inherits from `allauth.socialaccount.providers.oauth2.provider.OAuth2Provider`
- **OAuth2Adapter** - Inherits from `allauth.socialaccount.providers.oauth2.views.OAuth2Adapter`
- **ProviderAccount** (optional) - Inherits from `allauth.socialaccount.providers.base.ProviderAccount`

### Required Methods

| Method | Purpose |
|--------|---------|
| `extract_uid(data)` | Extract unique user ID from provider response (must return string) |
| `complete_login(request, app, token, **kwargs)` | Fetch user profile and return SocialLogin instance |

### Recommended Methods

| Method | Purpose |
|--------|---------|
| `extract_common_fields(data)` | Map provider data to Django User fields (email, username, name, etc.) |
| `extract_email_addresses(data)` | Extract multiple email addresses with verification status |
| `get_default_scope()` | Define default OAuth2 scopes for the provider |

## Complete Working Example

This example implements a fictional "ExampleCorp" OAuth2 provider. Copy and adapt this structure for your provider.

### provider.py

```python
from allauth.account.models import EmailAddress
from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider


class ExampleCorpAccount(ProviderAccount):
    """Optional: Customize account display."""

    def get_profile_url(self):
        return self.account.extra_data.get("profile_url")

    def get_avatar_url(self):
        return self.account.extra_data.get("avatar")

    def to_str(self):
        name = self.account.extra_data.get("display_name")
        return name or super().to_str()


class ExampleCorpProvider(OAuth2Provider):
    id = "examplecorp"  # Unique lowercase identifier
    name = "ExampleCorp"  # Human-readable name
    account_class = ExampleCorpAccount

    def get_default_scope(self):
        """Default OAuth2 scopes."""
        return ["read:user", "read:email"]

    def extract_uid(self, data):
        """
        Extract unique user identifier.
        MUST return a string, not an integer.
        """
        return str(data["user_id"])

    def extract_common_fields(self, data):
        """Map provider data to Django User model fields."""
        return dict(
            email=data.get("email"),
            username=data.get("username"),
            name=data.get("display_name"),
        )

    def extract_email_addresses(self, data):
        """
        Extract email addresses with verification status.
        Returns list of EmailAddress objects.
        """
        ret = []
        if data.get("email"):
            ret.append(
                EmailAddress(
                    email=data["email"],
                    primary=True,
                    verified=data.get("email_confirmed", False),
                )
            )
        return ret


# Required: Export provider classes for registration
provider_classes = [ExampleCorpProvider]
```

### views.py

```python
from allauth.socialaccount.adapter import get_adapter
from allauth.socialaccount.providers.base import ProviderException
from allauth.socialaccount.providers.oauth2.views import (
    OAuth2Adapter,
    OAuth2CallbackView,
    OAuth2LoginView,
)


class ExampleCorpOAuth2Adapter(OAuth2Adapter):
    provider_id = "examplecorp"  # Must match Provider.id

    # OAuth2 endpoints - replace with your provider's URLs
    access_token_url = "https://auth.examplecorp.com/oauth/token"
    authorize_url = "https://auth.examplecorp.com/oauth/authorize"
    profile_url = "https://api.examplecorp.com/v2/user"

    def complete_login(self, request, app, token, **kwargs):
        """
        Fetch user profile and return SocialLogin instance.
        Called after OAuth2 token exchange.
        """
        headers = {"Authorization": f"Bearer {token.token}"}

        with get_adapter().get_requests_session() as sess:
            resp = sess.get(self.profile_url, headers=headers)

            if resp.status_code != 200:
                raise ProviderException(
                    f"Failed to fetch user profile: {resp.status_code}"
                )

            extra_data = resp.json()

            # Validate required fields
            if "user_id" not in extra_data:
                raise ProviderException("Provider response missing user_id")

        return self.get_provider().sociallogin_from_response(request, extra_data)


# Required: Create view instances
oauth2_login = OAuth2LoginView.adapter_view(ExampleCorpOAuth2Adapter)
oauth2_callback = OAuth2CallbackView.adapter_view(ExampleCorpOAuth2Adapter)
```

### urls.py

```python
from allauth.socialaccount.providers.oauth2.urls import default_urlpatterns
from .provider import ExampleCorpProvider

urlpatterns = default_urlpatterns(ExampleCorpProvider)
```

## Configuration

### 1. Add to INSTALLED_APPS

```python
INSTALLED_APPS = [
    # ...
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'myapp.providers.examplecorp',  # Add your custom provider
    # ...
]
```

### 2. Configure Provider Settings

```python
SOCIALACCOUNT_PROVIDERS = {
    'examplecorp': {
        'SCOPE': ['read:user', 'read:email'],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,  # Recommended for security
    }
}
```

### 3. Create Social App in Admin

1. Navigate to Django admin
2. Add a Social Application:
   - Provider: ExampleCorp
   - Name: ExampleCorp OAuth
   - Client ID: (from provider)
   - Secret key: (from provider)
   - Sites: Select your site

## Common Pitfalls

- **extract_uid must return string**: Use `str(data["id"])`, not `data["id"]`
- **Provider not found**: Ensure `provider_classes = [YourProvider]` is in provider.py
- **Import errors**: Add provider app to `INSTALLED_APPS`
- **Callback URL mismatch**: Verify OAuth callback URL matches your domain and is registered with the provider

## Key Points

- Keep provider ID lowercase with no spaces
- Handle missing data gracefully with `.get()` methods
- Validate provider responses before processing
- Use `ProviderException` for provider-specific errors
- Enable PKCE (`OAUTH_PKCE_ENABLED`) for enhanced security
