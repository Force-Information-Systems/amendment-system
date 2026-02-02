# Azure Deployment Guide - Amendment Tracking System

This guide will help you deploy the Amendment Tracking System to Azure so your colleagues can access it.

---

## 📋 Prerequisites

Before starting, ensure you have:

- [ ] Azure account with active subscription
- [ ] Azure CLI installed on your machine ([Download here](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli))
- [ ] Git installed
- [ ] Node.js and npm installed (for frontend build)
- [ ] Python 3.9+ installed

---

## 🏗️ Architecture Overview

We'll deploy two Azure App Services:

```
┌─────────────────────────────────────────────────────────┐
│                        USERS                            │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────┐
│  Azure Static Web App / App Service (Frontend)          │
│  • React Application                                    │
│  • URL: https://your-frontend.azurewebsites.net        │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────┐
│  Azure App Service (Backend)                            │
│  • FastAPI + Python                                     │
│  • SQLite Database (or Azure SQL)                       │
│  • URL: https://your-backend.azurewebsites.net         │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Deployment Options

### Option A: Quick Deployment (Recommended for Getting Started)
- Uses Azure App Service for both frontend and backend
- SQLite database (included in deployment)
- Fastest setup (~30 minutes)

### Option B: Production Deployment (Recommended for Company Use)
- Uses Azure Static Web Apps for frontend
- Azure App Service for backend
- Azure SQL Database (more robust)
- Better performance and scalability (~1-2 hours)

---

## 🎯 OPTION A: Quick Deployment (Recommended)

### Step 1: Login to Azure

```bash
# Login to Azure
az login

# Verify your subscription
az account show
```

### Step 2: Create Resource Group

```bash
# Create a resource group (choose your preferred region)
az group create --name amendment-system-rg --location eastus
```

Available locations: `eastus`, `westus`, `westeurope`, `uksouth`, etc.

### Step 3: Deploy Backend (FastAPI)

#### 3.1 Create App Service Plan

```bash
# Create an App Service Plan (B1 tier - suitable for small teams)
az appservice plan create \
  --name amendment-backend-plan \
  --resource-group amendment-system-rg \
  --sku B1 \
  --is-linux
```

**Cost:** B1 tier ~$13/month (can scale up/down as needed)

#### 3.2 Create Web App for Backend

```bash
# Create the backend web app (Python 3.9)
az webapp create \
  --resource-group amendment-system-rg \
  --plan amendment-backend-plan \
  --name your-amendment-backend \
  --runtime "PYTHON:3.9"
```

⚠️ **Replace `your-amendment-backend` with a unique name** (must be globally unique across Azure)

#### 3.3 Configure Backend Environment Variables

```bash
# Set environment variables
az webapp config appsettings set \
  --resource-group amendment-system-rg \
  --name your-amendment-backend \
  --settings \
    SECRET_KEY="$(openssl rand -hex 32)" \
    ALGORITHM="HS256" \
    ACCESS_TOKEN_EXPIRE_MINUTES="1440" \
    CORS_ORIGINS="https://your-amendment-frontend.azurewebsites.net" \
    DATABASE_URL="sqlite:///./amendment_system.db"
```

⚠️ **Replace `your-amendment-frontend` with your actual frontend app name** (you'll create this in Step 4)

#### 3.4 Deploy Backend Code

```bash
# Navigate to backend directory
cd /Users/wingle/Repos/amendment-system/backend

# Create a .zip file for deployment
zip -r backend-deploy.zip . -x "*.pyc" -x "__pycache__/*" -x "*.db" -x ".env"

# Deploy to Azure
az webapp deployment source config-zip \
  --resource-group amendment-system-rg \
  --name your-amendment-backend \
  --src backend-deploy.zip
```

#### 3.5 Configure Startup Command

```bash
# Set the startup command
az webapp config set \
  --resource-group amendment-system-rg \
  --name your-amendment-backend \
  --startup-file "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
```

#### 3.6 Copy Database to Azure

```bash
# Upload your database using FTP or Azure CLI
# First, get FTP credentials:
az webapp deployment list-publishing-credentials \
  --name your-amendment-backend \
  --resource-group amendment-system-rg

