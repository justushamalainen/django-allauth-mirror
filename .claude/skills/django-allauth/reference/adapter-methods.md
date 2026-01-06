# django-allauth Adapter Methods Reference

Quick reference for customizing django-allauth behavior through adapter method overrides.

## Adapter Class Hierarchy

django-allauth uses two main adapter classes:

- **DefaultAccountAdapter** - Handles standard authentication (signup, login, email, phone)
- **DefaultSocialAccountAdapter** - Handles social authentication (OAuth providers)

Override these adapters in your settings:
```python
ACCOUNT_ADAPTER = 'myapp.adapter.MyAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'myapp.adapter.MySocialAccountAdapter'
```

---

## Top 15 Most-Used Methods (Full Documentation)

### DefaultAccountAdapter Methods

#### get_login_redirect_url()
**Signature:** `def get_login_redirect_url(self, request)`

Returns the URL to redirect to after logging in. URLs passed explicitly (e.g., via `next` parameter) take precedence.

**Example:**
```python
def get_login_redirect_url(self, request):
    if request.user.is_staff:
        return '/admin/dashboard/'
    return '/user/dashboard/'
```

---

#### save_user()
**Signature:** `def save_user(self, request, user, form, commit=True)`

Saves a new User instance using information from the signup form. Use this to add custom fields during registration.

**Example:**
```python
def save_user(self, request, user, form, commit=True):
    user = super().save_user(request, user, form, commit=False)
    user.referral_code = request.session.get('referral')
    user.signup_source = request.GET.get('source', 'direct')
    if commit:
        user.save()
    return user
```

---

#### clean_email()
**Signature:** `def clean_email(self, email: str) -> str`

Validates email addresses. Override to block disposable emails or enforce domain restrictions.

**Example:**
```python
def clean_email(self, email):
    domain = email.split('@')[1].lower()
    if domain in DISPOSABLE_EMAIL_DOMAINS:
        raise ValidationError("Disposable email addresses are not allowed")
    return super().clean_email(email)
```

---

#### clean_password()
**Signature:** `def clean_password(self, password, user=None)`

Validates passwords. Override to add custom password requirements.

**Example:**
```python
def clean_password(self, password, user=None):
    if not any(char in '!@#$%^&*' for char in password):
        raise ValidationError("Password must contain a special character")
    return super().clean_password(password, user)
```

---

#### post_login()
**Signature:** `def post_login(self, request, user, *, email_verification, signal_kwargs, email, signup, redirect_url)`

Called after successful login. Use for tracking login events or updating user data.

**Example:**
```python
def post_login(self, request, user, **kwargs):
    LoginEvent.objects.create(
        user=user,
        ip_address=self.get_client_ip(request),
        timestamp=timezone.now()
    )
    return super().post_login(request, user, **kwargs)
```

---

#### is_open_for_signup()
**Signature:** `def is_open_for_signup(self, request)`

Controls whether signups are allowed. Use for invite-only signups or feature flags.

**Example:**
```python
def is_open_for_signup(self, request):
    invite_code = request.GET.get('invite')
    if not invite_code or not Invitation.objects.filter(code=invite_code, used=False).exists():
        raise ImmediateHttpResponse(redirect('signup_closed'))
    return True
```

---

#### get_signup_redirect_url()
**Signature:** `def get_signup_redirect_url(self, request)`

Returns the URL to redirect to after signing up.

**Example:**
```python
def get_signup_redirect_url(self, request):
    return '/onboarding/welcome/'
```

---

#### send_mail()
**Signature:** `def send_mail(self, template_prefix: str, email: str, context: dict) -> None`

Sends emails using django-allauth templates. Override for logging or queuing.

**Example:**
```python
def send_mail(self, template_prefix, email, context):
    logger.info(f"Sending {template_prefix} to {email}")
    super().send_mail(template_prefix, email, context)
```

---

