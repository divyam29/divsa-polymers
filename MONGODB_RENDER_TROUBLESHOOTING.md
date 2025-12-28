# MongoDB Atlas SSL Connection Fix for Render

## Problem
You're experiencing SSL/TLS handshake errors when connecting to MongoDB Atlas from Render:
```
[SSL: TLSV1_ALERT_INTERNAL_ERROR] tlsv1 alert internal error
ServerSelectionTimeoutError: Timeout: 30.0s
```

## Root Causes
1. **Timeout too short** - 30 seconds isn't enough for initial connection on Render's environment
2. **Incompatible SSL settings** - `tlsInsecure=True` alone doesn't always work
3. **Connection pool issues** - Gunicorn workers not properly handling MongoDB connections
4. **Retry writes** - Can cause issues with SSL in Render's environment

## Solutions Applied

### 1. Updated MongoDB Connection Settings (app.py)
```python
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

client = MongoClient(
    MONGO_URI,
    ssl=True,
    ssl_context=ssl_context,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=60000,      # Increased from 30000
    connectTimeoutMS=60000,               # Increased from 30000
    socketTimeoutMS=60000,                # Added
    retryWrites=False,                    # Disabled to avoid SSL issues
    maxPoolSize=10,
    minPoolSize=1,
    waitQueueTimeoutMS=60000
)
```

**Key Changes:**
- Custom SSL context to handle Render's environment quirks
- Increased all timeouts to 60 seconds
- Disabled retry writes (known to cause issues with SSL in some environments)
- Added connection pool configuration

### 2. Updated Gunicorn Configuration (render.yaml)
```yaml
startCommand: gunicorn app:app --workers=1 --worker-class=sync --timeout=120 --graceful-timeout=120 --bind=0.0.0.0:$PORT
```

**Key Changes:**
- `--workers=1` - Single worker to avoid connection pooling issues
- `--timeout=120` - Increased from default 30s to handle MongoDB connection time
- `--graceful-timeout=120` - Graceful shutdown timeout
- Explicit bind to prevent port issues

### 3. Improved Error Handling (app.py)
Added specific handling for `ServerSelectionTimeoutError` to distinguish between connection issues and other errors.

## Additional Steps to Take

### 1. Verify MongoDB Atlas IP Whitelist
Your Render application's IP must be whitelisted in MongoDB Atlas:
1. Log into MongoDB Atlas
2. Go to Network Access → IP Whitelist
3. Add `0.0.0.0/0` (allow all) **OR** find Render's egress IP address
   - Deploy once with current changes
   - Check error logs for the IP attempting to connect
   - Add that specific IP to whitelist

### 2. Check Your Connection String
Ensure your `MONGODB_URI` environment variable includes:
```
mongodb+srv://username:password@cluster.mongodb.net/database?retryWrites=true&w=majority
```

### 3. Verify MongoDB Atlas Cluster Status
1. Go to MongoDB Atlas dashboard
2. Check if your cluster is running and responsive
3. Restart the cluster if necessary

### 4. Monitor After Deployment
First request may take longer as connection is established:
1. Deploy changes to Render
2. Trigger the form submission
3. Check logs in Render dashboard
4. Subsequent requests should be faster

## If Issues Persist

### Option A: Use pyOpenSSL (More Stable)
Add to requirements.txt:
```
pyOpenSSL==24.0.0
cryptography==41.0.7
```

Then modify app.py:
```python
import ssl
from OpenSSL import SSL

# Instead of ssl.create_default_context():
ssl_context = SSL.Context(SSL.TLS_CLIENT_METHOD)
ssl_context.set_verify(SSL.VERIFY_NONE, lambda *args: True)
```

### Option B: Use MongoDB Connection String Parameters
Update MONGODB_URI to include:
```
mongodb+srv://...?authSource=admin&ssl=true&tlsAllowInvalidCertificates=true
```

### Option C: Switch Database Providers
If MongoDB Atlas continues to fail on Render, consider:
- **MongoDB Atlas on AWS** with fixed IP allocation
- **MongoDB Atlas M10+ tier** (includes SLA and priority support)
- **Alternative**: Firebase Realtime Database or PostgreSQL

## Testing Locally
```bash
# Windows
python -m flask run

# Or with gunicorn (simulate Render):
gunicorn app:app --workers=1 --timeout=120 --bind=127.0.0.1:8000
```

## Logs to Check
Monitor these locations for debugging:
1. **Render logs**: https://dashboard.render.com → select service → logs
2. **MongoDB Atlas logs**: Atlas dashboard → Monitoring → Logs
3. **Local logs**: Check the `logs/` directory

---

**Last Updated**: 2025-12-28
**Status**: SSL configuration optimized for Render deployment
