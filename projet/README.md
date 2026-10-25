# Projet 13 — Signalement citoyen des problèmes urbains

Application Flask de démonstration pour recevoir, suivre et traiter des signalements de problèmes urbains.

## Prérequis

- Python 3.10 ou supérieur
- Windows, macOS ou Linux
- Un navigateur récent
- PowerPoint ou LibreOffice Impress pour adapter le rapport généré

SQLite est inclus avec Python. Aucune installation de serveur de base de données n’est nécessaire.

## Installation sous Windows (PowerShell)

Depuis le dossier `Groupe13/projet` :

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python donnees_test.py
python app.py
```

Sur le PC, ouvrir http://127.0.0.1:5000. L’application ajuste automatiquement sa mise en page à l’écran: bureau large sur PC, menu compact et une colonne sur téléphone.

### Ouvrir sur un téléphone

1. Connecter le PC et le téléphone au même réseau Wi-Fi.
2. Sur le PC, relever son adresse IPv4 locale avec `ipconfig` (exemple : `192.168.1.25`).
3. Laisser le serveur en cours d’exécution puis saisir `http://ADRESSE-IP-DU-PC:5000` dans le navigateur du téléphone, par exemple `http://192.168.1.25:5000`.
4. Si Windows affiche une demande pour autoriser Python dans le pare-feu, autoriser l’accès sur le réseau privé. Ne pas exposer ce serveur de développement sur un réseau public.

Il n’y a pas deux applications séparées à installer: le même serveur sert la version adaptée au PC ou au téléphone selon la largeur de l’écran.

Le dossier `.venv` est un environnement local: ne pas le remettre. La base SQLite est créée dans `data/signalements.db` par `donnees_test.py`.

## Installation sous macOS ou Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python donnees_test.py
python app.py
```

## Connexions de démonstration

Les agents de test sont `agent1` à `agent8`; le mot de passe commun de démonstration est `Demo-2026!`. Les mots de passe ne sont stockés qu’en empreinte PBKDF2.

Chaque agent ne voit que les demandes du service associé. Pour une installation réelle, définir une valeur `SECRET_KEY` aléatoire, retirer les comptes de démonstration et utiliser un serveur WSGI en mode production.

## Fonctionnalités

- Dépôt public d’un signalement avec description, repère, quartier, catégorie et photo JPG/PNG (2 Mo maximum).
- Aperçu de la photo et contrôle de description (20 caractères minimum) avant l’envoi.
- Génération d’un code de suivi et consultation de l’historique des interventions.
- Liste publique filtrable par quartier et catégorie; les signalements rejetés restent privés.
- Espace agent protégé, traitement par service, changement de statut et motif obligatoire en cas de rejet.
- API JSON `GET /api/statistiques` : signalements par catégorie/quartier, délai moyen de résolution, demandes non traitées depuis plus de 7 jours et évolution hebdomadaire.
- Protection CSRF, validation serveur, requêtes SQL paramétrées et clés étrangères SQLite.

## Données de test

`python donnees_test.py` reconstruit la base avec 5 catégories, 12 quartiers, 200 signalements répartis sur 3 mois, 250 interventions et 8 agents. Il associe automatiquement les images WebP de `static/images/` aux signalements de démonstration. Les photos réelles envoyées par le formulaire sont enregistrées dans `static/uploads/` avec un nom aléatoire.

## Export SQL et rapport

- `python exporter_base.py` génère `export_projet.sql` à partir de la base existante.
- `python generer_rapport.py` génère un diaporama PowerPoint de travail de 15 diapositives dans le dossier `Groupe13`. Compléter le contenu et intégrer les captures d’écran avant la remise.
- La vidéo `video_demo.mp4` et les captures ordinateur/téléphone restent à réaliser par le groupe.

## Contrôles rapides

- `GET /` : accueil et filtres
- `GET /signaler` : formulaire de dépôt
- `GET /suivi` : recherche par code
- `GET /api/statistiques` : statistiques JSON
- `GET /connexion` : espace agents

## Structure remise

Le dossier parent `Groupe13` contient le projet, le rapport PowerPoint, la vidéo de démonstration et les captures ordinateur/téléphone. Ne pas inclure `.venv`, `__pycache__` ou un environnement virtuel dans la remise.