#### pre_login()
**Signature:** `def pre_login(self, request, user, *, email_verification, signal_kwargs, email, signup, redirect_url)`

Called just before login. Use for account state validation or pre-login checks.

**Example:**
```python
def pre_login(self, request, user, **kwargs):
    if hasattr(user, 'is_suspended') and user.is_suspended:
        raise ImmediateHttpResponse(redirect('account_suspended'))
    return super().pre_login(request, user, **kwargs)
```

---

#### populate_username()
**Signature:** `def populate_username(self, request, user)`

Generates a username when required but missing. Override to customize username generation.

**Example:**
```python
def populate_username(self, request, user):
    if not user.username and user.email:
        base = user.email.split('@')[0]
        user.username = self.generate_unique_username([base])
```

---

#### clean_username()
**Signature:** `def clean_username(self, username, shallow=False)`

Validates usernames. Override to add custom username rules.

**Example:**
```python
def clean_username(self, username, shallow=False):
    if len(username) < 5:
        raise ValidationError("Username must be at least 5 characters")
    return super().clean_username(username, shallow)
```

---

#### authentication_failed()
**Signature:** `def authentication_failed(self, request, **credentials)`

Called when authentication fails. Use for tracking failed attempts or account lockout.

**Example:**
```python
def authentication_failed(self, request, **credentials):
    email = credentials.get('email', '')
    FailedLogin.objects.create(
        email=email,
        ip_address=self.get_client_ip(request),
        timestamp=timezone.now()
    )
```

---

### DefaultSocialAccountAdapter Methods

#### pre_social_login()
**Signature:** `def pre_social_login(self, request, sociallogin)`

Invoked after successful social authentication but before login is processed. Use to connect social accounts to existing users.

**Example:**
```python
def pre_social_login(self, request, sociallogin):
    if sociallogin.is_existing:
        return
    if sociallogin.email_addresses:
        email = sociallogin.email_addresses[0].email
        try:
            user = User.objects.get(email=email)
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            pass
```

---

#### populate_user()
**Signature:** `def populate_user(self, request, sociallogin, data)`

Extracts data from social provider to populate user fields.

**Example:**
```python
def populate_user(self, request, sociallogin, data):
    user = super().populate_user(request, sociallogin, data)
    if 'location' in data:
        user.city = data['location'].get('city')
    if 'avatar_url' in data:
        user.avatar_url = data['avatar_url']
    return user
```

---

#### is_auto_signup_allowed()
**Signature:** `def is_auto_signup_allowed(self, request, sociallogin)`

Determines whether auto-signup (without signup form) is allowed for this social login.

**Example:**
```python
def is_auto_signup_allowed(self, request, sociallogin):
    if sociallogin.email_addresses:
        email = sociallogin.email_addresses[0].email
        if email.endswith('@company.com') and sociallogin.email_addresses[0].verified:
            return True
    return False
```

---

## Additional Methods (Quick Reference)

### DefaultAccountAdapter - Redirect URLs

| Method | Signature | Use Case |
|--------|-----------|----------|
| get_logout_redirect_url | `(request)` | Customize logout destination |
| get_email_verification_redirect_url | `(email_address)` | Post-email-verification redirect |
| get_password_change_redirect_url | `(request)` | Post-password-change redirect |

### DefaultAccountAdapter - Email Handling

