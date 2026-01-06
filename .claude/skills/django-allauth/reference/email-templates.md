# Email Templates Guide

Comprehensive guide to django-allauth's email template system, covering all 40 built-in templates, customization strategies, and production best practices.

## Table of Contents

1. [Template Inventory](#template-inventory)
2. [Context Variables by Template](#context-variables-by-template)
3. [Creating Custom Templates](#creating-custom-templates)
4. [HTML vs Plain Text](#html-vs-plain-text)
5. [Email Backend Configuration](#email-backend-configuration)
6. [Customizing via Adapter](#customizing-via-adapter)
7. [Testing Emails Locally](#testing-emails-locally)

---

## Template Inventory

Django-allauth ships with 40 email templates (20 pairs of subject + message).

### Account Module Templates (28 files)

Located in: `allauth/templates/account/email/`

**Base Templates:**
- `base_message.txt` - Base template for all emails
- `base_notification.txt` - Base template for notification emails (security alerts)

**Email Verification:**
- `email_confirmation_subject.txt` / `email_confirmation_message.txt`
  - Purpose: Email verification for adding new email addresses
- `email_confirmation_signup_subject.txt` / `email_confirmation_signup_message.txt`
  - Purpose: Email verification during initial signup (extends email_confirmation)
- `email_confirm_subject.txt` / `email_confirm_message.txt`
  - Purpose: Legacy verification template (deprecated)

**Password Management:**
- `password_reset_subject.txt` / `password_reset_message.txt`
  - Purpose: Legacy password reset template (deprecated)
- `password_reset_key_subject.txt` / `password_reset_key_message.txt`
  - Purpose: Password reset with URL link
- `password_reset_code_subject.txt` / `password_reset_code_message.txt`
  - Purpose: Password reset with 6-8 digit code
- `password_set_subject.txt` / `password_set_message.txt`
  - Purpose: Password created for the first time
- `password_changed_subject.txt` / `password_changed_message.txt`
  - Purpose: Security notification when password changes

**Login:**
- `login_code_subject.txt` / `login_code_message.txt`
  - Purpose: Passwordless login code

**Email Management Notifications:**
- `email_changed_subject.txt` / `email_changed_message.txt`
  - Purpose: Security notification when email address changes
- `email_deleted_subject.txt` / `email_deleted_message.txt`
  - Purpose: Security notification when email address is removed

**Account Status:**
- `account_already_exists_subject.txt` / `account_already_exists_message.txt`
  - Purpose: Sent when signup attempted with existing email
- `unknown_account_subject.txt` / `unknown_account_message.txt`
  - Purpose: Sent for password reset on unlisted email (enumeration prevention)

### MFA Module Templates (8 files)

Located in: `allauth/templates/mfa/email/`

**TOTP (Authenticator App):**
- `totp_activated_subject.txt` / `totp_activated_message.txt`
  - Purpose: Security notification when TOTP is enabled
- `totp_deactivated_subject.txt` / `totp_deactivated_message.txt`
  - Purpose: Security notification when TOTP is disabled

**WebAuthn (Security Keys):**
- `webauthn_added_subject.txt` / `webauthn_added_message.txt`
  - Purpose: Security notification when security key is added
- `webauthn_removed_subject.txt` / `webauthn_removed_message.txt`
  - Purpose: Security notification when security key is removed

**Recovery Codes:**
- `recovery_codes_generated_subject.txt` / `recovery_codes_generated_message.txt`
  - Purpose: Notification when recovery codes are regenerated

### Social Account Module Templates (4 files)

Located in: `allauth/templates/socialaccount/email/`

- `account_connected_subject.txt` / `account_connected_message.txt`
  - Purpose: Security notification when social account is linked
- `account_disconnected_subject.txt` / `account_disconnected_message.txt`
  - Purpose: Security notification when social account is unlinked

---

## Context Variables by Template

All templates have access to these base context variables via `render_mail()`:

```python
{
    'request': request,           # HttpRequest object
    'email': email,               # Recipient email address
    'current_site': site,         # Site object (from Django Sites framework)
}
```

### Email Confirmation Templates

**Template:** `account/email/email_confirmation_message.txt`

```python
{
    'user': user,                 # User object
    'current_site': site,         # Site object
    'key': 'abc123...',           # Verification key (64 chars)
    'activate_url': 'https://...',  # Full verification URL
    'code': '123456',             # 6-digit code (if EMAIL_VERIFICATION_BY_CODE_ENABLED)
}
```

**Usage in template:**
```django
{% load account %}
{% user_display user as user_display %}

Hello {{ user_display }},

Please confirm your email address by clicking:
{{ activate_url }}

Or enter this code: {{ code }}
```

### Password Reset Templates

**Template:** `account/email/password_reset_key_message.txt`

```python
{
    'password_reset_url': 'https://...',  # Full reset URL
    'username': 'john_doe',                # Username (if available)
    'current_site': site,
}
```

**Template:** `account/email/password_reset_code_message.txt`

```python
{
    'code': '12345678',          # 6-8 digit code
    'current_site': site,
}
```

### Login Code Template

**Template:** `account/email/login_code_message.txt`

```python
{
    'code': '123456',            # 6-digit code
    'current_site': site,
}
```

### Notification Templates (Security Alerts)

All notification templates extend `base_notification.txt` and include:

```python
{
    'timestamp': datetime,       # When the action occurred
    'ip': '192.168.1.1',        # IP address of the request
    'user_agent': 'Mozilla/...',  # Browser user agent string
}
```

**Password Changed:**
```python
{
    # base notification context
}
```

**Email Changed:**
```python
{
    'from_email': 'old@example.com',
    'to_email': 'new@example.com',
    # + base notification context
}
```

**Social Account Connected:**
```python
{
    'provider': 'Google',        # Provider display name
    # + base notification context
}
```

### Account Already Exists Template

**Template:** `account/email/account_already_exists_message.txt`

```python
{
    'signup_url': 'https://...',          # Signup page URL
    'password_reset_url': 'https://...',  # Password reset URL
    'current_site': site,
}
```

---

## Creating Custom Templates

### Directory Structure

Create templates in your project's template directory:

```
your_project/
├── templates/
│   ├── account/
│   │   └── email/
│   │       ├── email_confirmation_subject.txt
│   │       ├── email_confirmation_message.txt
│   │       ├── email_confirmation_message.html  # HTML version
│   │       ├── password_reset_key_subject.txt
│   │       ├── password_reset_key_message.txt
│   │       └── password_reset_key_message.html
│   ├── mfa/
│   │   └── email/
│   │       ├── totp_activated_subject.txt
│   │       └── totp_activated_message.txt
│   └── socialaccount/
│       └── email/
│           ├── account_connected_subject.txt
│           └── account_connected_message.txt
```

### Overriding Default Templates

**1. Copy and Modify:**

```bash
# Copy default template to your project
cp venv/lib/python3.x/site-packages/allauth/templates/account/email/email_confirmation_message.txt \
   templates/account/email/email_confirmation_message.txt
```

**2. Customize the Template:**

```django
{% extends "account/email/base_message.txt" %}
{% load account %}
{% load i18n %}

{% block content %}
{% autoescape off %}
{% user_display user as user_display %}

Hi {{ user_display }},

Thanks for signing up at {{ current_site.name }}!

To activate your account, click here:
{{ activate_url }}

This link expires in 7 days.

Questions? Reply to this email.

Best regards,
The {{ current_site.name }} Team
{% endautoescape %}
{% endblock content %}
```

### Subject Line Customization

Subjects are automatically formatted with prefix:

```django
{# account/email/email_confirmation_subject.txt #}
{% load i18n %}
{% blocktrans %}Confirm Your Email Address{% endblocktrans %}
```

The adapter adds prefix automatically (default: `[site.name]`):

```python
# Result: "[My Site] Confirm Your Email Address"
```

### Template Extension Setting

Control HTML template file extension:

```python
# settings.py
ACCOUNT_TEMPLATE_EXTENSION = 'html'  # default
# ACCOUNT_TEMPLATE_EXTENSION = 'jinja2'
```

This affects which HTML templates are loaded when creating multipart emails.

---

## HTML vs Plain Text

### Default: Plain Text Only

Django-allauth ships with **only plain text templates**. By default, emails are sent as `text/plain`.

### Creating HTML Versions

To send multipart emails (plain text + HTML), create HTML versions of message templates:

**1. Create HTML Template:**

```django
{# templates/account/email/email_confirmation_message.html #}
{% load account %}
{% load i18n %}

<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; }
        .header { background: #007bff; color: white; padding: 20px; }
        .content { padding: 20px; }
        .button {
            background: #28a745;
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 5px;
            display: inline-block;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ current_site.name }}</h1>
    </div>
    <div class="content">
        {% user_display user as user_display %}
        <h2>Hi {{ user_display }},</h2>

        <p>Thanks for signing up! Please confirm your email address:</p>

        <p><a href="{{ activate_url }}" class="button">Confirm Email</a></p>

        <p>Or copy this link:<br>{{ activate_url }}</p>

        <p>This link expires in 7 days.</p>

        <hr>
        <p style="font-size: 12px; color: #666;">
            You received this email because you signed up at {{ current_site.name }}.
        </p>
    </div>
</body>
</html>
```

### MultiAlternatives Handling

The `render_mail()` method automatically handles multipart emails:

```python
# From adapter.py
def render_mail(self, template_prefix, email, context, headers=None):
    # Tries to load both .txt and .html versions
    html_ext = app_settings.TEMPLATE_EXTENSION  # 'html'

    for ext in [html_ext, "txt"]:
        try:
            template_name = f"{template_prefix}_message.{ext}"
            bodies[ext] = render_to_string(template_name, context).strip()
        except TemplateDoesNotExist:
            pass

    # If both exist, creates multipart email
    if "txt" in bodies:
        msg = EmailMultiAlternatives(subject, bodies["txt"], from_email, to)
        if html_ext in bodies:
            msg.attach_alternative(bodies[html_ext], "text/html")
```

**Result:** Recipients see HTML if their client supports it, plain text otherwise.

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
Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit
Subject: [My Site] Confirm Your Email Address
From: noreply@example.com
To: user@example.com

Hello from My Site!

You're receiving this email because user john_doe has given...
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

# Optional: Track opens/clicks
SENDGRID_TRACK_EMAIL_OPENS = True
SENDGRID_TRACK_CLICKS_HTML = True
SENDGRID_TRACK_CLICKS_PLAIN = True
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

Override adapter methods in your custom adapter:

```python
# adapters.py
from allauth.account.adapter import DefaultAccountAdapter
from django.conf import settings

class MyAccountAdapter(DefaultAccountAdapter):

    def send_mail(self, template_prefix: str, email: str, context: dict) -> None:
        """
        Override to add custom context or change behavior.
        """
        # Add custom context variables
        context['company_name'] = 'Acme Corp'
        context['support_email'] = settings.SUPPORT_EMAIL

        # Call parent implementation
        super().send_mail(template_prefix, email, context)

    def format_email_subject(self, subject) -> str:
        """
        Customize email subject line formatting.
        """
        # Custom prefix instead of [Site Name]
        return f"🔐 {subject} - Acme Corp"

    def get_from_email(self):
        """
        Dynamically determine 'from' email address.
        """
        # Use different sender based on environment
        if settings.DEBUG:
            return 'dev@example.com'
        return 'noreply@acmecorp.com'

    def render_mail(self, template_prefix, email, context, headers=None):
        """
        Override to add custom headers or modify email creation.
        """
        # Add custom headers
        if headers is None:
            headers = {}
        headers['X-App-Name'] = 'Acme Authentication'
        headers['X-Environment'] = settings.ENVIRONMENT

        # Call parent implementation
        return super().render_mail(template_prefix, email, context, headers)
```

### Preventing Emails Conditionally

```python
class MyAccountAdapter(DefaultAccountAdapter):

    def should_send_confirmation_mail(self, request, email_address, signup) -> bool:
        """
        Control whether confirmation email should be sent.
        """
        # Don't send confirmation for internal email addresses
        if email_address.email.endswith('@acmecorp.com'):
            return False

        return True

    def send_password_reset_mail(self, user, email, context):
        """
        Control whether password reset email should be sent.
        """
        # Block password reset for social-only users
        if not user.has_usable_password():
            return  # Don't send email

        super().send_password_reset_mail(user, email, context)
```

### Custom Email Sending Logic

```python
class MyAccountAdapter(DefaultAccountAdapter):

    def send_mail(self, template_prefix: str, email: str, context: dict) -> None:
        """
        Send via custom email service with tracking.
        """
        from myapp.email import EmailService

        # Build email using render_mail
        msg = self.render_mail(template_prefix, email, context)

        # Send via custom service
        EmailService.send(
            to=email,
            subject=msg.subject,
            body=msg.body,
            html=msg.alternatives[0][0] if msg.alternatives else None,
            tags=['django-allauth', template_prefix.split('/')[-1]],
        )
```

---

## Testing Emails Locally

### Console Backend Testing

```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

Run signup flow and check console output:

```bash
python manage.py runserver
# Visit http://localhost:8000/accounts/signup/
# Check terminal for email output
```

### File Backend Testing

Save emails to files for inspection:

```python
# settings.py (development only)
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = BASE_DIR / 'tmp' / 'emails'
```

Emails saved to `tmp/emails/` directory:

```bash
ls tmp/emails/
# 20240115-123045-123456789.log
cat tmp/emails/20240115-123045-123456789.log
```

### Template Preview View

Create a view to preview email templates:

```python
# views.py
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from allauth.account.adapter import get_adapter
from django.contrib.sites.shortcuts import get_current_site

@staff_member_required
def preview_email(request, template_name):
    """Preview email templates with sample data."""
    adapter = get_adapter(request)

    # Sample context
    context = {
        'user': request.user,
        'current_site': get_current_site(request),
        'activate_url': 'https://example.com/verify/abc123',
        'password_reset_url': 'https://example.com/reset/xyz789',
        'code': '123456',
        'key': 'abcdef123456',
    }

    # Render email
    template_prefix = f'account/email/{template_name}'
    msg = adapter.render_mail(template_prefix, request.user.email, context)

    # Display in browser
    html_body = None
    if msg.alternatives:
        html_body = msg.alternatives[0][0]

    return render(request, 'admin/email_preview.html', {
        'subject': msg.subject,
        'text_body': msg.body,
        'html_body': html_body,
    })

# urls.py
urlpatterns = [
    path('admin/preview-email/<str:template_name>/', preview_email),
]
```

### Test Assertions

Test that emails are sent correctly:

```python
# tests.py
from django.test import TestCase
from django.core import mail
from allauth.account.models import EmailAddress

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

    def test_notification_email_includes_security_info(self):
        """Test notification emails include IP and timestamp."""
        from allauth.account.adapter import get_adapter

        adapter = get_adapter(self.request)
        adapter.send_notification_mail(
            'account/email/password_changed',
            self.user
        )

        email = mail.outbox[0]
        self.assertIn('IP address:', email.body)
        self.assertIn('Browser:', email.body)
        self.assertIn('Date:', email.body)
```

---

## Best Practices

### 1. Always Provide Plain Text

Even if using HTML emails, always provide a plain text version:

```
templates/account/email/
├── email_confirmation_message.txt   # Required
└── email_confirmation_message.html  # Optional
```

### 2. Keep Subjects Short

Email subject lines should be under 50 characters for mobile compatibility.

### 3. Security Information in Notifications

Always include IP, user agent, and timestamp in security notification emails:

```django
{% extends "account/email/base_notification.txt" %}
```

### 4. Test Email Deliverability

Before production:
- Test with multiple email clients (Gmail, Outlook, Apple Mail)
- Check spam score using mail-tester.com
- Verify SPF/DKIM records

### 5. Link Expiration

Clearly state when verification/reset links expire:

```django
This link expires in {{ expiration_hours }} hours.
```

### 6. Unsubscribe Links

For notification emails, consider adding unsubscribe functionality:

```django
<p>
    Don't want these emails?
    <a href="{{ unsubscribe_url }}">Manage email preferences</a>
</p>
```

---

## Troubleshooting

### Emails Not Sending

**Check email backend:**
```python
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Body', 'from@example.com', ['to@example.com'])
```

**Check adapter configuration:**
```python
>>> from allauth.account.adapter import get_adapter
>>> adapter = get_adapter()
>>> adapter.get_from_email()
```

### Wrong Site Domain in Emails

Verify Django Sites framework configuration:

```python
python manage.py shell
>>> from django.contrib.sites.models import Site
>>> site = Site.objects.get_current()
>>> print(site.domain, site.name)
```

Update if incorrect:
```python
>>> site.domain = 'yourdomain.com'
>>> site.name = 'Your Site Name'
>>> site.save()
```

### HTML Templates Not Loading

1. Check `ACCOUNT_TEMPLATE_EXTENSION` setting
2. Verify HTML template file exists
3. Check template syntax is valid

### Custom Context Not Appearing

Override `send_mail()` in adapter to add context:

```python
def send_mail(self, template_prefix, email, context):
    context['custom_var'] = 'value'
    super().send_mail(template_prefix, email, context)
```
