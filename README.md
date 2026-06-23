# Paperless Letter Generator

A companion web application for [Paperless-ngx](https://docs.paperless-ngx.com/) that generates PDF letters from LaTeX templates.

## Features

- **LaTeX templates** stored and managed in the database via web UI
- **Template variables** auto-discovered from `{{ var_name }}` placeholders
- **Address book** linked to Paperless correspondents (stored locally)
- **Reply flow** — create replies to existing documents
- **One-click send** — push generated PDFs into Paperless-ngx as new documents
- **German letter templates** (DIN 5008 `scrlttr2`) included by default

## Quick Start

```bash
# Clone the repository
git clone https://github.com/your/paperless-letter-generator.git
cd paperless-letter-generator

# Run as root
sudo bash install.sh
```

The installer will:
1. Install Python 3, Node.js, TeX Live
2. Create a system user and directories
3. Set up a Python virtual environment
4. Build the Vue.js frontend
5. Prompt for Paperless-ngx API URL and token
6. Run database migrations
7. Seed default templates
8. Install and start a systemd service

## Paperless-ngx Integration

Add a **Custom Link** in Paperless-ngx:
1. Go to Settings → Custom Links
2. Name: `Letter Generator`
3. URL: `http://YOUR_VM_IP:8050`
4. Target: `_self` (opens in same tab)

The service uses the Paperless-ngx REST API to:
- Fetch correspondents
- Fetch document details (for replies)
- Post generated PDFs as new documents