| Method | Signature | Use Case |
|--------|-----------|----------|
| format_email_subject | `(subject) -> str` | Customize email subject formatting |
| get_from_email | `()` | Set 'from' email address dynamically |
| render_mail | `(template_prefix, email, context, headers=None)` | Customize email rendering |
| send_password_reset_mail | `(user, email, context)` | Control password reset logic |
| get_reset_password_from_key_url | `(key)` | Customize password reset URL |
| get_email_confirmation_url | `(request, emailconfirmation)` | Customize confirmation URLs (mobile deep links) |
| should_send_confirmation_mail | `(request, email_address, signup) -> bool` | Control when to send confirmation emails |
| send_account_already_exists_mail | `(email: str)` | Notify about existing accounts |
| send_confirmation_mail | `(request, emailconfirmation, signup)` | Send verification emails |
| send_notification_mail | `(template_prefix, user, context=None, email=None)` | Send account activity notifications |
| generate_emailconfirmation_key | `(email)` | Generate email confirmation keys |
| stash_verified_email | `(request, email)` | Store verified email in session |
| unstash_verified_email | `(request)` | Retrieve stashed verified email |
| is_email_verified | `(request, email)` | Check if email is pre-verified |
| can_delete_email | `(email_address) -> bool` | Control email deletion |

### DefaultAccountAdapter - User Management

| Method | Signature | Use Case |
|--------|-----------|----------|
| new_user | `(request)` | Instantiate new User with custom defaults |
| generate_unique_username | `(txts, regex=None)` | Generate unique usernames |
| get_user_search_fields | `()` | Define searchable user fields |
| set_password | `(user, password)` | Set password with logging |

### DefaultAccountAdapter - Validation

| Method | Signature | Use Case |
|--------|-----------|----------|
| clean_phone | `(phone: str) -> str` | Validate phone numbers |
| validate_unique_email | `(email)` | Check email uniqueness |

### DefaultAccountAdapter - Authentication Lifecycle

| Method | Signature | Use Case |
|--------|-----------|----------|
| login | `(request, user)` | Set up user session |
| logout | `(request)` | Clear user session |
| confirm_email | `(request, email_address)` | Mark email as confirmed |
| pre_authenticate | `(request, **credentials)` | Pre-authentication checks |
| authenticate | `(request, **credentials)` | Authenticate without logging in |
| reauthenticate | `(user, password)` | Re-authenticate for sensitive operations |
| get_login_stages | `()` | Define multi-step login flow |
| get_reauthentication_methods | `(user)` | Available reauthentication options |
| is_login_by_code_required | `(login) -> bool` | Require code-based login |
| respond_user_inactive | `(request, user)` | Handle inactive user login |
| respond_email_verification_sent | `(request, user)` | Post-verification-sent response |

### DefaultAccountAdapter - Phone/SMS (Required for Phone Support)

| Method | Signature | Use Case |
|--------|-----------|----------|
| phone_form_field | `(**kwargs)` | Custom phone field widget |
| send_unknown_account_sms | `(phone: str, **kwargs)` | SMS for unknown phone numbers |
| send_account_already_exists_sms | `(phone: str)` | SMS for existing accounts |
| send_verification_code_sms | `(user, phone: str, code: str, **kwargs)` | **Required:** Send SMS verification code |
| set_phone | `(user, phone: str, verified: bool)` | **Required:** Store phone on user |
| get_phone | `(user) -> Optional[Tuple[str, bool]]` | **Required:** Retrieve user phone |
| set_phone_verified | `(user, phone: str)` | **Required:** Mark phone as verified |
| get_user_by_phone | `(phone: str)` | **Required:** Look up user by phone |

### DefaultAccountAdapter - Code Generation

| Method | Signature | Use Case |
|--------|-----------|----------|
| generate_login_code | `() -> str` | Generate passwordless login code |
| generate_password_reset_code | `() -> str` | Generate password reset code |
| generate_email_verification_code | `() -> str` | Generate email verification code |
| generate_phone_verification_code | `(*, user, phone: str) -> str` | Generate phone verification code |

### DefaultAccountAdapter - Messaging & Utility

| Method | Signature | Use Case |
|--------|-----------|----------|
| add_message | `(request, level, message_template=None, ...)` | Add Django messages |
| is_safe_url | `(url)` | Validate redirect URL safety |
| is_ajax | `(request)` | Detect AJAX requests |
| get_client_ip | `(request) -> str` | Extract client IP address |
| get_http_user_agent | `(request: HttpRequest) -> str` | Extract user agent string |
| ajax_response | `(request, response, redirect_to=None, ...)` | Generate JSON responses |

