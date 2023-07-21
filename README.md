# Tapudsou

Python script that tells you when you need to add money to your lunch card.

## Installation

You need to add your credentials under the `tapudsou` identifier to your system specific credential manager.
Refer to the `keyring` [documentation](https://github.com/jaraco/keyring) for that part, or use the script `add_credentials.py`.

## Setup daily automatic launch

### On MacOS, using `launchd`

The following commands suppose you are sitting inside the project directory.

1. Change `$FULLPATH_TO_TAPUDSOU`, `$USERNAME` and `$THRESHOLD` in `tapudsou.sh` with your settings
1. Change `$FULLPATH_TO_TAPUDSOU_SH`, `$MY_HOUR` and `$MY_MINUTE` in `local.tapudsou.plist` with your settings
2. Add user execution permission to the shell script:
```console:
chmod 755 ./tapudsou.sh
```
3. Move `local.tapudsou.plist` to `~/Library/LaunchAgents`:
```console:
mv ./local.tapudsou.plist ~/Library/LaunchAgents/local.tapudsou.plist
```
4. Load agent:
```console:
launchctl load ~/Library/LaunchAgents/local.tapudsou.plist
```

#### Tips

- You can check that your agent has been properly loaded using:
```console:
launchctl list | grep local.tapudsou
```

- Once loaded, you can execute your agent immediately using:
```console:
launchctl start local.tapudsou
```

- If you make changes to `local.tapudsou.plist`, you need to reload it or they will not be applied:
```console:
launchctl unload ~/Library/LaunchAgents/local.tapudsou.plist
launchctl load ~/Library/LaunchAgents/local.tapudsou.plist
```

## Usage

```
usage: main.py [-h] username threshold

positional arguments:
  username
  threshold   Account balance in € below which to alert

options:
  -h, --help  show this help message and exit
```