import os
import sys
import platform
import subprocess
import getpass
from abc import ABC, abstractmethod
from pathlib import Path

# Configuration globale
APP_NAME = "local.tapudsou"
SERVICE_ID = "tapudsou"
BASE_DIR = Path(__file__).parent.absolute()

class BaseInstaller(ABC):
    def __init__(self):
        self.venv_dir = BASE_DIR / "venv"
        self.venv_python = (
            self.venv_dir / ("Scripts" if os.name == "nt" else "bin") / "python"
        )
        # Données partagées collectées une seule fois
        self.email = None
        self.threshold = "15.0"
        self.hour = "10"
        self.minute = "00"

    def setup_venv(self):
        """Crée l'environnement et installe les bibliothèques nécessaires."""
        print("--- 1. Préparation de l'environnement ---")
        if not self.venv_dir.exists():
            subprocess.run([sys.executable, "-m", "venv", str(self.venv_dir)], check=True)
        
        # Installation/Mise à jour des dépendances (inclut keyring et requests)
        subprocess.run([str(self.venv_python), "-m", "pip", "install", "--upgrade", "pip"], check=True)
        subprocess.run([str(self.venv_python), "-m", "pip", "install", "-r", "requirements.txt"], check=True)

    def collect_info(self):
        """Collecte toutes les informations en une seule fois."""
        print("\n--- 2. Configuration de vos préférences ---")
        self.email = input("Email (identifiant cantine) : ").strip()
        password = getpass.getpass("Mot de passe (identifiant cantine) : ")
        self.threshold = input("Seuil d'alerte en € [15.0] : ") or "15.0"
        self.hour = input("Heure d'execution de la tâche planifiée (0-23) [10] : ") or "10"
        self.minute = input("Minute d'execution de la tâche planifiée (0-59) [00] : ") or "00"

        # Sauvegarde immédiate du mot de passe dans le trousseau via le venv
        print("Enregistrement sécurisé du mot de passe...")
        self._set_keyring_password(password)

    def _set_keyring_password(self, password):
        """Exécute une commande python dans le venv pour utiliser keyring."""
        # On utilise une commande inline pour éviter de dépendre d'un fichier externe
        cmd = [
            str(self.venv_python), "-c",
            f"import keyring; keyring.set_password('{SERVICE_ID}', '{self.email}', '{password}')"
        ]
        subprocess.run(cmd, check=True)

    @abstractmethod
    def install_scheduler(self):
        pass

    @abstractmethod
    def run_test(self):
        pass

class MacOSInstaller(BaseInstaller):
    def install_scheduler(self):
        print("\n--- 3. Installation de l'agent macOS ---")
        
        # 1. Création du wrapper shell personnalisé
        shell_script = BASE_DIR / "tapudsou.sh"
        # Utilisation de l'email et du seuil collectés précédemment
        content = f"#!/bin/bash\n{self.venv_python} {BASE_DIR}/main.py {self.email} {self.threshold}\n"
        shell_script.write_text(content)
        shell_script.chmod(0o755)

        # 2. Création du fichier .plist
        plist_path = Path.home() / "Library/LaunchAgents" / f"{APP_NAME}.plist"
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{APP_NAME}</string>
    <key>Program</key>
    <string>{shell_script}</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>{self.hour}</integer>
        <key>Minute</key>
        <integer>{self.minute}</integer>
    </dict>
    <key>WorkingDirectory</key>
    <string>{BASE_DIR}</string>
    <key>StandardOutPath</key>
    <string>{BASE_DIR}/tapudsou.log</string>
    <key>StandardErrorPath</key>
    <string>{BASE_DIR}/tapudsou.err</string>
</dict>
</plist>"""
        plist_path.write_text(plist_content)

        # 3. Chargement de l'agent
        subprocess.run(["launchctl", "unload", str(plist_path)], capture_output=True)
        subprocess.run(["launchctl", "load", str(plist_path)], check=True)
        print(f"Planification activée : la vérification du solde s'effectuera quotidiennement à {self.hour}h{self.minute}.")

    def run_test(self):
        print("\n--- 4. Test de lancement ---")
        subprocess.run(["launchctl", "start", APP_NAME], check=True)
        print("L'agent a été lancé. Si votre solde est bas, une fenêtre s'ouvrira.")

class WindowsInstaller(BaseInstaller):
    """Squelette pour la future implémentation Windows."""
    def install_scheduler(self):
        print("\n[INFO] Mode Windows : Configuration du Planificateur de tâches requise (à implémenter).")
        print(f"Commande à planifier : {self.venv_python} {BASE_DIR}/main.py {self.email} {self.threshold}")

    def run_test(self):
        pass

def main():
    system = platform.system()
    installer = MacOSInstaller() if system == "Darwin" else WindowsInstaller()

    try:
        installer.setup_venv()
        installer.collect_info()
        installer.install_scheduler()
        installer.run_test()
        print("\nInstallation terminée avec succès !")
    except Exception as e:
        print(f"\n[ERREUR] Échec de l'installation : {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()