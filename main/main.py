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
    
    username = config.get("username", "admin")
    password = config.get("password", "")
    interval = config.get("interval", 60)
    enabled = config.get("enabled", True)
    
    print(f"Configuration loaded:")
    print(f"  Username: {username}")
    print(f"  Password: {'*' * len(password) if password else '(not set)'}")
    print(f"  Interval: {interval} seconds")
    print(f"  Enabled: {enabled}")
    
    # Main loop
    while True:
        if enabled:
            print(f"Addon is working... (interval: {interval}s)")
        else:
            print("Addon is disabled")
        
        time.sleep(interval)


if __name__ == "__main__":
    main()