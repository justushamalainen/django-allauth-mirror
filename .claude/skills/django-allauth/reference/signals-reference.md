# Signals Reference

Django-allauth emits signals at key points in the authentication lifecycle, allowing you to hook into user actions like login, signup, email verification, and social account connections.

## Account Signals

### user_logged_in

**When fired:** After a user successfully logs in.

**Arguments:**
- `sender`: The class of the User model
- `request`: The HTTP request object
- `user`: The User instance that logged in

**Example:**
```python
from allauth.account.signals import user_logged_in
from django.dispatch import receiver

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Track user login for analytics."""
    print(f"User {user.username} logged in from {request.META.get('REMOTE_ADDR')}")
    # Update last_login_ip, send to analytics, etc.
```

### user_logged_out

**When fired:** After a user logs out.

**Arguments:**
- `sender`: The class of the User model
- `request`: The HTTP request object
- `user`: The User instance that logged out

**Example:**
```python
from allauth.account.signals import user_logged_out
from django.dispatch import receiver

@receiver(user_logged_out)
def handle_logout(sender, request, user, **kwargs):
    """Clean up user session data."""
    print(f"User {user.username} logged out")
    # Clear caches, log audit trail, etc.
```

### user_signed_up

**When fired:** After a new user signs up, before login (unless email verification is required).

**Arguments:**
- `sender`: The class of the User model
- `request`: The HTTP request object
- `user`: The newly created User instance

**Example:**
```python
from allauth.account.signals import user_signed_up
from django.dispatch import receiver

@receiver(user_signed_up)
def create_user_profile(sender, request, user, **kwargs):
    """Create a profile when user signs up."""
    from .models import Profile
    Profile.objects.create(
        user=user,
        signup_ip=request.META.get('REMOTE_ADDR'),
        referrer=request.META.get('HTTP_REFERER')
    )
```

### password_set

**When fired:** When a user sets their password (e.g., after signing up via social auth).

**Arguments:**
- `sender`: The class of the User model
- `request`: The HTTP request object
- `user`: The User instance

**Example:**
```python
from allauth.account.signals import password_set
from django.dispatch import receiver

@receiver(password_set)
def notify_password_set(sender, request, user, **kwargs):
    """Notify user when password is set."""
    from django.core.mail import send_mail
    send_mail(
        'Password Set Successfully',
        f'Hi {user.username}, your password has been set.',
        'noreply@example.com',
        [user.email]
    )
```

### password_changed

**When fired:** When a user changes their password.

**Arguments:**
- `sender`: The class of the User model
- `request`: The HTTP request object
- `user`: The User instance

**Example:**
```python
from allauth.account.signals import password_changed
from django.dispatch import receiver

@receiver(password_changed)
def log_password_change(sender, request, user, **kwargs):
    """Log password changes for security auditing."""
    import logging
    logger = logging.getLogger('security')
    logger.info(f'Password changed for user {user.id} from IP {request.META.get("REMOTE_ADDR")}')
```

### password_reset

**When fired:** After a user successfully resets their password.

**Arguments:**
- `sender`: The class of the User model
- `request`: The HTTP request object
- `user`: The User instance

**Example:**
```python
from allauth.account.signals import password_reset
from django.dispatch import receiver

@receiver(password_reset)
def handle_password_reset(sender, request, user, **kwargs):
    """Notify security team of password reset."""
    # Send notification, invalidate sessions, etc.
    print(f"Password reset for {user.email}")
```

### email_confirmed

**When fired:** After a user confirms their email address.

**Arguments:**
- `sender`: The EmailAddress model class
- `request`: The HTTP request object
- `email_address`: The EmailAddress instance that was confirmed

**Example:**
```python
from allauth.account.signals import email_confirmed
from django.dispatch import receiver

@receiver(email_confirmed)
def welcome_user(sender, request, email_address, **kwargs):
    """Send welcome email after email confirmation."""
    user = email_address.user
    from django.core.mail import send_mail
    send_mail(
        'Welcome to Our Platform!',
        f'Hi {user.username}, thanks for confirming your email!',
        'welcome@example.com',
        [email_address.email]
    )
```

### email_confirmation_sent

**When fired:** After an email confirmation is sent.

**Arguments:**
- `sender`: The EmailConfirmation model class
- `request`: The HTTP request object
- `confirmation`: The EmailConfirmation instance
- `signup`: Boolean indicating if this is for a new signup

