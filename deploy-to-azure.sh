#!/bin/bash

# Amendment System - Azure Deployment Script
# This script automates the deployment to Azure

set -e  # Exit on error

echo "=============================================="
echo "  Amendment System - Azure Deployment"
echo "=============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
RESOURCE_GROUP="amendment-system-rg"
LOCATION="eastus"
APP_PLAN="amendment-backend-plan"
BACKEND_APP=""
FRONTEND_APP=""

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}! $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed. Please install it first."
    echo "Visit: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

print_success "Azure CLI is installed"

# Check if logged in
if ! az account show &> /dev/null; then
    print_warning "Not logged into Azure. Logging in..."
    az login
fi

print_success "Logged into Azure"

# Get app names from user
echo ""
echo "Enter your application names (must be globally unique):"
read -p "Backend app name (e.g., mycompany-amendment-backend): " BACKEND_APP
read -p "Frontend app name (e.g., mycompany-amendment-frontend): " FRONTEND_APP

if [ -z "$BACKEND_APP" ] || [ -z "$FRONTEND_APP" ]; then
    print_error "App names cannot be empty"
    exit 1
fi

echo ""
echo "Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Location: $LOCATION"
echo "  Backend: $BACKEND_APP"
echo "  Frontend: $FRONTEND_APP"
echo ""
read -p "Proceed with deployment? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Deployment cancelled"
    exit 0
fi

# Create resource group
echo ""
echo "Step 1: Creating resource group..."
if az group create --name "$RESOURCE_GROUP" --location "$LOCATION" &> /dev/null; then
    print_success "Resource group created"
else
    print_warning "Resource group already exists or failed to create"
fi

# Create App Service Plan
echo ""
echo "Step 2: Creating App Service Plan..."
if az appservice plan create \
    --name "$APP_PLAN" \
    --resource-group "$RESOURCE_GROUP" \
    --sku B1 \
    --is-linux &> /dev/null; then
    print_success "App Service Plan created"
else
    print_warning "App Service Plan already exists or failed to create"
fi

# Deploy Backend
echo ""
echo "Step 3: Deploying Backend..."
echo "  3.1: Creating backend web app..."
if az webapp create \
    --resource-group "$RESOURCE_GROUP" \
    --plan "$APP_PLAN" \
    --name "$BACKEND_APP" \
    --runtime "PYTHON:3.9" &> /dev/null; then
    print_success "Backend web app created"
else
    print_warning "Backend web app already exists or failed to create"
fi

echo "  3.2: Configuring backend settings..."
SECRET_KEY=$(openssl rand -hex 32)
az webapp config appsettings set \
    --resource-group "$RESOURCE_GROUP" \
    --name "$BACKEND_APP" \
    --settings \
        SECRET_KEY="$SECRET_KEY" \
        ALGORITHM="HS256" \
        ACCESS_TOKEN_EXPIRE_MINUTES="1440" \
        CORS_ORIGINS="https://${FRONTEND_APP}.azurewebsites.net" \
        DATABASE_URL="sqlite:///./amendment_system.db" \
    &> /dev/null

print_success "Backend settings configured"

echo "  3.3: Packaging backend code..."
cd backend
zip -r backend-deploy.zip . -x "*.pyc" -x "__pycache__/*" -x "*.db" -x ".env" &> /dev/null
print_success "Backend code packaged"

echo "  3.4: Deploying backend to Azure..."
az webapp deployment source config-zip \
    --resource-group "$RESOURCE_GROUP" \
    --name "$BACKEND_APP" \
    --src backend-deploy.zip &> /dev/null

print_success "Backend deployed"

echo "  3.5: Setting startup command..."
az webapp config set \
    --resource-group "$RESOURCE_GROUP" \
    --name "$BACKEND_APP" \
    --startup-file "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000" \
    &> /dev/null

print_success "Backend startup command set"
cd ..

# Deploy Frontend
echo ""
echo "Step 4: Deploying Frontend..."
echo "  4.1: Creating .env.production file..."
cd frontend
cat > .env.production << EOF
REACT_APP_API_URL=https://${BACKEND_APP}.azurewebsites.net/api
GENERATE_SOURCEMAP=false
EOF

print_success ".env.production created"

echo "  4.2: Installing dependencies..."
npm install &> /dev/null
print_success "Dependencies installed"

echo "  4.3: Building production bundle..."
npm run build &> /dev/null
print_success "Production bundle built"

echo "  4.4: Creating frontend web app..."
if az webapp create \
    --resource-group "$RESOURCE_GROUP" \
    --plan "$APP_PLAN" \
    --name "$FRONTEND_APP" \
    --runtime "NODE:18-lts" &> /dev/null; then
    print_success "Frontend web app created"
else
    print_warning "Frontend web app already exists or failed to create"
fi

echo "  4.5: Packaging frontend build..."
cd build
zip -r ../frontend-deploy.zip . &> /dev/null
cd ..
print_success "Frontend build packaged"

echo "  4.6: Deploying frontend to Azure..."
az webapp deployment source config-zip \
    --resource-group "$RESOURCE_GROUP" \
    --name "$FRONTEND_APP" \
    --src frontend-deploy.zip &> /dev/null

print_success "Frontend deployed"
cd ..

# Enable HTTPS
echo ""
echo "Step 5: Securing applications..."
az webapp update \
    --resource-group "$RESOURCE_GROUP" \
    --name "$BACKEND_APP" \
    --https-only true &> /dev/null

az webapp update \
    --resource-group "$RESOURCE_GROUP" \
    --name "$FRONTEND_APP" \
    --https-only true &> /dev/null

print_success "HTTPS enabled for both apps"

# Restart apps
echo ""
echo "Step 6: Restarting applications..."
az webapp restart --name "$BACKEND_APP" --resource-group "$RESOURCE_GROUP" &> /dev/null
az webapp restart --name "$FRONTEND_APP" --resource-group "$RESOURCE_GROUP" &> /dev/null
print_success "Applications restarted"

# Get URLs
BACKEND_URL="https://${BACKEND_APP}.azurewebsites.net"
FRONTEND_URL="https://${FRONTEND_APP}.azurewebsites.net"

echo ""
echo "=============================================="
echo "  🎉 Deployment Complete!"
echo "=============================================="
echo ""
echo "Your Amendment System is now live on Azure!"
echo ""
echo "Frontend URL: $FRONTEND_URL"
echo "Backend URL:  $BACKEND_URL"
echo "API Docs:     ${BACKEND_URL}/docs"
echo ""
echo "Next steps:"
echo "1. Visit $FRONTEND_URL to access the application"
echo "2. Create user accounts or upload your database"
echo "3. Share the URL with your colleagues!"
echo ""
print_warning "Note: Database is empty. You need to either:"
echo "  - Upload your existing amendment_system.db file"
echo "  - Create new user accounts via the backend API"
echo ""
echo "To view logs:"
echo "  Backend:  az webapp log tail --name $BACKEND_APP --resource-group $RESOURCE_GROUP"
echo "  Frontend: az webapp log tail --name $FRONTEND_APP --resource-group $RESOURCE_GROUP"
echo ""
