#!/usr/bin/env python3
"""
Django-AllAuth Adapter Generator

An interactive tool to generate custom adapter classes for django-allauth.
Helps you quickly scaffold adapter code with commonly overridden methods.

Usage:
    python generate_adapter.py
    python generate_adapter.py --template redirect
    python generate_adapter.py --adapter account --output myapp/adapters.py
    python generate_adapter.py --template full --adapter social
"""

import argparse
import os
import sys
from typing import Dict, List, Set, Tuple


# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def colorize(text: str, color: str) -> str:
    """Add color to text for terminal output."""
    return f"{color}{text}{Colors.ENDC}"


# Method metadata: (category, signature, description, usage_percentage, example_hint)
ACCOUNT_ADAPTER_METHODS = {
    # Redirect URLs (most common - 80%)
    'get_login_redirect_url': (
        'redirect',
        'def get_login_redirect_url(self, request):',
        'Returns the URL to redirect to after logging in.',
        80,
        'return "/dashboard/"  # Custom redirect after login'
    ),
    'get_signup_redirect_url': (
        'redirect',
        'def get_signup_redirect_url(self, request):',
        'Returns the URL to redirect to after signing up.',
        70,
        'return "/welcome/"  # Custom welcome page'
    ),
    'get_logout_redirect_url': (
        'redirect',
        'def get_logout_redirect_url(self, request):',
        'Returns the URL to redirect to after logging out.',
        60,
        'return "/"  # Redirect to homepage'
    ),
    'get_email_verification_redirect_url': (
        'redirect',
        'def get_email_verification_redirect_url(self, email_address):',
        'Returns the URL to redirect to after email verification.',
        50,
        'return "/email-verified/"  # Custom confirmation page'
    ),
    'get_password_change_redirect_url': (
        'redirect',
        'def get_password_change_redirect_url(self, request):',
        'Returns the URL to redirect to after password change.',
        40,
        'return "/profile/"  # Go to profile after password change'
    ),

    # Email Customization (60%)
    'format_email_subject': (
        'email',
        'def format_email_subject(self, subject):',
        'Formats the subject line for outgoing emails.',
        60,
        'return f"[MyApp] {subject}"  # Custom email prefix'
    ),
    'get_from_email': (
        'email',
        'def get_from_email(self):',
        'Returns the "from" email address for outgoing emails.',
        55,
        'return "noreply@myapp.com"  # Custom from address'
    ),
    'render_mail': (
        'email',
        'def render_mail(self, template_prefix, email, context, headers=None):',
        'Renders an email message. Override to customize email rendering.',
        30,
        '# Add custom headers or modify email structure\nheaders = headers or {}\nheaders["X-App-ID"] = "myapp"\nreturn super().render_mail(template_prefix, email, context, headers)'
    ),
    'send_mail': (
        'email',
        'def send_mail(self, template_prefix: str, email: str, context: dict) -> None:',
        'Sends an email. Override to customize email delivery.',
        40,
        '# Add logging or custom email queue\nlogger.info(f"Sending {template_prefix} to {email}")\nsuper().send_mail(template_prefix, email, context)'
    ),
    'send_password_reset_mail': (
        'email',
        'def send_password_reset_mail(self, user, email, context):',
        'Sends the password reset email. Override to customize reset emails.',
        45,
        '# Only send to users with usable passwords\nif user.has_usable_password():\n    return super().send_password_reset_mail(user, email, context)'
    ),
    'send_confirmation_mail': (
        'email',
        'def send_confirmation_mail(self, request, emailconfirmation, signup):',
        'Sends email confirmation/verification mail.',
        50,
        '# Customize confirmation email context\nsuper().send_confirmation_mail(request, emailconfirmation, signup)'
    ),
    'send_account_already_exists_mail': (
        'email',
        'def send_account_already_exists_mail(self, email: str) -> None:',
        'Sends notification that account already exists (enumeration prevention).',
        25,
        '# Custom "account exists" message\nsuper().send_account_already_exists_mail(email)'
    ),
    'should_send_confirmation_mail': (
        'email',
        'def should_send_confirmation_mail(self, request, email_address, signup) -> bool:',
        'Determines whether to send a confirmation email.',
        35,
        '# Skip emails for internal domains\nif email_address.email.endswith("@company.com"):\n    return False\nreturn super().should_send_confirmation_mail(request, email_address, signup)'
    ),
    'send_notification_mail': (
        'email',
        'def send_notification_mail(self, template_prefix, user, context=None, email=None):',
        'Sends notification emails (e.g., password changed, email added).',
        30,
        '# Add custom notification logic\nsuper().send_notification_mail(template_prefix, user, context, email)'
    ),
    'get_email_confirmation_url': (
        'email',
        'def get_email_confirmation_url(self, request, emailconfirmation):',
        'Constructs the email confirmation URL.',
        40,
        '# Use custom frontend URL for SPA\nreturn f"https://myapp.com/verify/{emailconfirmation.key}"'
    ),
    'get_reset_password_from_key_url': (
        'email',
        'def get_reset_password_from_key_url(self, key):',
        'Returns the URL for the password reset form.',
        35,
        '# Custom password reset URL\nreturn f"https://myapp.com/reset-password/{key}"'
    ),

    # User Data Flow (40%)
    'new_user': (
        'user_data',
        'def new_user(self, request):',
        'Instantiates a new User instance.',
        40,
        '# Set default values for new users\nuser = super().new_user(request)\nuser.is_active = True\nreturn user'
    ),
    'populate_username': (
        'user_data',
        'def populate_username(self, request, user):',
        'Fills in a valid username if required and missing.',
        35,
        '# Custom username generation\nsuper().populate_username(request, user)'
    ),
    'save_user': (
        'user_data',
        'def save_user(self, request, user, form, commit=True):',
        'Saves a new User instance from signup form data.',
        45,
        '# Save extra profile fields\nuser = super().save_user(request, user, form, commit=False)\nuser.profile_type = form.cleaned_data.get("profile_type")\nif commit:\n    user.save()\nreturn user'
    ),
    'generate_unique_username': (
        'user_data',
        'def generate_unique_username(self, txts, regex=None):',
        'Generates a unique username from provided text options.',
        25,
        '# Custom username generation logic\nreturn super().generate_unique_username(txts, regex)'
    ),

    # Validation Hooks (40%)
    'clean_username': (
        'validation',
        'def clean_username(self, username, shallow=False):',
        'Validates and cleans username. Hook for custom username restrictions.',
        40,
        '# Block certain usernames\nif username.lower() in ["admin", "root", "system"]:\n    raise self.validation_error("username_blacklisted")\nreturn super().clean_username(username, shallow)'
    ),
    'clean_email': (
        'validation',
        'def clean_email(self, email: str) -> str:',
        'Validates and cleans email. Hook for custom email restrictions.',
        45,
        '# Block disposable email domains\nif email.split("@")[1] in ["tempmail.com", "throwaway.email"]:\n    raise forms.ValidationError("Disposable email addresses not allowed")\nreturn super().clean_email(email)'
    ),
    'clean_password': (
        'validation',
        'def clean_password(self, password, user=None):',
        'Validates password. Hook for custom password requirements.',
        35,
        '# Custom password validation\nif len(set(password)) < 6:\n    raise forms.ValidationError("Password must contain at least 6 unique characters")\nreturn super().clean_password(password, user)'
    ),
    'validate_unique_email': (
        'validation',
        'def validate_unique_email(self, email):',
        'Validates that email is unique. Hook for custom uniqueness checks.',
        30,
        '# Custom email uniqueness validation\nreturn super().validate_unique_email(email)'
    ),

    # Phone Verification (15%)
    'clean_phone': (
        'phone',
        'def clean_phone(self, phone: str) -> str:',
        'Validates and cleans phone number.',
        15,
        '# Normalize phone format\nimport phonenumbers\ntry:\n    parsed = phonenumbers.parse(phone, "US")\n    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)\nexcept:\n    raise forms.ValidationError("Invalid phone number")'
    ),
    'send_verification_code_sms': (
        'phone',
        'def send_verification_code_sms(self, user, phone: str, code: str, **kwargs):',
        'Sends SMS verification code. REQUIRED for phone number verification.',
        15,
        '# Integrate with SMS provider (Twilio, AWS SNS, etc.)\nfrom twilio.rest import Client\nclient = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)\nclient.messages.create(\n    to=phone,\n    from_=settings.TWILIO_FROM_NUMBER,\n    body=f"Your verification code is: {code}"\n)'
    ),
    'set_phone': (
        'phone',
        'def set_phone(self, user, phone: str, verified: bool):',
        'Sets phone number for user. REQUIRED for phone verification.',
        15,
        '# Store phone on user profile\nuser.profile.phone = phone\nuser.profile.phone_verified = verified\nuser.profile.save()'
    ),
    'get_phone': (
        'phone',
        'def get_phone(self, user):',
        'Gets phone number for user. Returns tuple (phone, verified). REQUIRED.',
        15,
        '# Retrieve phone from user profile\nif hasattr(user, "profile") and user.profile.phone:\n    return (user.profile.phone, user.profile.phone_verified)\nreturn None'
    ),
    'set_phone_verified': (
        'phone',
        'def set_phone_verified(self, user, phone: str):',
        'Marks phone number as verified. REQUIRED for phone verification.',
        15,
        '# Mark phone as verified\nuser.profile.phone_verified = True\nuser.profile.save()'
    ),
    'get_user_by_phone': (
        'phone',
        'def get_user_by_phone(self, phone: str):',
        'Looks up user by phone number. REQUIRED for phone verification.',
        15,
        '# Find user by phone\nfrom django.contrib.auth import get_user_model\nUser = get_user_model()\ntry:\n    profile = Profile.objects.get(phone=phone)\n    return profile.user\nexcept Profile.DoesNotExist:\n    return None'
    ),
    'generate_phone_verification_code': (
        'phone',
        'def generate_phone_verification_code(self, *, user, phone: str) -> str:',
        'Generates verification code for phone. Override for custom code generation.',
        10,
        '# Generate 6-digit code\nimport random\nreturn str(random.randint(100000, 999999))'
    ),

    # Auth Lifecycle (20%)
    'is_open_for_signup': (
        'lifecycle',
        'def is_open_for_signup(self, request):',
        'Controls whether signup is allowed. Return False to disable signups.',
        50,
        '# Disable signups during maintenance\nif settings.MAINTENANCE_MODE:\n    from allauth.exceptions import ImmediateHttpResponse\n    from django.shortcuts import redirect\n    raise ImmediateHttpResponse(redirect("/maintenance/"))\nreturn True'
    ),
    'pre_login': (
        'lifecycle',
        'def pre_login(self, request, user, *, email_verification, signal_kwargs, email, signup, redirect_url):',
        'Called before user is logged in. Can abort login by raising exception.',
        25,
        '# Enforce additional checks before login\nif not user.profile.terms_accepted:\n    from allauth.exceptions import ImmediateHttpResponse\n    from django.shortcuts import redirect\n    raise ImmediateHttpResponse(redirect("/accept-terms/"))\nreturn super().pre_login(request, user, email_verification=email_verification, signal_kwargs=signal_kwargs, email=email, signup=signup, redirect_url=redirect_url)'
    ),
    'post_login': (
        'lifecycle',
        'def post_login(self, request, user, *, email_verification, signal_kwargs, email, signup, redirect_url):',
        'Called after user is logged in. Customize post-login actions.',
        30,
        '# Log login activity\nimport logging\nlogger.info(f"User {user.id} logged in from {self.get_client_ip(request)}")\nreturn super().post_login(request, user, email_verification=email_verification, signal_kwargs=signal_kwargs, email=email, signup=signup, redirect_url=redirect_url)'
    ),
    'pre_authenticate': (
        'lifecycle',
        'def pre_authenticate(self, request, **credentials):',
        'Called before authentication. Handles rate limiting.',
        15,
        '# Custom pre-authentication logic\nsuper().pre_authenticate(request, **credentials)'
    ),
    'authenticate': (
        'lifecycle',
        'def authenticate(self, request, **credentials):',
        'Authenticates user with given credentials.',
        20,
        '# Custom authentication logic\nreturn super().authenticate(request, **credentials)'
    ),
    'authentication_failed': (
        'lifecycle',
        'def authentication_failed(self, request, **credentials):',
        'Called when authentication fails. Hook for logging or notifications.',
        15,
        '# Log failed authentication attempts\nimport logging\nlogger.warning(f"Failed login attempt: {credentials.get(\'email\', \'unknown\')}")'
    ),
    'confirm_email': (
        'lifecycle',
        'def confirm_email(self, request, email_address):',
        'Marks email as confirmed. Hook for custom confirmation logic.',
        25,
        '# Custom email confirmation logic\nresult = super().confirm_email(request, email_address)\n# Award bonus points for email verification\nif result:\n    email_address.user.profile.add_points(100)\nreturn result'
    ),
    'login': (
        'lifecycle',
        'def login(self, request, user):',
        'Performs the actual login. Override with caution.',
        10,
        '# Custom login logic (advanced)\nsuper().login(request, user)'
    ),
    'logout': (
        'lifecycle',
        'def logout(self, request):',
        'Performs the actual logout. Override to customize logout behavior.',
        10,
        '# Custom logout logic\nsuper().logout(request)\n# Clear custom session data\nrequest.session.flush()'
    ),
}

