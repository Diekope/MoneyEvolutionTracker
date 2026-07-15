# 💼 MoneyTracker — Summer 2026

A minimalist and elegant macOS application to track the evolution of your net worth over the summer.

[![Download macOS App](https://img.shields.io/badge/Download-macOS%20App-00ADB5?style=for-the-badge&logo=apple)](https://github.com/Diekope/MoneyEvolutionTracker/releases/download/v1.0.0/MoneyTracker-macOS.zip)

The application offers three interfaces:
1. **Web Dashboard (Recommended GUI)**: A modern and responsive web interface with dynamic charts and an easy-to-use calendar date picker.
2. **macOS Status Bar Widget**: An icon and context menu integrated directly into your macOS menu bar (`rumps`), showing your current balance and net growth.
3. **Terminal CLI**: An interactive console interface inside your terminal.

---

## 🚀 First Launch & Initialization

On the very first launch, the application is completely empty.
It will ask you to configure:
1. **Your monetary goal** (in Euros).
2. **Your target end date** (via a standard calendar date picker).

Once validated, this will unlock the main dashboard (Web or CLI) where you can add, edit, or delete entries.

### Global Shortcuts
Thanks to `uv`, you can run the following commands from any folder in your terminal:
*   **`patrimoine`**: Starts the status bar app (macOS menu bar).
*   **`patrimoine-gui`**: Starts the local background server and opens the web dashboard in your default browser.
*   **`patrimoine-cli`**: Starts the interactive CLI in your terminal.

### Project Directory Launch
If you are in the project folder, you can also run:
```bash
uv run main.py          # Starts the Status Bar app (macOS)
uv run main.py --gui    # Starts the Web Dashboard (background server + browser)
uv run main.py --cli    # Starts the interactive console menu
```

---

## 🛠️ Web Dashboard Features (Recommended)

- **Native Date Picker (Calendar)**: Solves all date formatting issues using the standard HTML5 date input native to macOS (Safari/Chrome/Firefox).
- **Dynamic & Interactive Chart**: Powered by **Chart.js** with animated tooltips on hover (displaying values and notes) and a custom neon gradient color.
- **Responsive Form**: Save new entries or edit them easily. Clicking a row in the table automatically pre-fills the form for modification.
- **Easy Deletion**: Simply click the 🗑️ button next to any entry.
- **Keep-Alive Server**: Clicking **Fermer la page** closes the browser tab but keeps the local server running in the background.
- **Objective Management**: Click **⚙️ Objectif** to adjust or reset your savings target and end date at any time.

---

## ⚙️ Background Startup (macOS Launch Agent)

The application uses a **macOS Launch Agent** to run in the background and start automatically whenever your Mac boots up.

### 1. Enable Auto-Start (Run at boot)
To configure and load the application to run automatically at startup:
```bash
launchctl load ~/Library/LaunchAgents/fr.valquitravaille.moneytracking.plist
```
*This command immediately starts the application (the 💼 icon will appear in your menu bar and the web server will start listening on port `5005`) and registers it to load automatically on boot.*

> [!IMPORTANT]
> The Launch Agent file contains absolute paths specific to the user who configured it. If sharing this project with someone else, they should edit the plist file located at `~/Library/LaunchAgents/fr.valquitravaille.moneytracking.plist` to match their own system username and folder location, or simply run the manual startup command.

### 2. Disable Auto-Start (Stop permanently)
To stop the background agent and prevent it from launching at boot:
```bash
launchctl unload ~/Library/LaunchAgents/fr.valquitravaille.moneytracking.plist
```
*This will immediately kill the background server, remove the menu bar icon, and deregister the startup service.*

> [!NOTE]
> Clicking **Quit** in the macOS menu bar icon stops the application and the local server immediately. It will **not** restart automatically during your current session. It will only start again when you reboot/restart your Mac.

### 3. Check status
To check if the background server is currently running:
```bash
lsof -i :5005
```

---

## 📂 Data Structure

All your data is saved locally on your machine:
*   Data entries: [patrimoine.csv](file:///Users/ValQuiTravaille/Projects/Tests/MoneyTracking/patrimoine.csv)
*   Objective configuration: `config.json`

---

## ⚠️ Troubleshooting macOS Gatekeeper Warning

Since the application is not signed with a paid Apple Developer certificate, macOS will block it on first open with a warning like *"MoneyTracker is damaged"* or *"developer cannot be verified"*. This is a standard security precaution.

To open the app:
1.  **Right-click** (or Control-click) `MoneyTracker.app` in Finder and select **Open**.
2.  If it still doesn't open, open your terminal and run the following command to remove the quarantine flag:
    ```bash
    xattr -cr /path/to/MoneyTracker.app
    ```
    *(e.g., `xattr -cr ~/Downloads/MoneyTracker.app` if you downloaded it to your Downloads folder).*
3.  Double-click `MoneyTracker.app` to launch normally.
