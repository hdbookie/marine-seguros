# Setting Up Persistent Storage in Railway

## Problem
When deploying new versions to Railway, the SQLite database files (`data/dashboard.db` and `data/auth.db`) are lost because they're stored in the application directory, which gets replaced on each deployment.

## Solution
Use Railway's persistent volumes to store the database files outside the application directory.

## Steps to Configure in Railway

1. **Go to your Railway project dashboard**
2. **Click on your service (marine-seguros)**
3. **Go to the "Settings" tab**
4. **Scroll down to "Volumes"**
5. **Click "Add Volume"**
6. **Configure the volume:**
   - Mount path: `/data`
   - Name: `marine-data` (or any name you prefer)
   - Size: 1GB (or more if needed)
7. **Click "Create Volume"**

## Update Application Configuration

After creating the volume, the application code has been updated to automatically use the volume path.

### Environment Variable Configuration

1. In Railway, add an environment variable:
   - Name: `DATA_PATH`
   - Value: `/data`

2. The application will automatically use this path for:
   - SQLite database files (`dashboard.db` and `auth.db`)
   - Uploaded files storage
   - File registry

### What the Code Changes Do

The updated code checks for the `DATA_PATH` environment variable:
- If `DATA_PATH` is set (e.g., `/data` in production), it uses that path
- If not set, it defaults to the local `data` directory (for development)

This means:
- In Railway with volume: Files stored in `/data/` (persistent)
- In local development: Files stored in `./data/` (local directory)

## Verify Data Persistence

After setting up the volume:

1. Deploy your application
2. Upload some data through the web interface
3. Make another deployment
4. Check if the data persists

## Important Notes

- The volume is mounted at `/data` in the container
- All files stored in this directory will persist across deployments
- Make sure to backup important data regularly
- The volume is specific to your Railway environment