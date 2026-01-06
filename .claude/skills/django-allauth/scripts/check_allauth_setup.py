#!/usr/bin/env python
"""
Django-allauth Setup Verification Script

Verifies common django-allauth installation issues and optionally auto-fixes them.

Usage:
    python check_allauth_setup.py           # Check only
    python check_allauth_setup.py --fix     # Check and auto-fix

Exit Codes:
    0 - All checks passed
    1 - Some checks failed
    2 - Critical error (Django not loaded)
"""

import sys
import os
import argparse
from pathlib import Path

# Output symbols
OK = "✓"
FAIL = "✗"
WARN = "⚠"


def print_result(name, passed, message="", warning=False, fixed=False):
    """Print a single check result."""
    symbol = OK if passed else (WARN if warning else FAIL)
    status = "PASS" if passed else ("WARN" if warning else "FAIL")
    print(f"{symbol} {status}: {name}")
    if message:
        print(f"  {message}")
    if fixed:
        print("  [FIX APPLIED]")
    print()
    return 1 if passed else (0.5 if warning else 0)


def initialize_django():
    """Initialize Django environment and return settings."""
    print("=" * 60)
    print("Django-allauth Setup Verification")
    print("=" * 60 + "\n")

    try:
        import django
        from django.conf import settings

        if not settings.configured:
            if 'DJANGO_SETTINGS_MODULE' not in os.environ:
                if Path('manage.py').exists():
                    import re
                    with open('manage.py', 'r') as f:
                        match = re.search(r'DJANGO_SETTINGS_MODULE["\']?\s*,\s*["\']([^"\']+)', f.read())
                        if match:
                            os.environ.setdefault('DJANGO_SETTINGS_MODULE', match.group(1))

                if 'DJANGO_SETTINGS_MODULE' not in os.environ:
                    raise Exception("Cannot find Django settings. Set DJANGO_SETTINGS_MODULE or run from project directory.")

            django.setup()

        print(f"{OK} Django {django.get_version()} initialized")
        print(f"  Settings: {os.environ.get('DJANGO_SETTINGS_MODULE', 'N/A')}\n")
        return settings

    except ImportError:
        print(f"{FAIL} Django not installed. Run: pip install django")
        return None
    except Exception as e:
        print(f"{FAIL} Django init failed: {e}")
        return None


def check_python_version():
    """Check Python version."""
    major, minor = sys.version_info[:2]
    return print_result(
        "Python Version",
        major >= 3 and minor >= 8,
        f"Python {major}.{minor} ({'OK' if minor >= 8 else 'requires 3.8+'})"
    )


def check_django_version():
    """Check Django version."""
    import django
    version = django.VERSION[:2]
    return print_result(
        "Django Version",
        version >= (3, 2),
        f"Django {django.get_version()} ({'OK' if version >= (3, 2) else 'requires 3.2+'})"
    )


def check_installed_apps(settings):
    """Check INSTALLED_APPS configuration."""
    apps = list(settings.INSTALLED_APPS)
    required = ['django.contrib.auth', 'django.contrib.messages', 'django.contrib.sites', 'allauth', 'allauth.account']
    missing = [app for app in required if app not in apps]

    if missing:
        return print_result("INSTALLED_APPS", False, f"Missing: {', '.join(missing)}")

    # Check order
    django_idx = max([apps.index(a) for a in apps if a.startswith('django.contrib.')], default=-1)
    allauth_apps = [a for a in ['allauth', 'allauth.account', 'allauth.socialaccount'] if a in apps]
    order_ok = all(apps.index(a) > django_idx for a in allauth_apps)

    if not order_ok:
        return print_result("INSTALLED_APPS", False, "allauth apps should come after django.contrib apps", warning=True)

    optional = [a for a in ['allauth.socialaccount', 'allauth.mfa', 'allauth.headless'] if a in apps]
    msg = f"Required apps present" + (f" + {', '.join(optional)}" if optional else "")
    return print_result("INSTALLED_APPS", True, msg)


def check_middleware(settings):
    """Check MIDDLEWARE configuration."""
    middleware = list(getattr(settings, 'MIDDLEWARE', []))
    required = [
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'allauth.account.middleware.AccountMiddleware',
    ]
    missing = [mw for mw in required if mw not in middleware]

    if missing:
        msg = f"Missing: {', '.join([m.split('.')[-1] for m in missing])}"
        if 'allauth.account.middleware.AccountMiddleware' in missing:
            msg += " (AccountMiddleware required in allauth 0.57+)"
        return print_result("MIDDLEWARE", False, msg)

    return print_result("MIDDLEWARE", True, "Required middleware present")


def check_auth_backends(settings):
    """Check AUTHENTICATION_BACKENDS configuration."""
    backends = list(getattr(settings, 'AUTHENTICATION_BACKENDS', []))
    required = ['django.contrib.auth.backends.ModelBackend', 'allauth.account.auth_backends.AuthenticationBackend']
    missing = [b for b in required if b not in backends]

    if missing:
        return print_result("AUTHENTICATION_BACKENDS", False, f"Missing: {', '.join([b.split('.')[-1] for b in missing])}")
    return print_result("AUTHENTICATION_BACKENDS", True, "Backends configured")