SOCIAL_ADAPTER_METHODS = {
    # Social Auth Flow (most common)
    'pre_social_login': (
        'social_flow',
        'def pre_social_login(self, request, sociallogin):',
        'Called after OAuth but BEFORE login. CRITICAL: Use to connect existing accounts or abort login.',
        90,
        '''# Connect to existing account if email matches
from allauth.account.models import EmailAddress
if sociallogin.is_existing:
    return
try:
    email = sociallogin.email_addresses[0].email
    existing_email = EmailAddress.objects.get(email__iexact=email, verified=True)
    # Connect the social account to existing user
    sociallogin.connect(request, existing_email.user)
except (IndexError, EmailAddress.DoesNotExist):
    pass'''
    ),
    'on_authentication_error': (
        'social_flow',
        'def on_authentication_error(self, request, provider, error=None, exception=None, extra_context=None):',
        'Called when OAuth authentication fails. Hook for error handling.',
        30,
        '# Log authentication errors\nimport logging\nlogger.error(f"OAuth error with {provider.name}: {error}")\n# Optionally redirect to custom error page\n# from allauth.exceptions import ImmediateHttpResponse\n# from django.shortcuts import redirect\n# raise ImmediateHttpResponse(redirect("/oauth-error/"))'
    ),
    'is_auto_signup_allowed': (
        'social_flow',
        'def is_auto_signup_allowed(self, request, sociallogin):',
        'Controls whether social login auto-creates accounts. Return False to require form.',
        60,
        '''# Require form for certain providers or conditions
if sociallogin.account.provider == "twitter":
    # Twitter doesn't always provide email
    return False
# Auto-signup only if email is verified
if sociallogin.email_addresses:
    return sociallogin.email_addresses[0].verified
return True'''
    ),
    'is_open_for_signup': (
        'social_flow',
        'def is_open_for_signup(self, request, sociallogin):',
        'Controls whether social signup is allowed.',
        40,
        '# Delegate to account adapter or add custom logic\nreturn get_account_adapter(request).is_open_for_signup(request)'
    ),

    # User Data
    'populate_user': (
        'user_data',
        'def populate_user(self, request, sociallogin, data):',
        'Extracts user data from OAuth provider data. Customize data extraction.',
        70,
        '''# Extract additional fields from provider data
user = super().populate_user(request, sociallogin, data)
# Map provider-specific fields
if sociallogin.account.provider == "github":
    user.profile.github_username = data.get("login")
    user.profile.bio = data.get("bio")
return user'''
    ),
    'save_user': (
        'user_data',
        'def save_user(self, request, sociallogin, form=None):',
        'Saves newly signed up social login user.',
        40,
        '# Custom save logic for social users\nuser = super().save_user(request, sociallogin, form)\n# Set user as active by default for social signups\nuser.is_active = True\nuser.save()\nreturn user'
    ),
    'new_user': (
        'user_data',
        'def new_user(self, request, sociallogin):',
        'Instantiates a new User for social login.',
        20,
        '# Delegate to account adapter\nreturn get_account_adapter().new_user(request)'
    ),
    'get_signup_form_initial_data': (
        'user_data',
        'def get_signup_form_initial_data(self, sociallogin):',
        'Provides initial data for signup form when auto-signup is disabled.',
        30,
        '# Add custom initial data\ninitial = super().get_signup_form_initial_data(sociallogin)\n# Add provider-specific data\nif sociallogin.account.provider == "google":\n    initial["preferred_language"] = "en"\nreturn initial'
    ),

    # Connection Management
    'get_connect_redirect_url': (
        'connection',
        'def get_connect_redirect_url(self, request, socialaccount):',
        'Returns URL to redirect after connecting a social account.',
        35,
        '# Custom redirect after social connection\nreturn "/profile/connected/"'
    ),
    'validate_disconnect': (
        'connection',
        'def validate_disconnect(self, account, accounts) -> None:',
        'Validates whether social account can be disconnected. Raise error to prevent.',
        25,
        '''# Prevent disconnecting if no password set
from django.core.exceptions import ValidationError
if not account.user.has_usable_password():
    if len(accounts) == 1:
        raise ValidationError("Cannot disconnect your only login method. Set a password first.")'''
    ),

    # Email Verification
    'is_email_verified': (
        'email',
        'def is_email_verified(self, provider, email):',
        'Determines if email from provider should be trusted as verified.',
        40,
        '''# Trust emails from certain providers
trusted_providers = ["google", "github", "microsoft"]
if provider.id in trusted_providers:
    return True
# Check domain-specific rules
if email.endswith("@company.com"):
    return True
return False'''
    ),
    'can_authenticate_by_email': (
        'email',
        'def can_authenticate_by_email(self, login, email):',
        'Controls whether social login can authenticate by matching email.',
        30,
        '''# WARNING: Security sensitive! Disable for untrusted providers
# Only allow for verified email providers
if login.provider.id in ["google", "github"]:
    return True
return False'''
    ),
}

