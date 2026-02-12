# Tapudsou

**Tapudsou** is a lightweight utility designed to automatically monitor your Innovorder (Dupont Restauration) lunch card balance and alert you when a top-up is required.

## 1. Prerequisites

Before proceeding, ensure the following requirements are met :

* **Python 3** : This script assumes `python3` is already installed on your system.
* **Account Activation** : You must have an active account on the Innovorder platform. Instructions provided by [Dupont Restauration](assets/innovorder_setup_guide.jpg) are summarized below.
  * **Portal** : [https://ewallet.innovorder.fr/1249/home](https://ewallet.innovorder.fr/1249/home).
  * **First Login** : Use `lastname.firstname@ara.fr` with the temporary password `12345`.
  * **Setup** : Follow the prompts to set your definitive email and personal password.



---

## 2. Intent and Security

The script follows a "set and forget" philosophy :

* **Automated Monitoring** : It runs daily at a scheduled time via a system agent (`launchd` on macOS).
* **Security** : Your password is **never stored in plain text**. The script utilizes the `keyring` library to delegate secret storage to your OS-native secure vault (macOS Keychain).
* **Alerts** : It fetches your exact balance from the Innovorder API. If it falls below your chosen threshold, the script triggers a system notification and opens the recharge portal in your browser.

---

## 3. Installation

Follow these steps to set up the automation on your machine :

1. **Clone the repository** :
```bash
git clone git@github.com:rderollepot/tapudsou.git
cd tapudsou
git checkout macos_launchd

```


2. **Run the automated setup** :
```bash
python3 setup.py
```

> [!NOTE]
> **macOS Users**: When running the script for the first time, a macOS security popup will appear asking to authorize Python to access your Keychain to securely retrieve your login credentials.
>
> ![macOS Keychain Prompt](assets/macos_keychain_prompt.png)


3. **Configuration** :
The installer will prompt you for :
  * Your Innovorder email and password.
  * The balance threshold in € (e.g., `15.0`).
  * The preferred daily execution time (Hour/Minute).



The `setup.py` script automatically creates a virtual environment, installs dependencies, secures your credentials, and registers the macOS background agent.

---

## 4. Manual Testing and Logs

To verify the installation or debug issues without waiting for the next scheduled run :

* **Trigger the agent immediately** :
```bash
launchctl start local.tapudsou

```


* **Check Execution Logs** :
If the script does not seem to trigger, consult the logs in the project directory :
  * `tapudsou.log` : Standard output of the script.
  * `tapudsou.err` : Detailed error messages (e.g., network issues or credential errors).



---

## 5. Uninstallation

To completely remove the script and its associated data from your system :

1. **Remove the scheduler** :
```bash
launchctl unload ~/Library/LaunchAgents/local.tapudsou.plist
rm ~/Library/LaunchAgents/local.tapudsou.plist

```


2. **Clear stored credentials** :
```bash
security delete-generic-password -s "tapudsou"

```


3. **Delete local files** :
```bash
cd ..
rm -rf tapudsou

```
