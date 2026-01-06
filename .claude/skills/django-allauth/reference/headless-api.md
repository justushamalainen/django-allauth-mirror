# Headless API Guide

This guide covers django-allauth's headless API for building decoupled frontends (SPAs, mobile apps) with Django as a backend authentication service.

## Installation & Setup

### Basic Installation

```bash
pip install "django-allauth[headless]"
```

### Configuration

```python
# settings.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.headless',  # Add this for headless API
    'myapp',
]

SITE_ID = 1
HEADLESS_ONLY = True
HEADLESS_CLIENTS = ('browser', 'app')

# Frontend URLs for email links
HEADLESS_FRONTEND_URLS = {
    'account_confirm_email': 'https://app.example.com/verify-email/{key}',
    'account_reset_password': 'https://app.example.com/password/reset/{key}',
}
```

### URL Configuration

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('_allauth/', include('allauth.headless.urls')),
]
```

### Client Types

**Browser Client** (`/_allauth/browser/v1/`)
- For: Single-page applications (React, Vue, Angular)
- Auth: Session cookies + CSRF protection
- Requirement: Same root domain as backend

**App Client** (`/_allauth/app/v1/`)
- For: Mobile applications (iOS, Android)
- Auth: `X-Session-Token` header (no cookies)
- Requirement: Secure token storage

---

## CORS Configuration

Required when frontend and backend are on different origins.

### Development

```python
# settings.py
INSTALLED_APPS = [
    'corsheaders',  # pip install django-cors-headers
    # ... other apps
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Must be early
    'django.middleware.common.CommonMiddleware',
    # ... other middleware
]

CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',
]

CORS_ALLOW_CREDENTIALS = True

from corsheaders.defaults import default_headers
CORS_ALLOW_HEADERS = list(default_headers) + ['X-Session-Token']
```

### Production

```python
# settings.py
CORS_ALLOWED_ORIGINS = ['https://app.example.com']
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = ['https://app.example.com']

# Cookie settings for browser client
SESSION_COOKIE_SAMESITE = 'None'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = 'None'
CSRF_COOKIE_SECURE = True
```

---

## JWT Token Strategy

### Configuration

```python
# settings.py

# Enable JWT strategy
HEADLESS_TOKEN_STRATEGY = 'allauth.headless.tokens.strategies.jwt.JWTTokenStrategy'

# JWT signing key (REQUIRED)
HEADLESS_JWT_PRIVATE_KEY = env('JWT_PRIVATE_KEY')

# Token lifetimes
HEADLESS_JWT_ACCESS_TOKEN_EXPIRES_IN = 300  # 5 minutes
HEADLESS_JWT_REFRESH_TOKEN_EXPIRES_IN = 86400  # 24 hours

# Rotate refresh tokens (recommended)
HEADLESS_JWT_ROTATE_REFRESH_TOKEN = True
```

### Session vs JWT

| Feature | Session | JWT |
|---------|---------|-----|
| Storage | Server-side | Client-side |
| Scalability | Requires session store | Stateless |
| Invalidation | Instant | Delayed |
| Use case | Same domain SPAs | Mobile apps, microservices |

---

## API Endpoints

All endpoints are under `/_allauth/{client}/v1/` where `{client}` is `browser` or `app`.

### Endpoint Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/config` | GET | Get configuration |
| `/auth/signup` | POST | Register user |
| `/auth/login` | POST | Login |
| `/auth/session` | GET | Get user profile |
| `/auth/session` | DELETE | Logout |
| `/auth/email/verify` | POST | Verify email |
| `/auth/email/verify/resend` | POST | Resend verification |
| `/auth/password/request` | POST | Request password reset |
| `/auth/password/reset` | POST | Reset password |
| `/account/password/change` | POST | Change password |
| `/account/email` | GET/POST/DELETE | Manage emails |
| `/auth/2fa/authenticate` | POST | Complete MFA |
| `/account/authenticators` | GET | List authenticators |
| `/account/authenticators/totp` | POST | Activate TOTP |
| `/tokens/refresh` | POST | Refresh token (app only) |

For social authentication, see [social-providers.md](./social-providers.md).

---

## Key Endpoints

### 1. Signup

**POST** `/_allauth/{client}/v1/auth/signup`