CATEGORY_INFO = {
    'redirect': {
        'name': 'Redirect URLs',
        'description': 'Control where users are redirected after various actions',
        'popularity': 80,
        'account': True,
        'social': False,
    },
    'email': {
        'name': 'Email Customization',
        'description': 'Customize email sending, formatting, and verification',
        'popularity': 60,
        'account': True,
        'social': True,
    },
    'user_data': {
        'name': 'User Data Flow',
        'description': 'Control user creation, data extraction, and saving',
        'popularity': 40,
        'account': True,
        'social': True,
    },
    'validation': {
        'name': 'Validation Hooks',
        'description': 'Add custom validation for usernames, emails, passwords',
        'popularity': 40,
        'account': True,
        'social': False,
    },
    'phone': {
        'name': 'Phone Verification',
        'description': 'Implement phone number verification (SMS integration required)',
        'popularity': 15,
        'account': True,
        'social': False,
    },
    'lifecycle': {
        'name': 'Auth Lifecycle',
        'description': 'Control login/logout flow, authentication, and pre/post hooks',
        'popularity': 20,
        'account': True,
        'social': False,
    },
    'social_flow': {
        'name': 'Social Auth Flow',
        'description': 'Control OAuth flow, account linking, and auto-signup',
        'popularity': 70,
        'account': False,
        'social': True,
    },
    'connection': {
        'name': 'Connection Management',
        'description': 'Handle social account connections and disconnections',
        'popularity': 30,
        'account': False,
        'social': True,
    },
}

