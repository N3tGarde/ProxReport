# proxreport
Lightweight, self-hosted, one-page dashboard for a Proxmox VE node.

Goals:
- Minimal dependencies (Python standard library only)
- Host health + capacity planning
- HTTPS + HTTP Basic Auth
- Collect metrics from the host OS (no Proxmox API)

## Quick start (local / dev)
1) Create a config:
- Copy `config.example.ini` to `config.ini` and adjust ports/cert paths.

2) Create a self-signed cert (example):
```bash
mkdir -p tls
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout tls/key.pem -out tls/cert.pem \
  -days 365 -subj "/CN=proxreport"
```

3) Create a users file entry:
```bash
python3 -m proxreport hash-password --username admin
# You'll be prompted for a password; it prints a line like:
# admin:<salt_hex>:<sha256_hex>
```
Save the output line to `users.txt`.

4) Run:
```bash
python3 -m proxreport serve --config ./config.ini
```
Open: `https://<host>:<https_port>/`

## Smoke test
- Confirm redirect:
```bash
curl -I http://<host>:<http_port>/
```
- Confirm auth + HTTPS:
```bash
curl -k -u <user>:<password> https://<host>:<https_port>/
```

On a Proxmox VE host you can also do a quick syntax check:
```bash
python3 -m py_compile proxreport/*.py
```

## Deploy on a Proxmox VE host (systemd)
Suggested layout:
- Repo: `/opt/proxreport`
- Config: `/etc/proxreport/config.ini`
- Users: `/etc/proxreport/users.txt`
- TLS: `/etc/proxreport/tls/{cert.pem,key.pem}`

Steps:
1) Copy the repo to `/opt/proxreport`.
2) Create `/etc/proxreport/` and place config/users/tls.
3) Install the unit:
- Copy `systemd/proxreport.service` to `/etc/systemd/system/`
- `systemctl daemon-reload`
- `systemctl enable --now proxreport`

If you want to bind to `80/443`, consider enabling the commented capability lines in the unit.

## Notes on password storage
Users are stored as `username:salt_hex:sha256_hex` where:
- `sha256_hex = SHA256(salt_bytes + password_utf8)`

This avoids storing plaintext passwords and keeps the implementation stdlib-only.

## License
MIT (see `LICENSE`).
