#!/usr/bin/env python
"""
Django-allauth Setup Verification Script

This script verifies and optionally auto-fixes common django-allauth installation issues.

Usage:
    python check_allauth_setup.py                 # Check only (read-only)
    python check_allauth_setup.py --fix          # Check and auto-fix issues
    python check_allauth_setup.py --verbose      # Detailed output
    python check_allauth_setup.py --fix --verbose # Fix with details

Requirements:
    - Must be run from a Django project directory (where manage.py is located)
    - Django settings must be properly configured

Exit Codes:
    0 - All checks passed
    1 - Some checks failed (configuration issues found)
    2 - Critical error (unable to load Django, etc.)
"""

import sys
import os
import argparse
from pathlib import Path


# Symbols for output
CHECK_MARK = "✓"
CROSS_MARK = "✗"
WARNING = "⚠"


class CheckResult:
    """Represents the result of a single check."""

    def __init__(self, name, passed=False, warning=False, message="", fix_applied=False):
        self.name = name
        self.passed = passed
        self.warning = warning
        self.message = message
        self.fix_applied = fix_applied

    def __str__(self):
        if self.passed:
            symbol = CHECK_MARK
            status = "PASS"
        elif self.warning:
            symbol = WARNING
            status = "WARN"
        else:
            symbol = CROSS_MARK
            status = "FAIL"

        result = f"{symbol} {status}: {self.name}"
        if self.message:
            result += f"\n  {self.message}"
        if self.fix_applied:
            result += "\n  [FIX APPLIED]"

        return result