# Then use FTP client or Azure CLI to upload amendment_system.db
# Alternatively, create fresh database on Azure (users will need to be recreated)
```

#### 3.7 Verify Backend is Running

```bash
# Get the backend URL
az webapp show \
  --name your-amendment-backend \
  --resource-group amendment-system-rg \
  --query defaultHostName -o tsv

# Test the API
curl https://your-amendment-backend.azurewebsites.net/api/health
```

### Step 4: Deploy Frontend (React)

#### 4.1 Build the Frontend

```bash
# Navigate to frontend directory
cd /Users/wingle/Repos/amendment-system/frontend

# Update API endpoint in production build
# Create a production environment file
cat > .env.production << EOF
REACT_APP_API_URL=https://your-amendment-backend.azurewebsites.net
EOF

# Build the production bundle
npm install
npm run build
```

⚠️ **Replace `your-amendment-backend` with your actual backend app name**

#### 4.2 Update Frontend API Configuration

Before building, update the API client to use environment variable:

Edit `src/services/api.js`:

```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  // ... rest of config
});
```

#### 4.3 Create Web App for Frontend

```bash
# Create frontend web app (Node 18)
az webapp create \
  --resource-group amendment-system-rg \
  --plan amendment-backend-plan \
  --name your-amendment-frontend \
  --runtime "NODE:18-lts"
```

⚠️ **Replace `your-amendment-frontend` with a unique name**

#### 4.4 Deploy Frontend Build

```bash
# Navigate to build directory
cd /Users/wingle/Repos/amendment-system/frontend

# Create deployment package
cd build
zip -r ../frontend-deploy.zip .
cd ..

# Deploy to Azure
az webapp deployment source config-zip \
  --resource-group amendment-system-rg \
  --name your-amendment-frontend \
  --src frontend-deploy.zip
```

#### 4.5 Configure Frontend for SPA Routing

```bash
# Create web.config for proper React routing
cat > web.config << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <system.webServer>
    <rewrite>
      <rules>
        <rule name="React Routes" stopProcessing="true">
          <match url=".*" />
          <conditions logicalGrouping="MatchAll">
            <add input="{REQUEST_FILENAME}" matchType="IsFile" negate="true" />
            <add input="{REQUEST_FILENAME}" matchType="IsDirectory" negate="true" />
          </conditions>
          <action type="Rewrite" url="/" />
        </rule>
      </rules>
    </rewrite>
  </system.webServer>
</configuration>
EOF

# Add web.config to build and redeploy
```

### Step 5: Update CORS Settings

```bash
# Update backend CORS to allow frontend domain
az webapp config appsettings set \
  --resource-group amendment-system-rg \
  --name your-amendment-backend \
  --settings \
    CORS_ORIGINS="https://your-amendment-frontend.azurewebsites.net"

# Restart backend
az webapp restart \
  --name your-amendment-backend \
  --resource-group amendment-system-rg
```

### Step 6: Access Your Application

```bash
# Get your frontend URL
az webapp show \
  --name your-amendment-frontend \
  --resource-group amendment-system-rg \
  --query defaultHostName -o tsv
```

🎉 **Your application is now live!**

Access it at: `https://your-amendment-frontend.azurewebsites.net`

---

## 🔐 Security Configuration

### Enable HTTPS Only

```bash
# Backend
az webapp update \
  --resource-group amendment-system-rg \
  --name your-amendment-backend \
  --https-only true

# Frontend
az webapp update \
  --resource-group amendment-system-rg \
  --name your-amendment-frontend \
  --https-only true
```

### Configure Authentication (Optional but Recommended)

```bash
# Enable Azure AD authentication
az webapp auth update \
  --resource-group amendment-system-rg \
  --name your-amendment-frontend \
  --enabled true \
  --action LoginWithAzureActiveDirectory
```

---

## 👥 User Management

### Creating User Accounts

Since you're deploying to Azure, you have two options:

**Option 1: Use existing local database**
- Upload your current `amendment_system.db` which already has 4 user accounts
- Users can login with their existing credentials

**Option 2: Create new users via API**

```bash
# SSH into backend app
az webapp ssh --name your-amendment-backend --resource-group amendment-system-rg

# Run Python script to create users
python3 << EOF
from app.database import get_db
from app import crud
from app.models import Employee

db = next(get_db())

# Create admin user
employee = db.query(Employee).filter(Employee.email == "admin@yourcompany.com").first()
if employee:
    crud.set_employee_password(db, employee.employee_id, "SecurePassword123!")
    print(f"Created user: {employee.email}")
EOF
```

