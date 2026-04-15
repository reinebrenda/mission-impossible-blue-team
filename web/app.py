import os
import requests
import ipaddress
import socket
from urllib.parse import urlparse
from requests.exceptions import RequestException
from flask import Flask, request, jsonify, abort, make_response, render_template_string

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("JWT_SECRET", "dev-secret-CHANGE-ME")
app.config["JSON_SORT_KEYS"] = False

# =========================
# 🛡️ Protection SSRF
# =========================

def is_private_ip(hostname):
    try:
        # Résolution DNS (anti DNS rebinding)
        ip = socket.gethostbyname(hostname)
        return ipaddress.ip_address(ip).is_private
    except:
        return True


def is_blocked_host(hostname):
    blocked = ["localhost", "127.0.0.1", "vault"]
    return hostname in blocked


# =========================
# Pages
# =========================

HOME = """
<h1>Mission Pipeline</h1>
<p>Objectif : sécuriser <b>la supply chain</b>, les <b>secrets</b>, et l'app (<b>SSRF</b>, auth, logs).</p>
<ul>
  <li><a href="/status">/status</a></li>
  <li><a href="/whoami">/whoami</a></li>
  <li><a href="/fetch?url=https://example.com">/fetch</a></li>
  <li><a href="/admin?token=...">/admin</a></li>
</ul>
"""

@app.get("/")
def index():
    return render_template_string(HOME)


@app.get("/status")
def status():
    return jsonify({"service": "secure-app", "ok": True})


@app.get("/whoami")
def whoami():
    user = request.headers.get("X-User", "anonymous")
    resp = make_response(jsonify({"user": user}))
    resp.set_cookie("session", "secure", httponly=True, samesite="Strict")
    return resp


# =========================
# 🔥 Endpoint vuln corrigé
# =========================

@app.get("/fetch")
def fetch():
    url = request.args.get("url", "")

    if not url:
        return jsonify({"error": "Missing url parameter"}), 400

    parsed = urlparse(url)

    # 1️⃣ Vérifier le schéma
    if parsed.scheme not in ["http", "https"]:
        return jsonify({"error": "Only http/https allowed"}), 400

    hostname = parsed.hostname

    if not hostname:
        return jsonify({"error": "Invalid URL"}), 400

    # 2️⃣ Bloquer hosts internes
    if is_blocked_host(hostname):
        return jsonify({"error": "Access denied"}), 403

    # 3️⃣ Bloquer IP privées
    if is_private_ip(hostname):
        return jsonify({"error": "Private IP not allowed"}), 403

    try:
        r = requests.get(url, timeout=2)
        return (
            r.text,
            r.status_code,
            {"Content-Type": r.headers.get("Content-Type", "text/plain")},
        )

    except RequestException:
        return jsonify({"error": "Upstream request failed"}), 502


# =========================
# Admin
# =========================

@app.get("/admin")
def admin():
    token = request.args.get("token", "")

    if token != os.getenv("ADMIN_TOKEN", ""):
        abort(403)

    return jsonify({
        "admin": True,
        "flag_supply_chain": os.getenv("FLAG_SUPPLY", "FLAG{missing}")
    })


# =========================

if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=5000, debug=debug)