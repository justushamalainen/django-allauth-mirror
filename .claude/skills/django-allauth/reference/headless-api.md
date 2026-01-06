# Headless API Guide

This guide covers django-allauth's headless API for building decoupled frontends (SPAs, mobile apps) with Django as a backend authentication service.

## Table of Contents

1. [Installation & Setup](#installation--setup)
2. [Configuration](#configuration)
3. [JWT Token Strategy](#jwt-token-strategy)
4. [API Endpoints Reference](#api-endpoints-reference)
5. [CORS Configuration](#cors-configuration-critical)
6. [Frontend Integration](#frontend-integration)
7. [Mobile App Considerations](#mobile-app-considerations)
8. [OpenAPI Specification](#openapi-specification)

---

## Installation & Setup

### Basic Installation

Install django-allauth with headless support:

```bash
pip install "django-allauth[headless]"
```

The `[headless]` extra installs:
- `PyJWT` for JWT token generation
- Required cryptographic dependencies

### INSTALLED_APPS Configuration

Add to your `settings.py`:

```python
INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    # Allauth apps (order matters!)
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.headless',  # Add this for headless API

    # Optional: social providers
    'allauth.socialaccount.providers.google',

    # Optional: MFA support
    'allauth.mfa',

    # Your apps
    'myapp',
]

SITE_ID = 1
```

### URL Configuration

Add to your root `urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Headless API endpoints
    path('_allauth/', include('allauth.headless.urls')),

    # Optional: traditional views (if not using HEADLESS_ONLY)
    # path('accounts/', include('allauth.urls')),
]
```

This exposes two URL namespaces:
- `/_allauth/browser/v1/` - For browser-based SPAs (uses cookies + CSRF)
- `/_allauth/app/v1/` - For mobile/native apps (uses X-Session-Token header)

### Client Types: Browser vs App

The headless API supports two client types with different security models:

#### Browser Client (`/_allauth/browser/v1/`)

**Use for:** Single-page applications (React, Vue, Angular) running in a web browser

**Authentication:**
- Uses standard Django session cookies
- CSRF protection enabled (requires CSRF token in requests)
- Cookies set with `SameSite=Lax` by default

**Setup considerations:**
- Frontend and backend must share the same root domain (or subdomain with proper cookie domain config)
- CORS must allow credentials

#### App Client (`/_allauth/app/v1/`)

**Use for:** Mobile applications (iOS, Android) or desktop applications

**Authentication:**
- Uses `X-Session-Token` header (no cookies)
- No CSRF protection needed
- Session token returned in response metadata

**Setup considerations:**
- More flexible cross-origin setup
- Requires client-side token storage (secure storage on mobile)
- Token rotation on refresh for security

**Example - Choosing client type:**

```python
# settings.py

# Default: both clients enabled
HEADLESS_CLIENTS = ('browser', 'app')

# Only browser (SPAs only)
HEADLESS_CLIENTS = ('browser',)

# Only app (mobile only)
HEADLESS_CLIENTS = ('app',)
```

---

## Configuration

### Core Settings

```python
# settings.py

# Disable traditional allauth views (headless-only mode)
HEADLESS_ONLY = True

# Supported client types
HEADLESS_CLIENTS = ('browser', 'app')

# Frontend URLs for email links
HEADLESS_FRONTEND_URLS = {
    'account_confirm_email': 'https://app.example.com/verify-email/{key}',
    'account_reset_password': 'https://app.example.com/password/reset/{key}',
    'socialaccount_login_cancelled': 'https://app.example.com/login?cancelled=1',
}
```

### HEADLESS_ONLY Mode

When `HEADLESS_ONLY = True`:
- Traditional HTML views (`/accounts/login/`, etc.) are **disabled**
- Only API endpoints (`/_allauth/`) work
- Reduces attack surface and eliminates template rendering overhead

**Warning:** Cannot mix traditional views and headless API in production with `HEADLESS_ONLY = True`. Choose one approach.

### HEADLESS_FRONTEND_URLS

Maps backend flows to frontend routes. Used in:
- Email verification links
- Password reset emails
- Social login redirects

**Format:**
- Keys: allauth URL names (see adapter methods for full list)
- Values: Frontend URLs with `{key}` placeholder for tokens

**Example:**

```python
HEADLESS_FRONTEND_URLS = {
    # Email verification
    'account_confirm_email': 'https://app.example.com/auth/verify/{key}',

    # Password reset
    'account_reset_password': 'https://app.example.com/auth/reset/{key}',
    'account_reset_password_from_key': 'https://app.example.com/auth/reset/{key}',

    # Social auth
    'socialaccount_login_cancelled': 'https://app.example.com/auth/cancelled',
    'socialaccount_login_error': 'https://app.example.com/auth/error',

    # Account management
    'account_change_email': 'https://app.example.com/account/email/{key}',
}
```

**Testing locally:**
```python
# Development settings
HEADLESS_FRONTEND_URLS = {
    'account_confirm_email': 'http://localhost:3000/verify-email/{key}',
}
```

---

## JWT Token Strategy

### Overview

django-allauth supports two token strategies:

1. **Session Strategy** (default) - Server-side session storage
2. **JWT Strategy** - Stateless JSON Web Tokens

### Configuring JWT Strategy

```python
# settings.py

# Enable JWT strategy
HEADLESS_TOKEN_STRATEGY = 'allauth.headless.tokens.strategies.jwt.JWTTokenStrategy'

# JWT signing key (REQUIRED - use a strong secret!)
HEADLESS_JWT_PRIVATE_KEY = env('JWT_PRIVATE_KEY')  # Load from environment

# Access token lifetime (default: 300 seconds = 5 minutes)
HEADLESS_JWT_ACCESS_TOKEN_EXPIRES_IN = 300

# Refresh token lifetime (default: 86400 seconds = 24 hours)
HEADLESS_JWT_REFRESH_TOKEN_EXPIRES_IN = 86400

# Rotate refresh tokens on each refresh (recommended for security)
HEADLESS_JWT_ROTATE_REFRESH_TOKEN = True  # default

# Authorization header scheme
HEADLESS_JWT_AUTHORIZATION_HEADER_SCHEME = 'Bearer'  # default

# Enable stateful validation (check token against database)
HEADLESS_JWT_STATEFUL_VALIDATION_ENABLED = False  # default
```

### JWT Configuration Options

#### HEADLESS_JWT_ACCESS_TOKEN_EXPIRES_IN

**Default:** `300` seconds (5 minutes)

Short-lived access tokens limit exposure if token is compromised.

**Recommendations:**
- SPAs: 5-15 minutes
- Mobile apps: 15-30 minutes
- High-security: 1-5 minutes

```python
# Short-lived (high security)
HEADLESS_JWT_ACCESS_TOKEN_EXPIRES_IN = 60

# Medium (balanced)
HEADLESS_JWT_ACCESS_TOKEN_EXPIRES_IN = 900  # 15 minutes

# Long-lived (less frequent refresh, lower security)
HEADLESS_JWT_ACCESS_TOKEN_EXPIRES_IN = 3600  # 1 hour
```

#### HEADLESS_JWT_REFRESH_TOKEN_EXPIRES_IN

**Default:** `86400` seconds (24 hours)

Refresh tokens are longer-lived and used to obtain new access tokens.

**Recommendations:**
- Web apps: 1-7 days
- Mobile apps: 7-30 days
- Remember me: 30-90 days

```python
# 7 days
HEADLESS_JWT_REFRESH_TOKEN_EXPIRES_IN = 604800

# 30 days
HEADLESS_JWT_REFRESH_TOKEN_EXPIRES_IN = 2592000
```

#### HEADLESS_JWT_ROTATE_REFRESH_TOKEN

**Default:** `True`

When enabled, each token refresh returns a **new** refresh token, and the old one is invalidated.

**Security impact:**
- ✓ Prevents token replay attacks
- ✓ Detects stolen tokens (multiple simultaneous refreshes fail)
- ✗ Requires careful client-side handling (update stored token)

```python
# High security (recommended)
HEADLESS_JWT_ROTATE_REFRESH_TOKEN = True

# Lower security (simpler client code)
HEADLESS_JWT_ROTATE_REFRESH_TOKEN = False
```

#### HEADLESS_JWT_STATEFUL_VALIDATION_ENABLED

**Default:** `False`

When enabled, validates JWT against database session on every request.

**Tradeoffs:**
- ✓ Instant token invalidation (logout, password change)
- ✓ Better security (detect compromised sessions)
- ✗ Database query on every request (performance impact)

```python
# Stateless (better performance)
HEADLESS_JWT_STATEFUL_VALIDATION_ENABLED = False

# Stateful (better security)
HEADLESS_JWT_STATEFUL_VALIDATION_ENABLED = True
```

### Session vs JWT Tradeoffs

| Feature | Session Strategy | JWT Strategy |
|---------|-----------------|--------------|
| **Storage** | Server-side (database/cache) | Client-side (localStorage/cookies) |
| **Scalability** | Requires session store sync across servers | Stateless, no server storage |
| **Invalidation** | Instant (delete session) | Delayed (wait for expiry)¹ |
| **Token size** | Small session ID (~32 bytes) | Large JWT (~200-500 bytes) |
| **Overhead** | Database query per request | Signature verification per request |
| **Security** | Session hijacking risk | Token theft risk² |
| **Use case** | Monolithic apps, high security | Microservices, mobile apps |

¹ Unless `HEADLESS_JWT_STATEFUL_VALIDATION_ENABLED = True`
² Mitigated by short expiry and refresh rotation

**Recommendation:**
- Use **Session** for: Browser SPAs on same domain, high-security requirements
- Use **JWT** for: Mobile apps, microservices, cross-domain setups

---

## API Endpoints Reference

All endpoints are versioned under `/_allauth/{client}/v1/`.

### Base Endpoints

#### GET `/_allauth/{client}/v1/config`

Retrieve frontend configuration (enabled providers, MFA settings, etc.)

**Response:**
```json
{
  "status": 200,
  "data": {
    "account": {
      "authentication_method": "email",
      "email_verification": "mandatory"
    },
    "socialaccount": {
      "providers": [
        {"id": "google", "name": "Google"}
      ]
    },
    "mfa": {
      "supported_types": ["totp", "recovery_codes"],
      "totp_tolerance": 1
    }
  }
}
```

### Authentication Endpoints

#### POST `/_allauth/{client}/v1/auth/login`

Authenticate with email/username and password.

**Request:**
```json
{
  "username": "user@example.com",
  "password": "SecurePass123!"
}
```

**Success (200):**
```json
{
  "status": 200,
  "meta": {
    "is_authenticated": true,
    "session_token": "abc123...",  // app client only
    "access_token": "eyJ0eXAi..."   // JWT strategy only
  }
}
```

**MFA Required (401):**
```json
{
  "status": 401,
  "meta": {
    "is_authenticated": false,
    "flows": [
      {"id": "mfa_authenticate", "is_pending": true}
    ]
  }
}
```

#### POST `/_allauth/{client}/v1/auth/signup`

Register a new user account.

**Request:**
```json
{
  "email": "newuser@example.com",
  "username": "newuser",
  "password": "SecurePass123!"
}
```

**Success (200):**
```json
{
  "status": 200,
  "data": {
    "user": {
      "id": 123,
      "username": "newuser",
      "email": "newuser@example.com"
    }
  },
  "meta": {
    "is_authenticated": true,
    "session_token": "xyz789..."
  }
}
```

#### GET `/_allauth/{client}/v1/auth/session`

Retrieve current session information.

**Success (200):**
```json
{
  "status": 200,
  "data": {
    "user": {
      "id": 123,
      "username": "user",
      "email": "user@example.com"
    }
  },
  "meta": {
    "is_authenticated": true
  }
}
```

**Not authenticated (401):**
```json
{
  "status": 401,
  "meta": {
    "is_authenticated": false,
    "flows": [
      {"id": "login"},
      {"id": "signup"}
    ]
  }
}
```

#### DELETE `/_allauth/{client}/v1/auth/session`

Logout (end current session).

**Success (200):**
```json
{
  "status": 200
}
```

### Email Verification

#### POST `/_allauth/{client}/v1/auth/email/verify`

Verify email address with code sent to user's email.

**Request:**
```json
{
  "key": "verification-key-from-email"
}
```

#### POST `/_allauth/{client}/v1/auth/email/verify/resend`

Resend verification email.

**Request:**
```json
{
  "email": "user@example.com"
}
```

### Password Management

#### POST `/_allauth/{client}/v1/auth/password/request`

Request password reset (sends email with reset link).

**Request:**
```json
{
  "email": "user@example.com"
}
```

#### POST `/_allauth/{client}/v1/auth/password/reset`

Reset password with code from email.

**Request:**
```json
{
  "key": "reset-key-from-email",
  "password": "NewSecurePass456!"
}
```

#### POST `/_allauth/{client}/v1/account/password/change`

Change password (requires authentication).

**Request:**
```json
{
  "current_password": "OldPass123!",
  "new_password": "NewPass456!"
}
```

### Account Management

#### GET `/_allauth/{client}/v1/account/email`

List user's email addresses.

**Response:**
```json
{
  "status": 200,
  "data": [
    {
      "email": "user@example.com",
      "primary": true,
      "verified": true
    },
    {
      "email": "user2@example.com",
      "primary": false,
      "verified": false
    }
  ]
}
```

#### POST `/_allauth/{client}/v1/account/email`

Add a new email address.

**Request:**
```json
{
  "email": "newemail@example.com"
}
```

#### DELETE `/_allauth/{client}/v1/account/email`

Remove an email address.

**Request:**
```json
{
  "email": "oldemail@example.com"
}
```

### Multi-Factor Authentication

#### POST `/_allauth/{client}/v1/auth/2fa/authenticate`

Complete MFA challenge during login.

**Request:**
```json
{
  "code": "123456"
}
```

#### GET `/_allauth/{client}/v1/account/authenticators`

List active MFA authenticators.

**Response:**
```json
{
  "status": 200,
  "data": [
    {
      "type": "totp",
      "created_at": "2025-01-01T12:00:00Z"
    }
  ]
}
```

#### POST `/_allauth/{client}/v1/account/authenticators/totp`

Activate TOTP authenticator.

**Request:**
```json
{
  "secret": "BASE32SECRET",
  "code": "123456"
}
```

#### POST `/_allauth/{client}/v1/account/authenticators/recovery-codes`

Generate new recovery codes.

**Response:**
```json
{
  "status": 200,
  "data": {
    "unused_codes": ["code1", "code2", "code3"]
  }
}
```

### Social Authentication

#### GET `/_allauth/{client}/v1/auth/provider/redirect`

Initiate OAuth redirect flow.

**Query params:**
- `provider`: Provider ID (e.g., `google`)
- `callback_url`: Where to redirect after authentication
- `process`: `login` or `connect`

**Example:**
```
GET /_allauth/browser/v1/auth/provider/redirect?provider=google&callback_url=http://localhost:3000/auth/callback&process=login
```

#### POST `/_allauth/{client}/v1/auth/provider/token`

Authenticate with provider token (for mobile apps).

**Request:**
```json
{
  "provider": "google",
  "process": "login",
  "token": {
    "access_token": "ya29.a0AfH6SMB..."
  }
}
```

#### GET `/_allauth/{client}/v1/account/providers`

List connected social accounts.

**Response:**
```json
{
  "status": 200,
  "data": [
    {
      "provider": "google",
      "uid": "1234567890",
      "display": "user@gmail.com"
    }
  ]
}
```

### User Sessions (requires `allauth.usersessions`)

#### GET `/_allauth/{client}/v1/auth/sessions`

List all active sessions for the user.

**Response:**
```json
{
  "status": 200,
  "data": [
    {
      "id": "session-id-1",
      "ip": "192.168.1.1",
      "user_agent": "Mozilla/5.0...",
      "created_at": "2025-01-01T10:00:00Z"
    }
  ]
}
```

#### DELETE `/_allauth/{client}/v1/auth/sessions/{session_id}`

Sign out of specific session.

### Token Management (app client only)

#### POST `/_allauth/app/v1/tokens/refresh`

Refresh access token using refresh token (JWT strategy only).

**Request:**
```json
{
  "refresh_token": "eyJ0eXAiOi..."
}
```

**Response:**
```json
{
  "status": 200,
  "data": {
    "access_token": "eyJ0eXAiOi...",
    "refresh_token": "eyJ0eXAiOi..."  // New token if rotation enabled
  }
}
```

---

## CORS Configuration (CRITICAL)

### Why CORS Matters

If your frontend and backend are on **different origins** (different domain, port, or protocol), you **must** configure CORS properly or all API requests will fail.

**Common scenarios requiring CORS:**
- Frontend: `http://localhost:3000`, Backend: `http://localhost:8000`
- Frontend: `https://app.example.com`, Backend: `https://api.example.com`
- Any cross-origin SPA setup

### Install django-cors-headers

```bash
pip install django-cors-headers
```

### Configuration for Development

```python
# settings.py (DEVELOPMENT ONLY!)

INSTALLED_APPS = [
    'corsheaders',  # Add near top
    # ... other apps
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Must be early
    'django.middleware.common.CommonMiddleware',
    # ... other middleware
]

# Allow requests from frontend origin
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]

# Required for session cookies to work
CORS_ALLOW_CREDENTIALS = True

# Allow custom headers used by allauth
CORS_ALLOW_HEADERS = list(default_headers) + [
    'X-Session-Token',  # Required for app client
]
```

### Configuration for Production

**Never use `CORS_ALLOW_ALL_ORIGINS = True` in production!**

```python
# settings.py (PRODUCTION)

CORS_ALLOWED_ORIGINS = [
    'https://app.example.com',
    'https://www.example.com',
]

CORS_ALLOW_CREDENTIALS = True

# Explicitly list allowed headers
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-session-token',  # For app client
]

# CSRF settings for cross-origin
CSRF_TRUSTED_ORIGINS = [
    'https://app.example.com',
]

# Cookie settings for browser client
SESSION_COOKIE_SAMESITE = 'None'  # Required for cross-origin
SESSION_COOKIE_SECURE = True      # HTTPS only
CSRF_COOKIE_SAMESITE = 'None'
CSRF_COOKIE_SECURE = True
```

### Common CORS Errors and Fixes

#### Error: "No 'Access-Control-Allow-Origin' header"

**Cause:** CORS middleware not installed or frontend origin not whitelisted

**Fix:**
```python
CORS_ALLOWED_ORIGINS = ['http://localhost:3000']
```

#### Error: "Credentials flag is true, but Access-Control-Allow-Credentials is false"

**Cause:** Forgot to enable credentials

**Fix:**
```python
CORS_ALLOW_CREDENTIALS = True
```

#### Error: "Request header X-Session-Token is not allowed"

**Cause:** Custom header not whitelisted

**Fix:**
```python
from corsheaders.defaults import default_headers
CORS_ALLOW_HEADERS = list(default_headers) + ['X-Session-Token']
```

#### Error: Cookies not being sent/received

**Cause:** SameSite policy blocking cross-origin cookies

**Fix:**
```python
SESSION_COOKIE_SAMESITE = 'None'
SESSION_COOKIE_SECURE = True  # Requires HTTPS
```

#### Error: CSRF token missing or invalid

**Cause:** CSRF cookie not accessible to frontend

**Fix:**
```python
CSRF_COOKIE_SAMESITE = 'None'
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = ['https://app.example.com']
```

---

## Frontend Integration

### JWT Token Refresh Pattern

For JWT strategy, implement automatic token refresh to maintain authentication.

#### React Example with Axios

```javascript
// src/api/axios.js
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/_allauth/app/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Add access token
api.interceptors.request.use(
  (config) => {
    const accessToken = localStorage.getItem('access_token');
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: Handle 401 and refresh token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and haven't retried yet, try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post(
          'http://localhost:8000/_allauth/app/v1/tokens/refresh',
          { refresh_token: refreshToken }
        );

        const { access_token, refresh_token: newRefreshToken } = response.data.data;

        // Update stored tokens
        localStorage.setItem('access_token', access_token);
        if (newRefreshToken) {
          localStorage.setItem('refresh_token', newRefreshToken);
        }

        // Retry original request with new token
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed - redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
```

#### Usage in Components

```javascript
// src/components/Dashboard.jsx
import { useEffect, useState } from 'react';
import api from '../api/axios';

function Dashboard() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    api.get('/auth/session')
      .then(response => setUser(response.data.data.user))
      .catch(error => console.error('Failed to fetch session', error));
  }, []);

  return <div>Welcome, {user?.username}!</div>;
}
```

### Error Handling

Handle common API error codes:

```javascript
// src/utils/errorHandler.js
export function handleApiError(error) {
  const status = error.response?.status;
  const errors = error.response?.data?.errors;

  switch (status) {
    case 401:
      // Unauthorized - handled by interceptor
      return 'Please log in to continue.';

    case 409:
      // Conflict (e.g., email already exists)
      return errors?.[0]?.message || 'A conflict occurred.';

    case 429:
      // Rate limited
      return 'Too many requests. Please try again later.';

    default:
      return errors?.[0]?.message || 'An error occurred.';
  }
}
```

### Login Flow Example

```javascript
// src/pages/Login.jsx
import { useState } from 'react';
import api from '../api/axios';
import { handleApiError } from '../utils/errorHandler';

function Login() {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const response = await api.post('/auth/login', credentials);
      const { access_token, refresh_token } = response.data.meta;

      // Store tokens (JWT strategy)
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);

      // Redirect to dashboard
      window.location.href = '/dashboard';
    } catch (err) {
      setError(handleApiError(err));
    }
  };

  return (
    <form onSubmit={handleLogin}>
      <input
        type="text"
        placeholder="Email"
        value={credentials.username}
        onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
      />
      <input
        type="password"
        placeholder="Password"
        value={credentials.password}
        onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
      />
      {error && <p className="error">{error}</p>}
      <button type="submit">Log In</button>
    </form>
  );
}
```

---

## Mobile App Considerations

### App Client Type

Always use the **app** client (`/_allauth/app/v1/`) for mobile applications.

**Key differences from browser client:**
- Uses `X-Session-Token` header instead of cookies
- No CSRF protection needed
- Session token in response metadata

### Session Token Management

```javascript
// Example: React Native
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';

const api = axios.create({
  baseURL: 'https://api.example.com/_allauth/app/v1',
});

// Add session token to all requests
api.interceptors.request.use(async (config) => {
  const sessionToken = await AsyncStorage.getItem('session_token');
  if (sessionToken) {
    config.headers['X-Session-Token'] = sessionToken;
  }
  return config;
});

// Extract and store session token from responses
api.interceptors.response.use(async (response) => {
  const sessionToken = response.data?.meta?.session_token;
  if (sessionToken) {
    await AsyncStorage.setItem('session_token', sessionToken);
  }
  return response;
});

// Handle 410 Gone (invalid session)
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 410) {
      // Session invalid - clear and force re-login
      await AsyncStorage.removeItem('session_token');
      // Navigate to login screen
    }
    return Promise.reject(error);
  }
);
```

### Provider Token Authentication

For mobile apps using native OAuth (e.g., Google Sign-In SDK), authenticate with provider tokens:

```javascript
// Example: Google Sign-In in React Native
import { GoogleSignin } from '@react-native-google-signin/google-signin';
import api from './api';

async function signInWithGoogle() {
  try {
    // Get token from native Google SDK
    await GoogleSignin.hasPlayServices();
    const userInfo = await GoogleSignin.signIn();
    const tokens = await GoogleSignin.getTokens();

    // Authenticate with django-allauth
    const response = await api.post('/auth/provider/token', {
      provider: 'google',
      process: 'login',
      token: {
        access_token: tokens.accessToken,
      },
    });

    // Handle response (store session token, navigate)
    const { session_token } = response.data.meta;
    await AsyncStorage.setItem('session_token', session_token);

    // Navigate to home
  } catch (error) {
    console.error('Google sign in failed', error);
  }
}
```

### Token Storage Security

**iOS:** Use Keychain Services

```javascript
import * as Keychain from 'react-native-keychain';

// Store tokens securely
await Keychain.setGenericPassword('session_token', sessionToken);

// Retrieve tokens
const credentials = await Keychain.getGenericPassword();
const sessionToken = credentials.password;
```

**Android:** Use EncryptedSharedPreferences

```javascript
// Android automatically encrypts AsyncStorage on modern devices
// For older devices, use react-native-encrypted-storage
import EncryptedStorage from 'react-native-encrypted-storage';

await EncryptedStorage.setItem('session_token', sessionToken);
const sessionToken = await EncryptedStorage.getItem('session_token');
```

**Never:**
- Store tokens in plain text files
- Log tokens to console in production
- Include tokens in crash reports

---

## OpenAPI Specification

### Enable OpenAPI Documentation

django-allauth can serve an OpenAPI (Swagger) specification of the headless API.

```python
# settings.py

# Enable OpenAPI spec endpoint
HEADLESS_SERVE_SPECIFICATION = True

# Optional: Customize template (default: redoc)
HEADLESS_SPECIFICATION_TEMPLATE_NAME = 'headless/spec/redoc_cdn.html'
```

### Accessing the Specification

With `HEADLESS_SERVE_SPECIFICATION = True`, two endpoints are available:

#### Interactive Documentation
```
GET /_allauth/openapi
```

Renders interactive API documentation using ReDoc.

#### Raw OpenAPI YAML
```
GET /_allauth/openapi.yaml
```

Download the raw OpenAPI 3.0 specification in YAML format.

### Generating Client SDKs

Use the OpenAPI spec to generate client libraries:

```bash
# Download spec
curl http://localhost:8000/_allauth/openapi.yaml > allauth-api.yaml

# Generate TypeScript client
npx @openapitools/openapi-generator-cli generate \
  -i allauth-api.yaml \
  -g typescript-axios \
  -o ./src/api/generated

# Generate Python client
openapi-generator-cli generate \
  -i allauth-api.yaml \
  -g python \
  -o ./allauth_client
```

### Security Considerations

**Production:**
- Set `HEADLESS_SERVE_SPECIFICATION = False` (do not expose API docs publicly)
- Serve OpenAPI spec through a separate documentation site with authentication

**Development:**
- Enable for convenience: `HEADLESS_SERVE_SPECIFICATION = DEBUG`

---

## Summary

The django-allauth headless API provides a complete authentication solution for decoupled frontends:

✓ Two client types (browser, app) with appropriate security models
✓ Flexible token strategies (sessions, JWT)
✓ Comprehensive endpoints (auth, account management, MFA, social)
✓ Production-ready CORS and security configuration
✓ Mobile app support with provider token authentication
✓ OpenAPI specification for client generation

**Next steps:**
- Review [security.md](./security.md) for production hardening
- Check [social-providers.md](./social-providers.md) for OAuth setup
- See [customization.md](./customization.md) for adapting authentication flows
