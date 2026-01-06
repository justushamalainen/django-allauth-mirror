# django-allauth Adapter Methods Reference

Complete reference for customizing django-allauth behavior through adapter method overrides.

## Table of Contents
- [DefaultAccountAdapter Methods](#defaultaccountadapter-methods)
  - [Redirect URLs](#redirect-urls)
  - [Email Handling](#email-handling)
  - [User Management](#user-management)
  - [Validation](#validation)
  - [Authentication Lifecycle](#authentication-lifecycle)
  - [Phone/SMS](#phonesms)
  - [Code Generation](#code-generation)
  - [Messaging](#messaging)
  - [Utility Methods](#utility-methods)
- [DefaultSocialAccountAdapter Methods](#defaultsocialaccountadapter-methods)
- [Quick Reference Summary](#quick-reference-summary)

---

## DefaultAccountAdapter Methods

### Redirect URLs

#### get_signup_redirect_url()
**Signature:** `def get_signup_redirect_url(self, request)`

**Purpose:** Returns the default URL to redirect to directly after signing up.

**When to override:** Customize post-signup destination based on user attributes or request context.

**Example:**
```python
def get_signup_redirect_url(self, request):
    # Redirect new users to onboarding
    return '/onboarding/welcome/'
```

---

#### get_login_redirect_url()
**Signature:** `def get_login_redirect_url(self, request)`

**Purpose:** Returns the default URL to redirect to after logging in. Note that URLs passed explicitly (e.g., by passing along a `next` GET parameter) take precedence.

**When to override:** Implement role-based redirects or custom post-login flows.

**Example:**
```python
def get_login_redirect_url(self, request):
    # Redirect based on user role
    if request.user.is_staff:
        return '/admin/dashboard/'
    return '/user/dashboard/'
```

---

#### get_logout_redirect_url()
**Signature:** `def get_logout_redirect_url(self, request)`

**Purpose:** Returns the URL to redirect to after the user logs out. Note that this method is also invoked if you attempt to log out while no users is logged in.

**When to override:** Customize logout destination or show farewell pages.

**Example:**
```python
def get_logout_redirect_url(self, request):
    # Show goodbye page with feedback form
    return '/goodbye/?show_feedback=true'
```

---

#### get_email_verification_redirect_url()
**Signature:** `def get_email_verification_redirect_url(self, email_address)`

**Purpose:** The URL to return to after email verification.

**When to override:** Direct users to specific pages after confirming their email.

**Example:**
```python
def get_email_verification_redirect_url(self, email_address):
    if self.request.user.is_authenticated:
        return '/profile/complete/'
    return '/login/?verified=true'
```

---

#### get_password_change_redirect_url()
**Signature:** `def get_password_change_redirect_url(self, request)`

**Purpose:** The URL to redirect to after a successful password change/set. NOTE: Not called during the password reset flow.

**When to override:** Customize where users go after changing their password.

**Example:**
```python
def get_password_change_redirect_url(self, request):
    # Redirect to security settings
    return '/account/security/?password_changed=true'
```

---

### Email Handling

#### format_email_subject()
**Signature:** `def format_email_subject(self, subject) -> str`

**Purpose:** Formats the given email subject by adding a prefix.

**When to override:** Customize email subject formatting or add dynamic prefixes.

**Example:**
```python
def format_email_subject(self, subject):
    # Add environment prefix for staging
    if settings.DEBUG:
        return f"[DEV] {subject}"
    return f"[MyApp] {subject}"
```

---

#### get_from_email()
**Signature:** `def get_from_email(self)`

**Purpose:** This is a hook that can be overridden to programmatically set the 'from' email address for sending emails.

**When to override:** Use different from addresses based on context or email type.

**Example:**
```python
def get_from_email(self):
    # Use different from address for transactional emails
    return 'noreply@example.com'
```

---

#### render_mail()
**Signature:** `def render_mail(self, template_prefix, email, context, headers=None)`

**Purpose:** Renders an email to the specified address. `template_prefix` identifies the email that is to be sent, e.g., "account/email/email_confirmation".

**When to override:** Customize email rendering logic or add custom headers.

**Example:**
```python
def render_mail(self, template_prefix, email, context, headers=None):
    # Add custom headers
    if headers is None:
        headers = {}
    headers['X-Campaign-ID'] = context.get('campaign_id', 'default')
    return super().render_mail(template_prefix, email, context, headers)
```

---

#### send_mail()
**Signature:** `def send_mail(self, template_prefix: str, email: str, context: dict) -> None`

**Purpose:** Sends an email using the specified template prefix and context.

**When to override:** Add logging, integrate with email services, or queue emails.

**Example:**
```python
def send_mail(self, template_prefix, email, context):
    # Log all outgoing emails
    logger.info(f"Sending {template_prefix} to {email}")
    super().send_mail(template_prefix, email, context)
```

---

#### send_password_reset_mail()
**Signature:** `def send_password_reset_mail(self, user, email, context)`

**Purpose:** Method intended to be overridden in case you need to customize the logic used to determine whether a user is permitted to request a password reset.

**When to override:** Prevent password resets for social-only accounts or add custom validation.

**Example:**
```python
def send_password_reset_mail(self, user, email, context):
    # Block password reset for social-only users
    if not user.has_usable_password():
        raise ImmediateHttpResponse(
            redirect('account_password_reset_blocked')
        )
    return super().send_password_reset_mail(user, email, context)
```

---

#### get_reset_password_from_key_url()
**Signature:** `def get_reset_password_from_key_url(self, key)`

**Purpose:** Method intended to be overridden in case the password reset email needs to be adjusted.

**When to override:** Generate custom password reset URLs or add tracking parameters.

**Example:**
```python
def get_reset_password_from_key_url(self, key):
    # Add tracking parameter
    url = super().get_reset_password_from_key_url(key)
    return f"{url}?source=email"
```

---

#### get_email_confirmation_url()
**Signature:** `def get_email_confirmation_url(self, request, emailconfirmation)`

**Purpose:** Constructs the email confirmation (activation) URL. Note that if you have architected your system such that email confirmations are sent outside of the request context, `request` can be `None` here.

**When to override:** Customize confirmation URLs for mobile apps or add parameters.

**Example:**
```python
def get_email_confirmation_url(self, request, emailconfirmation):
    # Generate deep link for mobile app
    if request and request.GET.get('mobile'):
        return f"myapp://verify/{emailconfirmation.key}"
    return super().get_email_confirmation_url(request, emailconfirmation)
```

---

#### should_send_confirmation_mail()
**Signature:** `def should_send_confirmation_mail(self, request, email_address, signup) -> bool`

**Purpose:** Determines whether a confirmation email should be sent.

**When to override:** Implement custom logic for when to send confirmation emails.

**Example:**
```python
def should_send_confirmation_mail(self, request, email_address, signup):
    # Don't send confirmation for internal domains
    if email_address.email.endswith('@company.com'):
        return False
    return True
```

---

#### send_account_already_exists_mail()
**Signature:** `def send_account_already_exists_mail(self, email: str) -> None`

**Purpose:** Sends an email notifying that an account already exists with this email address.

**When to override:** Customize the account exists notification message.

**Example:**
```python
def send_account_already_exists_mail(self, email):
    # Add custom context for account recovery
    logger.info(f"Account exists attempt for {email}")
    super().send_account_already_exists_mail(email)
```

---

#### send_confirmation_mail()
**Signature:** `def send_confirmation_mail(self, request, emailconfirmation, signup)`

**Purpose:** Sends the email confirmation/verification email.

**When to override:** Add custom context or logging for confirmation emails.

**Example:**
```python
def send_confirmation_mail(self, request, emailconfirmation, signup):
    # Track signup source
    if signup and request.GET.get('ref'):
        # Store referral info before sending
        pass
    super().send_confirmation_mail(request, emailconfirmation, signup)
```

---

#### send_notification_mail()
**Signature:** `def send_notification_mail(self, template_prefix, user, context=None, email=None)`

**Purpose:** Sends notification emails to users about account activity.

**When to override:** Customize notification behavior or add filtering.

**Example:**
```python
def send_notification_mail(self, template_prefix, user, context=None, email=None):
    # Check user preferences before sending
    if user.email_preferences.notifications_enabled:
        super().send_notification_mail(template_prefix, user, context, email)
```

---

#### generate_emailconfirmation_key()
**Signature:** `def generate_emailconfirmation_key(self, email)`

**Purpose:** Generates a random key for email confirmation.

**When to override:** Use custom key generation algorithm or length.

**Example:**
```python
def generate_emailconfirmation_key(self, email):
    # Generate shorter keys
    return get_random_string(32).lower()
```

---

#### stash_verified_email()
**Signature:** `def stash_verified_email(self, request, email)`

**Purpose:** Stores a verified email address in the session temporarily.

**When to override:** Change where verified emails are stored (e.g., cache).

**Example:**
```python
def stash_verified_email(self, request, email):
    # Also store in cache for cross-session access
    cache.set(f'verified_email_{request.session.session_key}', email, 3600)
    super().stash_verified_email(request, email)
```

---

#### unstash_verified_email()
**Signature:** `def unstash_verified_email(self, request)`

**Purpose:** Retrieves and clears the stashed verified email address.

**When to override:** Retrieve from custom storage location.

**Example:**
```python
def unstash_verified_email(self, request):
    email = super().unstash_verified_email(request)
    # Also clear from cache
    cache.delete(f'verified_email_{request.session.session_key}')
    return email
```

---

#### is_email_verified()
**Signature:** `def is_email_verified(self, request, email)`

**Purpose:** Checks whether or not the email address is already verified beyond allauth scope, for example, by having accepted an invitation before signing up.

**When to override:** Integrate with external verification systems.

**Example:**
```python
def is_email_verified(self, request, email):
    # Check external verification service
    if ExternalVerification.objects.filter(email=email, verified=True).exists():
        return True
    return super().is_email_verified(request, email)
```

---

#### can_delete_email()
**Signature:** `def can_delete_email(self, email_address) -> bool`

**Purpose:** Returns whether or not the given email address can be deleted.

**When to override:** Add custom rules for email deletion.

**Example:**
```python
def can_delete_email(self, email_address):
    # Prevent deletion of corporate emails
    if email_address.email.endswith('@company.com'):
        return False
    return super().can_delete_email(email_address)
```

---

### User Management

#### new_user()
**Signature:** `def new_user(self, request)`

**Purpose:** Instantiates a new User instance.

**When to override:** Pre-populate user fields or use a custom user model.

**Example:**
```python
def new_user(self, request):
    user = super().new_user(request)
    # Set default timezone from request
    if hasattr(user, 'timezone'):
        user.timezone = request.session.get('timezone', 'UTC')
    return user
```

---

#### populate_username()
**Signature:** `def populate_username(self, request, user)`

**Purpose:** Fills in a valid username, if required and missing. If the username is already present it is assumed to be valid (unique).

**When to override:** Customize username generation logic.

**Example:**
```python
def populate_username(self, request, user):
    # Generate username from email prefix
    if not user.username and user.email:
        base = user.email.split('@')[0]
        user.username = self.generate_unique_username([base])
```

---

#### generate_unique_username()
**Signature:** `def generate_unique_username(self, txts, regex=None)`

**Purpose:** Generates a unique username from the provided text options.

**When to override:** Customize username generation algorithm.

**Example:**
```python
def generate_unique_username(self, txts, regex=None):
    # Add company suffix to all usernames
    modified_txts = [f"{txt}_corp" for txt in txts if txt]
    return super().generate_unique_username(modified_txts, regex)
```

---

#### save_user()
**Signature:** `def save_user(self, request, user, form, commit=True)`

**Purpose:** Saves a new `User` instance using information provided in the signup form.

**When to override:** Add custom user fields or perform additional setup.

**Example:**
```python
def save_user(self, request, user, form, commit=True):
    user = super().save_user(request, user, form, commit=False)
    # Set custom fields
    user.referral_code = request.session.get('referral')
    user.signup_source = request.GET.get('source', 'direct')
    if commit:
        user.save()
    return user
```

---

#### get_user_search_fields()
**Signature:** `def get_user_search_fields(self)`

**Purpose:** Returns list of user model fields that should be searchable.

**When to override:** Add custom fields to user search.

**Example:**
```python
def get_user_search_fields(self):
    fields = super().get_user_search_fields()
    # Add custom fields
    fields.extend(['phone_number', 'employee_id'])
    return fields
```

---

#### set_password()
**Signature:** `def set_password(self, user, password) -> None`

**Purpose:** Sets the password for the user.

**When to override:** Add password change logging or integrate with external systems.

**Example:**
```python
def set_password(self, user, password):
    # Log password changes
    PasswordChangeLog.objects.create(
        user=user,
        timestamp=timezone.now(),
        ip_address=self.get_client_ip(self.request)
    )
    super().set_password(user, password)
```

---

### Validation

#### clean_username()
**Signature:** `def clean_username(self, username, shallow=False)`

**Purpose:** Validates the username. You can hook into this if you want to (dynamically) restrict what usernames can be chosen.

**When to override:** Add custom username validation rules.

**Example:**
```python
def clean_username(self, username, shallow=False):
    # Enforce minimum length
    if len(username) < 5:
        raise ValidationError("Username must be at least 5 characters")
    # Block profanity
    if profanity_filter.contains_profanity(username):
        raise ValidationError("Username contains inappropriate content")
    return super().clean_username(username, shallow)
```

---

#### clean_email()
**Signature:** `def clean_email(self, email: str) -> str`

**Purpose:** Validates an email value. You can hook into this if you want to (dynamically) restrict what email addresses can be chosen.

**When to override:** Block disposable emails or enforce domain restrictions.

**Example:**
```python
def clean_email(self, email):
    # Block disposable email domains
    domain = email.split('@')[1].lower()
    if domain in DISPOSABLE_EMAIL_DOMAINS:
        raise ValidationError("Disposable email addresses are not allowed")
    # Enforce company domain for internal users
    if self.request.GET.get('internal') and not email.endswith('@company.com'):
        raise ValidationError("Internal users must use company email")
    return super().clean_email(email)
```

---

#### clean_password()
**Signature:** `def clean_password(self, password, user=None)`

**Purpose:** Validates a password. You can hook into this if you want to restrict the allowed password choices.

**When to override:** Add custom password requirements.

**Example:**
```python
def clean_password(self, password, user=None):
    # Require special character
    if not any(char in '!@#$%^&*' for char in password):
        raise ValidationError("Password must contain a special character")
    # Check against compromised password database
    if is_password_compromised(password):
        raise ValidationError("This password has been compromised")
    return super().clean_password(password, user)
```

---

#### clean_phone()
**Signature:** `def clean_phone(self, phone: str) -> str`

**Purpose:** Validates a phone number. You can hook into this if you want to (dynamically) restrict what phone numbers can be chosen.

**When to override:** Add phone number format validation or regional restrictions.

**Example:**
```python
def clean_phone(self, phone):
    # Validate format using phonenumbers library
    try:
        parsed = phonenumbers.parse(phone, 'US')
        if not phonenumbers.is_valid_number(parsed):
            raise ValidationError("Invalid phone number")
    except phonenumbers.NumberParseException:
        raise ValidationError("Invalid phone number format")
    return super().clean_phone(phone)
```

---

#### validate_unique_email()
**Signature:** `def validate_unique_email(self, email)`

**Purpose:** Validates that the email is unique across the system.

**When to override:** Customize uniqueness validation logic.

**Example:**
```python
def validate_unique_email(self, email):
    # Allow multiple accounts with same email in different tenants
    if not Tenant.objects.filter(
        users__email=email,
        id=self.request.tenant.id
    ).exists():
        return email
    raise ValidationError("Email already exists in this organization")
```

---

### Authentication Lifecycle

#### is_open_for_signup()
**Signature:** `def is_open_for_signup(self, request)`

**Purpose:** Checks whether or not the site is open for signups. Next to simply returning True/False you can also intervene the regular flow by raising an ImmediateHttpResponse.

**When to override:** Implement invite-only signups or feature flags.

**Example:**
```python
def is_open_for_signup(self, request):
    # Require invitation code
    invite_code = request.GET.get('invite')
    if not invite_code or not Invitation.objects.filter(
        code=invite_code, used=False
    ).exists():
        raise ImmediateHttpResponse(
            redirect('signup_closed')
        )
    return True
```

---

#### pre_login()
**Signature:** `def pre_login(self, request, user, *, email_verification, signal_kwargs, email, signup, redirect_url)`

**Purpose:** Called just before the user is logged in. Can be used to prevent login by raising an exception.

**When to override:** Add pre-login checks or account state validation.

**Example:**
```python
def pre_login(self, request, user, **kwargs):
    # Check if account is suspended
    if hasattr(user, 'is_suspended') and user.is_suspended:
        raise ImmediateHttpResponse(
            redirect('account_suspended')
        )
    # Check terms acceptance
    if not user.has_accepted_latest_terms:
        raise ImmediateHttpResponse(
            redirect('accept_terms')
        )
    return super().pre_login(request, user, **kwargs)
```

---

#### post_login()
**Signature:** `def post_login(self, request, user, *, email_verification, signal_kwargs, email, signup, redirect_url)`

**Purpose:** Called after the user successfully logs in. Returns the response to return to the user.

**When to override:** Track login events or customize post-login response.

**Example:**
```python
def post_login(self, request, user, **kwargs):
    # Track login
    LoginEvent.objects.create(
        user=user,
        timestamp=timezone.now(),
        ip_address=self.get_client_ip(request),
        user_agent=self.get_http_user_agent(request)
    )
    # Update last login location
    user.last_login_ip = self.get_client_ip(request)
    user.save(update_fields=['last_login_ip'])
    return super().post_login(request, user, **kwargs)
```

---

#### login()
**Signature:** `def login(self, request, user)`

**Purpose:** Actually logs the user in by setting up the session.

**When to override:** Customize session setup or add logging.

**Example:**
```python
def login(self, request, user):
    # Set custom session data
    request.session['login_time'] = timezone.now().isoformat()
    request.session['login_ip'] = self.get_client_ip(request)
    super().login(request, user)
```

---

#### logout()
**Signature:** `def logout(self, request)`

**Purpose:** Logs the user out by clearing the session.

**When to override:** Add cleanup tasks or logout logging.

**Example:**
```python
def logout(self, request):
    # Log logout event
    if request.user.is_authenticated:
        LogoutEvent.objects.create(
            user=request.user,
            timestamp=timezone.now()
        )
    super().logout(request)
```

---

#### confirm_email()
**Signature:** `def confirm_email(self, request, email_address)`

**Purpose:** Marks the email address as confirmed in the database.

**When to override:** Add post-confirmation actions or notifications.

**Example:**
```python
def confirm_email(self, request, email_address):
    result = super().confirm_email(request, email_address)
    # Award points for email verification
    user = email_address.user
    user.points += 10
    user.save()
    # Send welcome email
    self.send_mail('account/email/welcome', email_address.email, {'user': user})
    return result
```

---

#### pre_authenticate()
**Signature:** `def pre_authenticate(self, request, **credentials)`

**Purpose:** Called before authentication, handles rate limiting.

**When to override:** Add custom rate limiting or pre-auth checks.

**Example:**
```python
def pre_authenticate(self, request, **credentials):
    # Check for account lockout
    email = credentials.get('email', '')
    if AccountLockout.objects.filter(email=email, expires_at__gt=timezone.now()).exists():
        raise ValidationError("Account is temporarily locked")
    super().pre_authenticate(request, **credentials)
```

---

#### authenticate()
**Signature:** `def authenticate(self, request, **credentials)`

**Purpose:** Authenticates the user but does not log them in. See `login` for actually logging in.

**When to override:** Add custom authentication logic or logging.

**Example:**
```python
def authenticate(self, request, **credentials):
    user = super().authenticate(request, **credentials)
    if user:
        # Log successful auth
        AuthSuccess.objects.create(user=user, timestamp=timezone.now())
    return user
```

---

#### authentication_failed()
**Signature:** `def authentication_failed(self, request, **credentials)`

**Purpose:** Called when authentication fails.

**When to override:** Track failed login attempts or implement account lockout.

**Example:**
```python
def authentication_failed(self, request, **credentials):
    # Track failed attempts
    email = credentials.get('email', '')
    FailedLogin.objects.create(
        email=email,
        ip_address=self.get_client_ip(request),
        timestamp=timezone.now()
    )
    # Lock account after 5 failed attempts
    recent_failures = FailedLogin.objects.filter(
        email=email,
        timestamp__gte=timezone.now() - timedelta(hours=1)
    ).count()
    if recent_failures >= 5:
        AccountLockout.objects.create(
            email=email,
            expires_at=timezone.now() + timedelta(hours=1)
        )
```

---

#### reauthenticate()
**Signature:** `def reauthenticate(self, user, password)`

**Purpose:** Re-authenticates the user with their password for sensitive operations.

**When to override:** Add custom re-authentication logic or logging.

**Example:**
```python
def reauthenticate(self, user, password):
    success = super().reauthenticate(user, password)
    if success:
        # Track reauthentication
        ReauthEvent.objects.create(user=user, timestamp=timezone.now())
    return success
```

---

#### get_login_stages()
**Signature:** `def get_login_stages(self)`

**Purpose:** Returns list of login stages that should be executed after initial authentication.

**When to override:** Add custom login stages or modify the flow.

**Example:**
```python
def get_login_stages(self):
    stages = super().get_login_stages()
    # Add custom stage for terms acceptance
    stages.append('myapp.stages.TermsAcceptanceStage')
    return stages
```

---

#### get_reauthentication_methods()
**Signature:** `def get_reauthentication_methods(self, user)`

**Purpose:** Returns available reauthentication methods for the user. The order matters - first method is the default.

**When to override:** Customize available reauthentication options.

**Example:**
```python
def get_reauthentication_methods(self, user):
    methods = super().get_reauthentication_methods(user)
    # Add biometric option for mobile users
    if self.request.user_agent_is_mobile:
        methods.insert(0, {
            'id': 'biometric',
            'description': 'Use biometric authentication',
            'url': reverse('reauth_biometric')
        })
    return methods
```

---

#### is_login_by_code_required()
**Signature:** `def is_login_by_code_required(self, login) -> bool`

**Purpose:** Returns whether or not login-by-code is required for the given login.

**When to override:** Customize when code-based login is required.

**Example:**
```python
def is_login_by_code_required(self, login):
    # Require code for admin users
    if User.objects.filter(email=login, is_staff=True).exists():
        return True
    return super().is_login_by_code_required(login)
```

---

#### respond_user_inactive()
**Signature:** `def respond_user_inactive(self, request, user)`

**Purpose:** Returns the response when trying to login as an inactive user.

**When to override:** Customize inactive user handling.

**Example:**
```python
def respond_user_inactive(self, request, user):
    # Provide reactivation option
    messages.error(request, "Your account is inactive. Check your email for reactivation link.")
    return redirect('account_inactive_reactivate')
```

---

#### respond_email_verification_sent()
**Signature:** `def respond_email_verification_sent(self, request, user)`

**Purpose:** Returns the response after sending email verification.

**When to override:** Customize post-verification-sent behavior.

**Example:**
```python
def respond_email_verification_sent(self, request, user):
    # Redirect to custom confirmation page
    messages.success(request, "Please check your email to verify your account.")
    return redirect('email_verification_pending')
```

---

### Phone/SMS

#### phone_form_field()
**Signature:** `def phone_form_field(self, **kwargs)`

**Purpose:** Returns a form field used to input phone numbers.

**When to override:** Customize phone field widget or validation.

**Example:**
```python
def phone_form_field(self, **kwargs):
    from phonenumber_field.formfields import PhoneNumberField
    kwargs.setdefault('region', 'US')
    return PhoneNumberField(**kwargs)
```

---

#### send_unknown_account_sms()
**Signature:** `def send_unknown_account_sms(self, phone: str, **kwargs) -> None`

**Purpose:** In case enumeration prevention is enabled and a verification code is requested for an unlisted phone number, this method is invoked to send a text explaining that no account is on file.

**When to override:** Implement SMS sending for unknown accounts.

**Example:**
```python
def send_unknown_account_sms(self, phone, **kwargs):
    message = "No account found with this phone number. Sign up at example.com"
    send_sms(phone, message)
```

---

#### send_account_already_exists_sms()
**Signature:** `def send_account_already_exists_sms(self, phone: str) -> None`

**Purpose:** Sends SMS notifying that an account already exists with this phone number.

**When to override:** Implement SMS notification for existing accounts.

**Example:**
```python
def send_account_already_exists_sms(self, phone):
    message = "An account already exists with this number. Login at example.com"
    send_sms(phone, message)
```

---

#### send_verification_code_sms()
**Signature:** `def send_verification_code_sms(self, user, phone: str, code: str, **kwargs)`

**Purpose:** Sends a verification code via SMS. **Must be implemented to use phone verification.**

**When to override:** Required implementation - integrate with your SMS provider.

**Example:**
```python
def send_verification_code_sms(self, user, phone, code, **kwargs):
    # Integrate with Twilio
    from twilio.rest import Client
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        body=f"Your verification code is: {code}",
        from_=settings.TWILIO_PHONE_NUMBER,
        to=phone
    )
```

---

#### set_phone()
**Signature:** `def set_phone(self, user, phone: str, verified: bool)`

**Purpose:** Sets the phone number (and verified status) for the given user. **Must be implemented to use phone verification.**

**When to override:** Required implementation - store phone number on your user model.

**Example:**
```python
def set_phone(self, user, phone, verified):
    user.phone_number = phone
    user.phone_verified = verified
    user.save(update_fields=['phone_number', 'phone_verified'])
```

---

#### get_phone()
**Signature:** `def get_phone(self, user) -> typing.Optional[typing.Tuple[str, bool]]`

**Purpose:** Returns the phone number stored for the given user. A tuple of the phone number itself and whether or not the phone number was verified is returned. **Must be implemented to use phone verification.**

**When to override:** Required implementation - retrieve phone from your user model.

**Example:**
```python
def get_phone(self, user):
    if hasattr(user, 'phone_number') and user.phone_number:
        return (user.phone_number, user.phone_verified)
    return None
```

---

#### set_phone_verified()
**Signature:** `def set_phone_verified(self, user, phone: str)`

**Purpose:** Marks the specified phone number for the given user as verified. Note that the user is already expected to have the phone number attached to the account. **Must be implemented to use phone verification.**

**When to override:** Required implementation - mark phone as verified.

**Example:**
```python
def set_phone_verified(self, user, phone):
    user.phone_verified = True
    user.phone_verified_at = timezone.now()
    user.save(update_fields=['phone_verified', 'phone_verified_at'])
```

---

#### get_user_by_phone()
**Signature:** `def get_user_by_phone(self, phone: str)`

**Purpose:** Looks up a user given the specified phone number. Returns `None` if no user was found. **Must be implemented to use phone verification.**

**When to override:** Required implementation - query user by phone number.

**Example:**
```python
def get_user_by_phone(self, phone):
    User = get_user_model()
    try:
        return User.objects.get(phone_number=phone)
    except User.DoesNotExist:
        return None
```

---

### Code Generation

#### generate_login_code()
**Signature:** `def generate_login_code(self) -> str`

**Purpose:** Generates a new login code for passwordless authentication.

**When to override:** Customize code format or length.

**Example:**
```python
def generate_login_code(self):
    # Generate 8-digit numeric code
    return ''.join([str(random.randint(0, 9)) for _ in range(8)])
```

---

#### generate_password_reset_code()
**Signature:** `def generate_password_reset_code(self) -> str`

**Purpose:** Generates a new password reset code.

**When to override:** Customize reset code format.

**Example:**
```python
def generate_password_reset_code(self):
    # Generate memorable 6-character code
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    return ''.join(random.choice(chars) for _ in range(6))
```

---

#### generate_email_verification_code()
**Signature:** `def generate_email_verification_code(self) -> str`

**Purpose:** Generates a new email verification code.

**When to override:** Customize verification code format.

**Example:**
```python
def generate_email_verification_code(self):
    # Generate 6-digit code
    return str(random.randint(100000, 999999))
```

---

#### generate_phone_verification_code()
**Signature:** `def generate_phone_verification_code(self, *, user, phone: str) -> str`

**Purpose:** Generates a new phone verification code.

**When to override:** Customize phone verification code format.

**Example:**
```python
def generate_phone_verification_code(self, *, user, phone):
    # Generate 4-digit PIN
    return str(random.randint(1000, 9999))
```

---

### Messaging

#### add_message()
**Signature:** `def add_message(self, request, level, message_template=None, message_context=None, extra_tags="", message=None)`

**Purpose:** Wrapper of `django.contrib.messages.add_message` that reads the message text from a template.

**When to override:** Customize message handling or add message logging.

**Example:**
```python
def add_message(self, request, level, message_template=None, message_context=None, extra_tags="", message=None):
    # Log all messages
    if message or message_template:
        MessageLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            level=level,
            message=message or message_template,
            timestamp=timezone.now()
        )
    super().add_message(request, level, message_template, message_context, extra_tags, message)
```

---

### Utility Methods

#### is_safe_url()
**Signature:** `def is_safe_url(self, url)`

**Purpose:** Validates that a redirect URL is safe to use.

**When to override:** Add custom URL validation rules.

**Example:**
```python
def is_safe_url(self, url):
    # Block redirects to external sites
    if url.startswith('http') and 'example.com' not in url:
        return False
    return super().is_safe_url(url)
```

---

#### is_ajax()
**Signature:** `def is_ajax(self, request)`

**Purpose:** Determines if the request is an AJAX request.

**When to override:** Customize AJAX detection logic.

**Example:**
```python
def is_ajax(self, request):
    # Add custom header detection
    if request.META.get('HTTP_X_REQUESTED_BY') == 'mobile-app':
        return True
    return super().is_ajax(request)
```

---

#### get_client_ip()
**Signature:** `def get_client_ip(self, request) -> str`

**Purpose:** Extracts the client IP address from the request.

**When to override:** Customize IP extraction for your proxy setup.

**Example:**
```python
def get_client_ip(self, request):
    # Handle CloudFlare proxy
    cf_ip = request.META.get('HTTP_CF_CONNECTING_IP')
    if cf_ip:
        return cf_ip
    return super().get_client_ip(request)
```

---

#### get_http_user_agent()
**Signature:** `def get_http_user_agent(self, request: HttpRequest) -> str`

**Purpose:** Extracts the user agent string from the request.

**When to override:** Normalize or sanitize user agent strings.

**Example:**
```python
def get_http_user_agent(self, request):
    user_agent = super().get_http_user_agent(request)
    # Truncate to prevent storage issues
    return user_agent[:500]
```

---

#### ajax_response()
**Signature:** `def ajax_response(self, request, response, redirect_to=None, form=None, data=None)`

**Purpose:** Generates JSON response for AJAX requests.

**When to override:** Customize AJAX response format.

**Example:**
```python
def ajax_response(self, request, response, redirect_to=None, form=None, data=None):
    resp = super().ajax_response(request, response, redirect_to, form, data)
    # Add API version to response
    content = json.loads(resp.content)
    content['api_version'] = '2.0'
    return HttpResponse(json.dumps(content), status=resp.status_code, content_type='application/json')
```

---

## DefaultSocialAccountAdapter Methods

### pre_social_login()
**Signature:** `def pre_social_login(self, request, sociallogin)`

**Purpose:** Invoked just after a user successfully authenticates via a social provider, but before the login is actually processed (and before the pre_social_login signal is emitted). You can use this hook to intervene, e.g., abort the login by raising an ImmediateHttpResponse.

**When to override:** Connect social accounts to existing users, add business logic.

**Example:**
```python
def pre_social_login(self, request, sociallogin):
    # Auto-connect to existing user with same email
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

### on_authentication_error()
**Signature:** `def on_authentication_error(self, request, provider, error=None, exception=None, extra_context=None)`

**Purpose:** Invoked when there is an error in the authentication cycle. In this case, pre_social_login will not be reached. You can use this hook to intervene, e.g., redirect to an educational flow by raising an ImmediateHttpResponse.

**When to override:** Handle authentication errors gracefully or log failures.

**Example:**
```python
def on_authentication_error(self, request, provider, error=None, exception=None, extra_context=None):
    # Log authentication errors
    SocialAuthError.objects.create(
        provider=provider.id,
        error=error,
        exception_type=type(exception).__name__ if exception else None,
        timestamp=timezone.now()
    )
    # Redirect to custom error page
    messages.error(request, f"Authentication with {provider.name} failed. Please try again.")
```

---

### populate_user()
**Signature:** `def populate_user(self, request, sociallogin, data)`

**Purpose:** Hook that can be used to further populate the user instance. For convenience, several common fields are populated by default. Note that the user instance being populated represents a suggested User instance that represents the social user that is in the process of being logged in. The User instance need not be completely valid and conflict-free.

**When to override:** Extract additional data from social provider.

**Example:**
```python
def populate_user(self, request, sociallogin, data):
    user = super().populate_user(request, sociallogin, data)
    # Extract additional fields
    if 'location' in data:
        user.city = data['location'].get('city')
        user.country = data['location'].get('country')
    if 'avatar_url' in data:
        user.avatar_url = data['avatar_url']
    return user
```

---

### new_user()
**Signature:** `def new_user(self, request, sociallogin)`

**Purpose:** Instantiates a new User instance for social signup.

**When to override:** Pre-populate user with social-specific defaults.

**Example:**
```python
def new_user(self, request, sociallogin):
    user = super().new_user(request, sociallogin)
    # Mark as social signup
    user.signup_type = 'social'
    user.signup_provider = sociallogin.account.provider
    return user
```

---

### save_user()
**Signature:** `def save_user(self, request, sociallogin, form=None)`

**Purpose:** Saves a newly signed up social login. In case of auto-signup, the signup form is not available.

**When to override:** Perform additional setup during social signup.

**Example:**
```python
def save_user(self, request, sociallogin, form=None):
    user = super().save_user(request, sociallogin, form)
    # Send welcome email for social signups
    self.send_mail(
        'account/email/social_welcome',
        user.email,
        {'user': user, 'provider': sociallogin.account.provider}
    )
    return user
```

---

### is_auto_signup_allowed()
**Signature:** `def is_auto_signup_allowed(self, request, sociallogin)`

**Purpose:** Determines whether auto-signup (without showing signup form) is allowed for this social login.

**When to override:** Conditionally allow auto-signup based on provider or email.

**Example:**
```python
def is_auto_signup_allowed(self, request, sociallogin):
    # Allow auto-signup for verified corporate emails
    if sociallogin.email_addresses:
        email = sociallogin.email_addresses[0].email
        if email.endswith('@company.com') and sociallogin.email_addresses[0].verified:
            return True
    # Require signup form for others
    return False
```

---

### validate_disconnect()
**Signature:** `def validate_disconnect(self, account, accounts) -> None`

**Purpose:** Validate whether or not the socialaccount can be safely disconnected.

**When to override:** Add custom validation rules for disconnecting social accounts.

**Example:**
```python
def validate_disconnect(self, account, accounts):
    # Prevent disconnecting last social account if no password set
    if len(accounts) == 1 and not account.user.has_usable_password():
        raise ValidationError(
            "Cannot disconnect your only login method. Set a password first."
        )
    super().validate_disconnect(account, accounts)
```

---

### is_open_for_signup()
**Signature:** `def is_open_for_signup(self, request, sociallogin)`

**Purpose:** Checks whether or not the site is open for social signups.

**When to override:** Restrict social signups based on provider or conditions.

**Example:**
```python
def is_open_for_signup(self, request, sociallogin):
    # Only allow Google and GitHub signups
    if sociallogin.account.provider not in ['google', 'github']:
        raise ImmediateHttpResponse(
            redirect('signup_provider_not_allowed')
        )
    return super().is_open_for_signup(request, sociallogin)
```

---

### get_connect_redirect_url()
**Signature:** `def get_connect_redirect_url(self, request, socialaccount)`

**Purpose:** Returns the default URL to redirect to after successfully connecting a social account.

**When to override:** Customize post-connection redirect destination.

**Example:**
```python
def get_connect_redirect_url(self, request, socialaccount):
    # Redirect to profile with success message
    messages.success(request, f"Successfully connected {socialaccount.get_provider().name}")
    return reverse('user_profile')
```

---

### get_signup_form_initial_data()
**Signature:** `def get_signup_form_initial_data(self, sociallogin)`

**Purpose:** Returns initial data for the signup form when social auto-signup is not allowed.

**When to override:** Pre-fill additional form fields from social data.

**Example:**
```python
def get_signup_form_initial_data(self, sociallogin):
    initial = super().get_signup_form_initial_data(sociallogin)
    # Add phone from social data if available
    extra_data = sociallogin.account.extra_data
    if 'phone_number' in extra_data:
        initial['phone'] = extra_data['phone_number']
    return initial
```

---

### list_providers()
**Signature:** `def list_providers(self, request)`

**Purpose:** Returns a list of all available social authentication providers.

**When to override:** Filter providers based on request context.

**Example:**
```python
def list_providers(self, request):
    providers = super().list_providers(request)
    # Hide certain providers for mobile apps
    if request.user_agent_is_mobile:
        providers = [p for p in providers if p.id in ['google', 'apple']]
    return providers
```

---

### get_provider()
**Signature:** `def get_provider(self, request, provider, client_id=None)`

**Purpose:** Looks up a provider, supporting subproviders by looking up by provider_id.

**When to override:** Customize provider lookup logic.

**Example:**
```python
def get_provider(self, request, provider, client_id=None):
    # Add caching for provider lookup
    cache_key = f"provider_{provider}_{client_id}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    provider_obj = super().get_provider(request, provider, client_id)
    cache.set(cache_key, provider_obj, 3600)
    return provider_obj
```

---

### is_email_verified()
**Signature:** `def is_email_verified(self, provider, email)`

**Purpose:** Returns True if the given email encountered during a social login for the given provider is to be assumed verified.

**When to override:** Customize email verification assumptions.

**Example:**
```python
def is_email_verified(self, provider, email):
    # Trust all corporate emails from OAuth providers
    if email.endswith('@company.com') and provider.id in ['google', 'microsoft']:
        return True
    return super().is_email_verified(provider, email)
```

---

### can_authenticate_by_email()
**Signature:** `def can_authenticate_by_email(self, login, email)`

**Purpose:** Returns True if authentication by email is active for this login/email.

**When to override:** Control email-based authentication for social accounts.

**Example:**
```python
def can_authenticate_by_email(self, login, email):
    # Disable email auth for certain providers
    if login.provider.id in ['twitter', 'github']:
        return False
    return super().can_authenticate_by_email(login, email)
```

---

### generate_state_param()
**Signature:** `def generate_state_param(self, state: dict) -> str`

**Purpose:** Generates the state parameter for OAuth flows. The state parameter is used to preserve certain state before the handshake with the provider takes place.

**When to override:** Add custom state generation or encoding.

**Example:**
```python
def generate_state_param(self, state):
    # Add timestamp to state
    state['timestamp'] = timezone.now().isoformat()
    # Encode as JWT for tamper protection
    return jwt.encode(state, settings.SECRET_KEY, algorithm='HS256')
```

---

## Quick Reference Summary

| Method | Category | Override Frequency | Primary Use Case |
|--------|----------|-------------------|------------------|
| **DefaultAccountAdapter** | | | |
| get_login_redirect_url | Redirect URLs | Very High | Role-based redirects |
| get_signup_redirect_url | Redirect URLs | High | Custom signup flow |
| clean_email | Validation | High | Block disposable emails |
| clean_password | Validation | High | Custom password rules |
| save_user | User Management | High | Add custom fields |
| send_mail | Email Handling | Medium | Email logging/queuing |
| send_verification_code_sms | Phone/SMS | Required* | SMS integration |
| set_phone | Phone/SMS | Required* | Phone storage |
| get_phone | Phone/SMS | Required* | Phone retrieval |
| pre_login | Auth Lifecycle | Medium | Pre-login checks |
| post_login | Auth Lifecycle | High | Login tracking |
| is_open_for_signup | Auth Lifecycle | High | Invite-only signups |
| populate_username | User Management | Medium | Username generation |
| clean_username | Validation | Medium | Username rules |
| get_from_email | Email Handling | Low | Dynamic sender |
| format_email_subject | Email Handling | Low | Subject formatting |
| send_confirmation_mail | Email Handling | Low | Custom confirmation |
| get_email_confirmation_url | Email Handling | Medium | Mobile deep links |
| confirm_email | Auth Lifecycle | Low | Post-verification |
| authenticate | Auth Lifecycle | Low | Auth logging |
| authentication_failed | Auth Lifecycle | Medium | Failed login tracking |
| generate_login_code | Code Generation | Low | Custom code format |
| add_message | Messaging | Low | Message logging |
| get_client_ip | Utility | Medium | Proxy handling |
| is_safe_url | Utility | Low | URL validation |
| **DefaultSocialAccountAdapter** | | | |
| pre_social_login | Social Auth | Very High | Auto-connect accounts |
| populate_user | Social Auth | High | Extract social data |
| is_auto_signup_allowed | Social Auth | High | Conditional auto-signup |
| save_user | Social Auth | Medium | Social signup tracking |
| validate_disconnect | Social Auth | Medium | Disconnect rules |
| on_authentication_error | Social Auth | Medium | Error handling |
| get_connect_redirect_url | Social Auth | Low | Post-connect redirect |
| is_open_for_signup | Social Auth | Medium | Provider restrictions |
| is_email_verified | Social Auth | Medium | Email trust rules |
| get_signup_form_initial_data | Social Auth | Low | Form pre-fill |

**Note:** Methods marked "Required*" must be implemented to enable phone/SMS functionality.

---

## Usage Example: Custom Adapter

```python
# myapp/adapter.py
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.shortcuts import redirect

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

# settings.py
ACCOUNT_ADAPTER = 'myapp.adapter.MyAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'myapp.adapter.MySocialAccountAdapter'
```

---

**Related Documentation:**
- [Adapter Configuration Guide](/home/user/django-allauth-mirror/.claude/skills/django-allauth/guides/adapter-configuration.md)
- [Flow Customization Guide](/home/user/django-allauth-mirror/.claude/skills/django-allauth/guides/flow-customization.md)
- [Phone/SMS Implementation Guide](/home/user/django-allauth-mirror/.claude/skills/django-allauth/guides/phone-sms.md)
