# -*- coding: utf-8 -*-
import os
import sys
from flask import Flask, redirect, send_file, jsonify, request
from xedua_module import xedua_bp, car_state, led_config, pending_commands

app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Register main blueprint
app.register_blueprint(xedua_bp)

@app.route("/")
def home():
    return redirect("/xedua")

@app.route("/led")
def led_shortcut():
    return redirect("/xedua/led")

@app.route("/api/firmware/latest.bin")
@app.route("/firmware/xe_racing_s3.ino.bin")
def serve_firmware():
    fw_path = os.path.join(BASE_DIR, "firmware", "xe_racing_s3.ino.bin")
    if os.path.exists(fw_path):
        return send_file(fw_path, mimetype="application/octet-stream", as_attachment=True, download_name="xe_racing_s3.ino.bin")
    return jsonify({"error": "Firmware not found"}), 404

@app.route("/healthz")
def healthz():
    return jsonify({"status": "healthy", "service": "vlu-racing-cloud", "car_online": car_state.get("online", False)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=False)
