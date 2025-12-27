# Divsa Polymers (Flask)

Simple Flask site for Divsa Polymers.

Quick start (development):

```bash
python -m venv .venv
.venv\Scripts\activate    # Windows
pip install -r requirements.txt
python app.py
```

Production notes:

- Set environment variables: `SECRET_KEY`, `DATABASE_URL`, `PORT`, `HOST`.
- Run with a WSGI server (e.g. `gunicorn app:app -w 4 -b 0.0.0.0:8000`).
- Configure HTTPS at the reverse-proxy/load balancer and enable HSTS only for HTTPS hosts.
- Ensure `static/` contains optimized images (webp) and a `favicon.ico`.
- Logs are written to `logs/divsa.log` when not in debug mode.

SEO notes:

- `sitemap.xml` and `robots.txt` routes are provided.
- Update canonical URLs in `templates/index.html` to use your official domain.
