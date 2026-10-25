import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "data" / "signalements.db"
OUTPUT = BASE_DIR / "export_projet.sql"


def main():
    if not DATABASE.exists():
        raise SystemExit("Base absente. Exécutez d’abord : python donnees_test.py")
    with sqlite3.connect(DATABASE) as connection, OUTPUT.open("w", encoding="utf-8", newline="\n") as stream:
        for statement in connection.iterdump():
            stream.write(statement + "\n")
    print(f"Export SQL généré : {OUTPUT}")


if __name__ == "__main__":
    main()