### DefaultSocialAccountAdapter - Social Authentication

| Method | Signature | Use Case |
|--------|-----------|----------|
| on_authentication_error | `(request, provider, error=None, exception=None, ...)` | Handle social auth errors |
| new_user | `(request, sociallogin)` | Instantiate user for social signup |
| save_user | `(request, sociallogin, form=None)` | Save social signup |
| validate_disconnect | `(account, accounts)` | Validate social account disconnect |
| is_open_for_signup | `(request, sociallogin)` | Control social signup availability |
| get_connect_redirect_url | `(request, socialaccount)` | Post-connection redirect |
| get_signup_form_initial_data | `(sociallogin)` | Pre-fill signup form from social data |
| list_providers | `(request)` | List available social providers |
| get_provider | `(request, provider, client_id=None)` | Look up social provider |
| is_email_verified | `(provider, email)` | Trust email from social provider |
| can_authenticate_by_email | `(login, email)` | Allow email auth for social accounts |
| generate_state_param | `(state: dict) -> str` | Generate OAuth state parameter |

---

## Complete Usage Example

```python
# myapp/adapter.py
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from allauth.exceptions import ImmediateHttpResponse

class MyAccountAdapter(DefaultAccountAdapter):

    def get_login_redirect_url(self, request):
        """Redirect based on user role"""
        if request.user.is_staff:
            return '/admin/dashboard/'
        return '/dashboard/'

    def clean_email(self, email):
        """Block disposable email domains"""
        email = super().clean_email(email)
        domain = email.split('@')[1].lower()
        if domain in settings.BLOCKED_EMAIL_DOMAINS:
            raise ValidationError("Please use a non-disposable email address")
        return email

    def save_user(self, request, user, form, commit=True):
        """Add referral tracking"""
        user = super().save_user(request, user, form, commit=False)
        user.referral_code = request.session.get('referral_code')
        if commit:
            user.save()
        return user

    def post_login(self, request, user, **kwargs):
        """Track login events"""
        LoginEvent.objects.create(
            user=user,
            ip_address=self.get_client_ip(request),
            timestamp=timezone.now()
        )
        return super().post_login(request, user, **kwargs)

class MySocialAccountAdapter(DefaultSocialAccountAdapter):

    def pre_social_login(self, request, sociallogin):
        """Auto-connect to existing users by email"""
        if sociallogin.is_existing:
            return

        if sociallogin.email_addresses:
            email = sociallogin.email_addresses[0].email
            try:
                user = User.objects.get(email=email)
                sociallogin.connect(request, user)
            except User.DoesNotExist:
                pass

    def populate_user(self, request, sociallogin, data):
        """Extract additional profile data"""
        user = super().populate_user(request, sociallogin, data)
        if 'picture' in data:
            user.avatar_url = data['picture']
        return user

    def is_auto_signup_allowed(self, request, sociallogin):
        """Allow auto-signup for verified corporate emails"""
        if sociallogin.email_addresses:
            email = sociallogin.email_addresses[0].email
            if email.endswith('@company.com') and sociallogin.email_addresses[0].verified:
                return True
        return False

# settings.py
ACCOUNT_ADAPTER = 'myapp.adapter.MyAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'myapp.adapter.MySocialAccountAdapter'
```

---

**Related Documentation:**
- [Adapter Configuration Guide](/home/user/django-allauth-mirror/.claude/skills/django-allauth/guides/adapter-configuration.md)
- [Flow Customization Guide](/home/user/django-allauth-mirror/.claude/skills/django-allauth/guides/flow-customization.md)
- [Phone/SMS Implementation Guide](/home/user/django-allauth-mirror/.claude/skills/django-allauth/guides/phone-sms.md)
