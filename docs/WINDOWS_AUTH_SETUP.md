# Windows Authentication / Active Directory Setup Guide

## Overview

The Amendment Tracking System supports **hybrid authentication**:
1. **Windows/Active Directory** (LDAP) - Primary authentication method
2. **Local password authentication** - Fallback method

When Windows/AD authentication is enabled, the system will:
- Try to authenticate against Active Directory first
- Fall back to local password authentication if AD fails
- Auto-create employee accounts from AD on first login
- Set new AD users with "User" role (admins must be manually promoted)

## Prerequisites

- Access to Active Directory server
- LDAP/LDAPS connectivity to AD server
- Service account credentials (optional, but recommended for search operations)
- Python package `ldap3` (already installed)

## Configuration

### Step 1: Configure Environment Variables

Copy `.env.example` to `.env` and configure the Active Directory settings:

```bash
# Active Directory / LDAP Configuration
AD_ENABLED=true
AD_SERVER=ldap://dc.yourcompany.com
AD_PORT=389
AD_USE_SSL=false
AD_DOMAIN=YOURCOMPANY
AD_SEARCH_BASE=DC=yourcompany,DC=com
```

### Configuration Parameters Explained

| Parameter | Description | Example |
|-----------|-------------|---------|
| `AD_ENABLED` | Set to `true` to enable AD authentication | `true` |
| `AD_SERVER` | LDAP URL of your AD server | `ldap://dc.company.com` or `ldaps://dc.company.com` |
| `AD_PORT` | LDAP port (389 for LDAP, 636 for LDAPS) | `389` |
| `AD_USE_SSL` | Use SSL/TLS (LDAPS) | `true` for port 636, `false` for port 389 |
| `AD_DOMAIN` | NetBIOS domain name | `COMPANY` |
| `AD_SEARCH_BASE` | LDAP search base for user lookups | `DC=company,DC=com` |

### Step 2: Find Your AD Server Information

#### Windows (from command prompt):
```cmd
# Find domain controller
nslookup _ldap._tcp.dc._msdcs.YOURDOMAIN.COM

# Test LDAP connectivity
ldp.exe
```

#### Linux/Mac:
```bash
# Find domain controller
dig _ldap._tcp.dc._msdcs.yourdomain.com SRV

# Test LDAP connectivity
ldapsearch -x -H ldap://dc.company.com -b "DC=company,DC=com"
```

### Step 3: Restart the Backend Server

After configuring `.env`, restart the backend:

```bash
cd backend
python3 -m uvicorn app.main:app --reload
```

## How It Works

### Authentication Flow

```
User Login
    ↓
Is AD_ENABLED=true?
    ↓
YES → Try AD Authentication
    ↓
AD Success?
    ↓
YES → Employee exists in DB?
    ↓
NO → Auto-create employee from AD
    ↓
Generate JWT token → Login successful
    ↓
NO (AD failed) → Try local password authentication
    ↓
Local auth success? → Login successful
    ↓
NO → Login failed (401 error)
```

### Auto-Created Employee Fields

When a user logs in with AD for the first time:

