#!/usr/bin/env python3
import os
import sys
import csv
import json
import datetime
import subprocess
import webbrowser
import threading
import time
import logging
from flask import Flask, render_template, request, jsonify
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import rumps

# Persistent data directory in user home folder
DATA_DIR = os.path.join(os.path.expanduser("~"), ".moneytracking")
os.makedirs(DATA_DIR, exist_ok=True)
DATA_FILE = os.path.join(DATA_DIR, "patrimoine.csv")
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


# Initialize Flask App using bundled templates folder
app = Flask(__name__, template_folder=get_resource_path("templates"))

# Quiet Flask logging
log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)


def init_empty_files():
    """Initializes files without any default values."""
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["date", "valeur", "note"])
            writer.writeheader()


def load_config():
    """Loads goal and end date configuration."""
    if not os.path.exists(CONFIG_FILE):
        return None
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_config(objectif, date_fin):
    """Saves goal and end date configuration."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"objectif": float(objectif), "date_fin": date_fin}, f, indent=4)


def load_data():
    """Loads and sorts data chronologically."""
    init_empty_files()
    data = []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    data.append(
                        {
                            "date": datetime.datetime.strptime(
                                row["date"].strip(), "%Y-%m-%d"
                            ).date(),
                            "valeur": float(row["valeur"].strip()),
                            "note": row.get("note", "").strip(),
                        }
                    )
                except ValueError:
                    continue
    except Exception as e:
        print(f"Erreur lors du chargement des données: {e}")

    # Sort by date
    data.sort(key=lambda x: x["date"])
    return data


def save_entry(date_str, valeur, note="", overwrite=False):
    """Saves a single entry to the CSV file, accumulating or replacing if date already exists."""
    data = load_data()
    target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()

    updated = False
    for entry in data:
        if entry["date"] == target_date:
            if overwrite:
                entry["valeur"] = float(valeur)
                entry["note"] = note
            else:
                entry["valeur"] += float(valeur)
                if note:
                    if entry["note"]:
                        entry["note"] = f"{entry['note']}, {note}"
                    else:
                        entry["note"] = note
            updated = True
            break

    if not updated:
        data.append({"date": target_date, "valeur": float(valeur), "note": note})

    data.sort(key=lambda x: x["date"])

    with open(DATA_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "valeur", "note"])
        writer.writeheader()
        for entry in data:
            writer.writerow(
                {
                    "date": entry["date"].strftime("%Y-%m-%d"),
                    "valeur": entry["valeur"],
                    "note": entry["note"],
                }
            )


def delete_entry(date_str):
    """Deletes an entry by its date string."""
    data = load_data()
    target_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    new_data = [entry for entry in data if entry["date"] != target_date]

    with open(DATA_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "valeur", "note"])
        writer.writeheader()
        for entry in new_data:
            writer.writerow(
                {
                    "date": entry["date"].strftime("%Y-%m-%d"),
                    "valeur": entry["valeur"],
                    "note": entry["note"],
                }
            )


def get_stats():
    """Calculates statistics: current value, change since start, percentage."""
    data = load_data()
    if not data:
        return 0.0, 0.0, 0.0

    latest = data[-1]["valeur"]
    first = data[0]["valeur"]
    diff = latest - first
    pct = (diff / first * 100) if first != 0 else 0.0
    return latest, diff, pct


def generate_chart():
    """Generates a beautiful dark-mode matplotlib chart and opens it."""
    data = load_data()
    config = load_config()

    if not data:
        plt.style.use("dark_background")
        fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
        fig.patch.set_facecolor("#121212")
        ax.set_facecolor("#1a1a1a")
        ax.text(
            0.5,
            0.5,
            "Aucune donnée enregistrée.\nSaisissez votre patrimoine dans la page web.",
            color="#AAAAAA",
            fontsize=12,
            ha="center",
            va="center",
        )
        ax.set_title(
            "Évolution de votre Patrimoine",
            fontsize=14,
            fontweight="bold",
            color="#EEEEEE",
            pad=15,
        )
        plt.tight_layout()
        chart_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "patrimoine_evolution.png"
        )
        plt.savefig(chart_path, facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close()
        try:
            subprocess.run(["open", chart_path])
        except Exception:
            pass
        return chart_path

    dates = [entry["date"] for entry in data]
    valeurs = [entry["valeur"] for entry in data]
    notes = [entry["note"] for entry in data]

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
    fig.patch.set_facecolor("#121212")
    ax.set_facecolor("#1a1a1a")

    (line,) = ax.plot(
        dates,
        valeurs,
        color="#00ADB5",
        linewidth=3,
        marker="o",
        markersize=8,
        markerfacecolor="#EEEEEE",
        markeredgecolor="#00ADB5",
        markeredgewidth=2,
        label="Patrimoine",
    )

    ax.fill_between(
        dates,
        valeurs,
        min(valeurs) * 0.98 if min(valeurs) > 0 else 0,
        color="#00ADB5",
        alpha=0.15,
    )

    if config:
        goal = config["objectif"]
        ax.axhline(
            y=goal,
            color="#FF5722",
            linestyle="--",
            linewidth=1.5,
            alpha=0.8,
            label=f"Objectif ({goal:,.0f} €)",
        )

    # Set x limits to recorded dates to avoid squishing data when end_date is far in the future
    margin = datetime.timedelta(days=2) if len(dates) > 1 else datetime.timedelta(days=1)
    ax.set_xlim(min(dates) - margin, max(dates) + margin)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax.xaxis.set_major_locator(
        mdates.DayLocator(
            interval=max(1, (max(dates) - min(dates)).days // 6)
            if len(dates) > 1
            else 1
        )
    )
    plt.xticks(rotation=15, color="#AAAAAA")
    plt.yticks(color="#AAAAAA")

    ax.grid(True, linestyle="--", alpha=0.2, color="#555555")

    for i, (date, val, note) in enumerate(zip(dates, valeurs, notes)):
        if note:
            offset = 15 if i % 2 == 0 else -25
            ax.annotate(
                note,
                xy=(date, val),
                xytext=(0, offset),
                textcoords="offset points",
                arrowprops=dict(arrowstyle="-", color="#00ADB5", alpha=0.5),
                fontsize=8,
                color="#EEEEEE",
                ha="center",
                bbox=dict(
                    boxstyle="round,pad=0.3", fc="#252525", ec="#333333", alpha=0.8
                ),
            )

    latest, diff, pct = get_stats()
    sign = "+" if diff >= 0 else ""

    if config:
        progression = (
            (latest / config["objectif"] * 100) if config["objectif"] != 0 else 0
        )
        stat_text = f"Actuel : {latest:,.2f} €  ({sign}{diff:,.2f} € | {sign}{pct:.2f}%)  —  Objectif : {config['objectif']:,.2f} € ({progression:.1f}%)"
    else:
        stat_text = (
            f"Actuel : {latest:,.2f} €  ({sign}{diff:,.2f} € | {sign}{pct:.2f}%)"
        )

    # Put subtitle on ax title and main title on fig suptitle to prevent overlapping
    ax.set_title(stat_text, fontsize=10, color="#00ADB5", pad=10)
    fig.suptitle("Évolution de votre Patrimoine", fontsize=14, fontweight="bold", color="#EEEEEE")
    ax.legend(
        loc="upper left", framealpha=0.6, facecolor="#1e1e1e", edgecolor="#333333"
    )

    for spine in ax.spines.values():
        spine.set_color("#333333")

    plt.tight_layout(rect=[0, 0, 1, 0.93])

    chart_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "patrimoine_evolution.png"
    )
    plt.savefig(chart_path, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()

    try:
        subprocess.run(["open", chart_path])
    except Exception:
        pass
    return chart_path


# --- FLASK WEB SERVER ROUTES ---
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/data", methods=["GET"])
def get_data():
    config = load_config()
    entries = load_data()
    latest, diff, pct = get_stats()
    return jsonify(
        {
            "config": config,
            "entries": [
                {
                    "date": e["date"].strftime("%Y-%m-%d"),
                    "valeur": e["valeur"],
                    "note": e["note"],
                }
                for e in entries
            ],
            "stats": {"latest": latest, "diff": diff, "pct": pct},
        }
    )


@app.route("/api/config", methods=["POST"])
def update_config():
    req_data = request.json
    try:
        goal = float(req_data["objectif"])
        date_fin = req_data["date_fin"]
        # Validate date
        datetime.datetime.strptime(date_fin, "%Y-%m-%d")
        save_config(goal, date_fin)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/entries", methods=["POST"])
def create_or_update_entry():
    req_data = request.json
    try:
        date_str = req_data["date"]
        valeur = float(req_data["valeur"])
        note = req_data.get("note", "").strip()
        overwrite = req_data.get("overwrite", False)
        # Validate date
        datetime.datetime.strptime(date_str, "%Y-%m-%d")
        save_entry(date_str, valeur, note, overwrite=overwrite)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/entries/<date_str>", methods=["DELETE"])
def remove_entry(date_str):
    try:
        datetime.datetime.strptime(date_str, "%Y-%m-%d")
        delete_entry(date_str)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/shutdown", methods=["POST"])
def shutdown():
    def kill_server():
        time.sleep(0.5)
        os._exit(0)

    threading.Thread(target=kill_server).start()
    return jsonify({"status": "shutdown_initiated"})


# Threading locks and starts
FLASK_STARTED = False
flask_lock = threading.Lock()


def ensure_server_running():
    global FLASK_STARTED
    with flask_lock:
        if not FLASK_STARTED:
            server_thread = threading.Thread(
                target=lambda: app.run(host="127.0.0.1", port=5005, debug=False),
                daemon=True,
            )
            server_thread.start()
            FLASK_STARTED = True


def run_web_gui():
    """Starts the Flask server on the main thread and opens the web browser."""
    init_empty_files()

    def open_browser():
        time.sleep(0.8)
        webbrowser.open("http://127.0.0.1:5005")

    threading.Thread(target=open_browser, daemon=True).start()

    print("\n" + "=" * 60)
    print(" 🚀 SERVEUR DE PATRIMOINE LANCÉ")
    print(" L'interface web s'ouvre automatiquement dans votre navigateur.")
    print(" URL : http://127.0.0.1:5005")
    print("=" * 60 + "\n")
    print("Pour quitter : cliquez sur le bouton 'Quitter' dans la page web")
    print("ou appuyez sur Ctrl+C dans ce terminal.")

    app.run(host="127.0.0.1", port=5005, debug=False)


# --- TERMINAL / CLI INTERFACE ---
def run_cli():
    """Runs a beautiful interactive terminal menu."""
    init_empty_files()

    config = load_config()
    if not config:
        print("\n" + "=" * 50)
        print(" ⚙️ CONFIGURATION INITIALE (Suivi de Patrimoine)")
        print("=" * 50)
        print("Tout est vide. Veuillez configurer vos objectifs d'abord :\n")

        while True:
            goal_str = input("Objectif monétaire (€) : ").strip()
            try:
                goal = float(goal_str.replace(" ", "").replace(",", "."))
                if goal <= 0:
                    raise ValueError
                break
            except ValueError:
                print("❌ Veuillez entrer une valeur numérique positive.")

        while True:
            date_str = (
                input("Date de fin [AAAA-MM-JJ] (défaut: 2026-09-30) : ").strip()
                or "2026-09-30"
            )
            try:
                datetime.datetime.strptime(date_str, "%Y-%m-%d")
                break
            except ValueError:
                print("❌ Date invalide. Utilisez le format AAAA-MM-JJ.")

        save_config(goal, date_str)
        print("✅ Configuration enregistrée avec succès !")
        config = load_config()

    print("\n" + "=" * 50)
    print(" 💼 SUIVI DE PATRIMOINE (Mode Terminal)")
    print("=" * 50)

    while True:
        data = load_data()
        latest, diff, pct = get_stats()
        goal = config["objectif"]
        progress_pct = (latest / goal * 100) if goal != 0 else 0
        sign = "+" if diff >= 0 else ""

        print(
            f"\n📊 Actuel : \033[1;36m{latest:,.2f} €\033[0m ({sign}{diff:,.2f} € | {sign}{pct:.2f}%)"
        )
        print(
            f"🎯 Objectif : {goal:,.2f} € d'ici le {config['date_fin']} (Progression: {progress_pct:.1f}%)"
        )
        print("-" * 50)
        print("1. ➕ Ajouter / Modifier une entrée")
        print("2. 🗑️ Supprimer une entrée")
        print("3. 🖥️ Ouvrir l'interface graphique (Navigateur)")
        print("4. 📅 Voir l'historique complet (Console)")
        print("5. 📈 Afficher le graphique d'évolution (PNG)")
        print("6. ⚙️ Modifier les paramètres d'objectif")
        print("7. 🚪 Quitter")
        print("-" * 50)

        choice = input("Votre choix (1-7) : ").strip()

        if choice == "1":
            default_date = datetime.date.today().strftime("%Y-%m-%d")
            date_str = (
                input(f"Date [AAAA-MM-JJ] (défaut: {default_date}) : ").strip()
                or default_date
            )
            try:
                datetime.datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                print("❌ Format de date invalide. Utilisez AAAA-MM-JJ.")
                continue

            val_str = input("Valeur (€) : ").strip()
            try:
                valeur = float(val_str.replace(" ", "").replace(",", "."))
            except ValueError:
                print("❌ Valeur numérique invalide.")
                continue

            note = input("Note / Commentaire : ").strip()
            save_entry(date_str, valeur, note)
            print(f"✅ Entrée enregistrée pour le {date_str} !")

        elif choice == "2":
            if not data:
                print("Aucune donnée enregistrée à supprimer.")
                continue

            print("\n📋 Choisissez l'entrée à supprimer :")
            for idx, entry in enumerate(data):
                print(
                    f"{idx + 1}. {entry['date'].strftime('%Y-%m-%d')} — {entry['valeur']:,.2f} € ({entry['note']})"
                )

            del_choice = input(
                "Entrez le numéro à supprimer (ou Entrée pour annuler) : "
            ).strip()
            if not del_choice:
                continue

            try:
                del_idx = int(del_choice) - 1
                if 0 <= del_idx < len(data):
                    date_to_del = data[del_idx]["date"].strftime("%Y-%m-%d")
                    delete_entry(date_to_del)
                    print(f"✅ Entrée du {date_to_del} supprimée !")
                else:
                    print("❌ Numéro hors plage.")
            except ValueError:
                print("❌ Saisie invalide.")

        elif choice == "3":
            print("Démarrage du serveur web local...")
            ensure_server_running()
            webbrowser.open("http://127.0.0.1:5005")
            input(
                "\nInterface web ouverte sur http://127.0.0.1:5005 !\nAppuyez sur Entrée pour revenir au menu..."
            )

        elif choice == "4":
            if not data:
                print("Aucune donnée enregistrée.")
                continue
            print("\n📋 HISTORIQUE DES SAISIES :")
            print(f"{'Date':<12} | {'Valeur (€)':<15} | {'Note':<25}")
            print("-" * 58)
            for entry in data:
                print(
                    f"{entry['date'].strftime('%Y-%m-%d'):<12} | {entry['valeur']:>12,.2f} € | {entry['note']:<25}"
                )

        elif choice == "5":
            print("Génération et ouverture du graphique...")
            generate_chart()

        elif choice == "6":
            while True:
                goal_str = input("Nouvel objectif monétaire (€) : ").strip()
                try:
                    goal = float(goal_str.replace(" ", "").replace(",", "."))
                    if goal <= 0:
                        raise ValueError
                    break
                except ValueError:
                    print("❌ Veuillez entrer une valeur numérique positive.")

            while True:
                date_str = input("Nouvelle date de fin [AAAA-MM-JJ] : ").strip()
                try:
                    datetime.datetime.strptime(date_str, "%Y-%m-%d")
                    break
                except ValueError:
                    print("❌ Date invalide. Utilisez le format AAAA-MM-JJ.")

            save_config(goal, date_str)
            config = load_config()
            print("✅ Configuration mise à jour !")

        elif choice == "7":
            print("\nAu revoir !")
            break
        else:
            print("❌ Option invalide.")


# --- MACOS STATUS BAR APP ---
class PatrimoineApp(rumps.App):
    def __init__(self):
        super().__init__("Patrimoine", title="💼 ...")
        ensure_server_running()
        self.update_menu()
        self.timer = rumps.Timer(self.refresh_ui, 10)
        self.timer.start()

    def refresh_ui(self, _=None):
        self.update_menu()

    def update_menu(self):
        """Reloads data and updates the status bar title and menu."""
        config = load_config()

        if not config:
            self.title = "💼 Configurer"
            self.menu.clear()
            self.menu.add(
                rumps.MenuItem(
                    "⚙️ Configurer l'Objectif (Web)", callback=self.on_open_gui
                )
            )
            self.menu.add(rumps.separator)
            self.menu.add(rumps.MenuItem("Quit", callback=rumps.quit_application))
            return

        latest, diff, pct = get_stats()
        sign = "+" if diff >= 0 else ""

        self.title = f"💼 {latest:,.0f}€ ({sign}{pct:.1f}%)"

        self.menu.clear()
        self.menu.add(
            rumps.MenuItem(f"Patrimoine Actuel : {latest:,.2f} €", callback=self.on_open_gui)
        )
        self.menu.add(
            rumps.MenuItem(
                f"Objectif : {config['objectif']:,.2f} € ({latest / config['objectif'] * 100:.1f}%)",
                callback=self.on_open_gui,
            )
        )
        self.menu.add(rumps.MenuItem(f"Cible : {config['date_fin']}", callback=self.on_open_gui))
        self.menu.add(rumps.separator)

        self.menu.add(
            rumps.MenuItem("🖥️ Ouvrir l'interface Web", callback=self.on_open_gui)
        )
        self.menu.add(
            rumps.MenuItem(
                "📈 Afficher le graphique (PNG)", callback=self.on_show_chart
            )
        )
        self.menu.add(
            rumps.MenuItem(
                "➕ Ajouter une entrée (Rapide)...", callback=self.on_add_entry
            )
        )
        self.menu.add(
            rumps.MenuItem(
                "📋 Voir l'historique (Texte)", callback=self.on_view_history
            )
        )
        self.menu.add(
            rumps.MenuItem("⚙️ Modifier l'Objectif", callback=self.on_reset_config)
        )
        self.menu.add(
            rumps.MenuItem("📂 Ouvrir le fichier CSV", callback=self.on_open_csv)
        )

        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("Quit", callback=rumps.quit_application))

    def on_open_gui(self, _):
        ensure_server_running()
        webbrowser.open("http://127.0.0.1:5005")

    def on_show_chart(self, _):
        generate_chart()

    def on_add_entry(self, _):
        window = rumps.Window(
            title="Ajouter une entrée de patrimoine",
            message="Saisissez la valeur de votre patrimoine en euros.\nFormat de date: AAAA-MM-JJ (aujourd'hui par défaut)",
            ok="Enregistrer",
            cancel="Annuler",
            dimensions=(300, 40),
        )
        window.add_buttons("Ajouter Note")
        response = window.run()

        if response.clicked == 1:
            val_text = response.text.strip()
            if not val_text:
                rumps.alert("Erreur", "Veuillez entrer une valeur numérique.")
                return
            try:
                valeur = float(val_text.replace(" ", "").replace(",", "."))
            except ValueError:
                rumps.alert("Erreur", "Valeur numérique invalide.")
                return

            note_win = rumps.Window(
                title="Note",
                message="Ajoutez une note optionnelle :",
                ok="Continuer",
                cancel="Sans note",
                dimensions=(300, 20),
            )
            note_response = note_win.run()
            note = note_response.text.strip() if note_response.clicked == 1 else ""

            today = datetime.date.today().strftime("%Y-%m-%d")
            save_entry(today, valeur, note)
            self.update_menu()
            rumps.notification(
                "Succès", "Patrimoine mis à jour", f"Nouveau solde: {valeur:,.2f} €"
            )

        elif response.clicked == 3:
            val_text = response.text.strip()
            try:
                valeur = float(val_text.replace(" ", "").replace(",", "."))
            except ValueError:
                rumps.alert("Erreur", "Valeur numérique invalide.")
                return
            note_win = rumps.Window(
                title="Ajouter Note",
                message="Entrez une note pour cette saisie :",
                dimensions=(300, 20),
            )
            note_response = note_win.run()
            note = note_response.text.strip()

            today = datetime.date.today().strftime("%Y-%m-%d")
            save_entry(today, valeur, note)
            self.update_menu()
            rumps.notification(
                "Succès", "Patrimoine mis à jour", f"Nouveau solde: {valeur:,.2f} €"
            )

    def on_view_history(self, _):
        data = load_data()
        if not data:
            rumps.alert("Historique", "Aucune entrée de patrimoine enregistrée.")
            return

        history_lines = [f"{'Date':<10} | {'Valeur':<12} | Note"]
        history_lines.append("-" * 40)
        for entry in data:
            history_lines.append(
                f"{entry['date'].strftime('%Y-%m-%d')} | {entry['valeur']:>10,.2f} € | {entry['note']}"
            )

        rumps.alert("Historique du Patrimoine", "\n".join(history_lines))

    def on_reset_config(self, _):
        ensure_server_running()
        webbrowser.open("http://127.0.0.1:5005")

    def on_open_csv(self, _):
        subprocess.run(["open", DATA_FILE])


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] in ["--cli", "-c"]:
            run_cli()
        elif sys.argv[1] in ["--gui", "-g", "--web"]:
            run_web_gui()
        else:
            print(f"Argument inconnu: {sys.argv[1]}")
            print(
                "Arguments valides: --cli pour la console, --gui pour l'interface web."
            )
    else:
        # Default runs status bar app
        try:
            init_empty_files()
            app = PatrimoineApp()
            app.run()
        except Exception as e:
            print(f"Impossible de démarrer la GUI Status Bar App: {e}")
            print("Démarrage en mode Web GUI...")
            run_web_gui()


if __name__ == "__main__":
    main()
