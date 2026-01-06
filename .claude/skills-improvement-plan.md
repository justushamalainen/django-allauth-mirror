# Django-AllAuth Skills Improvement Plan

Based on comprehensive review by 16 specialized subagents, this document outlines improvements to the skills plan.

---

## Executive Summary

**Overall Plan Rating: 6.5/10** - Solid foundation but significant gaps identified

| Section | Current Coverage | Priority |
|---------|-----------------|----------|
| Setup & Installation | 40% | **CRITICAL** |
| Social Authentication | 50% | **HIGH** |
| Customization | 40% | **HIGH** |
| MFA | 40% | **MEDIUM** |
| Headless API | 30% | **HIGH** |
| Email Configuration | 50% | **MEDIUM** |
| Security | 30% | **CRITICAL** |
| Custom Providers | 60% | **LOW** |

---

## Section 1: Setup & Installation

### Critical Gaps Identified

1. **Missing Prerequisites**
   - Python 3.8+ requirement not mentioned
   - Django 4.2+ requirement not mentioned
   - Email backend configuration (CRITICAL - emails fail silently without it)
   - `SESSION_ENGINE` cannot be `signed_cookies` (verification codes lost)

2. **Custom User Model Integration** (80% of Django projects use this)
   - `ACCOUNT_USER_MODEL_USERNAME_FIELD` configuration
   - `ACCOUNT_USER_MODEL_EMAIL_FIELD` configuration
   - Migration path for existing users

3. **Django Sites Framework** (completely missing)
   - Required for email verification links
   - `SITE_ID` configuration
   - Multi-site deployment considerations

4. **Post-Installation Checklist** missing:
   - Verify `/accounts/login/` loads
   - Check database migrations
   - Validate email backend
   - Test SITE_ID configuration

### Improvements for `check_allauth_setup.py`

Current plan is too vague. Script should:
```
✓ Check Django/Python versions
✓ Validate INSTALLED_APPS order
✓ Check SESSION_ENGINE (not signed_cookies)
✓ Verify EMAIL_BACKEND configuration
✓ Test TEMPLATES context processors
✓ Validate database connection
✓ Check migrations have run
✓ Validate ACCOUNT_SIGNUP_FIELDS syntax
✓ Cross-check EMAIL_VERIFICATION with signup fields
✓ AUTO-FIX common issues (not just report)
```

---

## Section 2: Social Authentication

### Critical Gaps Identified

1. **127 Providers Organization**
   - Need decision tree for choosing providers
   - Provider registry by category (OAuth2 vs OIDC vs SAML)
   - Documentation status matrix

2. **OAuth2 vs OIDC Differences** (completely missing)
   - When to use generic `openid_connect` provider
   - ID token vs userinfo endpoint differences
   - Discovery endpoint (`.well-known/openid-configuration`)

3. **Callback URL Configuration** (highest error source)
   - Domain mismatch debugging guide
   - HTTPS vs HTTP issues
   - Port number handling
   - Verification script needed

4. **Security Gaps** (from security reviewer)
   - PKCE support not documented (`OAUTH_PKCE_ENABLED`)
   - State parameter CSRF protection not explained
   - Token storage security (`SOCIALACCOUNT_STORE_TOKENS` stores in plaintext)
   - Account takeover via `EMAIL_AUTHENTICATION` setting

### New Reference Files Needed

- `reference/callback-url-debugging.md` - Common errors and fixes
- `reference/oauth2-vs-oidc.md` - Protocol differences
- `reference/social-security.md` - OAuth security best practices

---

## Section 3: Customization

### Critical Gaps Identified

1. **Adapter Methods Reference** (severely incomplete)
   - Plan shows 1 example; DefaultAccountAdapter has 60+ methods
   - Need categorized reference table:
     - Redirect methods (5 methods)
     - Email methods (10+ methods)
     - User creation methods (5 methods)
     - Validation methods (4 methods)
     - Phone methods (4+ methods)
     - Auth lifecycle methods (5+ methods)

2. **SocialAccountAdapter** (completely missing from plan)
   - `pre_social_login()` - critical intervention point
   - `populate_user()` - data extraction
   - `is_auto_signup_allowed()` - access control

3. **Signals** (incomplete list)
   - Missing: `authentication_step_completed`
   - Missing: All social account signals
   - Need real-world examples for each

4. **Form Customization** (too vague)
   - Need complete form class inventory
   - Field addition patterns
   - Settings configuration examples

### Improvements for `generate_adapter.py`

Should be categorized by use-case:
```
Categories:
├── Redirect URLs (most common - 80%)
├── Email Customization (very common - 60%)
├── User Data Flow (common - 40%)
├── Validation Hooks (common - 40%)
├── Phone Verification (specialized - 15%)
└── Auth Lifecycle (advanced - 20%)
```