| Field | Value |
|-------|-------|
| `employee_name` | From AD `displayName` attribute |
| `email` | From AD `mail` attribute |
| `windows_login` | Username used for login |
| `role` | **User** (default - must be manually promoted to Admin) |
| `is_active` | `true` |
| `password_hash` | `NULL` (AD-only users don't need local password) |

### Promoting AD Users to Admin

AD users are created with "User" role by default. To promote to Admin:

**Option 1: Using SQL**
```sql
UPDATE employees
SET role = 'Admin'
WHERE windows_login = 'username';
```

**Option 2: Using Admin UI**
1. Login as an existing admin
2. Go to Admin → Employees
3. Edit the employee and change role to "Admin"

## Testing AD Authentication

### Test 1: Verify AD Configuration

```bash
cd /Users/wingle/Repos/amendment-system

# Create test script
cat > test_ad_auth.py << 'EOF'
import os
os.environ['AD_ENABLED'] = 'true'
os.environ['AD_SERVER'] = 'ldap://your-dc.company.com'
os.environ['AD_DOMAIN'] = 'COMPANY'
os.environ['AD_SEARCH_BASE'] = 'DC=company,DC=com'

from backend.app.auth import authenticate_windows_user

# Test with your AD credentials
result = authenticate_windows_user('your_username', 'your_password')

if result:
    print("✓ AD Authentication successful!")
    print(f"  Username: {result['username']}")
    print(f"  Display Name: {result['display_name']}")
    print(f"  Email: {result['email']}")
else:
    print("✗ AD Authentication failed")
EOF

python3 test_ad_auth.py
```

### Test 2: Login via API

```bash
# Test AD user login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "ad_username", "password": "ad_password"}'

# Should return JWT token
```

### Test 3: Verify Auto-Created Employee

```bash
# Check if employee was created
curl http://localhost:8000/api/employees?windows_login=ad_username
```

## Troubleshooting

### Issue 1: "Failed to connect to AD server"

**Possible causes:**
- AD server not accessible from network
- Firewall blocking LDAP port (389/636)
- Incorrect `AD_SERVER` URL

**Solutions:**
```bash
# Test connectivity
ping dc.company.com
telnet dc.company.com 389

# Check firewall
sudo nmap -p 389,636 dc.company.com
```

### Issue 2: "Invalid credentials" but credentials are correct

**Possible causes:**
- Wrong `AD_DOMAIN` format
- User account locked or disabled in AD
- Password expired

**Solutions:**
- Verify domain: Use NetBIOS name (e.g., `COMPANY` not `company.com`)
- Check user status in Active Directory Users and Computers
- Try logging in on a Windows machine first

### Issue 3: "LDAP Bind Error"

**Possible causes:**
- Username format incorrect
- User not in search base
- Insufficient permissions

**Solutions:**
```python
# Try different username formats:
# 1. NetBIOS format: DOMAIN\username
# 2. UPN format: username@domain.com
# 3. DN format: CN=User Name,OU=Users,DC=domain,DC=com
```

### Issue 4: User attributes not found

**Possible causes:**
- Search base incorrect
- User in different OU
- Attributes not populated in AD

**Solutions:**
```bash
# Search for user manually
ldapsearch -x -H ldap://dc.company.com \
  -b "DC=company,DC=com" \
  "(sAMAccountName=username)" \
  displayName mail cn
```

## Security Best Practices

### 1. Use LDAPS (SSL/TLS)

For production, always use encrypted LDAP:

```bash
AD_SERVER=ldaps://dc.company.com
AD_PORT=636
AD_USE_SSL=true
```

### 2. Network Security

- Run AD authentication on internal network only
- Use VPN for remote access
- Restrict LDAP port access with firewall

### 3. Service Account (Optional)

For advanced scenarios, use a dedicated service account:

```bash
AD_BIND_USER=CN=AppService,OU=ServiceAccounts,DC=company,DC=com
AD_BIND_PASSWORD=secure_password_here
```

### 4. Audit Logging

Monitor authentication attempts:

```bash
# Check application logs
tail -f backend/logs/auth.log

# SQL query for login activity
SELECT employee_name, windows_login, last_login, role
FROM employees
WHERE last_login > datetime('now', '-7 days')
ORDER BY last_login DESC;
```

## Local Authentication Fallback

Even with AD enabled, local password authentication still works:

1. **Admin account** (created during setup):
   - Username: `admin`
   - Password: `admin123`

2. **Any employee with password_hash set**:
   - System tries AD first
   - Falls back to local password if AD fails
   - Useful for:
     - Testing
     - Emergency access when AD is down
     - Non-AD users (contractors, external users)

## Disabling AD Authentication

To temporarily disable AD authentication:

```bash
# In .env file
AD_ENABLED=false
```

Or comment out the AD configuration:

```bash
# AD_ENABLED=true
```

The system will fall back to local password authentication only.

## Common AD Configurations

### Standard Active Directory
```bash
AD_ENABLED=true
AD_SERVER=ldap://dc01.company.com
AD_PORT=389
AD_USE_SSL=false
AD_DOMAIN=COMPANY
AD_SEARCH_BASE=DC=company,DC=com
```

### Secure LDAP (LDAPS)
```bash
AD_ENABLED=true
AD_SERVER=ldaps://dc01.company.com
AD_PORT=636
AD_USE_SSL=true
AD_DOMAIN=COMPANY
AD_SEARCH_BASE=DC=company,DC=com
```

### Multi-Domain Forest
```bash
AD_ENABLED=true
AD_SERVER=ldap://dc01.company.com
AD_PORT=389
AD_USE_SSL=false
AD_DOMAIN=COMPANY
AD_SEARCH_BASE=DC=company,DC=com
# Users can login with: COMPANY\username or SUBSIDIARY\username
```

### With Global Catalog
```bash
AD_ENABLED=true
AD_SERVER=ldap://dc01.company.com
AD_PORT=3268  # Global Catalog port
AD_USE_SSL=false
AD_DOMAIN=COMPANY
AD_SEARCH_BASE=GC=company,GC=com
```

## Support

For issues or questions:
1. Check application logs: `backend/logs/`
2. Enable debug mode: `SQL_ECHO=True` in `.env`
3. Review LDAP connectivity with `ldp.exe` (Windows) or `ldapsearch` (Linux/Mac)

## Summary

✅ **Phase 2 Complete**: Windows/Active Directory integration implemented!

**Key Features:**
- LDAP authentication against Active Directory
- Auto-creation of employee accounts on first AD login
- Fallback to local password authentication
- Secure NTLM authentication
- Comprehensive error handling
- Production-ready with LDAPS support

**Default Behavior:**
- AD disabled by default (set `AD_ENABLED=true` to enable)
- Local admin account always works
- AD users get "User" role (promote to Admin manually)
- Failed AD auth falls back to local password
