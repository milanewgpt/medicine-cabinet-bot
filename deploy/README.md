# Deploy templates

This folder contains production templates used on a reference VPS.

## Systemd

- `deploy/systemd/medicine-bot.service`

Notes:

- If you run multiple services on the same host, avoid port conflicts.
- The provided unit uses `--port 8001` (instead of `8000`) to coexist with other apps.

## Nginx

- `deploy/nginx/medicine-bot.nginx.conf`

Notes:

- Update `server_name` and SSL certificate paths.
- Upstream is `http://127.0.0.1:8001`.

