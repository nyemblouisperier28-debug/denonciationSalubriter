import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from werkzeug.security import generate_password_hash


BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "data" / "signalements.db"
CATEGORIES = [
    ("Voirie", "Voirie"),
    ("Ordures", "Propreté"),
    ("Éclairage", "Éclairage"),
    ("Eau", "Eau"),
    ("Autre", "Services généraux"),
]
QUARTIERS = [
    "Centre", "Nord", "Sud", "Est", "Ouest", "Riverside",
    "Marché", "Gare", "Université", "Parc", "Port", "Plateau",
]
DESCRIPTIONS = [
    "Un nid-de-poule profond rend cette rue difficile à emprunter.",
    "Des déchets sont accumulés près du passage piéton depuis plusieurs jours.",
    "Le lampadaire ne fonctionne plus et la rue est très sombre la nuit.",
    "Une fuite d'eau forme une flaque importante sur le trottoir.",
    "Le caniveau est bouché et l'eau ne s'écoule plus après la pluie.",
]


def main():
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    demo_images = sorted((BASE_DIR / "static" / "images").glob("*.webp"))
    if not demo_images:
        raise SystemExit("Aucune image WebP trouvée dans static/images.")
    connection = sqlite3.connect(DATABASE)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript((BASE_DIR / "schema.sql").read_text(encoding="utf-8"))
    connection.execute("DELETE FROM interventions")
    connection.execute("DELETE FROM signalements")
    connection.execute("DELETE FROM agents")
    connection.execute("DELETE FROM categories")
    connection.execute("DELETE FROM quartiers")
    connection.executemany(
        "INSERT INTO categories(nom, service_responsable) VALUES (?, ?)", CATEGORIES
    )
    connection.executemany("INSERT INTO quartiers(nom) VALUES (?)", [(name,) for name in QUARTIERS])
    services = sorted({service for _, service in CATEGORIES})
    for number in range(8):
        service = services[number % len(services)]
        connection.execute(
            "INSERT INTO agents(nom, service, login, mot_de_passe_hash) VALUES (?, ?, ?, ?)",
            (f"Agent {number + 1:02d}", service, f"agent{number + 1}", generate_password_hash("Demo-2026!")),
        )

    random.seed(13)
    now = datetime.now()
    report_rows = []
    for number in range(200):
        category_id = number % len(CATEGORIES) + 1
        district_id = number % len(QUARTIERS) + 1
        status = ("nouveau", "en cours", "résolu", "rejeté")[number % 4]
        created = now - timedelta(days=random.randrange(90), hours=random.randrange(24))
        image = demo_images[number % len(demo_images)]
        report_rows.append((
            category_id, district_id, DESCRIPTIONS[number % len(DESCRIPTIONS)],
            f"images/{image.name}", f"Rue de démonstration, repère {number + 1}",
            f"URB-{number + 1:06d}", created.strftime("%Y-%m-%d %H:%M:%S"), status,
        ))
    connection.executemany(
        """INSERT INTO signalements
           (categorie_id, quartier_id, description, photo, adresse, code_suivi, date_creation, statut)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        report_rows,
    )
    report_ids = [row[0] for row in connection.execute("SELECT id FROM signalements ORDER BY id")]
    for number in range(250):
        report_id = report_ids[number % len(report_ids)]
        agent_id = number % 8 + 1
        status = ("en cours", "résolu", "nouveau", "rejeté")[number % 4]
        when = now - timedelta(days=random.randrange(90), hours=random.randrange(24))
        connection.execute(
            """INSERT INTO interventions(signalement_id, agent_id, date_intervention, commentaire, nouveau_statut)
               VALUES (?, ?, ?, ?, ?)""",
            (report_id, agent_id, when.strftime("%Y-%m-%d %H:%M:%S"), "Intervention de démonstration.", status),
        )
    connection.commit()
    counts = {
        table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ("categories", "quartiers", "signalements", "interventions", "agents")
    }
    connection.close()
    print("Base de démonstration créée :", counts)
    print(f"Images WebP utilisées : {len(demo_images)}")
    print("Comptes de test : agent1 à agent8 / Demo-2026!")


if __name__ == "__main__":
    main()