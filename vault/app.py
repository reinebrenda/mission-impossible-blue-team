import os
from flask import Flask, request, jsonify, abort

app = Flask(__name__)

@app.get("/secret")
def secret():
    tok = request.args.get("token", "")
    if tok != os.getenv("VAULT_TOKEN", ""):
        abort(403)
    return jsonify({
        "vault": "ok",
        "flag_vault": os.getenv("FLAG_VAULT", "FLAG{missing}")
    })

@app.get("/health")
def health():
    return jsonify({"ok": True})

@app.errorhandler(403)
def forbidden(e):
    return jsonify({"error": "Forbidden"}), 403

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7000)