class AllauthSetupChecker:
    """Main checker class for django-allauth setup verification."""

    def __init__(self, fix=False, verbose=False):
        self.fix = fix
        self.verbose = verbose
        self.results = []
        self.settings = None
        self.settings_file_path = None

    def log_verbose(self, message):
        """Print message only in verbose mode."""
        if self.verbose:
            print(f"  [VERBOSE] {message}")

    def add_result(self, result):
        """Add a check result."""
        self.results.append(result)
        print(result)
        print()  # Blank line for readability

    def initialize_django(self):
        """Initialize Django environment."""
        print("=" * 70)
        print("Django-allauth Setup Verification")
        print("=" * 70)
        print()

        try:
            import django
            from django.conf import settings

            # Try to setup Django if not already configured
            if not settings.configured:
                # Look for Django settings module
                if 'DJANGO_SETTINGS_MODULE' not in os.environ:
                    # Try to find settings.py in current directory
                    if Path('manage.py').exists():
                        # Try to extract settings module from manage.py
                        with open('manage.py', 'r') as f:
                            content = f.read()
                            if 'DJANGO_SETTINGS_MODULE' in content:
                                import re
                                match = re.search(r'DJANGO_SETTINGS_MODULE["\']?\s*,\s*["\']([^"\']+)', content)
                                if match:
                                    os.environ.setdefault('DJANGO_SETTINGS_MODULE', match.group(1))

                if 'DJANGO_SETTINGS_MODULE' not in os.environ:
                    raise Exception(
                        "Cannot find Django settings. Please run this script from your Django project "
                        "directory or set DJANGO_SETTINGS_MODULE environment variable."
                    )

                django.setup()

            self.settings = settings
            self.find_settings_file()

            print(f"{CHECK_MARK} Django initialized successfully")
            print(f"  Django version: {django.get_version()}")
            print(f"  Settings module: {os.environ.get('DJANGO_SETTINGS_MODULE', 'N/A')}")
            if self.settings_file_path:
                print(f"  Settings file: {self.settings_file_path}")
            print()

            return True

        except ImportError:
            print(f"{CROSS_MARK} Django is not installed")
            print("  Install Django: pip install django")
            return False
        except Exception as e:
            print(f"{CROSS_MARK} Failed to initialize Django: {e}")
            return False

    def find_settings_file(self):
        """Attempt to find the settings.py file for auto-fixing."""
        settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', '')
        if settings_module:
            # Convert module path to file path
            module_path = settings_module.replace('.', '/')
            possible_paths = [
                f"{module_path}.py",
                f"{module_path}/__init__.py",
            ]

            for path in possible_paths:
                if Path(path).exists():
                    self.settings_file_path = Path(path).absolute()
                    self.log_verbose(f"Found settings file: {self.settings_file_path}")
                    return

        self.log_verbose("Could not locate settings file for auto-fixing")

    def check_python_version(self):
        """Check Python version compatibility."""
        major, minor = sys.version_info[:2]
        required_major, required_minor = 3, 8

        if major > required_major or (major == required_major and minor >= required_minor):
            self.add_result(CheckResult(
                "Python Version",
                passed=True,
                message=f"Python {major}.{minor} (requires 3.8+)"
            ))
        else:
            self.add_result(CheckResult(
                "Python Version",
                passed=False,
                message=f"Python {major}.{minor} found, but 3.8+ is required for django-allauth"
            ))

    def check_django_version(self):
        """Check Django version compatibility."""
        import django
        version_tuple = django.VERSION[:2]

        if version_tuple >= (3, 2):
            self.add_result(CheckResult(
                "Django Version",
                passed=True,
                message=f"Django {django.get_version()} (requires 3.2+)"
            ))
        else:
            self.add_result(CheckResult(
                "Django Version",
                passed=False,
                message=f"Django {django.get_version()} found, but 3.2+ is required"
            ))

    def check_installed_apps(self):
        """Check INSTALLED_APPS configuration."""
        installed_apps = list(self.settings.INSTALLED_APPS)

        required_apps = [
            'django.contrib.auth',
            'django.contrib.messages',
            'django.contrib.sites',
            'allauth',
            'allauth.account',
        ]

        optional_apps = [
            'allauth.socialaccount',
            'allauth.mfa',
            'allauth.usersessions',
            'allauth.headless',
        ]

        missing_required = [app for app in required_apps if app not in installed_apps]
        present_optional = [app for app in optional_apps if app in installed_apps]

        # Check order (allauth apps should come after django.contrib apps)
        order_issues = []
        django_contrib_index = max(
            [installed_apps.index(app) for app in installed_apps if app.startswith('django.contrib.')],
            default=-1
        )

        for app in ['allauth', 'allauth.account', 'allauth.socialaccount']:
            if app in installed_apps:
                app_index = installed_apps.index(app)
                if app_index < django_contrib_index:
                    order_issues.append(f"{app} should come after django.contrib apps")

        if missing_required:
            message = f"Missing required apps: {', '.join(missing_required)}"
            if self.fix and self.settings_file_path:
                message += "\n  Auto-fix not implemented for INSTALLED_APPS (manual edit required)"
            self.add_result(CheckResult("INSTALLED_APPS", passed=False, message=message))
        elif order_issues:
            self.add_result(CheckResult(
                "INSTALLED_APPS Order",
                passed=False,
                warning=True,
                message="\n  ".join(order_issues)
            ))
        else:
            message = f"All required apps present: {', '.join(required_apps)}"
            if present_optional:
                message += f"\n  Optional apps: {', '.join(present_optional)}"
            self.add_result(CheckResult("INSTALLED_APPS", passed=True, message=message))

    def check_middleware(self):
        """Check MIDDLEWARE configuration."""
        middleware = list(getattr(self.settings, 'MIDDLEWARE', []))

        required_middleware = [
            'django.middleware.common.CommonMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'allauth.account.middleware.AccountMiddleware',
        ]

        missing = [mw for mw in required_middleware if mw not in middleware]

        if missing:
            message = f"Missing middleware: {', '.join(missing)}"
            if 'allauth.account.middleware.AccountMiddleware' in missing:
                message += "\n  AccountMiddleware is REQUIRED in django-allauth 0.57+"
            self.add_result(CheckResult("MIDDLEWARE", passed=False, message=message))
        else:
            self.add_result(CheckResult("MIDDLEWARE", passed=True, message="All required middleware present"))

    def check_authentication_backends(self):
        """Check AUTHENTICATION_BACKENDS configuration."""
        backends = list(getattr(self.settings, 'AUTHENTICATION_BACKENDS', []))

        required_backends = [
            'django.contrib.auth.backends.ModelBackend',
            'allauth.account.auth_backends.AuthenticationBackend',
        ]

        missing = [b for b in required_backends if b not in backends]

        if missing:
            self.add_result(CheckResult(
                "AUTHENTICATION_BACKENDS",
                passed=False,
                message=f"Missing backends: {', '.join(missing)}"
            ))
        else:
            self.add_result(CheckResult(
                "AUTHENTICATION_BACKENDS",
                passed=True,
                message="Required authentication backends configured"
            ))

    def check_session_engine(self):
        """Check SESSION_ENGINE configuration."""
        session_engine = getattr(self.settings, 'SESSION_ENGINE', 'django.contrib.sessions.backends.db')

        if 'signed_cookies' in session_engine:
            self.add_result(CheckResult(
                "SESSION_ENGINE",
                passed=False,
                message=(
                    f"Current: {session_engine}\n"
                    "  signed_cookies backend loses verification codes!\n"
                    "  Use 'django.contrib.sessions.backends.db' or 'cached_db' instead"
                )
            ))
        else:
            self.add_result(CheckResult(
                "SESSION_ENGINE",
                passed=True,
                message=f"{session_engine} (compatible)"
            ))

    def check_email_backend(self):
        """Check EMAIL_BACKEND configuration."""
        email_backend = getattr(self.settings, 'EMAIL_BACKEND', None)

        if not email_backend:
            self.add_result(CheckResult(
                "EMAIL_BACKEND",
                passed=False,
                message="EMAIL_BACKEND not configured (emails will fail silently)"
            ))
        elif 'dummy' in email_backend.lower():
            self.add_result(CheckResult(
                "EMAIL_BACKEND",
                passed=False,
                warning=True,
                message=f"{email_backend} (emails will be discarded)"
            ))
        elif 'console' in email_backend.lower():
            self.add_result(CheckResult(
                "EMAIL_BACKEND",
                passed=True,
                warning=True,
                message=f"{email_backend} (development only - emails print to console)"
            ))
        else:
            self.add_result(CheckResult(
                "EMAIL_BACKEND",
                passed=True,
                message=f"{email_backend}"
            ))

    def check_templates(self):
        """Check TEMPLATES context processors."""
        templates = getattr(self.settings, 'TEMPLATES', [])

        if not templates:
            self.add_result(CheckResult("TEMPLATES", passed=False, message="TEMPLATES not configured"))
            return

        required_processors = [
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
        ]

        for template_config in templates:
            if template_config.get('BACKEND') == 'django.template.backends.django.DjangoTemplates':
                processors = template_config.get('OPTIONS', {}).get('context_processors', [])
                missing = [p for p in required_processors if p not in processors]

                if missing:
                    self.add_result(CheckResult(
                        "TEMPLATES Context Processors",
                        passed=False,
                        message=f"Missing processors: {', '.join(missing)}"
                    ))
                else:
                    self.add_result(CheckResult(
                        "TEMPLATES Context Processors",
                        passed=True,
                        message="All required context processors present"
                    ))
                return

        self.add_result(CheckResult(
            "TEMPLATES",
            passed=False,
            message="DjangoTemplates backend not found"
        ))

    def check_database(self):
        """Check database connection."""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")

            db_engine = self.settings.DATABASES['default']['ENGINE']
            db_name = self.settings.DATABASES['default'].get('NAME', 'N/A')

            self.add_result(CheckResult(
                "Database Connection",
                passed=True,
                message=f"Connected to {db_engine} ({db_name})"
            ))
        except Exception as e:
            self.add_result(CheckResult(
                "Database Connection",
                passed=False,
                message=f"Cannot connect to database: {e}"
            ))

    def check_migrations(self):
        """Check if all migrations have been applied."""
        try:
            from django.core.management import call_command
            from io import StringIO

            out = StringIO()
            call_command('showmigrations', '--plan', stdout=out, no_color=True)
            output = out.getvalue()

            # Check for unapplied migrations (lines starting with [ ] instead of [X])
            unapplied = [line.strip() for line in output.split('\n') if line.strip().startswith('[ ]')]

            if unapplied:
                # Filter for allauth-related migrations
                allauth_unapplied = [m for m in unapplied if 'allauth' in m.lower()]

                if allauth_unapplied:
                    message = f"Unapplied allauth migrations found:\n  " + "\n  ".join(allauth_unapplied[:5])
                    if len(allauth_unapplied) > 5:
                        message += f"\n  ... and {len(allauth_unapplied) - 5} more"
                    message += "\n  Run: python manage.py migrate"

                    self.add_result(CheckResult("Migrations", passed=False, message=message))
                else:
                    message = f"{len(unapplied)} unapplied migrations (not allauth-related)"
                    self.add_result(CheckResult("Migrations", passed=True, warning=True, message=message))
            else:
                self.add_result(CheckResult("Migrations", passed=True, message="All migrations applied"))

        except Exception as e:
            self.add_result(CheckResult(
                "Migrations",
                passed=False,
                message=f"Cannot check migrations: {e}"
            ))

    def check_sites_framework(self):
        """Check Sites framework configuration and create Site if needed."""
        try:
            site_id = getattr(self.settings, 'SITE_ID', None)

            if site_id is None:
                self.add_result(CheckResult(
                    "SITE_ID",
                    passed=False,
                    message="SITE_ID not configured (required for email verification links)"
                ))
                return

            from django.contrib.sites.models import Site

            try:
                site = Site.objects.get(pk=site_id)
                self.add_result(CheckResult(
                    "Sites Framework",
                    passed=True,
                    message=f"SITE_ID={site_id}, domain={site.domain}, name={site.name}"
                ))
            except Site.DoesNotExist:
                message = f"SITE_ID={site_id} but Site object doesn't exist"

                if self.fix:
                    try:
                        site = Site.objects.create(
                            pk=site_id,
                            domain='localhost:8000',
                            name='Local Development'
                        )
                        self.add_result(CheckResult(
                            "Sites Framework",
                            passed=True,
                            message=f"Created Site: domain={site.domain}, name={site.name}",
                            fix_applied=True
                        ))
                    except Exception as e:
                        self.add_result(CheckResult(
                            "Sites Framework",
                            passed=False,
                            message=f"{message}\n  Failed to create: {e}"
                        ))
                else:
                    message += "\n  Run with --fix to create Site object automatically"
                    self.add_result(CheckResult("Sites Framework", passed=False, message=message))

        except Exception as e:
            self.add_result(CheckResult(
                "Sites Framework",
                passed=False,
                message=f"Error checking Sites framework: {e}"
            ))

    def run_all_checks(self):
        """Run all verification checks."""
        self.check_python_version()
        self.check_django_version()
        self.check_installed_apps()
        self.check_middleware()
        self.check_authentication_backends()
        self.check_session_engine()
        self.check_email_backend()
        self.check_templates()
        self.check_database()
        self.check_migrations()
        self.check_sites_framework()

    def print_summary(self):
        """Print summary of all checks."""
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)

        passed = sum(1 for r in self.results if r.passed and not r.warning)
        warnings = sum(1 for r in self.results if r.warning)
        failed = sum(1 for r in self.results if not r.passed and not r.warning)
        fixes_applied = sum(1 for r in self.results if r.fix_applied)

        print(f"{CHECK_MARK} Passed: {passed}")
        if warnings > 0:
            print(f"{WARNING} Warnings: {warnings}")
        if failed > 0:
            print(f"{CROSS_MARK} Failed: {failed}")
        if fixes_applied > 0:
            print(f"  Fixes Applied: {fixes_applied}")

        print()

        if failed > 0:
            print("⚠ Some checks failed. Review the issues above and fix your Django settings.")
            if not self.fix:
                print("  Run with --fix to automatically fix some common issues.")
            return 1
        elif warnings > 0:
            print("⚠ All critical checks passed, but there are some warnings.")
            return 0
        else:
            print("✓ All checks passed! Your django-allauth setup looks good.")
            return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Verify and optionally auto-fix django-allauth installation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    Check setup (read-only)
  %(prog)s --fix             Check and auto-fix issues
  %(prog)s --verbose         Detailed output
  %(prog)s --fix --verbose   Fix with detailed output
        """
    )

    parser.add_argument(
        '--fix',
        action='store_true',
        help='Automatically fix common configuration issues'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed output'
    )

    args = parser.parse_args()

    checker = AllauthSetupChecker(fix=args.fix, verbose=args.verbose)

    # Initialize Django
    if not checker.initialize_django():
        return 2

    # Run all checks
    checker.run_all_checks()

    # Print summary and return exit code
    return checker.print_summary()


if __name__ == '__main__':
    sys.exit(main())
