import os
import re
import json
import requests
import socket
import ipaddress
from urllib.parse import urlparse
from requests.exceptions import RequestException
from flask import Flask, request, jsonify, abort, make_response, render_template_string

app = Flask(__name__)

# still intentionally flawed for the exercise
app.config["SECRET_KEY"] = os.getenv("JWT_SECRET", "dev-secret-CHANGE-ME")
app.config["JSON_SORT_KEYS"] = False

HOME = """
<h1>Mission Pipeline</h1>
<p>Objectif : sécuriser <b>la supply chain</b> (build/test/scan), les <b>secrets</b>, et l'app (<b>SSRF</b>, auth, logs).</p>
<ul>
  <li><a href="/status">/status</a></li>
  <li><a href="/whoami">/whoami</a></li>
  <li><a href="/fetch?url=https://example.com">/fetch</a> (⚠️ SSRF)</li>
  <li><a href="/admin">/admin</a> (secured)</li>
  <li><a href="/docs">/docs</a> (pistes DevSecOps)</li>
</ul>
<p><b>Note</b> : tout reste local. Les “flags” sont dans les variables d’environnement.</p>
"""

@app.get("/")
def index():
    return render_template_string(HOME)

@app.get("/status")
def status():
    return jsonify({"service": "escape-app-expert", "ok": True})

# Weak identity (left as-is for workshop)
@app.get("/whoami")
def whoami():
    user = request.headers.get("X-User", "anonymous")
    resp = make_response(jsonify({"user": user}))
    resp.set_cookie("session", "dev", httponly=False, samesite="Lax")
    return resp


# 🔐 Helper: detect private IP
def is_private_ip(hostname):
    try:
        ip = socket.gethostbyname(hostname)
        return ipaddress.ip_address(ip).is_private
    except:
        return True


# 🔴 SSRF FIX
@app.get("/fetch")
def fetch():
    url = request.args.get("url", "")
    if not url:
        return jsonify({"error": "Missing url parameter"}), 400

    # Parse URL
    parsed = urlparse(url)
    hostname = parsed.hostname

    if not hostname:
        return jsonify({"error": "Invalid URL"}), 400

    # Block dangerous schemes
    if parsed.scheme not in ["http", "https"]:
        return jsonify({"error": "Only http/https allowed"}), 400

    # Block internal services
    if hostname in ["localhost", "127.0.0.1", "vault"]:
        return jsonify({"error": "Access denied"}), 403

    # Block private IP ranges (Docker included)
    if is_private_ip(hostname):
        return jsonify({"error": "Private IP not allowed"}), 403

    if url.startswith("file://"):
        return jsonify({"error": "file:// URLs are not allowed"}), 400

    try:
        r = requests.get(url, timeout=2)
        return (
            r.text,
            r.status_code,
            {"Content-Type": r.headers.get("Content-Type", "text/plain")},
        )
    except RequestException:
        return jsonify({
            "error": "Upstream request failed"
        }), 502


# 🔐 SECURED ADMIN
@app.get("/admin")
def admin():
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        abort(401)

    if not auth_header.startswith("Bearer "):
        abort(401)

    token = auth_header.split(" ")[1]

    if token != os.getenv("ADMIN_TOKEN"):
        abort(403)

    return jsonify({
        "admin": True,
        "flag_supply_chain": os.getenv("FLAG_SUPPLY", "FLAG{missing}")
    })


@app.get("/docs")
def docs():
    return render_template_string("""
<h2>DevSecOps targets (expert)</h2>
<ol>
  <li>Supply chain: tests + SAST + dependency audit + image scan + SBOM + signing</li>
  <li>Secrets hygiene: no .env committed, no tokens in repo, add secret scanning</li>
  <li>AppSec: SSRF mitigation, auth hardening, safer cookies, logging</li>
  <li>Build hardening: pin base image, non-root user, .dockerignore, minimal image</li>
</ol>
<p>Tip: there is an internal service on the Docker network you should not be able to read from the web app.</p>
""")


if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=5000, debug=debug)