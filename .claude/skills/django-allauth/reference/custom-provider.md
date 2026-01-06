# Custom Provider Implementation Guide

This guide demonstrates how to create a custom OAuth2 provider for django-allauth. You'll learn the required structure, classes, methods, and testing approaches.

## Table of Contents

1. [Provider Structure](#provider-structure)
2. [Required Classes](#required-classes)
3. [Required Methods](#required-methods)
4. [Strongly Recommended Methods](#strongly-recommended-methods)
5. [Step-by-Step Implementation](#step-by-step-implementation)
6. [Testing Custom Providers](#testing-custom-providers)
7. [Error Handling](#error-handling)
8. [Complete Working Example](#complete-working-example)

## Provider Structure

Your custom provider should follow this directory structure:

```
myapp/providers/custom/
├── __init__.py
├── provider.py      # Provider and Account classes
├── views.py         # Adapter class
└── urls.py          # URL patterns
```

## Required Classes

### 1. OAuth2Provider (or OpenIDConnectProvider)

Inherits from `allauth.socialaccount.providers.oauth2.provider.OAuth2Provider`

### 2. OAuth2Adapter

Inherits from `allauth.socialaccount.providers.oauth2.views.OAuth2Adapter`

### 3. ProviderAccount (optional)

Inherits from `allauth.socialaccount.providers.base.ProviderAccount`

## Required Methods

These methods MUST be implemented in your Provider class:

### extract_uid()

**Returns:** `str` - A unique identifier for the user from the provider

```python
def extract_uid(self, data):
    """Extract the unique user ID from the provider's response data."""
    return str(data["id"])  # MUST return string, not int
```

### complete_login()

**Returns:** `SocialLogin` - A SocialLogin instance

Implement this in your Adapter class:

```python
def complete_login(self, request, app, token, **kwargs):
    """
    Fetch user data from the provider and return a SocialLogin instance.

    Args:
        request: The Django request object
        app: The SocialApp instance
        token: The SocialToken object with access_token
        **kwargs: Additional keyword arguments

    Returns:
        SocialLogin instance
    """
    headers = {"Authorization": f"Bearer {token.token}"}
    with get_adapter().get_requests_session() as sess:
        resp = sess.get(self.profile_url, headers=headers)
        resp.raise_for_status()
        extra_data = resp.json()
    return self.get_provider().sociallogin_from_response(request, extra_data)
```

## Strongly Recommended Methods

### extract_common_fields()

Maps provider data to Django User model fields:

```python
def extract_common_fields(self, data):
    """Extract common user fields from provider data."""
    return dict(
        email=data.get("email"),
        username=data.get("username"),
        name=data.get("name"),
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
    )
```

### extract_email_addresses()

Returns a list of EmailAddress objects:

```python
def extract_email_addresses(self, data):
    """Extract multiple email addresses from provider data."""
    ret = []
    for email_data in data.get("emails", []):
        ret.append(
            EmailAddress(
                email=email_data["email"],
                primary=email_data.get("primary", False),
                verified=email_data.get("verified", False),
            )
        )
    return ret
```

### get_default_scope()

Returns the default OAuth2 scopes:

```python
def get_default_scope(self):
    """Return the default scope for this provider."""
    return ["profile", "email"]
```

## Step-by-Step Implementation

### Step 1: Create provider.py

```python
from allauth.account.models import EmailAddress
from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider


class CustomProviderAccount(ProviderAccount):
    """Optional: Customize how the account is displayed."""

    def get_profile_url(self):
        """Return the URL to the user's profile on the provider."""
        return self.account.extra_data.get("profile_url")

    def get_avatar_url(self):
        """Return the URL to the user's avatar/profile picture."""
        return self.account.extra_data.get("avatar_url")

    def to_str(self):
        """Return a string representation of the account."""
        # Fallback to username if name is None
        name = self.account.extra_data.get("name")
        if name:
            return name
        return self.account.extra_data.get("username", super().to_str())


class CustomProvider(OAuth2Provider):
    id = "customprovider"  # Must be unique and lowercase
    name = "Custom Provider"  # Human-readable name
    account_class = CustomProviderAccount

    def get_default_scope(self):
        """Return the default OAuth2 scopes."""
        return ["profile", "email"]

    def extract_uid(self, data):
        """
        Extract unique user identifier.
        CRITICAL: Must return a string, not an integer.
        """
        return str(data["id"])

    def extract_common_fields(self, data):
        """Extract fields to populate Django User model."""
        return dict(
            email=data.get("email"),
            username=data.get("username"),
            name=data.get("name"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
        )

    def extract_email_addresses(self, data):
        """
        Extract multiple email addresses.
        Returns a list of EmailAddress objects.
        """
        ret = []
        # If provider returns a list of emails
        for email_data in data.get("emails", []):
            ret.append(
                EmailAddress(
                    email=email_data["email"],
                    primary=email_data.get("primary", False),
                    verified=email_data.get("verified", False),
                )
            )
        # If there's a single email field and not in emails list
        if not ret and data.get("email"):
            ret.append(
                EmailAddress(
                    email=data["email"],
                    primary=True,
                    verified=data.get("email_verified", False),
                )
            )
        return ret

    def extract_extra_data(self, data):
        """
        Extract provider-specific data to store in SocialAccount.extra_data.
        This is optional - by default, all data is stored.
        Use this to filter out sensitive or unnecessary data.
        """
        # Remove temporary data that shouldn't be persisted
        if "temporary_token" in data:
            data = dict(data)
            data.pop("temporary_token")
        return data


# Required: Export provider classes for registration
provider_classes = [CustomProvider]
```

### Step 2: Create views.py

```python
from allauth.socialaccount.adapter import get_adapter
from allauth.socialaccount.providers.oauth2.views import (
    OAuth2Adapter,
    OAuth2CallbackView,
    OAuth2LoginView,
)


class CustomProviderOAuth2Adapter(OAuth2Adapter):
    provider_id = "customprovider"  # Must match Provider.id

    # OAuth2 endpoints - replace with your provider's URLs
    access_token_url = "https://provider.example.com/oauth/token"
    authorize_url = "https://provider.example.com/oauth/authorize"
    profile_url = "https://api.provider.example.com/v1/user"

    # Optional: Configure token exchange method (default: "POST")
    access_token_method = "POST"

    # Optional: Use basic auth for token exchange
    basic_auth = False

    # Optional: Custom scope delimiter (default: " ")
    scope_delimiter = " "

    def complete_login(self, request, app, token, **kwargs):
        """
        Fetch user profile and return SocialLogin instance.

        This method is called after the OAuth2 token exchange.
        It should fetch the user's profile data and return a SocialLogin.
        """
        # Set up authorization header
        headers = {"Authorization": f"Bearer {token.token}"}

        # Fetch user profile
        with get_adapter().get_requests_session() as sess:
            resp = sess.get(self.profile_url, headers=headers)
            resp.raise_for_status()
            extra_data = resp.json()

        # Optional: Fetch additional data (e.g., email addresses)
        # emails = self.get_emails(headers)
        # if emails:
        #     extra_data["emails"] = emails

        # Convert provider data to SocialLogin
        return self.get_provider().sociallogin_from_response(request, extra_data)

    # Optional: Fetch additional data from other endpoints
    def get_emails(self, headers):
        """Example: Fetch user's email addresses from separate endpoint."""
        emails_url = "https://api.provider.example.com/v1/user/emails"
        with get_adapter().get_requests_session() as sess:
            resp = sess.get(emails_url, headers=headers)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()


# Required: Create view instances
oauth2_login = OAuth2LoginView.adapter_view(CustomProviderOAuth2Adapter)
oauth2_callback = OAuth2CallbackView.adapter_view(CustomProviderOAuth2Adapter)
```

### Step 3: Create urls.py

```python
from allauth.socialaccount.providers.oauth2.urls import default_urlpatterns
from .provider import CustomProvider


urlpatterns = default_urlpatterns(CustomProvider)
```

### Step 4: Register in settings.py

```python
INSTALLED_APPS = [
    # ...
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'myapp.providers.custom',  # Add your custom provider
    # ...
]

SOCIALACCOUNT_PROVIDERS = {
    'customprovider': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,  # Enable PKCE for enhanced security
    }
}
```

## Testing Custom Providers

### Using OAuth2TestsMixin

```python
from http import HTTPStatus
from django.test import TestCase

from tests.apps.socialaccount.base import OAuth2TestsMixin
from tests.mocking import MockedResponse
from myapp.providers.custom.provider import CustomProvider


class CustomProviderTests(OAuth2TestsMixin, TestCase):
    provider_id = CustomProvider.id

    def get_mocked_response(self):
        """
        Return mocked API responses for testing.

        Returns a list of MockedResponse objects that simulate
        the provider's API responses during the OAuth flow.
        """
        return MockedResponse(
            HTTPStatus.OK,
            """
            {
                "id": 12345,
                "username": "testuser",
                "email": "test@example.com",
                "name": "Test User",
                "first_name": "Test",
                "last_name": "User",
                "avatar_url": "https://example.com/avatar.jpg",
                "profile_url": "https://example.com/testuser",
                "email_verified": true
            }
            """,
        )

    def get_expected_to_str(self):
        """Return the expected string representation of the account."""
        return "Test User"

    def test_extract_uid_returns_string(self):
        """Ensure extract_uid returns a string, not an integer."""
        provider = self.provider
        data = {"id": 12345}
        uid = provider.extract_uid(data)
        self.assertIsInstance(uid, str)
        self.assertEqual(uid, "12345")

    def test_extract_common_fields(self):
        """Test that common fields are extracted correctly."""
        provider = self.provider
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "name": "Test User",
            "first_name": "Test",
            "last_name": "User",
        }
        fields = provider.extract_common_fields(data)
        self.assertEqual(fields["email"], "test@example.com")
        self.assertEqual(fields["username"], "testuser")
        self.assertEqual(fields["name"], "Test User")
```

## Error Handling

### Using ProviderException

Raise `ProviderException` when encountering provider-specific errors:

```python
from allauth.socialaccount.providers.base import ProviderException


class CustomProviderOAuth2Adapter(OAuth2Adapter):
    # ...

    def complete_login(self, request, app, token, **kwargs):
        headers = {"Authorization": f"Bearer {token.token}"}

        with get_adapter().get_requests_session() as sess:
            resp = sess.get(self.profile_url, headers=headers)

            # Check for provider-specific errors
            if resp.status_code == 403:
                raise ProviderException(
                    "Insufficient permissions. Please ensure the app "
                    "has the required scopes."
                )

            resp.raise_for_status()
            extra_data = resp.json()

            # Validate required fields
            if "id" not in extra_data:
                raise ProviderException(
                    "Provider did not return a user ID. "
                    "The response may be malformed."
                )

        return self.get_provider().sociallogin_from_response(request, extra_data)
```

### Error Display

Errors are automatically displayed to users via the `socialaccount/authentication_error.html` template. You can customize this template in your project.

## Complete Working Example

Here's a complete example for a fictional "ExampleCorp" OAuth2 provider:

**myapp/providers/examplecorp/provider.py:**

```python
from allauth.account.models import EmailAddress
from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider


class ExampleCorpAccount(ProviderAccount):
    def get_profile_url(self):
        return self.account.extra_data.get("profile_url")

    def get_avatar_url(self):
        return self.account.extra_data.get("avatar")

    def to_str(self):
        name = self.account.extra_data.get("display_name")
        return name or super().to_str()


class ExampleCorpProvider(OAuth2Provider):
    id = "examplecorp"
    name = "ExampleCorp"
    account_class = ExampleCorpAccount

    def get_default_scope(self):
        return ["read:user", "read:email"]

    def extract_uid(self, data):
        return str(data["user_id"])

    def extract_common_fields(self, data):
        return dict(
            email=data.get("email"),
            username=data.get("username"),
            name=data.get("display_name"),
        )

    def extract_email_addresses(self, data):
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


provider_classes = [ExampleCorpProvider]
```

**myapp/providers/examplecorp/views.py:**

```python
from allauth.socialaccount.adapter import get_adapter
from allauth.socialaccount.providers.base import ProviderException
from allauth.socialaccount.providers.oauth2.views import (
    OAuth2Adapter,
    OAuth2CallbackView,
    OAuth2LoginView,
)


class ExampleCorpOAuth2Adapter(OAuth2Adapter):
    provider_id = "examplecorp"

    access_token_url = "https://auth.examplecorp.com/oauth/token"
    authorize_url = "https://auth.examplecorp.com/oauth/authorize"
    profile_url = "https://api.examplecorp.com/v2/user"

    def complete_login(self, request, app, token, **kwargs):
        headers = {"Authorization": f"Bearer {token.token}"}

        with get_adapter().get_requests_session() as sess:
            resp = sess.get(self.profile_url, headers=headers)

            if resp.status_code != 200:
                raise ProviderException(
                    f"Failed to fetch user profile: {resp.status_code}"
                )

            extra_data = resp.json()

            if "user_id" not in extra_data:
                raise ProviderException("Provider response missing user_id")

        return self.get_provider().sociallogin_from_response(request, extra_data)


oauth2_login = OAuth2LoginView.adapter_view(ExampleCorpOAuth2Adapter)
oauth2_callback = OAuth2CallbackView.adapter_view(ExampleCorpOAuth2Adapter)
```

**myapp/providers/examplecorp/urls.py:**

```python
from allauth.socialaccount.providers.oauth2.urls import default_urlpatterns
from .provider import ExampleCorpProvider

urlpatterns = default_urlpatterns(ExampleCorpProvider)
```

## Best Practices

1. **Always return strings from extract_uid()** - Not integers, even if the provider uses numeric IDs
2. **Handle missing data gracefully** - Use `.get()` instead of direct key access
3. **Validate provider responses** - Check for required fields before processing
4. **Use proper error handling** - Raise `ProviderException` for provider-specific issues
5. **Test thoroughly** - Use `OAuth2TestsMixin` to ensure all flows work correctly
6. **Document required scopes** - Make it clear what OAuth2 scopes your provider needs
7. **Consider PKCE** - Enable `OAUTH_PKCE_ENABLED` for enhanced security
8. **Extract multiple emails** - Implement `extract_email_addresses()` if provider supports it
9. **Store minimal data** - Override `extract_extra_data()` to filter sensitive information
10. **Follow naming conventions** - Use lowercase, no spaces for provider ID

## Troubleshooting

### "extract_uid must return a string"
Ensure `extract_uid()` returns `str(data["id"])`, not just `data["id"]`.

### "No module named 'myapp.providers.custom'"
Add your provider app to `INSTALLED_APPS` in settings.py.

### "Provider not found"
Ensure `provider_classes = [YourProvider]` is defined in provider.py.

### "Missing required scope"
Check your provider's default scopes and configure them in `SOCIALACCOUNT_PROVIDERS`.

### "Authentication error" on callback
Verify your OAuth2 callback URL is registered with the provider and matches your configured domain.