Interactive + template-based hybrid approach recommended.

---

## Section 4: Multi-Factor Authentication

### Critical Gaps Identified

1. **TOTP Setup**
   - Tolerance explanation missing (`TOTP_TOLERANCE=0` tradeoffs)
   - Secret storage encryption (DEFAULT IS PLAINTEXT!)
   - Clock drift handling

2. **WebAuthn Browser Compatibility** (severely incomplete - only 23 lines in docs)
   - No browser support matrix
   - No fallback strategy for unsupported browsers
   - Passkey-specific requirements undocumented

3. **Recovery Codes**
   - No storage/backup guidance
   - No rate limiting on consumption
   - Account recovery flow undefined

4. **MFA Enforcement** (completely missing)
   - No built-in enforcement mechanism documented
   - Grace period implementation needed
   - Admin bypass patterns needed

### Security Warnings Required

```markdown
⚠️ CRITICAL: TOTP secrets stored in PLAINTEXT by default
- Override encrypt()/decrypt() methods in MFAAdapter
- Example implementation with Fernet encryption needed

⚠️ CRITICAL: MFA_TOTP_INSECURE_BYPASS_CODE
- NEVER set in production
- Only for development/testing

⚠️ HIGH RISK: Trust cookie age is 14 days
- Consider reducing to 7 days or less
- Document implications of cookie theft
```

---

## Section 5: Headless/API Mode

### Critical Gaps Identified

1. **CORS Configuration** (critically incomplete)
   - No preflight OPTIONS handling explanation
   - Missing credentials config details
   - No troubleshooting guide
   - Development vs production setup needed

2. **JWT vs Session Token Tradeoffs** (poorly explained)
   - Storage location guidance missing
   - Refresh token rotation patterns
   - Frontend request interceptor examples needed

3. **Frontend Code Examples** (incomplete)
   - JWT token refresh pattern missing
   - TypeScript interfaces missing
   - Error scenario handling missing
   - Only React example (need Vue/Next.js)

4. **API Endpoint Documentation**
   - 34 endpoints identified but not fully documented
   - OpenAPI spec generation mentioned but not explained
   - Mobile app considerations missing

### New Reference Files Needed

- `reference/headless-cors.md` - CORS setup and debugging
- `reference/headless-jwt.md` - JWT implementation guide
- `reference/headless-frontend.md` - Frontend integration patterns

---

## Section 6: Email Configuration

### Critical Gaps Identified

1. **Complete Template Inventory** (40 templates found)
   - Account module: 28 templates
   - Social module: 4 templates
   - MFA module: 8 templates
   - Context variables for each template needed

2. **HTML vs Plain Text**
   - Only plain text templates ship by default
   - HTML creation pattern not documented
   - MultiAlternatives email handling not explained

3. **Deliverability Best Practices** (completely missing)
   - SPF/DKIM/DMARC setup
   - Bounce handling (NO INFRASTRUCTURE EXISTS)
   - ISP throttling compliance
   - Email validation integration

4. **Testing Email Locally**
   - Console backend usage
   - Template preview view
   - Test assertions for email content

---

## Section 7: Security Best Practices

### Critical Gaps Identified (Most Severe Section)

**Current Coverage: 30%** - Needs expansion from ~50 lines to 300+ lines

1. **OWASP Authentication Controls**
   - Password policies partially covered
   - Session security 30% documented
   - CSRF protection 0% documented
   - Account enumeration 0% documented

2. **Attack Vectors Not Documented**
   - Account enumeration attacks
   - Credential stuffing
   - Session hijacking
   - OAuth state tampering
   - Email verification bypass
   - Password reset vulnerabilities

3. **Missing Security Settings Documentation**
   - `PREVENT_ENUMERATION` (default: True, but not explained)
   - `EMAIL_UNKNOWN_ACCOUNTS` (leaks account existence)
   - `LOGOUT_ON_PASSWORD_CHANGE` (defaults to False - security gap!)
   - `CONFIRM_EMAIL_ON_GET` (security toggle)
   - Rate limiting format syntax

4. **Social Account Security** (0% documented)
   - Provider trust model
   - Token storage risks
   - Account linking security
   - Email authentication risks

### New Reference Files Needed

- `reference/security-checklist.md` - Pre-deployment audit
- `reference/session-security.md` - Session management
- `reference/rate-limiting.md` - Advanced configuration
- `reference/attack-mitigations.md` - Common attack scenarios

---

## Section 8: Custom Social Provider

### Assessment: Best Section (60% coverage)