TEMPLATES = {
    'redirect': {
        'name': 'Redirect URLs Template',
        'description': 'All redirect methods for customizing navigation flow',
        'account_methods': ['get_login_redirect_url', 'get_signup_redirect_url',
                           'get_logout_redirect_url', 'get_email_verification_redirect_url',
                           'get_password_change_redirect_url'],
        'social_methods': ['get_connect_redirect_url'],
    },
    'email': {
        'name': 'Email Customization Template',
        'description': 'All email-related methods for customizing email behavior',
        'account_methods': ['format_email_subject', 'get_from_email', 'send_mail',
                           'send_confirmation_mail', 'get_email_confirmation_url'],
        'social_methods': ['is_email_verified'],
    },
    'social': {
        'name': 'Social Account Linking Template',
        'description': 'Essential methods for handling social authentication',
        'account_methods': [],
        'social_methods': ['pre_social_login', 'populate_user', 'is_auto_signup_allowed'],
    },
    'validation': {
        'name': 'Validation Template',
        'description': 'All validation methods for custom rules',
        'account_methods': ['clean_username', 'clean_email', 'clean_password', 'validate_unique_email'],
        'social_methods': [],
    },
    'full': {
        'name': 'Complete Template',
        'description': 'All available methods (for reference)',
        'account_methods': list(ACCOUNT_ADAPTER_METHODS.keys()),
        'social_methods': list(SOCIAL_ADAPTER_METHODS.keys()),
    },
}


