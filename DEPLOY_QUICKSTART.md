# Azure Deployment - Quick Start

Get your Amendment System online in 15 minutes!

## Prerequisites

1. **Azure account** - Create one at https://azure.microsoft.com/free
2. **Azure CLI** - Install from https://docs.microsoft.com/en-us/cli/azure/install-azure-cli

## Automated Deployment (Easiest)

### Option 1: One-Click Script

```bash
# Navigate to project directory
cd /Users/wingle/Repos/amendment-system

# Run the automated deployment script
./deploy-to-azure.sh
```

The script will:
- ✅ Create all Azure resources
- ✅ Deploy backend (Python/FastAPI)
- ✅ Deploy frontend (React)
- ✅ Configure HTTPS
- ✅ Set up CORS
- ✅ Give you the live URLs

**Time:** ~10-15 minutes

### What You'll Need

When running the script, you'll be asked for:

1. **Backend app name** - Choose a unique name (e.g., `yourcompany-amendment-backend`)
2. **Frontend app name** - Choose a unique name (e.g., `yourcompany-amendment-frontend`)

💡 **Tip:** Use your company name to make it unique!

## Manual Deployment

If you prefer step-by-step control, follow: [`AZURE_DEPLOYMENT_GUIDE.md`](./AZURE_DEPLOYMENT_GUIDE.md)

## After Deployment

### 1. Upload Your Database (Important!)

Your current database has 789 amendments and 4 user accounts. You need to upload it:

```bash
# Get your backend app name from deployment
BACKEND_APP="your-amendment-backend"

# Use Azure CLI to upload database
az webapp ssh --name $BACKEND_APP --resource-group amendment-system-rg

# Once connected, upload your database file
# (Use FTP, FTPS, or Azure Storage Explorer)
```

**Alternative:** Let Azure create a fresh database and manually recreate users.

### 2. Test the Application

```bash
# Visit your frontend URL (you'll get this from the deployment)
https://your-amendment-frontend.azurewebsites.net

# Login with your existing credentials
Username: william-fis
Password: fis123
```

### 3. Share with Colleagues

Send them the frontend URL and their login credentials!

## Cost

💰 **~$13-18/month** for unlimited colleagues to use the system

- App Service Plan (B1): ~$13/month
- Storage: ~$1-5/month

You can scale up/down anytime based on usage.

## Troubleshooting

### Backend not responding?

```bash
# Check backend logs
az webapp log tail --name your-amendment-backend --resource-group amendment-system-rg

# Restart backend
az webapp restart --name your-amendment-backend --resource-group amendment-system-rg
```

### Frontend showing errors?

1. Check browser console (F12)
2. Verify API URL is correct:
   ```bash
   cat frontend/.env.production
   ```
3. Make sure CORS is configured on backend

### Can't login?

1. Verify database was uploaded correctly
2. Check that user accounts exist
3. Ensure passwords are set correctly

## Updating the Application

### Update Backend

```bash
cd backend
zip -r backend-deploy.zip . -x "*.pyc" -x "__pycache__/*" -x "*.db" -x ".env"
az webapp deployment source config-zip \
  --resource-group amendment-system-rg \
  --name your-amendment-backend \
  --src backend-deploy.zip
```

### Update Frontend

```bash
cd frontend
npm run build
cd build
zip -r ../frontend-deploy.zip .
cd ..
az webapp deployment source config-zip \
  --resource-group amendment-system-rg \
  --name your-amendment-frontend \
  --src frontend-deploy.zip
```

## Custom Domain (Optional)

Want to use your company domain like `amendments.yourcompany.com`?

```bash
# Add custom domain
az webapp config hostname add \
  --webapp-name your-amendment-frontend \
  --resource-group amendment-system-rg \
  --hostname amendments.yourcompany.com

# Enable SSL
az webapp config ssl bind \
  --name your-amendment-frontend \
  --resource-group amendment-system-rg \
  --certificate-thumbprint <thumbprint> \
  --ssl-type SNI
```

## Monitoring

### View Logs

```bash
# Real-time backend logs
az webapp log tail --name your-amendment-backend --resource-group amendment-system-rg

# Real-time frontend logs
az webapp log tail --name your-amendment-frontend --resource-group amendment-system-rg
```

### Check Resource Usage

```bash
# View resource group
az group show --name amendment-system-rg

# List all resources
az resource list --resource-group amendment-system-rg -o table
```

## Cleanup (Delete Everything)

If you want to remove everything from Azure:

```bash
# Delete the entire resource group
az group delete --name amendment-system-rg

# Confirm deletion when prompted
```

⚠️ **Warning:** This deletes ALL resources and data. Make sure to backup your database first!

## Support

- 📖 Full guide: [`AZURE_DEPLOYMENT_GUIDE.md`](./AZURE_DEPLOYMENT_GUIDE.md)
- 🐛 Issues: Check Azure Portal logs
- 📊 Monitoring: Enable Application Insights in Azure Portal

## Success Checklist

After deployment, verify:

- [ ] Frontend loads at your Azure URL
- [ ] Backend API docs accessible at `/docs`
- [ ] Can login successfully
- [ ] Can view amendments list
- [ ] HTTPS is enforced (lock icon in browser)
- [ ] Colleagues can access the URL

## Next Steps

1. **Enable monitoring** - Set up Application Insights
2. **Configure backups** - Regular database backups
3. **Set up alerts** - Get notified if app goes down
4. **Custom domain** - Use your company domain
5. **Azure AD auth** - Single sign-on for your organization

---

**Ready to deploy?** Run `./deploy-to-azure.sh` and you'll be live in minutes! 🚀
