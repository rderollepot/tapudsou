import keyring
import getpass

# add entry to the user os secret manager
username = input("Email : ")
password = getpass.getpass("Mot de passe : ")
keyring.set_password("tapudsou", username, password)
