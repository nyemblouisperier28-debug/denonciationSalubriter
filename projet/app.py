import os
import secrets
import sqlite3
import mimetypes
from functools import wraps
from pathlib import Path

from flask import (Flask,abort,flash,g,jsonify,redirect,render_template,request,session,url_for,)
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "data" / "signalements.db"
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
STATUTS = {"nouveau", "en cours", "résolu", "rejeté"}
mimetypes.add_type("image/webp", ".webp")

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-this-secret"),
    MAX_CONTENT_LENGTH=2 * 1024 * 1024,
    UPLOAD_FOLDER=str(BASE_DIR / "static" / "uploads"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("FLASK_ENV") == "production",
)
csrf = CSRFProtect(app)

def get_db():
    if "db" not in g:
        DATABASE.parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "agent_id" not in session:
            flash("Connectez-vous pour accéder à cet espace.", "warning")
            return redirect(url_for("connexion", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def allowed_image(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    db = get_db()
    category_id = request.args.get("categorie", type=int)
    district_id = request.args.get("quartier", type=int)
    clauses = ["s.statut != 'rejeté'"]
    values = []
    if category_id:
        clauses.append("s.categorie_id = ?")
        values.append(category_id)
    if district_id:
        clauses.append("s.quartier_id = ?")
        values.append(district_id)
    reports = db.execute(
        """SELECT s.*, c.nom AS categorie, q.nom AS quartier
           FROM signalements s
           JOIN categories c ON c.id = s.categorie_id
           JOIN quartiers q ON q.id = s.quartier_id
           WHERE """ + " AND ".join(clauses) + " ORDER BY s.date_creation DESC LIMIT 50",
        values,
    ).fetchall()
    categories = db.execute("SELECT id, nom FROM categories ORDER BY nom").fetchall()
    districts = db.execute("SELECT id, nom FROM quartiers ORDER BY nom").fetchall()
    return render_template(
        "index.html", reports=reports, categories=categories, districts=districts,
        selected_category=category_id, selected_district=district_id,
    )


@app.route("/signaler", methods=["GET", "POST"])
def nouveau_signalement():
    db = get_db()
    categories = db.execute("SELECT id, nom FROM categories ORDER BY nom").fetchall()
    districts = db.execute("SELECT id, nom FROM quartiers ORDER BY nom").fetchall()
    if request.method == "POST":
        description = request.form.get("description", "").strip()
        address = request.form.get("adresse", "").strip()
        phone = request.form.get("telephone", "").strip()
        category_id = request.form.get("categorie_id", type=int)
        district_id = request.form.get("quartier_id", type=int)
        photo = request.files.get("photo")
        errors = []
        if len(description) < 20:
            errors.append("La description doit contenir au moins 20 caractères.")
        if not category_id or not district_id or not address:
            errors.append("Veuillez renseigner la catégorie, le quartier et le repère.")
        if not photo or not photo.filename:
            errors.append("Une photo est obligatoire pour le signalement.")
        elif not allowed_image(photo.filename):
            errors.append("La photo doit être au format JPG, JPEG ou PNG.")
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("nouveau.html", categories=categories, districts=districts)

        filename = f"{secrets.token_hex(12)}_{secure_filename(photo.filename)}"
        photo.save(Path(app.config["UPLOAD_FOLDER"]) / filename)
        code = f"URB-{secrets.token_hex(4).upper()}"
        try:
            db.execute(
                """INSERT INTO signalements
                   (categorie_id, quartier_id, description, photo, adresse, telephone, code_suivi)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (category_id, district_id, description, filename, address, phone or None, code),
            )
            db.commit()
        except sqlite3.IntegrityError:
            (Path(app.config["UPLOAD_FOLDER"]) / filename).unlink(missing_ok=True)
            flash("Les informations choisies ne sont pas valides.", "error")
            return render_template("nouveau.html", categories=categories, districts=districts)
        flash(f"Votre signalement est enregistré. Code de suivi : {code}", "success")
        return redirect(url_for("suivi", code=code))
    return render_template("nouveau.html", categories=categories, districts=districts)


@app.route("/suivi", methods=["GET", "POST"])
def rechercher_suivi():
    if request.method == "POST":
        code = request.form.get("code", "").strip().upper()
        return redirect(url_for("suivi", code=code))
    return render_template("suivi_recherche.html")


@app.route("/suivi/<code>")
def suivi(code):
    db = get_db()
    report = db.execute(
        """SELECT s.*, c.nom AS categorie, q.nom AS quartier
           FROM signalements s JOIN categories c ON c.id=s.categorie_id
           JOIN quartiers q ON q.id=s.quartier_id WHERE s.code_suivi = ?""",
        (code.upper(),),
    ).fetchone()
    if report is None:
        abort(404)
    events = db.execute(
        """SELECT i.*, a.nom AS agent_nom FROM interventions i
           JOIN agents a ON a.id=i.agent_id WHERE i.signalement_id=? ORDER BY i.date_intervention DESC""",
        (report["id"],),
    ).fetchall()
    return render_template("suivi.html", report=report, events=events)


@app.route("/api/statistiques")
def api_statistiques():
    db = get_db()
    by_category = db.execute(
        """SELECT c.nom, COUNT(s.id) AS total FROM categories c
           LEFT JOIN signalements s ON s.categorie_id=c.id GROUP BY c.id ORDER BY c.nom"""
    ).fetchall()
    by_district = db.execute(
        """SELECT q.nom, COUNT(s.id) AS total FROM quartiers q
           LEFT JOIN signalements s ON s.quartier_id=q.id GROUP BY q.id ORDER BY q.nom"""
    ).fetchall()
    average = db.execute(
        """SELECT AVG(julianday(i.date_intervention)-julianday(s.date_creation)) AS jours
           FROM signalements s JOIN interventions i ON i.signalement_id=s.id
           WHERE i.nouveau_statut='résolu'"""
    ).fetchone()["jours"]
    overdue = db.execute(
        """SELECT COUNT(*) AS total FROM signalements WHERE statut IN ('nouveau','en cours')
           AND date_creation < datetime('now', '-7 days')"""
    ).fetchone()["total"]
    weekly = db.execute(
        """SELECT strftime('%Y-%W', date_creation) AS semaine, COUNT(*) AS total
           FROM signalements WHERE date_creation >= datetime('now', '-12 weeks')
           GROUP BY semaine ORDER BY semaine"""
    ).fetchall()
    return jsonify(
        par_categorie=[dict(row) for row in by_category],
        par_quartier=[dict(row) for row in by_district],
        delai_moyen_resolution_jours=round(average, 2) if average is not None else None,
        non_traites_plus_7_jours=overdue,
        evolution_hebdomadaire=[dict(row) for row in weekly],
    )


@app.route("/connexion", methods=["GET", "POST"])
def connexion():
    if request.method == "POST":
        login = request.form.get("login", "").strip()
        password = request.form.get("password", "")
        agent = get_db().execute("SELECT * FROM agents WHERE login = ?", (login,)).fetchone()
        if agent and check_password_hash(agent["mot_de_passe_hash"], password):
            session.clear()
            session["agent_id"] = agent["id"]
            session["agent_service"] = agent["service"]
            return redirect(url_for("administration"))
        flash("Identifiants incorrects.", "error")
    return render_template("connexion.html")


@app.route("/deconnexion", methods=["POST"])
@login_required
def deconnexion():
    session.clear()
    return redirect(url_for("index"))


@app.route("/administration")
@login_required
def administration():
    reports = get_db().execute(
        """SELECT s.*, c.nom AS categorie, q.nom AS quartier FROM signalements s
           JOIN categories c ON c.id=s.categorie_id JOIN quartiers q ON q.id=s.quartier_id
           WHERE c.service_responsable=? ORDER BY s.date_creation DESC""",
        (session["agent_service"],),
    ).fetchall()
    return render_template("administration.html", reports=reports, statuts=sorted(STATUTS))


@app.route("/administration/signalement/<int:report_id>", methods=["POST"])
@login_required
def modifier_signalement(report_id):
    db = get_db()
    report = db.execute(
        """SELECT s.id, c.service_responsable FROM signalements s
           JOIN categories c ON c.id=s.categorie_id WHERE s.id=?""", (report_id,),
    ).fetchone()
    if report is None or report["service_responsable"] != session["agent_service"]:
        abort(404)
    status = request.form.get("statut", "")
    comment = request.form.get("commentaire", "").strip()
    reason = request.form.get("motif_rejet", "").strip()
    if status not in STATUTS or not comment:
        flash("Choisissez un statut et ajoutez un commentaire d’intervention.", "error")
        return redirect(url_for("administration"))
    if status == "rejeté" and len(reason) < 5:
        flash("Un motif détaillé est obligatoire pour rejeter un signalement.", "error")
        return redirect(url_for("administration"))
    agent_id = session["agent_id"]
    db.execute("UPDATE signalements SET statut=? WHERE id=?", (status, report_id))
    db.execute(
        """INSERT INTO interventions(signalement_id, agent_id, commentaire, nouveau_statut)
           VALUES (?, ?, ?, ?)""",
        (report_id, agent_id, f"{comment} Motif de rejet : {reason}" if status == "rejeté" else comment, status),
    )
    db.commit()
    flash("Intervention enregistrée.", "success")
    return redirect(url_for("administration"))


@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404


@app.errorhandler(413)
def too_large(_error):
    flash("La photo dépasse la taille maximale de 2 Mo.", "error")
    return redirect(url_for("nouveau_signalement"))


if __name__ == "__main__":
    app.run(
        host=os.environ.get("FLASK_HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )