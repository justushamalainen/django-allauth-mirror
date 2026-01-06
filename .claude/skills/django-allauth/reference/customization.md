# Django-AllAuth Customization Guide

Quick reference for customizing django-allauth through adapters and forms.

## Table of Contents

1. [Adapter Pattern Overview](#adapter-pattern-overview)
2. [Creating Custom Adapters](#creating-custom-adapters)
3. [Registering Adapters](#registering-adapters)
4. [Form Customization](#form-customization)

---

## Adapter Pattern Overview

Adapters are the primary customization mechanism in django-allauth. They allow you to override default behavior without modifying the package code.

**Two main adapters:**
- `DefaultAccountAdapter` - Controls account authentication, registration, email
- `DefaultSocialAccountAdapter` - Controls social authentication behavior

**For detailed method references, see:**
- `/reference/adapter-methods.md` - Complete list of overridable adapter methods
- `/reference/signals-reference.md` - Signals for side effects (logging, notifications)

---

## Creating Custom Adapters

### Basic Account Adapter

```python
# myapp/adapters.py
from allauth.account.adapter import DefaultAccountAdapter

class MyAccountAdapter(DefaultAccountAdapter):

    def get_login_redirect_url(self, request):
        """Custom redirect after login"""
        if request.user.is_staff:
            return '/admin/'
        return '/dashboard/'
```

### Basic Social Account Adapter

```python
# myapp/adapters.py
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()

class MySocialAccountAdapter(DefaultSocialAccountAdapter):

    def pre_social_login(self, request, sociallogin):
        """Auto-connect social login to existing user by email"""
        if sociallogin.is_existing:
            return

        if sociallogin.email_addresses:
            email = sociallogin.email_addresses[0].email
            try:
                user = User.objects.get(email__iexact=email)
                sociallogin.connect(request, user)
            except User.DoesNotExist:
                pass
```

---

## Registering Adapters

### Account Adapter Registration

```python
# settings.py
ACCOUNT_ADAPTER = 'myapp.adapters.MyAccountAdapter'
```

### Social Account Adapter Registration

```python
# settings.py
SOCIALACCOUNT_ADAPTER = 'myapp.adapters.MySocialAccountAdapter'
```

### Both Adapters Together

```python
# settings.py
ACCOUNT_ADAPTER = 'myapp.adapters.MyAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'myapp.adapters.MySocialAccountAdapter'
```

---

## Form Customization

### Available Account Forms

Django-allauth provides these customizable forms via the `ACCOUNT_FORMS` setting:

| Form Class | Setting Key | Purpose |
|-----------|-------------|---------|
| `LoginForm` | `login` | Login page |
| `SignupForm` | `signup` | Signup page |
| `AddEmailForm` | `add_email` | Add email address |
| `ChangePasswordForm` | `change_password` | Change password |
| `ResetPasswordForm` | `reset_password` | Request password reset |
| `ResetPasswordKeyForm` | `reset_password_from_key` | Reset password with token |
| `SetPasswordForm` | `set_password` | Set password (no old password) |
| `UserTokenForm` | `user_token` | 2FA token input |

### Available Social Account Forms

Customize social account forms via the `SOCIALACCOUNT_FORMS` setting:

| Form Class | Setting Key | Purpose |
|-----------|-------------|---------|
| `SignupForm` | `signup` | Social signup form (when extra data needed) |
| `DisconnectForm` | `disconnect` | Disconnect social account |

### Override Forms in Settings

```python
# settings.py
ACCOUNT_FORMS = {
    'signup': 'myapp.forms.CustomSignupForm',
    'login': 'myapp.forms.CustomLoginForm',
    'reset_password': 'myapp.forms.CustomResetPasswordForm',
}

SOCIALACCOUNT_FORMS = {
    'signup': 'myapp.forms.CustomSocialSignupForm',
}
```

### Adding Custom Fields to Signup Form

**Step 1: Create custom form**

```python
# myapp/forms.py
from allauth.account.forms import SignupForm
from django import forms

class CustomSignupForm(SignupForm):

    first_name = forms.CharField(max_length=30, label='First Name')
    last_name = forms.CharField(max_length=30, label='Last Name')
    terms_accepted = forms.BooleanField(required=True)

    def save(self, request):
        user = super().save(request)
        # Additional processing if needed
        return user
```

**Step 2: Update adapter to save custom fields**

```python
# myapp/adapters.py
from allauth.account.adapter import DefaultAccountAdapter

class MyAccountAdapter(DefaultAccountAdapter):

    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=False)

        # Save custom fields to user
        user.first_name = form.cleaned_data.get('first_name', '')
        user.last_name = form.cleaned_data.get('last_name', '')

        if commit:
            user.save()

        return user
```

**Step 3: Register in settings**

```python
# settings.py
ACCOUNT_FORMS = {
    'signup': 'myapp.forms.CustomSignupForm',
}
ACCOUNT_ADAPTER = 'myapp.adapters.MyAccountAdapter'
```

### Customizing Social Signup Form

```python
# myapp/forms.py
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from django import forms

class CustomSocialSignupForm(SocialSignupForm):

    phone_number = forms.CharField(max_length=15, required=False)
    marketing_consent = forms.BooleanField(required=False)

    def save(self, request):
        user = super().save(request)
        # Process custom fields
        return user
```

```python
# settings.py
SOCIALACCOUNT_FORMS = {
    'signup': 'myapp.forms.CustomSocialSignupForm',
}
```

---

## Common Customization Patterns

### Pattern 1: Adapter for Business Logic

Use adapters to control authentication flow and redirects.

```python
class MyAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        # Role-based redirects
        pass

    def clean_email(self, email):
        # Email validation
        pass
```

### Pattern 2: Forms for User Input

Use forms to collect additional data during signup/login.

```python
class CustomSignupForm(SignupForm):
    extra_field = forms.CharField()
```

### Pattern 3: Adapter + Form Combination

Combine adapters and forms for complex requirements.

```python
# Form collects data
class CustomSignupForm(SignupForm):
    company = forms.CharField()

# Adapter processes it
class MyAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        # Save to user or related model
        pass
```

---

## See Also

- `/reference/adapter-methods.md` - Complete adapter method reference with examples
- `/reference/signals-reference.md` - Complete signals reference with examples
- `/reference/setup-guide.md` - Initial configuration
- `/reference/social-providers.md` - Provider-specific customization
