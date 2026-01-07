# Email Templates Guide

Quick reference for django-allauth's 40 email templates, customization, and configuration.

## Table of Contents

1. [Template Inventory](#template-inventory)
2. [Context Variables Reference](#context-variables-reference)
3. [Creating Custom Templates](#creating-custom-templates)
4. [Email Backend Configuration](#email-backend-configuration)
5. [Customizing via Adapter](#customizing-via-adapter)
6. [Testing Emails Locally](#testing-emails-locally)
7. [Best Practices](#best-practices)

---

## Template Inventory

Django-allauth ships with 40 email templates (20 subject/message pairs). All are plain text by default.

### Account Module (28 files)

Location: `allauth/templates/account/email/`

| Template | Purpose | Key Variables |
|----------|---------|---------------|
| `base_message.txt` | Base template for all emails | `current_site`, `email` |
| `base_notification.txt` | Base for security notifications | `timestamp`, `ip`, `user_agent` |
| **Email Verification** |
| `email_confirmation_subject.txt` / `_message.txt` | Verify email when adding new address | `user`, `activate_url`, `key`, `code` |
| `email_confirmation_signup_subject.txt` / `_message.txt` | Verify email during signup | Same as above |
| `email_confirm_subject.txt` / `_message.txt` | Legacy verification (deprecated) | `user`, `activate_url` |
| **Password Management** |
| `password_reset_key_subject.txt` / `_message.txt` | Password reset with URL | `password_reset_url`, `username` |
| `password_reset_code_subject.txt` / `_message.txt` | Password reset with code | `code` |
| `password_reset_subject.txt` / `_message.txt` | Legacy reset (deprecated) | `password_reset_url` |
| `password_set_subject.txt` / `_message.txt` | First-time password creation | `password_set_url` |
| `password_changed_subject.txt` / `_message.txt` | Security alert: password changed | Notification vars |
| **Login** |
| `login_code_subject.txt` / `_message.txt` | Passwordless login code | `code` |
| **Email Management** |
| `email_changed_subject.txt` / `_message.txt` | Security alert: email changed | `from_email`, `to_email` |
| `email_deleted_subject.txt` / `_message.txt` | Security alert: email removed | `deleted_email` |
| **Account Status** |
| `account_already_exists_subject.txt` / `_message.txt` | Signup with existing email | `signup_url`, `password_reset_url` |
| `unknown_account_subject.txt` / `_message.txt` | Reset on unlisted email (anti-enumeration) | None specific |

### MFA Module (8 files)

Location: `allauth/templates/mfa/email/`

| Template | Purpose | Key Variables |
|----------|---------|---------------|
| `totp_activated_subject.txt` / `_message.txt` | Security alert: TOTP enabled | Notification vars |
| `totp_deactivated_subject.txt` / `_message.txt` | Security alert: TOTP disabled | Notification vars |
| `webauthn_added_subject.txt` / `_message.txt` | Security alert: security key added | Notification vars |
| `webauthn_removed_subject.txt` / `_message.txt` | Security alert: security key removed | Notification vars |
| `recovery_codes_generated_subject.txt` / `_message.txt` | Recovery codes regenerated | Notification vars |

### Social Account Module (4 files)

Location: `allauth/templates/socialaccount/email/`

| Template | Purpose | Key Variables |
|----------|---------|---------------|
| `account_connected_subject.txt` / `_message.txt` | Security alert: social account linked | `provider` |
| `account_disconnected_subject.txt` / `_message.txt` | Security alert: social account unlinked | `provider` |

---

## Context Variables Reference

All templates receive base context from `render_mail()`:

| Variable | Type | Description | Available In |
|----------|------|-------------|--------------|
| `request` | HttpRequest | Current request object | All templates |
| `email` | str | Recipient email address | All templates |
| `current_site` | Site | Django Site object | All templates |
| `user` | User | User object | Most templates |
| **Verification/Authentication** |
| `activate_url` | str | Full email verification URL | Email confirmation |
| `key` | str | Verification key (64 chars) | Email confirmation |
| `code` | str | 6-8 digit verification code | Email/password/login codes |
| `password_reset_url` | str | Full password reset URL | Password reset |
| `password_set_url` | str | Full password set URL | Password set |
| `login_url` | str | Login page URL | Various |
| `signup_url` | str | Signup page URL | Account exists |
| **User Info** |
| `username` | str | Username (if available) | Password reset |
| **Security Notifications** |
| `timestamp` | datetime | When action occurred | All notifications |
| `ip` | str | Request IP address | All notifications |
| `user_agent` | str | Browser user agent | All notifications |
| `from_email` | str | Old email address | Email changed |
| `to_email` | str | New email address | Email changed |
| `deleted_email` | str | Removed email address | Email deleted |
| `provider` | str | Social provider name | Social account |

---

## Creating Custom Templates

### Directory Structure

Create templates in your project to override defaults:

```
your_project/
├── templates/
│   ├── account/
│   │   └── email/
│   │       ├── email_confirmation_subject.txt
│   │       ├── email_confirmation_message.txt
│   │       └── email_confirmation_message.html  # Optional HTML version
│   ├── mfa/
│   │   └── email/
│   │       └── totp_activated_message.txt
│   └── socialaccount/
│       └── email/
│           └── account_connected_message.txt
```

### Full Example: Email Confirmation Template

**templates/account/email/email_confirmation_message.txt**

```django
{% extends "account/email/base_message.txt" %}
{% load account %}
{% load i18n %}

{% block content %}
{% autoescape off %}
{# Get user's display name (username or email) #}
{% user_display user as user_display %}

{# Greeting #}
Hi {{ user_display }},

{# Purpose of email #}
Thanks for signing up at {{ current_site.name }}! Please confirm your email address to activate your account.

{# Primary action: URL-based verification #}
Click here to confirm your email:
{{ activate_url }}

{# Alternative action: code-based verification (if enabled) #}
{% if code %}
Or enter this verification code: {{ code }}
{% endif %}

{# Expiration notice #}
This link expires in 7 days.

{# Support contact #}
Questions? Reply to this email or visit {{ current_site.domain }}/support

{# Closing #}
Best regards,
The {{ current_site.name }} Team

{# Security footer #}
---
You received this email because someone signed up with this email address at {{ current_site.domain }}.
If you didn't sign up, you can safely ignore this email.
{% endautoescape %}
{% endblock content %}
```

**templates/account/email/email_confirmation_subject.txt**

```django
{% load i18n %}
{% blocktrans %}Confirm Your Email Address{% endblocktrans %}
```

**Note:** Subject is automatically prefixed by adapter (default: `[Site Name]`), resulting in:
```
[My Site] Confirm Your Email Address
```

### Creating HTML Versions

To send multipart emails (plain text + HTML), create `.html` versions alongside `.txt` files. The `render_mail()` method automatically detects and uses both versions.

**templates/account/email/email_confirmation_message.html**

```django
{% load account %}
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; }
        .button { background: #28a745; color: white; padding: 10px 20px;
                  text-decoration: none; border-radius: 5px; }
    </style>
</head>
<body>
    {% user_display user as user_display %}
    <h2>Hi {{ user_display }},</h2>
    <p>Thanks for signing up! Please confirm your email address:</p>
    <p><a href="{{ activate_url }}" class="button">Confirm Email</a></p>
    {% if code %}<p>Or enter code: <strong>{{ code }}</strong></p>{% endif %}
    <p>This link expires in 7 days.</p>
</body>
</html>
```

---

## Email Backend Configuration

### Console Backend (Development)

Prints emails to console instead of sending:

```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

**Output:**
```
Subject: [My Site] Confirm Your Email Address
From: noreply@example.com
To: user@example.com

Hello from My Site!
You're receiving this email because...
```

### File Backend (Development)

Save emails to files for inspection:

```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = BASE_DIR / 'tmp' / 'emails'
```

### SMTP Backend (Production)

```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'noreply@yourdomain.com'
SERVER_EMAIL = 'admin@yourdomain.com'
```

### SendGrid Configuration

```python
# settings.py
EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
SENDGRID_API_KEY = os.environ['SENDGRID_API_KEY']
DEFAULT_FROM_EMAIL = 'noreply@yourdomain.com'
```

```bash
pip install django-sendgrid-v5
```

### Mailgun Configuration

```python
# settings.py
EMAIL_BACKEND = 'anymail.backends.mailgun.EmailBackend'
ANYMAIL = {
    'MAILGUN_API_KEY': os.environ['MAILGUN_API_KEY'],
    'MAILGUN_SENDER_DOMAIN': 'mg.yourdomain.com',
}
DEFAULT_FROM_EMAIL = 'noreply@yourdomain.com'
```

```bash
pip install django-anymail[mailgun]
```

### Environment-Based Configuration

```python
# settings.py
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
    EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
    EMAIL_HOST_USER = os.environ['EMAIL_HOST_USER']
    EMAIL_HOST_PASSWORD = os.environ['EMAIL_HOST_PASSWORD']
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@example.com')
```

---

## Customizing via Adapter

Override adapter methods for advanced customization:

```python
# adapters.py
from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings

class MyAccountAdapter(DefaultAccountAdapter):

    def send_mail(self, template_prefix: str, email: str, context: dict) -> None:
        """Add custom context variables to all emails."""
        context['company_name'] = 'Acme Corp'
        context['support_email'] = settings.SUPPORT_EMAIL
        super().send_mail(template_prefix, email, context)

    def format_email_subject(self, subject) -> str:
        """Customize subject line formatting."""
        return f"Acme Corp - {subject}"

    def get_from_email(self):
        """Dynamically determine 'from' email address."""
        if settings.DEBUG:
            return 'dev@example.com'
        return 'noreply@acmecorp.com'

    def render_mail(self, template_prefix, email, context, headers=None):
        """Add custom headers to all emails."""
        if headers is None:
            headers = {}
        headers['X-App-Name'] = 'Acme Authentication'
        return super().render_mail(template_prefix, email, context, headers)
```

**Register adapter in settings:**

```python
# settings.py
ACCOUNT_ADAPTER = 'myapp.adapters.MyAccountAdapter'
```

### Conditional Email Sending

```python
class MyAccountAdapter(DefaultAccountAdapter):

    def should_send_confirmation_mail(self, request, email_address, signup) -> bool:
        """Don't send confirmation for internal email addresses."""
        if email_address.email.endswith('@acmecorp.com'):
            return False
        return True

    def send_password_reset_mail(self, user, email, context):
        """Block password reset for social-only users."""
        if not user.has_usable_password():
            return  # Don't send email
        super().send_password_reset_mail(user, email, context)
```

---

## Testing Emails Locally

### Console Backend Testing

```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

Run signup and check terminal output:

```bash
python manage.py runserver
# Visit http://localhost:8000/accounts/signup/
# Check terminal for email content
```

### Test Assertions

```python
# tests.py
from django.test import TestCase
from django.core import mail

class EmailTestCase(TestCase):

    def test_signup_email_sent(self):
        """Test that signup confirmation email is sent."""
        response = self.client.post('/accounts/signup/', {
            'email': 'test@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
        })

        # Check email was sent
        self.assertEqual(len(mail.outbox), 1)

        # Check email properties
        email = mail.outbox[0]
        self.assertEqual(email.to, ['test@example.com'])
        self.assertIn('Confirm Your Email', email.subject)
        self.assertIn('activate', email.body)

    def test_password_reset_email_content(self):
        """Test password reset email contains reset link."""
        user = User.objects.create_user('test', 'test@example.com', 'pass')

        response = self.client.post('/accounts/password/reset/', {
            'email': 'test@example.com',
        })

        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn('password/reset/key/', email.body)
```

---

## Best Practices

### 1. Always Provide Plain Text

Even if using HTML emails, always provide plain text versions:

```
templates/account/email/
├── email_confirmation_message.txt   # Required
└── email_confirmation_message.html  # Optional
```

### 2. Keep Subjects Short

Email subject lines should be under 50 characters for mobile compatibility.

### 3. Security Information in Notifications

Always include IP, user agent, and timestamp in security notifications by extending `base_notification.txt`:

```django
{% extends "account/email/base_notification.txt" %}
```

### 4. State Link Expiration

Clearly communicate when verification/reset links expire:

```django
This link expires in 7 days.
```

### 5. Verify Site Configuration

Before production, ensure Django Sites framework is configured correctly:

```python
python manage.py shell
>>> from django.contrib.sites.models import Site
>>> site = Site.objects.get_current()
>>> print(site.domain, site.name)
>>> # Update if needed:
>>> site.domain = 'yourdomain.com'
>>> site.name = 'Your Site Name'
>>> site.save()
```

### 6. Test Multiple Email Clients

Test emails in Gmail, Outlook, and Apple Mail before production deployment.