def check_session_engine(settings):
    """Check SESSION_ENGINE - signed_cookies breaks verification codes."""
    engine = getattr(settings, 'SESSION_ENGINE', 'django.contrib.sessions.backends.db')

    if 'signed_cookies' in engine:
        return print_result(
            "SESSION_ENGINE", False,
            "signed_cookies loses verification codes! Use 'db' or 'cached_db'"
        )
    return print_result("SESSION_ENGINE", True, engine.split('.')[-1])


def check_email_backend(settings):
    """Check EMAIL_BACKEND configuration."""
    backend = getattr(settings, 'EMAIL_BACKEND', None)

    if not backend:
        return print_result("EMAIL_BACKEND", False, "Not configured - emails will fail silently")
    if 'dummy' in backend.lower():
        return print_result("EMAIL_BACKEND", False, "Dummy backend - emails discarded", warning=True)
    if 'console' in backend.lower():
        return print_result("EMAIL_BACKEND", True, "Console backend (dev only)", warning=True)
    return print_result("EMAIL_BACKEND", True, backend.split('.')[-1])


def check_templates(settings):
    """Check TEMPLATES context processors."""
    templates = getattr(settings, 'TEMPLATES', [])
    if not templates:
        return print_result("TEMPLATES", False, "Not configured")

    required = ['django.template.context_processors.request']

    for config in templates:
        if config.get('BACKEND') == 'django.template.backends.django.DjangoTemplates':
            processors = config.get('OPTIONS', {}).get('context_processors', [])
            missing = [p for p in required if p not in processors]
            if missing:
                return print_result("TEMPLATES", False, "Missing 'request' context processor")
            return print_result("TEMPLATES", True, "Context processors OK")

    return print_result("TEMPLATES", False, "DjangoTemplates backend not found")


def check_site_id(settings, fix=False):
    """Check SITE_ID and Sites framework."""
    site_id = getattr(settings, 'SITE_ID', None)

    if site_id is None:
        return print_result("SITE_ID", False, "Not configured (required for email verification links)")

    try:
        from django.contrib.sites.models import Site
        try:
            site = Site.objects.get(pk=site_id)
            return print_result("Sites Framework", True, f"SITE_ID={site_id}, domain={site.domain}")
        except Site.DoesNotExist:
            if fix:
                try:
                    site = Site.objects.create(pk=site_id, domain='localhost:8000', name='Development')
                    return print_result("Sites Framework", True, f"Created Site: {site.domain}", fixed=True)
                except Exception as e:
                    return print_result("Sites Framework", False, f"Auto-fix failed: {e}")
            return print_result("Sites Framework", False, f"SITE_ID={site_id} but Site doesn't exist (use --fix)")
    except Exception as e:
        return print_result("Sites Framework", False, f"Error: {e}")


def check_migrations():
    """Check for unapplied allauth migrations."""
    try:
        from django.core.management import call_command
        from io import StringIO

        out = StringIO()
        call_command('showmigrations', '--plan', stdout=out, no_color=True)

        unapplied = [line for line in out.getvalue().split('\n') if '[ ]' in line and 'allauth' in line.lower()]

        if unapplied:
            return print_result("Migrations", False, f"{len(unapplied)} unapplied allauth migrations. Run: manage.py migrate")
        return print_result("Migrations", True, "All allauth migrations applied")
    except Exception as e:
        return print_result("Migrations", False, f"Check failed: {e}", warning=True)


def main():
    parser = argparse.ArgumentParser(description='Verify django-allauth installation')
    parser.add_argument('--fix', action='store_true', help='Auto-fix common issues')
    args = parser.parse_args()

    settings = initialize_django()
    if not settings:
        return 2

    # Run checks
    scores = []
    scores.append(check_python_version())
    scores.append(check_django_version())
    scores.append(check_installed_apps(settings))
    scores.append(check_middleware(settings))
    scores.append(check_auth_backends(settings))
    scores.append(check_session_engine(settings))
    scores.append(check_email_backend(settings))
    scores.append(check_templates(settings))
    scores.append(check_site_id(settings, fix=args.fix))
    scores.append(check_migrations())

    # Summary
    print("=" * 60)
    passed = sum(1 for s in scores if s == 1)
    warnings = sum(1 for s in scores if s == 0.5)
    failed = sum(1 for s in scores if s == 0)

    print(f"{OK} Passed: {passed}" + (f"  {WARN} Warnings: {warnings}" if warnings else "") + (f"  {FAIL} Failed: {failed}" if failed else ""))

    if failed:
        print("\n⚠ Fix the issues above. Use --fix for auto-fixes.")
        return 1
    elif warnings:
        print("\n⚠ All critical checks passed with warnings.")
    else:
        print("\n✓ django-allauth setup looks good!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
