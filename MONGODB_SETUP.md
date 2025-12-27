# MongoDB Atlas Setup for Render Deployment

## Quick Setup Steps

### 1. Create MongoDB Atlas Account
- Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
- Sign up with your email (free tier available)
- Create a new organization and project

### 2. Create a Free Cluster
- Click "Create" → Select "Free" tier
- Choose a cloud provider (AWS, Google Cloud, or Azure)
- Select a region close to your Render deployment (US, EU, etc.)
- Click "Create Cluster"

### 3. Create Database User
- In the left sidebar, go to **Database Access**
- Click "Add New Database User"
- Create username and password (save these!)
- Select "Built-in Role" → "Atlas admin"
- Click "Add User"

### 4. Whitelist IP Addresses
- Go to **Network Access** in the left sidebar
- Click "Add IP Address"
- Select "Allow access from anywhere" (0.0.0.0/0) for Render deployments
- Confirm

### 5. Get Your Connection String
- Go to **Databases** and click "Connect" on your cluster
- Select "Drivers" → "Python"
- Copy the connection string
- Format: `mongodb+srv://username:password@cluster.mongodb.net/divsa_polymers?retryWrites=true&w=majority`

### 6. Add to Render Environment Variables
In your Render dashboard:
1. Go to your app's **Environment** settings
2. Add a new environment variable:
   - **Key**: `DATABASE_URL`
   - **Value**: Your MongoDB connection string (replace `<password>` with your actual password)

### 7. Update Local .env (Optional)
For local testing, add to `.env`:
```
DATABASE_URL=mongodb+srv://username:password@cluster.mongodb.net/divsa_polymers?retryWrites=true&w=majority
```

### 8. Deploy
Push your changes to your repository:
```bash
git add .
git commit -m "Add MongoDB support for production"
git push
```
Render will automatically redeploy with the new DATABASE_URL.

## Notes
- The app automatically creates the `Inquiry` collection on first run
- MongoDB free tier has 512MB storage (sufficient for inquiry data)
- All your inquiry data will persist in MongoDB Atlas
- You can view/manage data directly in the MongoDB Atlas dashboard

## Troubleshooting
- **Connection failed**: Check IP whitelist and username/password in connection string
- **Database not found**: Collection is created automatically on first inquiry submission
- **Slow connections**: You might be using a region far from Render; adjust in MongoDB Atlas
