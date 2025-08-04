# Railway Setup Checklist

Follow these steps in order to set up both staging and production with persistent volumes.

## Part 1: Create Staging Service

- [ ] 1. Go to Railway Dashboard
- [ ] 2. Click "New Service" → "GitHub Repo"
- [ ] 3. Select `hdbookie/marine-seguros` repository
- [ ] 4. **IMPORTANT**: Change the service name to `marine-seguros-staging`
- [ ] 5. In Deploy settings, set branch to `staging`
- [ ] 6. Click "Deploy"

## Part 2: Add Volume to Staging

- [ ] 1. In staging service, go to "Settings" tab
- [ ] 2. Scroll down to "Volumes" section
- [ ] 3. Click "Add Volume"
- [ ] 4. Set:
  - Mount path: `/data`
  - Name: `marine-data-staging`
  - Size: 1GB
- [ ] 5. Click "Create Volume"

## Part 3: Configure Staging Environment Variables

- [ ] 1. In staging service, go to "Variables" tab
- [ ] 2. Add these variables:
  ```
  RAILWAY_ENVIRONMENT=staging
  DATA_PATH=/data
  PORT=8501
  GEMINI_API_KEY=<your-api-key>
  ```
- [ ] 3. Click "Add" for each variable

## Part 4: Add Volume to Production

- [ ] 1. Go to your production service (marine-seguros)
- [ ] 2. Go to "Settings" tab
- [ ] 3. Scroll down to "Volumes" section
- [ ] 4. Click "Add Volume"
- [ ] 5. Set:
  - Mount path: `/data`
  - Name: `marine-data-prod`
  - Size: 1GB (or larger for production)
- [ ] 6. Click "Create Volume"

## Part 5: Update Production Environment Variables

- [ ] 1. In production service, go to "Variables" tab
- [ ] 2. Add/Update these variables:
  ```
  RAILWAY_ENVIRONMENT=production
  DATA_PATH=/data
  PORT=8501
  GEMINI_API_KEY=<your-api-key>
  ```
- [ ] 3. Click "Add" or "Update" for each

## Part 6: Verify Deployments

### Staging:
- [ ] 1. Wait for staging to deploy (watch the logs)
- [ ] 2. Visit: `https://marine-seguros-staging.up.railway.app`
- [ ] 3. Check if the app loads correctly

### Production:
- [ ] 1. Production will redeploy automatically after adding volume
- [ ] 2. Visit: `https://marine-seguros.up.railway.app`
- [ ] 3. Ensure existing functionality still works

## Part 7: Test Data Persistence

### Test Staging:
- [ ] 1. Upload a test file in staging
- [ ] 2. Note the data shown
- [ ] 3. Trigger a redeploy (push to staging branch)
- [ ] 4. Check if data persists after redeploy

### Test Production:
- [ ] 1. Your existing data should remain
- [ ] 2. Upload a new file
- [ ] 3. Data should persist across deployments

## Troubleshooting

### If staging URL doesn't work:
1. Check service name is exactly `marine-seguros-staging`
2. Check deployment logs for errors
3. Verify environment variables are set

### If data doesn't persist:
1. Verify volume mount path is `/data`
2. Check `DATA_PATH=/data` environment variable
3. Look for errors in deployment logs

### If you see permission errors:
1. The volume should auto-create directories
2. Check logs for specific permission issues

## Success Indicators

✅ Both services have green status in Railway
✅ Both URLs are accessible
✅ Environment shows correctly in app (staging vs production)
✅ Data persists after redeployment
✅ Upload functionality works

## Next Steps

After setup is complete:
1. Set up GitHub Actions secrets (RAILWAY_TOKEN)
2. Test automated deployments
3. Set up monitoring/alerts
4. Document any custom configurations