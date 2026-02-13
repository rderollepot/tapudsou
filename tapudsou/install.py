from __future__ import annotations

"""Cross-platform installer for Tapudsou.

This module is the canonical installer implementation and is intended to be run
via ``python -m tapudsou.install``.
"""

from abc import ABC, abstractmethod
import getpass
import os
import platform
import subprocess
from typing import Final, Sequence

from pathlib import Path
from string import Template
import sys

from .config import APP_NAME, BASE_DIR, SERVICE_ID, UserConfig, load_user_config, save_user_config


PLIST_TEMPLATE: Final[Template] = Template(
    """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${label}</string>
    <key>Program</key>
    <string>${program}</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>${hour}</integer>
        <key>Minute</key>
        <integer>${minute}</integer>
    </dict>
    <key>WorkingDirectory</key>
    <string>${workdir}</string>
    <key>StandardOutPath</key>
    <string>${log_out}</string>
    <key>StandardErrorPath</key>
    <string>${log_err}</string>
</dict>
</plist>"""
)

SYSTEMD_SERVICE_TEMPLATE: Final[Template] = Template(
    """[Unit]
Description=Tapudsou Lunch Card Monitor
After=network.target

[Service]
Type=oneshot
WorkingDirectory=${workdir}
ExecStart=${python_path} -m tapudsou ${email} ${threshold}
Environment=DISPLAY=:0
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/${uid}/bus

[Install]
WantedBy=default.target
"""
)

SYSTEMD_TIMER_TEMPLATE: Final[Template] = Template(
    """[Unit]
Description=Run Tapudsou daily

[Timer]
OnCalendar=*-*-* ${hour}:${minute}:00
Persistent=true

[Install]
WantedBy=timers.target
"""
)