def print_header():
    """Print script header."""
    print("\n" + "=" * 70)
    print(colorize("  Django-AllAuth Adapter Generator", Colors.HEADER + Colors.BOLD))
    print("=" * 70)
    print()


def print_categories(adapter_type: str):
    """Print available categories for selection."""
    print(colorize("\nAvailable Method Categories:", Colors.BOLD))
    print()

    categories = []
    for cat_id, cat_info in CATEGORY_INFO.items():
        if adapter_type == 'account' and cat_info['account']:
            categories.append((cat_id, cat_info))
        elif adapter_type == 'social' and cat_info['social']:
            categories.append((cat_id, cat_info))

    for i, (cat_id, cat_info) in enumerate(categories, 1):
        popularity_bar = "█" * (cat_info['popularity'] // 10)
        print(f"  {colorize(f'[{i}]', Colors.CYAN)} {colorize(cat_info['name'], Colors.BOLD)}")
        print(f"      {cat_info['description']}")
        print(f"      Usage: {popularity_bar} {cat_info['popularity']}%")
        print()

    return [cat_id for cat_id, _ in categories]


def print_methods_in_category(methods_dict: Dict, category: str):
    """Print methods in a specific category."""
    methods = [(name, data) for name, data in methods_dict.items()
               if data[0] == category]

    if not methods:
        return []

    cat_info = CATEGORY_INFO[category]
    print(f"\n{colorize(cat_info['name'], Colors.BOLD + Colors.UNDERLINE)}")
    print(f"{cat_info['description']}\n")

    for i, (name, data) in enumerate(methods, 1):
        _, signature, description, popularity, _ = data
        print(f"  {colorize(f'[{i}]', Colors.GREEN)} {colorize(name, Colors.BOLD)}")
        print(f"      {description}")
        print(f"      Usage: {popularity}%")
        print()

    return [name for name, _ in methods]


def interactive_adapter_type() -> str:
    """Ask user to select adapter type."""
    print(colorize("\nSelect Adapter Type:", Colors.BOLD))
    print(f"  {colorize('[1]', Colors.CYAN)} Account Adapter (DefaultAccountAdapter)")
    print(f"      → Customize authentication, email, redirects, validation")
    print(f"  {colorize('[2]', Colors.CYAN)} Social Account Adapter (DefaultSocialAccountAdapter)")
    print(f"      → Customize OAuth flow, account linking, provider integration")
    print(f"  {colorize('[3]', Colors.CYAN)} Both")
    print(f"      → Generate both adapters in the same file")
    print()

    while True:
        choice = input(colorize("Your choice [1-3]: ", Colors.BOLD)).strip()
        if choice == '1':
            return 'account'
        elif choice == '2':
            return 'social'
        elif choice == '3':
            return 'both'
        print(colorize("Invalid choice. Please enter 1, 2, or 3.", Colors.RED))


def interactive_category_selection(adapter_type: str) -> List[str]:
    """Ask user to select categories."""
    categories = print_categories(adapter_type)

    print(colorize("\nSelect Categories (comma-separated numbers, or 'all'):", Colors.BOLD))
    print(colorize("Example: 1,2,4 or just press Enter to select manually", Colors.CYAN))

    choice = input(colorize("Your choice: ", Colors.BOLD)).strip().lower()

    if choice == 'all':
        return categories
    elif choice == '':
        return []
    else:
        try:
            indices = [int(x.strip()) for x in choice.split(',')]
            selected = [categories[i-1] for i in indices if 0 < i <= len(categories)]
            return selected
        except (ValueError, IndexError):
            print(colorize("Invalid input. Proceeding to method selection...", Colors.YELLOW))
            return []


def interactive_method_selection(adapter_type: str, categories: List[str]) -> Tuple[List[str], List[str]]:
    """Ask user to select specific methods."""
    account_methods = []
    social_methods = []

    if adapter_type in ['account', 'both']:
        print(colorize("\n" + "="*70, Colors.BLUE))
        print(colorize("ACCOUNT ADAPTER METHODS", Colors.BOLD))
        print(colorize("="*70, Colors.BLUE))

        if categories:
            for category in categories:
                if CATEGORY_INFO[category].get('account', False):
                    methods = print_methods_in_category(ACCOUNT_ADAPTER_METHODS, category)
                    print(colorize(f"\nSelect methods from {CATEGORY_INFO[category]['name']} (comma-separated, 'all', or Enter to skip):", Colors.BOLD))
                    choice = input(colorize("Your choice: ", Colors.BOLD)).strip().lower()

                    if choice == 'all':
                        account_methods.extend(methods)
                    elif choice:
                        try:
                            indices = [int(x.strip()) for x in choice.split(',')]
                            account_methods.extend([methods[i-1] for i in indices if 0 < i <= len(methods)])
                        except (ValueError, IndexError):
                            print(colorize("Invalid input. Skipping category.", Colors.YELLOW))

    if adapter_type in ['social', 'both']:
        print(colorize("\n" + "="*70, Colors.BLUE))
        print(colorize("SOCIAL ADAPTER METHODS", Colors.BOLD))
        print(colorize("="*70, Colors.BLUE))

        if categories:
            for category in categories:
                if CATEGORY_INFO[category].get('social', False):
                    methods = print_methods_in_category(SOCIAL_ADAPTER_METHODS, category)
                    print(colorize(f"\nSelect methods from {CATEGORY_INFO[category]['name']} (comma-separated, 'all', or Enter to skip):", Colors.BOLD))
                    choice = input(colorize("Your choice: ", Colors.BOLD)).strip().lower()

                    if choice == 'all':
                        social_methods.extend(methods)
                    elif choice:
                        try:
                            indices = [int(x.strip()) for x in choice.split(',')]
                            social_methods.extend([methods[i-1] for i in indices if 0 < i <= len(methods)])
                        except (ValueError, IndexError):
                            print(colorize("Invalid input. Skipping category.", Colors.YELLOW))

    return account_methods, social_methods


def apply_template(template_name: str, adapter_type: str) -> Tuple[List[str], List[str]]:
    """Apply a predefined template."""
    if template_name not in TEMPLATES:
        print(colorize(f"Unknown template: {template_name}", Colors.RED))
        print(f"Available templates: {', '.join(TEMPLATES.keys())}")
        sys.exit(1)

    template = TEMPLATES[template_name]
    print(colorize(f"\nApplying template: {template['name']}", Colors.GREEN))
    print(f"Description: {template['description']}\n")

    account_methods = template['account_methods'] if adapter_type in ['account', 'both'] else []
    social_methods = template['social_methods'] if adapter_type in ['social', 'both'] else []

    return account_methods, social_methods


def generate_adapter_code(adapter_type: str,
                          account_methods: List[str],
                          social_methods: List[str],
                          app_name: str = "myapp") -> str:
    """Generate the adapter code."""
    code = []

    # Header
    code.append('"""')
    code.append('Custom Adapters for django-allauth')
    code.append('')
    code.append('Generated by Django-AllAuth Adapter Generator')
    code.append('Customize the methods below according to your needs.')
    code.append('"""')
    code.append('')

    # Imports
    code.append('from django.conf import settings')
    code.append('from django.shortcuts import resolve_url')
    code.append('')

    if adapter_type in ['account', 'both']:
        code.append('from allauth.account.adapter import DefaultAccountAdapter')

    if adapter_type in ['social', 'both']:
        code.append('from allauth.socialaccount.adapter import DefaultSocialAccountAdapter')
        if adapter_type == 'social' and 'pre_social_login' in social_methods:
            code.append('from allauth.account.models import EmailAddress')

    code.append('')
    code.append('')

    # Account Adapter
    if adapter_type in ['account', 'both'] and account_methods:
        code.append('class CustomAccountAdapter(DefaultAccountAdapter):')
        code.append('    """')
        code.append('    Custom Account Adapter')
        code.append('    ')
        code.append('    Override methods to customize allauth account behavior.')
        code.append('    Methods included:')
        for method in account_methods:
            category, _, description, _, _ = ACCOUNT_ADAPTER_METHODS[method]
            code.append(f'    - {method}: {description}')
        code.append('    """')
        code.append('')

        for method_name in account_methods:
            category, signature, description, popularity, example = ACCOUNT_ADAPTER_METHODS[method_name]

            code.append(f'    # {CATEGORY_INFO[category]["name"]}: {description}')
            code.append(f'    # Usage: {popularity}% of projects override this method')
            code.append(f'    {signature}')
            code.append('        """')
            code.append(f'        {description}')
            code.append('        ')
            code.append('        TODO: Implement your custom logic here.')
            code.append('        """')
            code.append('        # Example implementation:')
            for line in example.split('\n'):
                code.append(f'        # {line}')
            code.append('        ')
            code.append(f'        # Default behavior:')
            code.append(f'        return super().{method_name}({_get_method_params(signature)})')
            code.append('')

        code.append('')

    # Social Account Adapter
    if adapter_type in ['social', 'both'] and social_methods:
        code.append('class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):')
        code.append('    """')
        code.append('    Custom Social Account Adapter')
        code.append('    ')
        code.append('    Override methods to customize OAuth/social authentication behavior.')
        code.append('    Methods included:')
        for method in social_methods:
            category, _, description, _, _ = SOCIAL_ADAPTER_METHODS[method]
            code.append(f'    - {method}: {description}')
        code.append('    """')
        code.append('')

        for method_name in social_methods:
            category, signature, description, popularity, example = SOCIAL_ADAPTER_METHODS[method_name]

            code.append(f'    # {CATEGORY_INFO[category]["name"]}: {description}')
            code.append(f'    # Usage: {popularity}% of projects override this method')
            code.append(f'    {signature}')
            code.append('        """')
            code.append(f'        {description}')
            code.append('        ')
            code.append('        TODO: Implement your custom logic here.')
            code.append('        """')
            code.append('        # Example implementation:')
            for line in example.split('\n'):
                code.append(f'        # {line}')
            code.append('        ')
            if method_name not in ['pre_social_login', 'on_authentication_error', 'validate_disconnect']:
                code.append(f'        # Default behavior:')
                code.append(f'        return super().{method_name}({_get_method_params(signature)})')
            code.append('')

        code.append('')

    return '\n'.join(code)


def _get_method_params(signature: str) -> str:
    """Extract parameter names from method signature for super() call."""
    # Extract parameters from "def method(self, param1, param2):"
    params_part = signature.split('(', 1)[1].rsplit(')', 1)[0]
    params = [p.strip().split('=')[0].split(':')[0].strip()
              for p in params_part.split(',') if p.strip() not in ['self', '']]

    # Filter out bare '*' (keyword-only separator) but keep **kwargs and *args
    filtered_params = []
    for p in params:
        if p == '*':
            continue  # Skip bare * separator
        elif p.startswith('**'):
            filtered_params.append(p)
        elif p.startswith('*'):
            filtered_params.append(p)
        elif p:
            filtered_params.append(f'{p}={p}')

    return ', '.join(filtered_params)


def generate_settings_snippet(adapter_type: str, app_name: str) -> str:
    """Generate settings configuration snippet."""
    snippet = ['\n# Add to your Django settings.py:\n']

    if adapter_type in ['account', 'both']:
        snippet.append(f"ACCOUNT_ADAPTER = '{app_name}.adapters.CustomAccountAdapter'")

    if adapter_type in ['social', 'both']:
        snippet.append(f"SOCIALACCOUNT_ADAPTER = '{app_name}.adapters.CustomSocialAccountAdapter'")

    return '\n'.join(snippet)


def write_output(code: str, settings_snippet: str, output_path: str = None):
    """Write generated code to file or stdout."""
    if output_path:
        # Ensure directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        with open(output_path, 'w') as f:
            f.write(code)

        print(colorize(f"\n✓ Adapter code written to: {output_path}", Colors.GREEN + Colors.BOLD))
        print(colorize(f"\n{settings_snippet}", Colors.CYAN))
        print(colorize(f"\n✓ Don't forget to add the settings configuration above!", Colors.YELLOW + Colors.BOLD))
    else:
        print(colorize("\n" + "="*70, Colors.GREEN))
        print(colorize("GENERATED ADAPTER CODE", Colors.BOLD))
        print(colorize("="*70 + "\n", Colors.GREEN))
        print(code)
        print(colorize("\n" + "="*70, Colors.CYAN))
        print(colorize("SETTINGS CONFIGURATION", Colors.BOLD))
        print(colorize("="*70, Colors.CYAN))
        print(settings_snippet)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate custom adapters for django-allauth',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python generate_adapter.py

  # Use redirect template for account adapter
  python generate_adapter.py --template redirect --adapter account

  # Generate both adapters with social template
  python generate_adapter.py --template social --adapter both

  # Save to specific file
  python generate_adapter.py --template email --output myapp/adapters.py

  # Generate full reference (all methods)
  python generate_adapter.py --template full

Available templates: redirect, email, social, validation, full
        """
    )

    parser.add_argument(
        '--adapter',
        choices=['account', 'social', 'both'],
        help='Adapter type to generate'
    )

    parser.add_argument(
        '--template',
        choices=list(TEMPLATES.keys()),
        help='Use a predefined template'
    )

    parser.add_argument(
        '--output',
        help='Output file path (default: print to stdout)'
    )

    parser.add_argument(
        '--app',
        default='myapp',
        help='Django app name for settings snippet (default: myapp)'
    )

    args = parser.parse_args()

    # Print header unless using template
    if not args.template:
        print_header()

    # Determine adapter type
    if args.adapter:
        adapter_type = args.adapter
    elif args.template:
        adapter_type = 'both'  # Templates can apply to both
    else:
        adapter_type = interactive_adapter_type()

    # Determine methods to include
    if args.template:
        account_methods, social_methods = apply_template(args.template, adapter_type)
    else:
        # Interactive mode
        print(colorize("\n" + "="*70, Colors.BLUE))
        print(colorize("METHOD SELECTION", Colors.BOLD))
        print(colorize("="*70, Colors.BLUE))

        categories = interactive_category_selection(adapter_type)

        if categories:
            account_methods, social_methods = interactive_method_selection(adapter_type, categories)
        else:
            print(colorize("\nNo categories selected. You can still select individual methods.", Colors.YELLOW))
            account_methods, social_methods = [], []

    # Ensure we have something to generate
    if not account_methods and not social_methods:
        print(colorize("\nNo methods selected. Exiting.", Colors.YELLOW))
        sys.exit(0)

    # Generate code
    print(colorize("\n" + "="*70, Colors.GREEN))
    print(colorize("GENERATING CODE...", Colors.BOLD))
    print(colorize("="*70, Colors.GREEN))

    code = generate_adapter_code(adapter_type, account_methods, social_methods, args.app)
    settings_snippet = generate_settings_snippet(adapter_type, args.app)

    # Write output
    write_output(code, settings_snippet, args.output)

    # Final message
    print(colorize("\n" + "="*70, Colors.GREEN))
    print(colorize("✓ Generation Complete!", Colors.BOLD + Colors.GREEN))
    print(colorize("="*70, Colors.GREEN))
    print(colorize("\nNext steps:", Colors.BOLD))
    print("  1. Review the generated code")
    print("  2. Uncomment and customize the example implementations")
    print("  3. Add the settings configuration to your settings.py")
    print("  4. Test your custom adapter behavior")
    print(colorize("\nDocumentation: https://docs.allauth.org/en/latest/account/advanced.html#adapter", Colors.CYAN))


if __name__ == '__main__':
    main()
