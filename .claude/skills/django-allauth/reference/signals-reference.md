# Signals Reference

Django-allauth emits signals at key points in the authentication lifecycle, allowing you to hook into user actions like login, signup, email verification, and social account connections.

## Account Signals

| Signal | Arguments | When Fired |
|--------|-----------|------------|
| `user_logged_in` | `sender`, `request`, `user` | After a user successfully logs in |
| `user_logged_out` | `sender`, `request`, `user` | After a user logs out |
| `user_signed_up` | `sender`, `request`, `user` | After a new user signs up, before login |
| `password_set` | `sender`, `request`, `user` | When a user sets their password (e.g., after social signup) |
| `password_changed` | `sender`, `request`, `user` | When a user changes their password |
| `password_reset` | `sender`, `request`, `user` | After a user successfully resets their password |

**Example - user_signed_up:**
```python
from allauth.account.signals import user_signed_up
from django.dispatch import receiver

@receiver(user_signed_up)
def create_user_profile(sender, request, user, **kwargs):
    """Create a profile when user signs up."""
    from .models import Profile
    Profile.objects.create(
        user=user,
        signup_ip=request.META.get('REMOTE_ADDR')
    )
```

## Email Signals

| Signal | Arguments | When Fired |
|--------|-----------|------------|
| `email_confirmed` | `sender`, `request`, `email_address` | After a user confirms their email address |
| `email_confirmation_sent` | `sender`, `request`, `confirmation`, `signup` | After an email confirmation is sent |
| `email_changed` | `sender`, `request`, `user`, `from_email_address`, `to_email_address` | When a user changes their email address |
| `email_added` | `sender`, `request`, `user`, `email_address` | When a user adds a new email address |
| `email_removed` | `sender`, `request`, `user`, `email_address` | When a user removes an email address |

## Social Account Signals

| Signal | Arguments | When Fired |
|--------|-----------|------------|
| `pre_social_login` | `sender`, `request`, `sociallogin` | After successful social auth but before login is processed |
| `social_account_added` | `sender`, `request`, `sociallogin` | After a user connects a social account |
| `social_account_updated` | `sender`, `request`, `sociallogin` | After an existing social account is reconnected with updated data |
| `social_account_removed` | `sender`, `request`, `socialaccount` | After a user disconnects a social account |

**Example - pre_social_login:**
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

## Signal Registration

### Using @receiver Decorator

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

```python
from allauth.account.signals import user_signed_up

def create_profile(sender, request, user, **kwargs):
    # Handler logic
    pass

# Connect the signal
user_signed_up.connect(create_profile)
```

## Common Patterns

### Multiple Signal Handler

```python
from allauth.account.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

@receiver([user_logged_in, user_logged_out])
def log_user_activity(sender, request, user, **kwargs):
    """Log login and logout events."""
    signal_name = kwargs.get('signal').__name__
    # Log activity
```

### Conditional Logic

```python
from allauth.socialaccount.signals import pre_social_login
from django.dispatch import receiver

@receiver(pre_social_login)
def handle_social_login(sender, request, sociallogin, **kwargs):
    """Handle different social providers."""
    if request.user.is_authenticated:
        # User is connecting additional account
        pass
    elif sociallogin.is_existing:
        # User is logging in with existing social account
        pass
    else:
        # New social signup
        pass
```

## Best Practices

1. **Always accept **kwargs** - Signal arguments may change in future versions
2. **Handle exceptions** - Don't let signal handlers crash the main flow
3. **Keep handlers fast** - Use background tasks for heavy operations
4. **Import in ready()** - Ensure signals are connected when Django starts
5. **Test signal handlers** - Write tests to ensure handlers work correctly

## Further Reading

- [Django Signals Documentation](https://docs.djangoproject.com/en/stable/topics/signals/)
- [django-allauth Signals](https://docs.allauth.org/en/latest/account/signals.html)