class BaseInstaller(ABC):
    """Base class shared by all OS-specific installers."""

    def __init__(self) -> None:
        self.venv_dir: Path = BASE_DIR / "venv"
        self.venv_python: Path = (
            self.venv_dir / ("Scripts" if os.name == "nt" else "bin") / "python"
        )
        self.config: UserConfig = load_user_config()
        self.lang: str = self.config.language
        self.translations: dict[str, dict[str, str]] = {
            "en": {
                "step1": "--- 1. Environment Preparation ---",
                "step2": "--- 2. Configuration of your preferences ---",
                "step3_macos": "--- 3. macOS Agent Installation ---",
                "step3_linux": "--- 3. Linux Systemd Installation ---",
                "step4": "--- 4. Launch test ---",
                "email_prompt": "Email (canteen identifier): ",
                "pass_prompt": "Password (canteen identifier): ",
                "threshold_prompt": "Alert threshold in € [15.0]: ",
                "hour_prompt": "Scheduled task execution hour (0-23) [10]: ",
                "minute_prompt": "Scheduled task execution minute (0-59) [00]: ",
                "save_pass": "Securely saving password...",
                "sched_enabled": "Scheduling enabled: the balance check will occur daily at {hour}:{minute}.",
                "agent_launched": "The agent has been launched. If your balance is low, a window will open.",
                "win_info": "\n[INFO] Windows Mode: Task Scheduler configuration required (to be implemented).",
                "win_cmd": "Command to schedule: {cmd}",
                "success": "\nInstallation completed successfully!",
                "error": "\n[ERROR] Installation failed: {e}",
                "venv_error": "\n[ERROR] Unable to create virtual environment.",
                "linux_hint": "Try: sudo apt install python3-venv python3-tk",
                "linux_configured": "Linux service configured for {hour}:{minute}.",
            },
            "fr": {
                "step1": "--- 1. Préparation de l'environnement ---",
                "step2": "--- 2. Configuration de vos préférences ---",
                "step3_macos": "--- 3. Installation de l'agent macOS ---",
                "step3_linux": "--- 3. Installation des unités Systemd (Linux) ---",
                "step4": "--- 4. Test de lancement ---",
                "email_prompt": "Email (identifiant cantine) : ",
                "pass_prompt": "Mot de passe (identifiant cantine) : ",
                "threshold_prompt": "Seuil d'alerte en € [15.0] : ",
                "hour_prompt": "Heure d'execution de la tâche planifiée (0-23) [10] : ",
                "minute_prompt": "Minute d'execution de la tâche planifiée (0-59) [00] : ",
                "save_pass": "Enregistrement sécurisé du mot de passe...",
                "sched_enabled": "Planification activée : la vérification du solde s'effectuera quotidiennement à {hour}h{minute}.",
                "agent_launched": "L'agent a été lancé. Si votre solde est bas, une fenêtre s'ouvrira.",
                "win_info": "\n[INFO] Mode Windows : Configuration du Planificateur de tâches requise (à implémenter).",
                "win_cmd": "Commande à planifier : {cmd}",
                "success": "\nInstallation terminée avec succès !",
                "error": "\n[ERREUR] Échec de l'installation : {e}",
                "venv_error": "\n[ERREUR] Impossible de créer l'environnement virtuel.",
                "linux_hint": "Essayez : sudo apt install python3-venv python3-tk",
                "linux_configured": "Service Linux configuré pour {hour}h{minute}.",
            },
        }

        self.email: str | None = None
        self.threshold: str = "15.0"
        self.hour: str = "10"
        self.minute: str = "00"

    def select_language(self) -> None:
        """Allow the user to choose the language."""

        choice = input(
            "Select language / Choisissez la langue (en/fr) [en]: "
        ).strip().lower()
        if choice in {"en", "fr"}:
            self.lang = choice
        else:
            self.lang = "en"

        self.config.language = self.lang
        save_user_config(self.config)

    def t(self, key: str, **kwargs: object) -> str:
        """Return a translated string for the current language."""

        text = self.translations.get(self.lang, self.translations["en"]).get(key, key)
        return text.format(**kwargs)

    def setup_venv(self) -> None:
        """Create the virtual environment and install dependencies."""

        print(self.t("step1"))
        try:
            if not self.venv_dir.exists():
                subprocess.run(
                    [sys.executable, "-m", "venv", str(self.venv_dir)],
                    check=True,
                )

            subprocess.run(
                [str(self.venv_python), "-m", "pip", "install", "--upgrade", "pip"],
                check=True,
            )
            requirements_path = BASE_DIR / "requirements.txt"
            subprocess.run(
                [
                    str(self.venv_python),
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    str(requirements_path),
                ],
                check=True,
            )
        except subprocess.CalledProcessError:
            print(self.t("venv_error"))
            if platform.system() == "Linux":
                print(self.t("linux_hint"))
            sys.exit(1)

    def collect_info(self) -> None:
        """Collect credentials and scheduling preferences."""

        print(f"\n{self.t('step2')}")
        self.email = input(self.t("email_prompt")).strip()
        password = getpass.getpass(self.t("pass_prompt"))
        self.threshold = input(self.t("threshold_prompt")) or "15.0"
        self.hour = input(self.t("hour_prompt")) or "10"
        self.minute = input(self.t("minute_prompt")) or "00"

        print(self.t("save_pass"))
        self._set_keyring_password(password)

    def _set_keyring_password(self, password: str) -> None:
        """Store the password in the keyring via the virtual environment.

        The password and email are passed through environment variables to avoid
        brittle shell escaping.
        """

        if self.email is None:
            raise ValueError("Email must be collected before storing the password.")

        env = os.environ.copy()
        env["TAPUDSOU_EMAIL"] = self.email
        env["TAPUDSOU_PASSWORD"] = password

        script = (
            "import os, keyring; "
            f"keyring.set_password({SERVICE_ID!r}, "
            "os.environ['TAPUDSOU_EMAIL'], os.environ['TAPUDSOU_PASSWORD'])"
        )
        cmd = [str(self.venv_python), "-c", script]
        subprocess.run(cmd, check=True, env=env)

    @abstractmethod
    def install_scheduler(self) -> None:
        """Install the OS-specific scheduler unit (launchd/systemd/etc.)."""

    @abstractmethod
    def run_test(self) -> None:
        """Trigger a one-off run of the installed job."""


