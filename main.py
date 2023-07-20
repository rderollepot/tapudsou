from tkinter.messagebox import showinfo
import argparse
import webbrowser

import requests
import keyring


def message_box(title, text):
    return showinfo(title, text)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('username')
    parser.add_argument('threshold', type=float, help='Account balance in € below which to alert')
    args = parser.parse_args()
    pwd = keyring.get_password("tapudsou", args.username)

    if not pwd:
        message_box("Tapudsou", f"Impossible de trouver le mot de passe")
        return

    headers = {
        "password": pwd,
        "rememberMe": "false",
        "grant_type": "password",
        "brandId": 1249,
        "username": args.username,
    }

    with requests.Session() as s:
        r = s.post("https://api.innovorder.fr/oauth/login", headers)
        rr = r.json()
        customer_id = rr['data']['customer']['customerId']
        headers = {
            "authorization": f"Bearer {rr['access_token']}"
        }

        r = s.get(f"https://api.innovorder.fr/customers/{customer_id}/balance", headers=headers)
        rr = r.json()
        balance = rr['data']['customerBalance']
        balance = float(balance) / 100.

        if balance < args.threshold:
            message_box("Tapudsou", f"Il reste {balance}€ sur ta carte de cantine!")
            webbrowser.open_new_tab("https://ewallet.innovorder.fr/1249/home")


if __name__ == '__main__':
    main()
