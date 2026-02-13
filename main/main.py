#!/usr/bin/env python3
"""SSL Sync addon main script."""
import json
import os
import posixpath
import stat
from pathlib import Path

import paramiko
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12


# В Home Assistant аддоні використовується /data/options.json
# Для локального тестування - data/options.json (відносний шлях)
CONFIG_FILE = Path("/data/options.json")
if not CONFIG_FILE.exists():
    CONFIG_FILE = Path(__file__).parent / "data" / "options.json"


def load_config():
    """Load configuration from options.json."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}


def connect_sftp(host, port, username, password):
    """Підключення до SFTP сервера."""
    try:
        # Створення SSH клієнта
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        print(f"Connecting to {host}:{port} as {username}...")
        ssh.connect(hostname=host, port=port, username=username, password=password)
        
        # Відкриття SFTP сесії
        sftp = ssh.open_sftp()
        print("✓ SFTP connection established")
        return ssh, sftp
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return None, None


def resolve_remote_filename(available_files, target_name):
    """Find matching filename on server, with or without .pem."""
    if not target_name:
        return None

    variants = [target_name]
    if target_name.lower().endswith(".pem"):
        variants.append(target_name[:-4])
    else:
        variants.append(f"{target_name}.pem")

    for variant in variants:
        if variant in available_files:
            return variant
    return None


def read_remote_file(sftp, remote_path, filename):
    """Read a remote file into memory as bytes."""
    remote_file = posixpath.join(remote_path.rstrip("/"), filename)
    with sftp.open(remote_file, "rb") as remote_fp:
        return remote_fp.read()


def fetch_ssl_files(sftp, remote_path, privkey_name, cert_name):
    """Fetch privkey and cert files into memory."""
    items = sftp.listdir_attr(remote_path)
    available_files = {item.filename for item in items if not stat.S_ISDIR(item.st_mode)}

    privkey_filename = resolve_remote_filename(available_files, privkey_name)
    cert_filename = resolve_remote_filename(available_files, cert_name)

    if not privkey_filename:
        print(f"✗ Private key not found: {privkey_name}")
        return None
    if not cert_filename:
        print(f"✗ Certificate not found: {cert_name}")
        return None

    privkey_bytes = read_remote_file(sftp, remote_path, privkey_filename)
    cert_bytes = read_remote_file(sftp, remote_path, cert_filename)

    print(f"✓ Loaded {privkey_filename} ({len(privkey_bytes)} bytes)")
    print(f"✓ Loaded {cert_filename} ({len(cert_bytes)} bytes)")

    return {
        "privkey_name": privkey_filename,
        "cert_name": cert_filename,
        "privkey_bytes": privkey_bytes,
        "cert_bytes": cert_bytes,
    }


def build_pfx_bytes(privkey_bytes, cert_bytes, password, friendly_name):
    """Build PFX/PKCS12 bytes in memory."""
    private_key = serialization.load_pem_private_key(privkey_bytes, password=None)
    certificate = x509.load_pem_x509_certificate(cert_bytes)
    name_bytes = friendly_name.encode("utf-8") if friendly_name else None
    if password:
        encryption = serialization.BestAvailableEncryption(password.encode("utf-8"))
    else:
        encryption = serialization.NoEncryption()

    return pkcs12.serialize_key_and_certificates(
        name=name_bytes,
        key=private_key,
        cert=certificate,
        cas=None,
        encryption_algorithm=encryption,
    )


def ensure_remote_dir(sftp, remote_dir):
    """Create remote directory path if missing."""
    if not remote_dir:
        return
    parts = [p for p in remote_dir.split("/") if p]
    current = ""
    for part in parts:
        current = f"{current}/{part}" if current else f"/{part}"
        try:
            sftp.stat(current)
        except IOError:
            sftp.mkdir(current)


def write_local_file(target_dir, filename, data):
    os.makedirs(target_dir, exist_ok=True)
    target_path = Path(target_dir) / filename
    with open(target_path, "wb") as fp:
        fp.write(data)


def write_remote_file(sftp, target_dir, filename, data):
    ensure_remote_dir(sftp, target_dir)
    remote_file = posixpath.join(target_dir.rstrip("/"), filename)
    with sftp.open(remote_file, "wb") as remote_fp:
        remote_fp.write(data)


def is_local_target(copy_cfg):
    host_address = (copy_cfg.get("host_address") or "").strip().lower()
    host_port = copy_cfg.get("host_port")
    return host_address in ("", "example.com") or not host_port


def main():
    # Завантаження конфігурації
    config = load_config()
    
    if not config:
        print("Configuration not found!")
        return
    
    # Отримання всіх параметрів
    ssh_host = config.get('ssh_host')
    ssh_port = config.get('ssh_port')
    ssh_logins = config.get('ssh_logins', {})
    ssh_path = config.get('ssh_path')
    ssl_privkey_name = config.get('ssl_privkey_name', 'privkey.pem')
    ssl_cert_name = config.get('ssl_cert_name', 'cert.pem')
    copy_configs = config.get('copy', [])
    
    print(f"=== SSL Sync Configuration ===")
    print(f"SSH Host: {ssh_host}:{ssh_port}")
    print(f"Remote Path: {ssh_path}")
    print(f"Private Key: {ssl_privkey_name}")
    print(f"Certificate: {ssl_cert_name}")
    
    # Підключення до SFTP
    ssh, sftp = connect_sftp(
        host=ssh_host,
        port=ssh_port,
        username=ssh_logins.get('username'),
        password=ssh_logins.get('password')
    )
    
    if not sftp:
        print("Failed to establish SFTP connection")
        return
    
    try:
        ssl_files = fetch_ssl_files(sftp, ssh_path, ssl_privkey_name, ssl_cert_name)
        if not ssl_files:
            return

        print("\n=== Copy Configurations ===")
        for idx, copy_cfg in enumerate(copy_configs, 1):
            print(f"\n{idx}. {copy_cfg.get('name')}")
            print(f"   SSL Name: {copy_cfg.get('ssl_name')}")
            print(f"   Host: {copy_cfg.get('host_address')}:{copy_cfg.get('host_port')}")
            print(f"   Path: {copy_cfg.get('path')}")
            print(f"   Convert to PFX: {copy_cfg.get('convert_to_PFX')}")

            target_path = copy_cfg.get("path") or "."
            convert_to_pfx = bool(copy_cfg.get("convert_to_PFX"))

            if convert_to_pfx:
                ssl_name = copy_cfg.get("ssl_name") or "certificate"
                if ssl_name.lower().endswith(".pfx"):
                    pfx_filename = ssl_name
                else:
                    pfx_filename = f"{ssl_name}.pfx"

                pfx_password = copy_cfg.get("ssl_password") or ""
                pfx_bytes = build_pfx_bytes(
                    ssl_files["privkey_bytes"],
                    ssl_files["cert_bytes"],
                    pfx_password,
                    ssl_name,
                )

                if is_local_target(copy_cfg):
                    write_local_file(target_path, pfx_filename, pfx_bytes)
                    print(f"   ✓ PFX saved locally: {target_path}/{pfx_filename}")
                else:
                    target_host = copy_cfg.get("host_address")
                    target_port = copy_cfg.get("host_port") or 22
                    target_user = copy_cfg.get("host_username")
                    target_pass = copy_cfg.get("host_password")

                    target_ssh, target_sftp = connect_sftp(
                        host=target_host,
                        port=target_port,
                        username=target_user,
                        password=target_pass,
                    )
                    if not target_sftp:
                        print("   ✗ Failed to connect to target host")
                        continue
                    try:
                        write_remote_file(target_sftp, target_path, pfx_filename, pfx_bytes)
                        print(f"   ✓ PFX uploaded: {target_path}/{pfx_filename}")
                    finally:
                        target_sftp.close()
                        target_ssh.close()
            else:
                privkey_name = ssl_files["privkey_name"]
                cert_name = ssl_files["cert_name"]
                privkey_bytes = ssl_files["privkey_bytes"]
                cert_bytes = ssl_files["cert_bytes"]

                if is_local_target(copy_cfg):
                    write_local_file(target_path, privkey_name, privkey_bytes)
                    write_local_file(target_path, cert_name, cert_bytes)
                    print(f"   ✓ PEM saved locally: {target_path}/{privkey_name}")
                    print(f"   ✓ PEM saved locally: {target_path}/{cert_name}")
                else:
                    target_host = copy_cfg.get("host_address")
                    target_port = copy_cfg.get("host_port") or 22
                    target_user = copy_cfg.get("host_username")
                    target_pass = copy_cfg.get("host_password")

                    target_ssh, target_sftp = connect_sftp(
                        host=target_host,
                        port=target_port,
                        username=target_user,
                        password=target_pass,
                    )
                    if not target_sftp:
                        print("   ✗ Failed to connect to target host")
                        continue
                    try:
                        write_remote_file(target_sftp, target_path, privkey_name, privkey_bytes)
                        write_remote_file(target_sftp, target_path, cert_name, cert_bytes)
                        print(f"   ✓ PEM uploaded: {target_path}/{privkey_name}")
                        print(f"   ✓ PEM uploaded: {target_path}/{cert_name}")
                    finally:
                        target_sftp.close()
                        target_ssh.close()

    finally:
        # Закриття з'єднання
        if sftp:
            sftp.close()
        if ssh:
            ssh.close()
        print("\n✓ Connection closed")


if __name__ == "__main__":
    main()