**Request:**
```json
{
  "email": "newuser@example.com",
  "username": "newuser",
  "password": "SecurePass123!"
}
```

**Response:**
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
    "session_token": "xyz789...",  // app client
    "access_token": "eyJ0eXAi..."   // JWT strategy
  }
}
```

### 2. Login

**POST** `/_allauth/{client}/v1/auth/login`

**Request:**
```json
{
  "username": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "status": 200,
  "meta": {
    "is_authenticated": true,
    "session_token": "abc123...",  // app client
    "access_token": "eyJ0eXAi...",  // JWT
    "refresh_token": "eyJ0eXAi..."  // JWT
  }
}
```

### 3. Logout

**DELETE** `/_allauth/{client}/v1/auth/session`

**Response:**
```json
{
  "status": 200
}
```

### 4. User Profile

**GET** `/_allauth/{client}/v1/auth/session`

**Response:**
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

### 5. Token Refresh

**POST** `/_allauth/app/v1/tokens/refresh`

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

### 6. Email Verification

**POST** `/_allauth/{client}/v1/auth/email/verify`

**Request:**
```json
{
  "key": "verification-key-from-email"
}
```

**Response:**
```json
{
  "status": 200,
  "meta": {
    "is_authenticated": true
  }
}
```

---

## Frontend Integration

### JWT Token Refresh

```javascript
// api.js
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/_allauth/app/v1',
});

// Add access token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 and refresh token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const { data } = await axios.post(
          'http://localhost:8000/_allauth/app/v1/tokens/refresh',
          { refresh_token: refreshToken }
        );

        localStorage.setItem('access_token', data.data.access_token);
        if (data.data.refresh_token) {
          localStorage.setItem('refresh_token', data.data.refresh_token);
        }

        originalRequest.headers.Authorization = `Bearer ${data.data.access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
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

### Login Example

```javascript
// Login.jsx
import { useState } from 'react';
import api from './api';

function Login() {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const { data } = await api.post('/auth/login', credentials);
      localStorage.setItem('access_token', data.meta.access_token);
      localStorage.setItem('refresh_token', data.meta.refresh_token);
      window.location.href = '/dashboard';
    } catch (err) {
      setError(err.response?.data?.errors?.[0]?.message || 'Login failed');
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
      {error && <p>{error}</p>}
      <button type="submit">Log In</button>
    </form>
  );
}
```

---

## Mobile Apps

### App Client

Use `/_allauth/app/v1/` for mobile applications.

**Key differences:**
- Uses `X-Session-Token` header (not cookies)
- No CSRF protection
- Token in response metadata

### Session Token Management

```javascript
// React Native
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';

const api = axios.create({
  baseURL: 'https://api.example.com/_allauth/app/v1',
});

// Add session token
api.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem('session_token');
  if (token) {
    config.headers['X-Session-Token'] = token;
  }
  return config;
});

// Store session token
api.interceptors.response.use(async (response) => {
  const token = response.data?.meta?.session_token;
  if (token) {
    await AsyncStorage.setItem('session_token', token);
  }
  return response;
});
```

### Secure Storage

**iOS:** Use Keychain
```javascript
import * as Keychain from 'react-native-keychain';

await Keychain.setGenericPassword('session_token', token);
const credentials = await Keychain.getGenericPassword();
```

**Android:** Use EncryptedStorage
```javascript
import EncryptedStorage from 'react-native-encrypted-storage';

await EncryptedStorage.setItem('session_token', token);
const token = await EncryptedStorage.getItem('session_token');
```

---

## OpenAPI Specification

Enable OpenAPI documentation:

```python
# settings.py (development only)
HEADLESS_SERVE_SPECIFICATION = DEBUG
```

**Endpoints:**
- `GET /_allauth/openapi` - Interactive documentation
- `GET /_allauth/openapi.yaml` - Raw OpenAPI spec

---

## Summary

The django-allauth headless API provides:
- Two client types (browser, app) with appropriate security
- Flexible token strategies (sessions, JWT)
- Complete authentication and account management endpoints
- Production-ready CORS configuration
- Mobile app support with secure token storage

**Next steps:**
- [security.md](./security.md) - Production hardening
- [social-providers.md](./social-providers.md) - OAuth setup
- [customization.md](./customization.md) - Adapting flows