**Example:**
```python
from allauth.account.signals import email_confirmation_sent
from django.dispatch import receiver

@receiver(email_confirmation_sent)
def track_confirmation_sent(sender, request, confirmation, signup, **kwargs):
    """Track email confirmation sends."""
    action = 'signup' if signup else 'email_verification'
    print(f"Confirmation sent to {confirmation.email_address.email} ({action})")
```

### email_changed

**When fired:** When a user changes their email address.

**Arguments:**
- `sender`: The class of the User model
- `request`: The HTTP request object
- `user`: The User instance
- `from_email_address`: The old EmailAddress instance
- `to_email_address`: The new EmailAddress instance

**Example:**
```python
from allauth.account.signals import email_changed
from django.dispatch import receiver

@receiver(email_changed)
def notify_email_change(sender, request, user, from_email_address, to_email_address, **kwargs):
    """Notify both old and new email addresses."""
    from django.core.mail import send_mail
    send_mail(
        'Email Address Changed',
        f'Your email was changed from {from_email_address.email} to {to_email_address.email}',
        'security@example.com',
        [from_email_address.email, to_email_address.email]
    )
```

### email_added

**When fired:** When a user adds a new email address to their account.

**Arguments:**
- `sender`: The EmailAddress model class
- `request`: The HTTP request object
- `user`: The User instance
- `email_address`: The EmailAddress instance that was added

**Example:**
```python
from allauth.account.signals import email_added
from django.dispatch import receiver

@receiver(email_added)
def track_email_added(sender, request, user, email_address, **kwargs):
    """Log when users add email addresses."""
    print(f"User {user.id} added email {email_address.email}")
```

### email_removed

**When fired:** When a user removes an email address from their account.

**Arguments:**
- `sender`: The EmailAddress model class
- `request`: The HTTP request object
- `user`: The User instance
- `email_address`: The EmailAddress instance that was removed

**Example:**
```python
from allauth.account.signals import email_removed
from django.dispatch import receiver

@receiver(email_removed)
def track_email_removed(sender, request, user, email_address, **kwargs):
    """Log when users remove email addresses."""
    print(f"User {user.id} removed email {email_address.email}")
```

## Social Account Signals

### pre_social_login

**When fired:** After successful social authentication but before login is processed. Fires for social logins, signups, and when connecting additional accounts.

**Arguments:**
- `sender`: The SocialLogin class
- `request`: The HTTP request object
- `sociallogin`: The SocialLogin instance containing social account data

**Example:**
```python
from allauth.socialaccount.signals import pre_social_login
from django.dispatch import receiver

@receiver(pre_social_login)
def link_to_existing_user(sender, request, sociallogin, **kwargs):
    """Auto-connect social account to existing user with same email."""
    if sociallogin.is_existing:
        return

    email = sociallogin.account.extra_data.get('email')
    if email:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            pass
```

### social_account_added

**When fired:** After a user connects a social account to their local account.

**Arguments:**
- `sender`: The SocialAccount model class
- `request`: The HTTP request object
- `sociallogin`: The SocialLogin instance

**Example:**
```python
from allauth.socialaccount.signals import social_account_added
from django.dispatch import receiver

@receiver(social_account_added)
def track_social_connection(sender, request, sociallogin, **kwargs):
    """Track when users connect social accounts."""
    provider = sociallogin.account.provider
    user = sociallogin.user
    print(f"User {user.id} connected {provider} account")
```

### social_account_updated

**When fired:** After an existing social account is reconnected with updated token and data.

**Arguments:**
- `sender`: The SocialAccount model class
- `request`: The HTTP request object
- `sociallogin`: The SocialLogin instance with updated data

**Example:**
```python
from allauth.socialaccount.signals import social_account_updated
from django.dispatch import receiver

@receiver(social_account_updated)
def sync_social_data(sender, request, sociallogin, **kwargs):
    """Sync user profile with updated social data."""
    user = sociallogin.user
    extra_data = sociallogin.account.extra_data

    # Update profile with fresh social data
    if hasattr(user, 'profile'):
        user.profile.avatar_url = extra_data.get('picture', '')
        user.profile.save()
```

### social_account_removed

**When fired:** After a user disconnects a social account.

**Arguments:**
- `sender`: The SocialAccount model class
- `request`: The HTTP request object
- `socialaccount`: The SocialAccount instance that was removed

**Example:**
```python
from allauth.socialaccount.signals import social_account_removed
from django.dispatch import receiver

@receiver(social_account_removed)
def handle_social_disconnect(sender, request, socialaccount, **kwargs):
    """Log social account disconnections."""
    print(f"User {socialaccount.user.id} disconnected {socialaccount.provider}")
```

## Signal Registration

### Using @receiver Decorator

