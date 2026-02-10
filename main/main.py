#!/usr/bin/env python3
"""SSL Sync addon main script."""
import json
import time
from pathlib import Path

CONFIG_FILE = Path("/data/options.json")


def load_config():
    """Load configuration from options.json."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}


def main():
    print("Starting SSL Sync addon...")
    
    # Load configuration
    config = load_config()
    
    databases = config.get("databases", [])
    logins = config.get("logins", [])
    rights = config.get("rights", [])
    
    print(f"Configuration loaded:")
    print(f"\nDatabases ({len(databases)}):")
    for db in databases:
        print(f"  - {db}")
    
    print(f"\nLogins ({len(logins)}):")
    for login in logins:
        username = login.get('username', '')
        password = login.get('password', '')
        print(f"  - {username}: {'*' * len(password)}")
    
    print(f"\nRights ({len(rights)}):")
    for right in rights:
        db = right.get('database', '')
        user = right.get('username', '')
        print(f"  - {user} -> {db}")
    
    # Main loop
    print("\nAddon is running...")
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()