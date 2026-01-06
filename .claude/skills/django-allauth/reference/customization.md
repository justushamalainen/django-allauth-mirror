# Django-AllAuth Customization Guide

Complete reference for customizing django-allauth behavior through adapters, signals, and forms.

## Table of Contents

1. [Adapter Pattern Overview](#adapter-pattern-overview)
2. [AccountAdapter Methods](#accountadapter-methods)
3. [SocialAccountAdapter Methods](#socialaccountadapter-methods)
4. [Signals Reference](#signals-reference)
5. [Form Customization](#form-customization)
6. [Real-World Examples](#real-world-examples)

---

## Adapter Pattern Overview

### What Are Adapters?

Adapters are the primary customization mechanism in django-allauth. They allow you to override default behavior without modifying the package code.

**Two main adapters:**
- `DefaultAccountAdapter` - Controls account authentication, registration, email
- `DefaultSocialAccountAdapter` - Controls social authentication behavior

### Creating a Custom Adapter

**Step 1: Create adapter class**

```python
# myapp/adapters.py
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings

class MyAccountAdapter(DefaultAccountAdapter):
    """Custom account adapter"""

    def get_login_redirect_url(self, request):
        """Redirect based on user type"""
        if request.user.is_staff:
            return '/admin/'
        return '/dashboard/'

class MySocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom social account adapter"""

    def pre_social_login(self, request, sociallogin):
        """Connect to existing user by email"""
        if sociallogin.is_existing:
            return

        # Try to connect by email
        try:
            user = User.objects.get(email=sociallogin.email_addresses[0].email)
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            pass
```

**Step 2: Register in settings**

```python
# settings.py
ACCOUNT_ADAPTER = 'myapp.adapters.MyAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'myapp.adapters.MySocialAccountAdapter'
```

---

## AccountAdapter Methods

### Redirect Methods (Most Commonly Overridden)

These control where users go after various actions.

#### `get_login_redirect_url(request)`

**When Called:** After successful login

**Default Behavior:** Returns `settings.LOGIN_REDIRECT_URL`

**Common Use Cases:**
- Role-based redirects
- Redirect to requested page
- First-time user onboarding

```python
def get_login_redirect_url(self, request):
    """Custom login redirect"""
    user = request.user

    # First-time users
    if not user.profile.onboarding_complete:
        return '/onboarding/'

    # Role-based
    if user.is_staff:
        return '/admin/'
    elif user.is_premium:
        return '/premium-dashboard/'

    return '/dashboard/'
```

#### `get_signup_redirect_url(request)`

**When Called:** After successful signup (before email verification)

**Default Behavior:** Returns `settings.ACCOUNT_SIGNUP_REDIRECT_URL` or login redirect

```python
def get_signup_redirect_url(self, request):
    """Redirect new users to onboarding"""
    return '/welcome/'
```

#### `get_logout_redirect_url(request)`

**When Called:** After logout

**Default Behavior:** Returns `settings.ACCOUNT_LOGOUT_REDIRECT_URL`

```python
def get_logout_redirect_url(self, request):
    """Keep users on current page after logout"""
    return request.META.get('HTTP_REFERER', '/')
```

#### `get_email_verification_redirect_url(email_address)`

**When Called:** After user clicks email verification link

**Default Behavior:** Returns login redirect if authenticated, else email confirmation page

```python
def get_email_verification_redirect_url(self, email_address):
    """Redirect to specific page after email verification"""
    if self.request.user.is_authenticated:
        return '/settings/email/'
    return '/login/?verified=true'
```

#### `get_password_change_redirect_url(request)`

**When Called:** After successful password change

**Default Behavior:** Returns to password change page

```python
def get_password_change_redirect_url(self, request):
    """Show success message on dashboard"""
    return '/dashboard/?password_changed=true'
```

---

### Email Methods

Control email sending, formatting, and content.

#### `send_mail(template_prefix, email, context)`

**When Called:** Whenever allauth sends an email

**Parameters:**
- `template_prefix`: e.g., `"account/email/email_confirmation"`
- `email`: Recipient email address
- `context`: Template context dict

**Common Use Cases:**
- Use custom email service (SendGrid, AWS SES)
- Add tracking pixels
- Queue emails for batch sending

```python
def send_mail(self, template_prefix, email, context):
    """Send email via SendGrid"""
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail

    msg = self.render_mail(template_prefix, email, context)

    message = Mail(
        from_email=self.get_from_email(),
        to_emails=email,
        subject=msg.subject,
        html_content=msg.alternatives[0][0] if msg.alternatives else msg.body
    )

    sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
    sg.send(message)
```

#### `render_mail(template_prefix, email, context, headers=None)`

**Returns:** `EmailMessage` or `EmailMultiAlternatives` object

**Override to:** Customize email content before sending

```python
def render_mail(self, template_prefix, email, context, headers=None):
    """Add custom headers and tracking"""
    msg = super().render_mail(template_prefix, email, context, headers)

    # Add custom header
    msg.extra_headers['X-Campaign-ID'] = 'auth-flow'

    # Add unsubscribe link
    context['unsubscribe_url'] = f'/unsubscribe/{email}/'

    return msg
```

#### `format_email_subject(subject)`

**Returns:** Formatted subject string

**Default Behavior:** Prepends `[Site Name]` prefix

```python
def format_email_subject(self, subject):
    """Custom subject prefix"""
    return f"🔐 MyApp - {subject}"
```

#### `get_from_email()`

**Returns:** From email address

**Default Behavior:** Returns `settings.DEFAULT_FROM_EMAIL`

```python
def get_from_email(self):
    """Use environment-specific from address"""
    if settings.DEBUG:
        return 'dev@example.com'
    return 'noreply@example.com'
```

#### `should_send_confirmation_mail(request, email_address, signup)`

**Returns:** Boolean - whether to send verification email

```python
def should_send_confirmation_mail(self, request, email_address, signup):
    """Skip verification for trusted domains"""
    if email_address.email.endswith('@mycompany.com'):
        return False
    return True
```

---

### User Creation Methods

Control how user accounts are created and populated.

#### `new_user(request)`

**Returns:** New unsaved User instance

**When Called:** At start of signup process

```python
def new_user(self, request):
    """Create user with custom defaults"""
    user = super().new_user(request)
    user.is_active = True  # Auto-activate
    user.language = request.LANGUAGE_CODE
    return user
```

#### `save_user(request, user, form, commit=True)`

**Returns:** Saved User instance

**When Called:** During signup after form validation

**Common Use Cases:**
- Create related models (Profile, Settings)
- Set additional user fields
- Send welcome notifications

```python
def save_user(self, request, user, form, commit=True):
    """Create user profile on signup"""
    user = super().save_user(request, user, form, commit=False)

    # Add custom field
    user.referral_code = form.cleaned_data.get('referral_code', '')

    if commit:
        user.save()

        # Create related profile
        from myapp.models import Profile
        Profile.objects.create(
            user=user,
            timezone=request.session.get('timezone', 'UTC'),
            source=request.GET.get('utm_source', 'direct')
        )

    return user
```

#### `populate_username(request, user)`

**When Called:** To generate username if not provided

**Default Behavior:** Generates from first name, last name, email

```python
def populate_username(self, request, user):
    """Custom username generation"""
    from allauth.account.utils import user_username, user_email

    email = user_email(user)
    if email:
        # Use email local part as base
        base = email.split('@')[0]
        username = self.generate_unique_username([base])
        user_username(user, username)
    else:
        super().populate_username(request, user)
```

---

### Validation Methods

Implement custom validation rules for usernames, emails, and passwords.

#### `clean_username(username, shallow=False)`

**Returns:** Validated username

**Raises:** `ValidationError` if invalid

**Parameters:**
- `shallow`: If True, skip database uniqueness check (for generation)

```python
def clean_username(self, username, shallow=False):
    """Additional username restrictions"""
    username = super().clean_username(username, shallow)

    # Block specific patterns
    blocked_patterns = ['admin', 'root', 'moderator']
    if any(pattern in username.lower() for pattern in blocked_patterns):
        raise ValidationError('This username is not allowed.')

    # Length requirements
    if len(username) < 4:
        raise ValidationError('Username must be at least 4 characters.')

    return username.lower()  # Force lowercase
```

#### `clean_email(email)`

**Returns:** Validated email address

**Common Use Cases:**
- Domain whitelisting/blacklisting
- Disposable email blocking
- Corporate email requirements

```python
def clean_email(self, email):
    """Validate email domain"""
    email = super().clean_email(email)

    # Whitelist corporate domains
    allowed_domains = ['mycompany.com', 'partner.com']
    domain = email.split('@')[1]

    if domain not in allowed_domains:
        raise ValidationError(
            f'Please use a company email address. '
            f'Allowed domains: {", ".join(allowed_domains)}'
        )

    return email
```

#### `clean_password(password, user=None)`

**Returns:** Validated password

**Default Behavior:** Runs Django's password validators

```python
def clean_password(self, password, user=None):
    """Additional password requirements"""
    password = super().clean_password(password, user)

    # Custom complexity rules
    if not any(c.isdigit() for c in password):
        raise ValidationError('Password must contain at least one number.')

    if not any(c in '!@#$%^&*' for c in password):
        raise ValidationError('Password must contain a special character.')

    return password
```

#### `validate_unique_email(email)`

**Returns:** Email if unique

**Raises:** `ValidationError` if email already exists

```python
def validate_unique_email(self, email):
    """Allow multiple accounts per email for testing"""
    if settings.DEBUG:
        return email  # Skip in development
    return super().validate_unique_email(email)
```

---

### Authentication Lifecycle Methods

Hook into the authentication process.

#### `pre_login(request, user, *, email_verification, signal_kwargs, email, signup, redirect_url)`

**When Called:** Before login is processed, after credentials verified

**Returns:** `None` or `HttpResponse` to abort login

**Common Use Cases:**
- Two-factor authentication trigger
- Account status checks
- Logging/analytics

```python
def pre_login(self, request, user, **kwargs):
    """Check account status before login"""
    # Check subscription
    if hasattr(user, 'subscription') and user.subscription.is_expired():
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect('/subscription/expired/')

    # Log login attempt
    from myapp.models import LoginLog
    LoginLog.objects.create(
        user=user,
        ip_address=self.get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )

    return super().pre_login(request, user, **kwargs)
```

#### `post_login(request, user, *, email_verification, signal_kwargs, email, signup, redirect_url)`

**When Called:** After successful login

**Returns:** `HttpResponse` (usually redirect)

**Note:** This is where `user_logged_in` signal is sent

```python
def post_login(self, request, user, **kwargs):
    """Update last login tracking"""
    from django.utils import timezone

    user.last_login_ip = self.get_client_ip(request)
    user.last_login = timezone.now()
    user.save(update_fields=['last_login_ip', 'last_login'])

    return super().post_login(request, user, **kwargs)
```

#### `authenticate(request, **credentials)`

**Returns:** User instance or None

**When Called:** During login form submission

**Note:** Includes rate limiting by default

```python
def authenticate(self, request, **credentials):
    """Custom authentication with logging"""
    user = super().authenticate(request, **credentials)

    if not user:
        # Log failed attempt
        from myapp.models import FailedLogin
        FailedLogin.objects.create(
            username=credentials.get('username', ''),
            ip_address=self.get_client_ip(request)
        )

    return user
```

#### `authentication_failed(request, **credentials)`

**When Called:** After failed authentication attempt

```python
def authentication_failed(self, request, **credentials):
    """Notify on suspicious activity"""
    ip = self.get_client_ip(request)
    failed_count = cache.get(f'failed_login_{ip}', 0) + 1
    cache.set(f'failed_login_{ip}', failed_count, timeout=3600)

    if failed_count >= 10:
        # Send alert email
        send_alert(f'Multiple failed logins from {ip}')
```

---

### Additional Utility Methods

#### `is_open_for_signup(request)`

**Returns:** Boolean - whether signup is allowed

```python
def is_open_for_signup(self, request):
    """Restrict signup to beta users"""
    beta_code = request.GET.get('beta')
    if beta_code == settings.BETA_CODE:
        return True
    return False
```

#### `is_safe_url(url)`

**Returns:** Boolean - whether redirect URL is safe

**Default Behavior:** Checks against `ALLOWED_HOSTS`

```python
def is_safe_url(self, url):
    """Allow additional trusted domains"""
    if url.startswith('https://docs.example.com'):
        return True
    return super().is_safe_url(url)
```

#### `add_message(request, level, message_template, message_context, extra_tags, message)`

**Displays a message to the user**

```python
def add_message(self, request, level, message_template=None,
                message_context=None, extra_tags='', message=None):
    """Customize messages"""
    # Override specific messages
    if message_template == 'account/messages/logged_in.txt':
        message = f"Welcome back, {request.user.first_name}!"

    super().add_message(request, level, message_template,
                       message_context, extra_tags, message)
```

---

## SocialAccountAdapter Methods

### `pre_social_login(request, sociallogin)`

**CRITICAL METHOD** - Main intervention point for social authentication

**When Called:** After OAuth flow completes, before account created/connected

**Common Use Cases:**
- Connect to existing user by email
- Enforce email verification
- Block certain providers
- Custom signup flow

```python
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.shortcuts import redirect

class MySocialAccountAdapter(DefaultSocialAccountAdapter):

    def pre_social_login(self, request, sociallogin):
        """Auto-connect social login to existing user"""

        # If already connected, do nothing
        if sociallogin.is_existing:
            return

        # If user is logged in, connect to that account
        if request.user.is_authenticated:
            sociallogin.connect(request, request.user)
            return

        # Try to find existing user by verified email
        if sociallogin.email_addresses:
            email = sociallogin.email_addresses[0].email
            try:
                user = User.objects.get(email__iexact=email)
                # Connect this social account to the existing user
                sociallogin.connect(request, user)
            except User.DoesNotExist:
                pass
```

### `populate_user(request, sociallogin, data)`

**Returns:** User instance with populated fields

**When Called:** During signup to extract data from provider

**Parameters:**
- `data`: Dict from provider (name, email, etc.)

```python
def populate_user(self, request, sociallogin, data):
    """Extract custom fields from social provider"""
    user = super().populate_user(request, sociallogin, data)

    # Extract provider-specific data
    if sociallogin.account.provider == 'google':
        user.timezone = data.get('locale', 'UTC')
        user.avatar_url = data.get('picture', '')

    elif sociallogin.account.provider == 'github':
        user.website = data.get('blog', '')
        user.bio = data.get('bio', '')

    return user
```

### `is_auto_signup_allowed(request, sociallogin)`

**Returns:** Boolean - whether to auto-create account

**Default Behavior:** Returns `settings.SOCIALACCOUNT_AUTO_SIGNUP`

**Common Use Cases:**
- Require email verification first
- Show signup form for additional data
- Domain-based access control

```python
def is_auto_signup_allowed(self, request, sociallogin):
    """Only auto-signup for company emails"""
    if sociallogin.email_addresses:
        email = sociallogin.email_addresses[0].email
        if email.endswith('@mycompany.com'):
            return True

    # Require signup form for external users
    return False
```

### `on_authentication_error(request, provider, error, exception, extra_context)`

**When Called:** When OAuth flow fails

**Common Use Cases:**
- Log errors
- Show helpful error messages
- Redirect to support

```python
def on_authentication_error(self, request, provider, error=None,
                            exception=None, extra_context=None):
    """Handle authentication errors"""
    import logging
    logger = logging.getLogger(__name__)

    logger.error(
        f'Social auth error: provider={provider.id}, '
        f'error={error}, exception={exception}'
    )

    # Redirect to error page with helpful message
    from allauth.exceptions import ImmediateHttpResponse
    from django.shortcuts import redirect

    raise ImmediateHttpResponse(
        redirect(f'/auth/error/?provider={provider.id}')
    )
```

### `new_user(request, sociallogin)`

**Returns:** New User instance

```python
def new_user(self, request, sociallogin):
    """Create user with social-specific defaults"""
    user = super().new_user(request, sociallogin)
    user.source = f'social_{sociallogin.account.provider}'
    return user
```

### `save_user(request, sociallogin, form=None)`

**Returns:** Saved User instance

**Note:** `form` is None during auto-signup

```python
def save_user(self, request, sociallogin, form=None):
    """Create user with social account data"""
    user = super().save_user(request, sociallogin, form)

    # Store provider avatar
    if sociallogin.account.provider == 'google':
        avatar_url = sociallogin.account.extra_data.get('picture')
        if avatar_url:
            from myapp.utils import download_avatar
            download_avatar(user, avatar_url)

    return user
```

---

## Signals Reference

Django-allauth emits signals at key points in the authentication flow.

### Account Signals

#### `user_signed_up`

**When:** User completes signup (before email verification)

**Arguments:**
- `sender`: User model class
- `request`: HttpRequest
- `user`: User instance

```python
from allauth.account.signals import user_signed_up
from django.dispatch import receiver

@receiver(user_signed_up)
def create_user_profile(sender, request, user, **kwargs):
    """Create profile for new users"""
    from myapp.models import Profile

    Profile.objects.create(
        user=user,
        referral_source=request.session.get('referral_source', 'direct'),
        signup_ip=request.META.get('REMOTE_ADDR')
    )
```

#### `user_logged_in`

**When:** User successfully logs in

**Arguments:**
- `sender`: User model class
- `request`: HttpRequest
- `response`: HttpResponse that will be returned
- `user`: User instance

```python
from allauth.account.signals import user_logged_in

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Track login events"""
    from myapp.models import LoginEvent

    LoginEvent.objects.create(
        user=user,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT')
    )
```

#### `email_confirmed`

**When:** User confirms email address

**Arguments:**
- `sender`: EmailAddress model class
- `request`: HttpRequest
- `email_address`: EmailAddress instance

```python
from allauth.account.signals import email_confirmed

@receiver(email_confirmed)
def activate_premium_trial(sender, request, email_address, **kwargs):
    """Start trial when email confirmed"""
    user = email_address.user

    if not hasattr(user, 'subscription'):
        from myapp.models import Subscription
        Subscription.objects.create(
            user=user,
            plan='trial',
            trial_days=14
        )
```

#### `password_changed`

**When:** User changes password

**Arguments:**
- `sender`: User model class
- `request`: HttpRequest
- `user`: User instance

```python
from allauth.account.signals import password_changed

@receiver(password_changed)
def notify_password_change(sender, request, user, **kwargs):
    """Send security notification"""
    from django.core.mail import send_mail

    send_mail(
        subject='Password Changed',
        message=f'Your password was changed from IP {request.META.get("REMOTE_ADDR")}',
        from_email='security@example.com',
        recipient_list=[user.email]
    )
```

#### `password_set`

**When:** Password set for user (e.g., after social login)

**Arguments:**
- `sender`: User model class
- `request`: HttpRequest
- `user`: User instance

```python
from allauth.account.signals import password_set

@receiver(password_set)
def enable_full_access(sender, request, user, **kwargs):
    """Grant additional permissions after password set"""
    user.can_download = True
    user.save()
```

#### `password_reset`

**When:** User resets password via email link

**Arguments:**
- `sender`: User model class
- `request`: HttpRequest
- `user`: User instance

```python
from allauth.account.signals import password_reset

@receiver(password_reset)
def clear_sessions_on_reset(sender, request, user, **kwargs):
    """Log out all sessions after password reset"""
    from django.contrib.sessions.models import Session

    # Delete all sessions for this user
    for session in Session.objects.all():
        data = session.get_decoded()
        if data.get('_auth_user_id') == str(user.id):
            session.delete()
```

### Social Account Signals

#### `pre_social_login`

**When:** Before social login processed (after OAuth flow)

**Arguments:**
- `sender`: SocialLogin class
- `request`: HttpRequest
- `sociallogin`: SocialLogin instance

```python
from allauth.socialaccount.signals import pre_social_login

@receiver(pre_social_login)
def link_to_local_user(sender, request, sociallogin, **kwargs):
    """Connect social account to existing user by email"""
    if sociallogin.is_existing:
        return

    try:
        email = sociallogin.email_addresses[0].email
        user = User.objects.get(email__iexact=email)
        sociallogin.connect(request, user)
    except (IndexError, User.DoesNotExist):
        pass
```

#### `social_account_added`

**When:** Social account connected to user

**Arguments:**
- `sender`: SocialAccount model class
- `request`: HttpRequest
- `sociallogin`: SocialLogin instance

```python
from allauth.socialaccount.signals import social_account_added

@receiver(social_account_added)
def notify_account_connected(sender, request, sociallogin, **kwargs):
    """Send confirmation email"""
    user = sociallogin.user
    provider_name = sociallogin.account.get_provider().name

    send_mail(
        subject=f'{provider_name} Account Connected',
        message=f'You connected your {provider_name} account.',
        from_email='noreply@example.com',
        recipient_list=[user.email]
    )
```

#### `social_account_updated`

**When:** Existing social account refreshed (token/data updated)

**Arguments:**
- `sender`: SocialAccount model class
- `request`: HttpRequest
- `sociallogin`: SocialLogin instance

```python
from allauth.socialaccount.signals import social_account_updated

@receiver(social_account_updated)
def sync_social_data(sender, request, sociallogin, **kwargs):
    """Update user data from provider"""
    user = sociallogin.user
    extra_data = sociallogin.account.extra_data

    # Update avatar if changed
    new_avatar = extra_data.get('picture')
    if new_avatar and user.avatar_url != new_avatar:
        user.avatar_url = new_avatar
        user.save()
```

#### `social_account_removed`

**When:** Social account disconnected from user

**Arguments:**
- `sender`: SocialAccount model class
- `request`: HttpRequest
- `socialaccount`: SocialAccount instance

```python
from allauth.socialaccount.signals import social_account_removed

@receiver(social_account_removed)
def audit_disconnection(sender, request, socialaccount, **kwargs):
    """Log account disconnection"""
    from myapp.models import AuditLog

    AuditLog.objects.create(
        user=socialaccount.user,
        action='social_disconnect',
        details=f'Disconnected {socialaccount.provider}'
    )
```

---

## Form Customization

### Available Forms

Django-allauth provides these customizable forms:

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

### Override Forms via Settings

```python
# settings.py
ACCOUNT_FORMS = {
    'signup': 'myapp.forms.CustomSignupForm',
    'login': 'myapp.forms.CustomLoginForm',
}
```

### Adding Custom Fields to Signup

**Step 1: Create custom form**

```python
# myapp/forms.py
from allauth.account.forms import SignupForm
from django import forms

class CustomSignupForm(SignupForm):
    """Signup form with additional fields"""

    first_name = forms.CharField(
        max_length=30,
        label='First Name',
        required=True
    )

    last_name = forms.CharField(
        max_length=30,
        label='Last Name',
        required=True
    )

    terms_accepted = forms.BooleanField(
        required=True,
        label='I accept the Terms of Service'
    )

    referral_code = forms.CharField(
        max_length=20,
        required=False,
        label='Referral Code (optional)'
    )

    def save(self, request):
        """Save additional fields"""
        user = super().save(request)

        # These are automatically saved by adapter.save_user()
        # if you need to save to related models, do it here

        if self.cleaned_data.get('referral_code'):
            from myapp.models import Referral
            Referral.objects.create(
                user=user,
                code=self.cleaned_data['referral_code']
            )

        return user
```

**Step 2: Update adapter to handle fields**

```python
# myapp/adapters.py
from allauth.account.adapter import DefaultAccountAdapter

class MyAccountAdapter(DefaultAccountAdapter):

    def save_user(self, request, user, form, commit=True):
        """Save form data to user"""
        user = super().save_user(request, user, form, commit=False)

        # Get custom fields from form
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

---

## Real-World Examples

### Example 1: Role-Based Redirects

**Scenario:** Redirect users to different dashboards based on their role.

```python
# myapp/adapters.py
from allauth.account.adapter import DefaultAccountAdapter

class RoleBasedAdapter(DefaultAccountAdapter):

    def get_login_redirect_url(self, request):
        """Redirect based on user role"""
        user = request.user

        if user.is_superuser:
            return '/admin/'

        # Check custom role field
        if hasattr(user, 'role'):
            if user.role == 'teacher':
                return '/teacher/dashboard/'
            elif user.role == 'student':
                return '/student/dashboard/'
            elif user.role == 'parent':
                return '/parent/dashboard/'

        # Default fallback
        return '/dashboard/'
```

### Example 2: Email Domain Restriction

**Scenario:** Only allow signups from company email addresses.

```python
# myapp/adapters.py
from allauth.account.adapter import DefaultAccountAdapter
from django.core.exceptions import ValidationError

class CorporateAdapter(DefaultAccountAdapter):

    def clean_email(self, email):
        """Only allow company emails"""
        email = super().clean_email(email)

        allowed_domains = [
            'company.com',
            'partner.com',
            'subsidiary.com'
        ]

        domain = email.split('@')[1].lower()

        if domain not in allowed_domains:
            raise ValidationError(
                f'Please use your company email. '
                f'Allowed domains: {", ".join(allowed_domains)}'
            )

        return email
```

### Example 3: Profile Creation on Signup

**Scenario:** Automatically create user profile with additional data.

```python
# myapp/adapters.py
from allauth.account.adapter import DefaultAccountAdapter

class ProfileCreatingAdapter(DefaultAccountAdapter):

    def save_user(self, request, user, form, commit=True):
        """Create profile when user signs up"""
        user = super().save_user(request, user, form, commit=False)

        if commit:
            user.save()

            # Create related profile
            from myapp.models import UserProfile
            UserProfile.objects.create(
                user=user,
                timezone=request.session.get('detected_timezone', 'UTC'),
                language=request.LANGUAGE_CODE,
                referral_source=request.GET.get('ref', 'direct'),
                signup_ip=self.get_client_ip(request)
            )

        return user
```

### Example 4: Social Account Auto-Connect

**Scenario:** Automatically connect social logins to existing accounts by email.

```python
# myapp/adapters.py
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()

class AutoConnectAdapter(DefaultSocialAccountAdapter):

    def pre_social_login(self, request, sociallogin):
        """Auto-connect social account to existing user"""

        # Skip if already linked
        if sociallogin.is_existing:
            return

        # Skip if no email
        if not sociallogin.email_addresses:
            return

        email = sociallogin.email_addresses[0].email

        # Find existing user by email
        try:
            user = User.objects.get(email__iexact=email)

            # Connect this social account to the user
            sociallogin.connect(request, user)

            # Log the connection
            import logging
            logger = logging.getLogger(__name__)
            logger.info(
                f'Auto-connected {sociallogin.account.provider} '
                f'account to user {user.id}'
            )

        except User.DoesNotExist:
            # No existing user, let signup proceed
            pass
```

### Example 5: Custom Email Templates

**Scenario:** Send emails using a custom template engine.

```python
# myapp/adapters.py
from allauth.account.adapter import DefaultAccountAdapter

class CustomEmailAdapter(DefaultAccountAdapter):

    def send_mail(self, template_prefix, email, context):
        """Send email via custom service"""
        from myapp.email import EmailService

        # Map template to email type
        email_types = {
            'account/email/email_confirmation': 'email_verification',
            'account/email/password_reset_key': 'password_reset',
            'account/email/email_confirmation_signup': 'welcome',
        }

        email_type = email_types.get(template_prefix, 'notification')

        # Send via custom service
        EmailService.send(
            to=email,
            template=email_type,
            context=context
        )
```

### Example 6: Audit Logging

**Scenario:** Log all authentication events for security auditing.

```python
# myapp/signals.py
from allauth.account.signals import (
    user_logged_in, user_signed_up, password_changed
)
from allauth.socialaccount.signals import social_account_added
from django.dispatch import receiver
from myapp.models import AuditLog

@receiver(user_logged_in)
def log_login(sender, request, user, **kwargs):
    AuditLog.objects.create(
        user=user,
        action='login',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT')
    )

@receiver(user_signed_up)
def log_signup(sender, request, user, **kwargs):
    AuditLog.objects.create(
        user=user,
        action='signup',
        ip_address=request.META.get('REMOTE_ADDR')
    )

@receiver(password_changed)
def log_password_change(sender, request, user, **kwargs):
    AuditLog.objects.create(
        user=user,
        action='password_change',
        ip_address=request.META.get('REMOTE_ADDR')
    )

@receiver(social_account_added)
def log_social_connect(sender, request, sociallogin, **kwargs):
    AuditLog.objects.create(
        user=sociallogin.user,
        action='social_connect',
        details=f'Provider: {sociallogin.account.provider}'
    )
```

---

## Summary

This guide covers the main customization points in django-allauth:

**Adapters:**
- AccountAdapter: 30+ overridable methods for account behavior
- SocialAccountAdapter: 10+ methods for social authentication

**Signals:**
- 11 account signals for lifecycle events
- 4 social account signals for OAuth events

**Forms:**
- 8 customizable forms via `ACCOUNT_FORMS` setting

**Key Patterns:**
1. Override adapter methods for business logic
2. Use signals for side effects (logging, notifications)
3. Customize forms for additional user input
4. Combine all three for complex requirements

For more examples, see:
- `/reference/setup-guide.md` - Initial configuration
- `/reference/social-providers.md` - Provider-specific examples
- `/reference/security.md` - Security best practices
