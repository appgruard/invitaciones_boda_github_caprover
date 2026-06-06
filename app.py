from __future__ import annotations

import json
import os
import re
import secrets
import uuid
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any

import qrcode
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename


ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}

DEFAULT_WEDDING = {
    "couple_names": "María & José",
    "short_intro": "Nos casamos",
    "hero_phrase": "Queremos celebrar este día tan especial junto a ti.",
    "event_date": "2026-12-20",
    "event_time": "17:30",
    "ceremony_title": "Ceremonia y recepción",
    "venue_name": "Villa del Mar",
    "venue_address": "Frente al mar, al atardecer",
    "venue_description": "Un lugar sereno, cálido y elegante para celebrar nuestro amor rodeados de quienes más queremos.",
    "maps_url": "",
    "dress_code": "Formal tropical",
    "personal_note": "Tu presencia hará que este día sea aún más especial.",
    "story_title": "Nuestra historia",
    "story_text": "Algunas historias comienzan sin hacer ruido y terminan convirtiéndose en hogar. Hoy queremos compartir contigo el inicio de una nueva etapa.",
    "rsvp_enabled": True,
    "max_companions": "2",
    "music_url": "",
    "hero_image": "",
    "couple_image_1": "",
    "couple_image_2": "",
    "venue_image": "",
    "gallery": [],
}