---

## 📊 Monitoring and Logs

### View Application Logs

```bash
# Stream backend logs
az webapp log tail \
  --name your-amendment-backend \
  --resource-group amendment-system-rg

# Stream frontend logs
az webapp log tail \
  --name your-amendment-frontend \
  --resource-group amendment-system-rg
```

### Enable Application Insights (Recommended)

```bash
# Create Application Insights
az monitor app-insights component create \
  --app amendment-insights \
  --location eastus \
  --resource-group amendment-system-rg

# Get instrumentation key
INSTRUMENTATION_KEY=$(az monitor app-insights component show \
  --app amendment-insights \
  --resource-group amendment-system-rg \
  --query instrumentationKey -o tsv)

# Configure backend to use Application Insights
az webapp config appsettings set \
  --resource-group amendment-system-rg \
  --name your-amendment-backend \
  --settings APPINSIGHTS_INSTRUMENTATIONKEY=$INSTRUMENTATION_KEY
```

---

## 💰 Cost Estimate

Based on B1 App Service Plan:

| Service | Estimated Cost |
|---------|----------------|
| App Service Plan (B1) | ~$13/month |
| Backend Web App | Included in plan |
| Frontend Web App | Included in plan |
| Storage (if using blob) | ~$1-5/month |
| **Total** | **~$14-18/month** |

You can share this across your entire team at this cost!

---

## 🔄 Updates and Maintenance

### Updating the Application

**Backend updates:**
```bash
cd /Users/wingle/Repos/amendment-system/backend
zip -r backend-deploy.zip . -x "*.pyc" -x "__pycache__/*" -x "*.db" -x ".env"
az webapp deployment source config-zip \
  --resource-group amendment-system-rg \
  --name your-amendment-backend \
  --src backend-deploy.zip
```

**Frontend updates:**
```bash
cd /Users/wingle/Repos/amendment-system/frontend
npm run build
cd build
zip -r ../frontend-deploy.zip .
cd ..
az webapp deployment source config-zip \
  --resource-group amendment-system-rg \
  --name your-amendment-frontend \
  --src frontend-deploy.zip
```

### Backup Database

```bash
# Download current database
az webapp ssh --name your-amendment-backend --resource-group amendment-system-rg
# Then: cat amendment_system.db > /tmp/backup.db
# Download via FTP or Azure CLI
```

---

## 🆘 Troubleshooting

### Backend not starting?

```bash
# Check logs
az webapp log tail --name your-amendment-backend --resource-group amendment-system-rg

# Check configuration
az webapp config appsettings list --name your-amendment-backend --resource-group amendment-system-rg

# Restart app
az webapp restart --name your-amendment-backend --resource-group amendment-system-rg
```

### Frontend showing blank page?

1. Check if API endpoint is correct in `.env.production`
2. Verify CORS settings on backend
3. Check browser console for errors
4. Ensure web.config is deployed for SPA routing

### Database issues?

1. Verify database file exists in `/home/site/wwwroot/`
2. Check file permissions
3. Consider migrating to Azure SQL for production

---

## 📞 Support

If you encounter issues:

1. Check Azure Portal logs
2. Review Application Insights (if enabled)
3. Test API endpoints directly: `https://your-backend.azurewebsites.net/docs`
4. Verify environment variables are set correctly

---

## ✅ Post-Deployment Checklist

- [ ] Backend is accessible and returns API docs
- [ ] Frontend loads in browser
- [ ] Can login successfully
- [ ] Can view amendments list
- [ ] HTTPS is enforced
- [ ] CORS is configured correctly
- [ ] Environment variables are set
- [ ] Monitoring/logging is enabled
- [ ] Database is accessible
- [ ] Users can be created/managed
- [ ] Share URL with colleagues!

---

## 🎉 Success!

Your Amendment Tracking System is now deployed to Azure!

**Share with colleagues:**
- URL: `https://your-amendment-frontend.azurewebsites.net`
- Admin credentials: (securely share through proper channels)

---

**Need help?** Check the troubleshooting section or review Azure App Service documentation.
