PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY,
    nom TEXT NOT NULL UNIQUE,
    service_responsable TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS quartiers (
    id INTEGER PRIMARY KEY,
    nom TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS agents (
    id INTEGER PRIMARY KEY,
    nom TEXT NOT NULL,
    service TEXT NOT NULL,
    login TEXT NOT NULL UNIQUE,
    mot_de_passe_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS signalements (
    id INTEGER PRIMARY KEY,
    categorie_id INTEGER NOT NULL REFERENCES categories(id),
    quartier_id INTEGER NOT NULL REFERENCES quartiers(id),
    description TEXT NOT NULL CHECK(length(description) >= 20),
    photo TEXT NOT NULL,
    adresse TEXT NOT NULL,
    telephone TEXT,
    date_creation TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    statut TEXT NOT NULL DEFAULT 'nouveau' CHECK(statut IN ('nouveau', 'en cours', 'résolu', 'rejeté')),
    code_suivi TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS interventions (
    id INTEGER PRIMARY KEY,
    signalement_id INTEGER NOT NULL REFERENCES signalements(id) ON DELETE CASCADE,
    agent_id INTEGER NOT NULL REFERENCES agents(id),
    date_intervention TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    commentaire TEXT NOT NULL,
    nouveau_statut TEXT NOT NULL CHECK(nouveau_statut IN ('nouveau', 'en cours', 'résolu', 'rejeté'))
);

CREATE INDEX IF NOT EXISTS idx_signalements_date ON signalements(date_creation DESC);
CREATE INDEX IF NOT EXISTS idx_signalements_filtres ON signalements(categorie_id, quartier_id, statut);
CREATE INDEX IF NOT EXISTS idx_signalements_code ON signalements(code_suivi);
CREATE INDEX IF NOT EXISTS idx_interventions_signalement ON interventions(signalement_id, date_intervention DESC);