# Production Deployment Guide

This guide explains how to take EduPortal from "Localhost" to a production Ubuntu VPS (e.g., DigitalOcean, AWS EC2).

## 1. Production Environment Configuration

In production, security and performance are paramount.

### A. The `.env` File
Create a robust `.env` file on your server (do NOT check this into Git):

```ini
# Security
SECRET_KEY=Input_A_Very_Long_Random_String_Here_Use_Python_Secrets
FLASK_ENV=production
FLASK_DEBUG=0

# Database (PostgreSQL is Mandatory for Prod)
# Format: postgresql://user:password@host:port/dbname
DATABASE_URL=postgresql://edu_admin:StrongPass123!@localhost:5432/eduportal_prod

# Optional: Mail Server
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USERNAME=apikey
MAIL_PASSWORD=your_api_key
```

### B. Python Dependencies
In production, we need a production-grade WSGI server.
```bash
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

---

## 2. Server Architecture

We use **Gunicorn** as the application server and **Nginx** as the reverse proxy (traffic cop).

### A. Run Gunicorn
Test it manually first:
```bash
gunicorn -w 4 -b 0.0.0.0:8000 run:app
```
*   `-w 4`: 4 Worker processes (Good for 2-CPU cores).
*   `run:app`: Looks for `app` object in `run.py`.

### B. Systemd Service (Keep it running)
Create `/etc/systemd/system/eduportal.service`:

```ini
[Unit]
Description=Gunicorn instance to serve EduPortal
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/EDU-PORTAL
Environment="PATH=/home/ubuntu/EDU-PORTAL/.venv/bin"
ExecStart=/home/ubuntu/EDU-PORTAL/.venv/bin/gunicorn --workers 4 --bind unix:eduportal.sock -m 007 run:app

[Install]
WantedBy=multi-user.target
```

---

## 3. Nginx Configuration (Reverse Proxy)

Create `/etc/nginx/sites-available/eduportal`:

```nginx
server {
    listen 80;
    server_name eduportal.youruniversity.edu;

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/ubuntu/EDU-PORTAL/eduportal.sock;
    }

    # Serve Static Files Directly (Huge Performance Boost)
    location /static {
        alias /home/ubuntu/EDU-PORTAL/app/static;
        expires 30d;
    }
}
```

Enable it:
```bash
ln -s /etc/nginx/sites-available/eduportal /etc/nginx/sites-enabled
sudo systemctl restart nginx
```

---

## 4. Database Lifecycle in Production

**⚠️ CRITICAL WARNING**: Never run `manage.py seed` or `reset_db.py` in production. It drops all tables!

### Initial Setup
1.  Create DB: `createdb eduportal_prod`
2.  Apply Schema: `flask db upgrade` (if using migrations) OR use the `schema.sql` manually.

### Updates
When you update code, use Alembic to migrate the database schema without losing data:
```bash
flask db migrate -m "Added new fee column"
flask db upgrade
```

---

## 5. SSL (HTTPS)
Secure your site with Let's Encrypt:
```bash
sudo apt install python3-certbot-nginx
sudo certbot --nginx -d eduportal.youruniversity.edu
```
