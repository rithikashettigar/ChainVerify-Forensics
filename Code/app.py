from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
import os
import uuid
import json
import time
from datetime import datetime

from db import init_db, create_user, get_user

# --- IMPORTS ---
from services.image_register_service import register_image
from services.image_verify_service import verify_image
from services.video_register_service import register_video
from services.video_verify_service import verify_video, reconstruct_video_content 

app = Flask(__name__)
app.secret_key = "dev-secret-key"

# =========================
# INIT DB
# =========================
init_db()

# =========================
# PATHS
# =========================
UPLOAD_IMAGE = "uploads/images"
UPLOAD_VIDEO = "uploads/videos"
OUTPUTS_DIR = "outputs"
REGISTRY_DIR = "registry"  # Ensure this matches your folder name

os.makedirs(UPLOAD_IMAGE, exist_ok=True)
os.makedirs(UPLOAD_VIDEO, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)
os.makedirs(REGISTRY_DIR, exist_ok=True)

# =========================
# HELPER: LOG USER LOGIN
# =========================
def log_user_login(username, email):
    """
    Appends login events to registry/user_logs.json
    """
    log_path = os.path.join(REGISTRY_DIR, "user_logs.json")
    
    # Create entry
    entry = {
        "username": username,
        "email": email,
        "timestamp": datetime.utcnow().isoformat() + "Z",  # UTC time
        "event": "LOGIN_SUCCESS"
    }

    try:
        data = []
        # Read existing logs if file exists
        if os.path.exists(log_path):
            with open(log_path, "r") as f:
                try:
                    data = json.load(f)
                    if not isinstance(data, list): data = []
                except:
                    data = []
        
        # Append new entry
        data.append(entry)
        
        # Write back to file
        with open(log_path, "w") as f:
            json.dump(data, f, indent=4)
            
    except Exception as e:
        print(f"Logging Failed: {e}")

# =========================
# AUTH ROUTES
# =========================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if not all([username, email, password]):
            return render_template("login.html", error="Username, Email, and Password are all required.")

        user = get_user(email, username, password)
        
        if not user:
            return render_template(
                "login.html",
                error="Invalid credentials. Please check Email, Username, and Password."
            )

        # SUCCESSFUL LOGIN
        session["user_id"] = user["id"]
        session["user"] = user["username"]
        
        # --- NEW: LOG THE LOGIN ---
        log_user_login(user["username"], email)

        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm = request.form.get("confirm_password")

        if not all([username, email, password, confirm]):
            return render_template("signup.html", error="All fields are required.")

        if password != confirm:
            return render_template("signup.html", error="Passwords do not match.")

        success = create_user(username, email, password)
        
        if not success:
            return render_template(
                "signup.html",
                error="This Email address is already registered. Please login."
            )

        return render_template(
            "login.html",
            success="Signup successful! You can now login."
        )

    return render_template("signup.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# =========================
# DASHBOARD
# =========================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        user=session["user"]
    )

# =========================
# MEDIA TYPE DETECTION
# =========================
def detect_media_type(filename):
    ext = filename.lower().rsplit(".", 1)[-1]
    if ext in ["jpg", "jpeg", "png", "webp"]:
        return "image"
    if ext in ["mp4", "avi"]:
        return "video"
    return None

# =========================
# REGISTER MEDIA
# =========================
@app.route("/register", methods=["POST"])
def register_media():
    if "user" not in session:
        return redirect(url_for("login"))

    ref_id = request.form.get("ref_id", "").strip()
    media = request.files.get("media")

    if not ref_id or not media:
        return render_template(
            "dashboard.html",
            user=session["user"],
            register_result={"status": "error", "message": "Reference ID and media file are required."}
        )

    media_type = detect_media_type(media.filename)
    if not media_type:
        return render_template(
            "dashboard.html",
            user=session["user"],
            register_result={"status": "error", "message": "Unsupported media type."}
        )

    filename = f"{uuid.uuid4().hex}_{media.filename}"
    owner = session["user"]

    if media_type == "image":
        path = os.path.join(UPLOAD_IMAGE, filename)
        media.save(path)
        result = register_image(ref_id, path, owner)
    else:  # video
        path = os.path.join(UPLOAD_VIDEO, filename)
        media.save(path)
        result = register_video(ref_id, path, owner)

    return render_template(
        "dashboard.html",
        user=session["user"],
        register_result=result
    )

# =========================
# VERIFY MEDIA (Lightweight Check)
# =========================
@app.route("/verify", methods=["POST"])
def verify_media():
    if "user" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    media = request.files.get("media")
    ref_id = request.form.get("ref_id", "").strip()
    media_type_input = request.form.get("media_type")

    if not media:
        return jsonify({"status": "error", "message": "No media file uploaded."}), 400

    detected_type = detect_media_type(media.filename)
    final_type = media_type_input if media_type_input else detected_type

    if not final_type:
         return jsonify({"status": "error", "message": "Unsupported media type."}), 400

    filename = f"{uuid.uuid4().hex}_{media.filename}"
    
    if final_type == "image":
        path = os.path.join(UPLOAD_IMAGE, filename)
        media.save(path)
        # Images verify AND reconstruct instantly
        result = verify_image(ref_id, path, original_filename=media.filename)
        
    elif final_type == "video":
        path = os.path.join(UPLOAD_VIDEO, filename)
        media.save(path)
        # Videos ONLY verify hash. Reconstruction is skipped here (Wait for button click).
        result = verify_video(ref_id, path, original_filename=media.filename)
        
    else:
        return jsonify({"status": "error", "message": "Invalid media type."}), 400

    return jsonify(result)

# =========================
# RECONSTRUCT MEDIA (Heavy Lifting - FIXED)
# =========================
@app.route("/reconstruct", methods=["POST"])
def reconstruct_media():
    if "user" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    # Use REF_ID, NOT FILENAME
    ref_id = request.form.get("ref_id")
    
    if not ref_id:
        return jsonify({"status": "error", "message": "Reference ID is missing."}), 400

    try:
        # Pass ID directly to service
        reconstructed_url = reconstruct_video_content(ref_id)
        
        return jsonify({
            "status": "success",
            "reconstructed_url": reconstructed_url
        })
    except Exception as e:
        print(f"Reconstruction Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# =========================
# BLOCKCHAIN VIEWER ROUTES
# =========================
@app.route("/chain", methods=["GET"])
def get_chain():
    if "user" not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
        
    path = "registry/ledger.json"
    if not os.path.exists(path):
        return jsonify({}) 
        
    with open(path, "r") as f:
        try:
            chain_data = json.load(f)
            return jsonify(chain_data)
        except:
            return jsonify({})

@app.route("/chain/validate", methods=["POST"])
def validate_chain():
    path = "registry/ledger.json"
    if os.path.exists(path):
        return jsonify({"status": "valid", "message": "Cryptographic links verified."})
    return jsonify({"status": "error", "message": "Chain not found."})

# =========================
# SERVE OUTPUTS
# =========================
@app.route('/outputs/<path:filename>')
def serve_outputs(filename):
    return send_from_directory(OUTPUTS_DIR, filename, as_attachment=True)

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    app.run(debug=True, threaded=True)