The simplest way to register signal handlers:

```python
# myapp/signals.py
from django.dispatch import receiver
from allauth.account.signals import user_signed_up, email_confirmed

@receiver(user_signed_up)
def handle_new_user(sender, request, user, **kwargs):
    # Your handler logic
    pass

@receiver(email_confirmed)
def handle_email_confirmed(sender, request, email_address, **kwargs):
    # Your handler logic
    pass
```

### Registration in apps.py

Ensure signals are imported when Django starts:

```python
# myapp/apps.py
from django.apps import AppConfig

class MyAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'

    def ready(self):
        import myapp.signals  # noqa
```

### Manual Connection

If you prefer explicit registration:

```python
# myapp/signals.py
from allauth.account.signals import user_signed_up

def create_profile(sender, request, user, **kwargs):
    # Handler logic
    pass

# Connect the signal
user_signed_up.connect(create_profile)
```

## Common Use Cases

### Create Profile on Signup

```python
from allauth.account.signals import user_signed_up
from django.dispatch import receiver
from .models import UserProfile

@receiver(user_signed_up)
def create_profile_on_signup(sender, request, user, **kwargs):
    """Automatically create profile for new users."""
    UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'display_name': user.username,
            'signup_date': user.date_joined
        }
    )
```

### Send Welcome Email

```python
from allauth.account.signals import email_confirmed
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string

@receiver(email_confirmed)
def send_welcome_email(sender, request, email_address, **kwargs):
    """Send welcome email after confirmation."""
    user = email_address.user
    html_message = render_to_string('emails/welcome.html', {'user': user})

    send_mail(
        subject='Welcome to Our Platform!',
        message=f'Welcome {user.username}!',
        from_email='welcome@example.com',
        recipient_list=[email_address.email],
        html_message=html_message
    )
```

### Audit Logging

```python
from allauth.account.signals import (
    user_logged_in, user_logged_out,
    password_changed, email_changed
)
from django.dispatch import receiver
from .models import AuditLog

@receiver([user_logged_in, user_logged_out, password_changed, email_changed])
def log_user_activity(sender, request, user, **kwargs):
    """Comprehensive audit logging."""
    signal_name = kwargs.get('signal').__name__

    AuditLog.objects.create(
        user=user,
        action=signal_name,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT'),
        timestamp=timezone.now()
    )
```

### Analytics Tracking

```python
from allauth.account.signals import user_signed_up, user_logged_in
from allauth.socialaccount.signals import social_account_added
from django.dispatch import receiver

@receiver(user_signed_up)
def track_signup(sender, request, user, **kwargs):
    """Send signup event to analytics."""
    # analytics.track(user.id, 'Signed Up', {...})
    pass

@receiver(user_logged_in)
def track_login(sender, request, user, **kwargs):
    """Send login event to analytics."""
    # analytics.track(user.id, 'Logged In', {...})
    pass

@receiver(social_account_added)
def track_social_connection(sender, request, sociallogin, **kwargs):
    """Track social account connections."""
    # analytics.track(sociallogin.user.id, 'Connected Social Account', {
    #     'provider': sociallogin.account.provider
    # })
    pass
```

### Auto-Connect Social Accounts

```python
from allauth.socialaccount.signals import pre_social_login
from django.dispatch import receiver
from django.contrib.auth import get_user_model

@receiver(pre_social_login)
def auto_connect_social_account(sender, request, sociallogin, **kwargs):
    """Automatically connect social accounts with matching email."""
    # Skip if user is already logged in or account already exists
    if request.user.is_authenticated or sociallogin.is_existing:
        return

    # Get email from social account
    email = sociallogin.account.extra_data.get('email')
    if not email:
        return

    # Find user with matching verified email
    User = get_user_model()
    try:
        user = User.objects.get(email=email)
        # Check if email is verified
        if user.emailaddress_set.filter(email=email, verified=True).exists():
            sociallogin.connect(request, user)
    except User.DoesNotExist:
        pass
```

## Best Practices

1. **Always accept **kwargs**: Signal arguments may change in future versions
2. **Handle exceptions**: Don't let signal handlers crash the main flow
3. **Keep handlers fast**: Use background tasks for heavy operations
4. **Import in ready()**: Ensure signals are connected when Django starts
5. **Use sender filtering**: Connect to specific senders when appropriate
6. **Test signal handlers**: Write tests to ensure handlers work correctly

## Further Reading

- [Django Signals Documentation](https://docs.djangoproject.com/en/stable/topics/signals/)
- [django-allauth Signals](https://docs.allauth.org/en/latest/account/signals.html)