Minor improvements needed:

1. **Method Requirements Table**
   - Required vs optional methods
   - Signature details

2. **Testing Patterns**
   - OAuth2TestsMixin usage
   - Mock response ordering

3. **Error Handling**
   - ProviderException usage
   - Error display in templates

---

## Overall Architecture Improvements

### 1. SKILL.md Structure

**Estimated lines: 250-300** (will stay under 500)

Recommended structure:
```
- Header/Description           → 5 lines
- Table of Contents            → 15 lines
- When to Use                  → 10 lines
- Core Concepts                → 30 lines
- Quick Start                  → 25 lines
- 8 Topic Overviews           → 100 lines (15 each)
- Helper Scripts Overview      → 20 lines
- Common Workflows            → 40 lines
- Troubleshooting             → 20 lines
```

### 2. Reference File Expansion

Add these new files:
```
reference/
├── setup-guide.md              (expand to 300 lines)
├── social-providers.md         (top 5 providers)
├── social-security.md          (NEW)
├── callback-url-debugging.md   (NEW)
├── oauth2-vs-oidc.md           (NEW)
├── customization.md            (expand to 400 lines)
├── adapter-methods.md          (NEW - comprehensive table)
├── mfa-setup.md                (expand)
├── mfa-security.md             (NEW)
├── headless-api.md             (expand)
├── headless-cors.md            (NEW)
├── headless-jwt.md             (NEW)
├── email-templates.md          (expand with all 40 templates)
├── email-deliverability.md     (NEW)
├── security.md                 (expand to 300+ lines)
├── security-checklist.md       (NEW)
├── attack-mitigations.md       (NEW)
└── custom-provider.md
```

### 3. Script Enhancements

| Script | Current Scope | Recommended Scope |
|--------|--------------|-------------------|
| `check_allauth_setup.py` | Verify only | Verify + Auto-fix |
| `add_social_provider.py` | All 127 | Top 5 providers (Phase 1) |
| `generate_adapter.py` | Basic | Categorized + Interactive |

New scripts to add:
- `generate_signal_handlers.py` - Signal boilerplate
- `generate_form_overrides.py` - Form customization
- `verify_oauth_callbacks.py` - Callback URL verification
- `security_audit.py` - Security settings compliance

### 4. Splitting Criteria

If SKILL.md exceeds 420 lines, split into:
- `django-allauth-setup` (Setup, Social, Email)
- `django-allauth-customize` (Customization, Signals, Forms)
- `django-allauth-security` (MFA, Security, Headless)

---

## Implementation Priority (Revised)

### Phase 1: Critical Foundation (Week 1-2)
1. ✓ SKILL.md with comprehensive overview
2. ✓ `setup-guide.md` with prerequisites, email config, Sites framework
3. ✓ `social-providers.md` (top 5 only)
4. ✓ `callback-url-debugging.md`
5. ✓ `check_allauth_setup.py` with auto-fix

**Milestone:** Install allauth + Google login in 2 prompts

### Phase 2: Customization (Week 2-3)
6. `customization.md` with 60+ adapter methods
7. `adapter-methods.md` categorized reference
8. `generate_adapter.py` with categories
9. Signal handlers documentation

**Milestone:** Create custom adapter correctly in 1 prompt

### Phase 3: Security (Week 3-4)
10. `security.md` expanded (300+ lines)
11. `security-checklist.md`
12. `attack-mitigations.md`
13. `mfa-security.md`
14. `security_audit.py` script

**Milestone:** Pass security review in 1 prompt

### Phase 4: Advanced (Week 4+)
15. `headless-api.md` with JWT patterns
16. `headless-cors.md`
17. `email-templates.md` (all 40 templates)
18. `email-deliverability.md`
19. Remaining scripts

---

## Key Metrics for Success

| Metric | Target |
|--------|--------|
| Setup tasks completed in messages | < 5 |
| Social provider added in messages | < 3 |
| Custom adapter created in messages | < 2 |
| Security audit completed in messages | < 3 |
| MFA setup completed in messages | < 4 |
| Headless API integrated in messages | < 5 |

---

## Conclusion

The original plan provides a solid foundation but requires significant expansion in:
1. **Security documentation** (most critical - 30% → 90%)
2. **Setup prerequisites** (40% → 95%)
3. **Adapter method reference** (10% → 80%)
4. **Headless/CORS configuration** (30% → 85%)

With these improvements, the skills will enable Claude to help developers:
- Install and configure django-allauth correctly first time
- Add social authentication with proper security
- Customize authentication flows idiomatically
- Implement MFA with security best practices
- Deploy headless API for SPAs/mobile apps
- Pass security audits