def create_app() -> Flask:
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_hex(32))

    data_dir = Path(os.environ.get("DATA_DIR", str(Path(app.root_path) / "data")))
    upload_dir = Path(os.environ.get("UPLOAD_DIR", str(Path(app.static_folder) / "uploads")))
    qr_dir = Path(os.environ.get("QR_DIR", str(Path(app.static_folder) / "qr")))

    data_dir.mkdir(parents=True, exist_ok=True)
    upload_dir.mkdir(parents=True, exist_ok=True)
    qr_dir.mkdir(parents=True, exist_ok=True)

    wedding_path = data_dir / "wedding.json"
    guests_path = data_dir / "guests.json"
    rsvp_path = data_dir / "rsvps.json"

    def read_json(path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return default

    def write_json(path: Path, data: Any) -> None:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def wedding() -> dict[str, Any]:
        data = DEFAULT_WEDDING | read_json(wedding_path, {})
        data["gallery"] = data.get("gallery") or []
        data["rsvp_enabled"] = bool(data.get("rsvp_enabled", True))
        return data

    def save_wedding(data: dict[str, Any]) -> None:
        write_json(wedding_path, data)

    def guests() -> dict[str, Any]:
        return read_json(guests_path, {})

    def save_guests(data: dict[str, Any]) -> None:
        write_json(guests_path, data)

    def rsvps() -> dict[str, Any]:
        return read_json(rsvp_path, {})

    def save_rsvps(data: dict[str, Any]) -> None:
        write_json(rsvp_path, data)

    def admin_required(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            password = os.environ.get("ADMIN_PASSWORD", "")
            if not password or session.get("admin_ok"):
                return func(*args, **kwargs)
            return redirect(url_for("login", next=request.path))
        return wrapper

    def allowed_image(filename: str) -> bool:
        return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

    def save_image(file, prefix: str) -> str:
        if not file or not file.filename:
            return ""
        if not allowed_image(file.filename):
            raise ValueError("Formato no permitido. Usa JPG, PNG, WEBP o GIF.")
        original = secure_filename(file.filename)
        ext = original.rsplit(".", 1)[1].lower()
        filename = f"{prefix}-{uuid.uuid4().hex[:10]}.{ext}"
        file.save(upload_dir / filename)
        return f"uploads/{filename}"

    def generate_qr(token: str) -> str:
        link = url_for("invitation", token=token, _external=True)
        filename = f"{token}.png"
        qrcode.make(link).save(qr_dir / filename)
        return f"qr/{filename}"

    @app.context_processor
    def inject_globals():
        return {"current_year": datetime.now().year}

    @app.route("/")
    def root():
        return redirect(url_for("admin"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if not os.environ.get("ADMIN_PASSWORD"):
            return redirect(url_for("admin"))

        if request.method == "POST":
            if request.form.get("password") == os.environ.get("ADMIN_PASSWORD"):
                session["admin_ok"] = True
                return redirect(request.args.get("next") or url_for("admin"))
            flash("Contraseña incorrecta.", "error")

        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.route("/admin", methods=["GET", "POST"])
    @admin_required
    def admin():
        wedding_data = wedding()
        guest_data = guests()
        rsvp_data = rsvps()

        if request.method == "POST":
            fields = [
                "couple_names",
                "short_intro",
                "hero_phrase",
                "event_date",
                "event_time",
                "ceremony_title",
                "venue_name",
                "venue_address",
                "venue_description",
                "maps_url",
                "dress_code",
                "personal_note",
                "story_title",
                "story_text",
                "max_companions",
                "music_url",
            ]

            for field in fields:
                wedding_data[field] = request.form.get(field, "").strip()

            wedding_data["rsvp_enabled"] = request.form.get("rsvp_enabled") == "on"

            try:
                image_map = {
                    "hero_image": "hero",
                    "couple_image_1": "couple-a",
                    "couple_image_2": "couple-b",
                    "venue_image": "venue",
                }

                for field, prefix in image_map.items():
                    saved = save_image(request.files.get(field), prefix)
                    if saved:
                        wedding_data[field] = saved

                new_gallery = []
                for file in request.files.getlist("gallery"):
                    saved = save_image(file, "gallery")
                    if saved:
                        new_gallery.append(saved)
                if new_gallery:
                    wedding_data["gallery"] = wedding_data.get("gallery", []) + new_gallery

                keep_gallery = request.form.getlist("keep_gallery")
                if keep_gallery:
                    wedding_data["gallery"] = [img for img in wedding_data.get("gallery", []) if img in keep_gallery]
                elif request.form.get("clear_gallery") == "on":
                    wedding_data["gallery"] = []

                save_wedding(wedding_data)
                flash("Invitación actualizada correctamente.", "success")
                return redirect(url_for("admin"))
            except ValueError as exc:
                flash(str(exc), "error")

        rows = []
        for token, guest in sorted(guest_data.items(), key=lambda row: row[1].get("created_at", ""), reverse=True):
            rows.append({
                "token": token,
                "public_link": url_for("invitation", token=token, _external=True),
                **guest,
                "rsvp": rsvp_data.get(token, {}),
            })

        stats = {
            "total": len(rows),
            "confirmed": len([r for r in rsvp_data.values() if r.get("status") == "confirmed"]),
            "declined": len([r for r in rsvp_data.values() if r.get("status") == "declined"]),
        }
        stats["pending"] = max(stats["total"] - stats["confirmed"] - stats["declined"], 0)

        return render_template("admin.html", wedding=wedding_data, guests=rows, stats=stats)

    @app.route("/admin/guest", methods=["POST"])
    @admin_required
    def create_guest():
        guest_data = guests()
        name = request.form.get("guest_name", "").strip()
        note = request.form.get("guest_note", "").strip()

        if not name:
            flash("El nombre del invitado es obligatorio.", "error")
            return redirect(url_for("admin"))

        base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:22]
        token = f"{base}-{uuid.uuid4().hex[:6]}" if base else uuid.uuid4().hex[:10]

        guest_data[token] = {
            "guest_name": name,
            "guest_note": note,
            "qr_filename": generate_qr(token),
            "created_at": datetime.utcnow().isoformat(),
        }
        save_guests(guest_data)
        flash(f"Invitación creada para {name}.", "success")
        return redirect(url_for("admin"))

    @app.route("/invite/<token>")
    def invitation(token: str):
        guest = guests().get(token)
        if not guest:
            return render_template("not_found.html"), 404

        return render_template(
            "invitation.html",
            wedding=wedding(),
            guest=guest,
            token=token,
            rsvp=rsvps().get(token, {}),
            invitation_url=url_for("invitation", token=token, _external=True),
        )

    @app.route("/invite/<token>/rsvp", methods=["POST"])
    def rsvp(token: str):
        if token not in guests():
            return render_template("not_found.html"), 404

        data = rsvps()
        data[token] = {
            "status": request.form.get("status", "confirmed"),
            "companions": request.form.get("companions", "0"),
            "message": request.form.get("message", "").strip(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        save_rsvps(data)
        flash("Gracias. Tu respuesta fue registrada.", "success")
        return redirect(url_for("invitation", token=token))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=os.environ.get("FLASK_DEBUG") == "1")