class MacOSInstaller(BaseInstaller):
    """Installer implementation for macOS using launchd."""

    def install_scheduler(self) -> None:
        print(f"\n{self.t('step3_macos')}")

        shell_script = BASE_DIR / f"{SERVICE_ID}.sh"
        content = (
            "#!/bin/bash\n"
            f"cd \"{BASE_DIR}\"\n"
            f"\"{self.venv_python}\" -m tapudsou "
            f"\"{self.email}\" {self.threshold}\n"
        )
        shell_script.write_text(content, encoding="utf-8")
        shell_script.chmod(0o755)

        plist_path = Path.home() / "Library/LaunchAgents" / f"{APP_NAME}.plist"
        plist_content = PLIST_TEMPLATE.substitute(
            label=APP_NAME,
            program=str(shell_script),
            hour=int(self.hour),
            minute=int(self.minute),
            workdir=str(BASE_DIR),
            log_out=str(BASE_DIR / f"{SERVICE_ID}.log"),
            log_err=str(BASE_DIR / f"{SERVICE_ID}.err"),
        )
        plist_path.write_text(plist_content, encoding="utf-8")

        subprocess.run(["launchctl", "unload", str(plist_path)], capture_output=True)
        subprocess.run(["launchctl", "load", str(plist_path)], check=True)
        print(self.t("sched_enabled", hour=self.hour, minute=self.minute))

    def run_test(self) -> None:
        print(f"\n{self.t('step4')}")
        subprocess.run(["launchctl", "start", APP_NAME], check=True)
        print(self.t("agent_launched"))


class LinuxInstaller(BaseInstaller):
    """Installer implementation for Linux using systemd user units."""

    def install_scheduler(self) -> None:
        print(f"\n{self.t('step3_linux')}")
        user_systemd_dir = Path.home() / ".config/systemd/user"
        user_systemd_dir.mkdir(parents=True, exist_ok=True)

        service_path = user_systemd_dir / f"{SERVICE_ID}.service"
        timer_path = user_systemd_dir / f"{SERVICE_ID}.timer"

        service_content = SYSTEMD_SERVICE_TEMPLATE.substitute(
            workdir=str(BASE_DIR),
            python_path=str(self.venv_python),
            email=self.email,
            threshold=self.threshold,
            uid=os.getuid(),
        )
        service_path.write_text(service_content, encoding="utf-8")

        timer_content = SYSTEMD_TIMER_TEMPLATE.substitute(
            hour=self.hour,
            minute=self.minute,
        )
        timer_path.write_text(timer_content, encoding="utf-8")

        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
        subprocess.run(
            ["systemctl", "--user", "enable", "--now", f"{SERVICE_ID}.timer"],
            check=True,
        )
        print(self.t("linux_configured", hour=self.hour, minute=self.minute))

    def run_test(self) -> None:
        print(f"\n{self.t('step4')}")
        subprocess.run(
            ["systemctl", "--user", "start", f"{SERVICE_ID}.service"],
            check=True,
        )


class WindowsInstaller(BaseInstaller):
    """Installer stub for Windows.

    A full Task Scheduler integration could be added later without breaking the
    public API of this class.
    """

    def install_scheduler(self) -> None:
        print(self.t("win_info"))
        cmd = f"\"{self.venv_python}\" -m tapudsou {self.email} {self.threshold}"
        print(self.t("win_cmd", cmd=cmd))

    def run_test(self) -> None:
        # Nothing to do for now on Windows.
        return


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint for the installer."""

    system = platform.system()
    if system == "Darwin":
        installer: BaseInstaller = MacOSInstaller()
    elif system == "Linux":
        installer = LinuxInstaller()
    elif system == "Windows":
        installer = WindowsInstaller()
    else:
        print(f"Error: System {system} is not supported yet.")
        return 1

    try:
        installer.select_language()
        installer.setup_venv()
        installer.collect_info()
        installer.install_scheduler()
        installer.run_test()
        print(installer.t("success"))
        return 0
    except Exception as exc:  # pragma: no cover - defensive wrapper
        print(installer.t("error", e=exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

