# Tapudsou

Python script that tells you when you need to add money to your lunch card.

## Installation

You need to add your credentials under the `tapudsou` identifier to your system specific credential manager.
Refer to the `keyring` [documentation](https://github.com/jaraco/keyring) for that part, or use the script `add_credentials.py`.

## Usage

```
usage: main.py [-h] username threshold

positional arguments:
  username
  threshold   Account balance in € below which to alert

options:
  -h, --help  show this help message and exit
```