# 💼 Suivi de Patrimoine — Été 2026

Une application macOS minimaliste et élégante pour suivre l'évolution de votre patrimoine sur la période estivale.
L'application propose trois interfaces :
1. **Mode Web Dashboard (GUI Recommandé)** : Une interface web moderne et ultra-fluide avec graphiques dynamiques et gestion simplifiée des dates.
2. **Mode Status Bar (macOS)** : Une icône et un menu directement intégrés dans la barre des menus macOS (`rumps`), affichant votre solde et l'évolution globale.
3. **Mode Terminal (CLI)** : Une console interactive dans votre terminal.

---

## 🚀 Premier Lancement & Initialisation

Au tout premier lancement (ou si vous réinitialisez), l'application est entièrement vide. 
Elle vous demandera d'abord de configurer :
1. **Votre objectif monétaire** (en euros).
2. **Votre date de fin** (au format AAAA-MM-JJ via un sélecteur de date calendrier standard).

Une fois validé, cela déverrouillera l'interface principale (Web ou CLI) où vous pouvez ajouter, modifier ou supprimer des entrées.

### Raccourcis globaux
Grâce à `uv`, vous pouvez utiliser les commandes suivantes depuis n'importe quel répertoire de votre terminal :
*   **`patrimoine`** : Lance l'icône dans la barre des menus macOS.
*   **`patrimoine-gui`** : Démarre le serveur local et ouvre le tableau de bord web.
*   **`patrimoine-cli`** : Lance la console interactive dans votre terminal.

### Lancement via le projet
Si vous êtes dans le répertoire du projet, vous pouvez aussi lancer :
```bash
uv run main.py          # Démarre l'application Status Bar (macOS)
uv run main.py --gui    # Démarre l'interface Web (Tableau de bord)
uv run main.py --cli    # Démarre la console interactive
```

---

## 🛠️ Fonctionnalités du Tableau de bord Web (Recommandé)

- **Sélecteur de date Natif (Calendrier)** : Résout tous les problèmes de changement de date grâce au sélecteur HTML5 natif de macOS (Safari/Chrome).
- **Graphique Dynamique et Interactif** : Propulsé par **Chart.js** avec des tooltips au survol de la souris montrant vos notes et un dégradé de couleur néon.
- **Formulaire de Saisie Réactif** : Remplissez ou modifiez les entrées. Cliquer sur une ligne du tableau remplit automatiquement le formulaire pour modification.
- **Suppression simple** : Bouton 🗑️ à côté de chaque entrée.
- **Bouton Quitter dédié** : Arrête instantanément le serveur local et ferme l'application proprement en cliquant sur **Quitter l'App**.
- **Gestionnaire d'Objectifs** : Modifiez à tout moment votre objectif d'épargne ou la date cible.

---

## 📂 Structure des données

Toutes vos saisies sont enregistrées localement :
*   Données : [patrimoine.csv](file:///Users/ValQuiTravaille/Projects/Tests/MoneyTracking/patrimoine.csv)
*   Configuration : `config.json`

---

## ⚙️ Démarrage et Arrêt Définitif (Arrière-plan macOS)

L'application utilise un **Launch Agent macOS** pour tourner automatiquement en tâche de fond et démarrer dès le démarrage du système.

### 1. Activer le démarrage automatique (Lancement définitif)
Pour configurer et activer l'application pour qu'elle s'exécute en arrière-plan à chaque démarrage de macOS :
```bash
launchctl load ~/Library/LaunchAgents/fr.valquitravaille.moneytracking.plist
```
*Cette commande démarre immédiatement l'application (l'icône 💼 apparaîtra dans la barre de menus et le serveur web sur le port `5005` sera actif) et s'assure qu'elle se lancera automatiquement après chaque redémarrage de votre Mac.*

### 2. Désactiver le démarrage automatique (Arrêt définitif)
Pour arrêter complètement le service en arrière-plan et l'empêcher de démarrer lors des prochains lancements de macOS :
```bash
launchctl unload ~/Library/LaunchAgents/fr.valquitravaille.moneytracking.plist
```
*Cela coupe immédiatement le serveur web et l'icône de la barre des tâches, et retire l'application des lancements automatiques.*

### 3. Comment vérifier si l'application tourne ?
Pour vérifier si le serveur web tourne en tâche de fond :
```bash
lsof -i :5005
```
Si un processus s'affiche, c'est que l'application est active et vous pouvez vous rendre sur [http://127.0.0.1:5005](http://127.0.0.1:5005).
