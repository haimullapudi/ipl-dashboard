#!/usr/bin/env python3
"""
Update GitHub secrets from .env file.
Reads MY11C_AUTH_TOKEN from .env and updates the GitHub repository secret.
"""

import os
import base64
import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen
import json

# Load .env file
def load_env():
    # Go up two levels from src/utils to reach project root
    env_path = Path(__file__).parent.parent.parent / '.env'
    env_vars = {}
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    except Exception as e:
        print(f"Error loading .env: {e}")
    return env_vars

def main():
    # Configuration
    GITHUB_OWNER = "haimullapudi"
    GITHUB_REPO = "ipl-dashboard"
    SECRET_NAME = "MY11C_AUTH_TOKEN"

    # Load environment variables
    env = load_env()

    # Get GitHub token
    github_token = env.get('GITHUB_TOKEN')
    if not github_token:
        print("Error: GITHUB_TOKEN not found in .env file")
        return

    # Get secret value
    secret_value = env.get('MY11C_AUTH_TOKEN')
    if not secret_value:
        print("Error: MY11C_AUTH_TOKEN not found in .env file")
        return

    print(f"Updating GitHub secret '{SECRET_NAME}' for {GITHUB_OWNER}/{GITHUB_REPO}...")

    try:
        # Get public key from GitHub
        url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/secrets/public-key"
        req = Request(url, headers={
            'Authorization': f'Bearer {github_token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        })
        with urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            key_id = data['key_id']
            public_key = data['key']
        print(f"Got public key (ID: {key_id})")

        # Install PyNaCl if not available
        try:
            import nacl.bindings
            from nacl.public import PublicKey
        except ImportError:
            print("Installing PyNaCl...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pynacl', '-q'])
            import nacl.bindings
            from nacl.public import PublicKey

        # Encrypt the secret
        nacl.bindings.sodium_init()
        pk = PublicKey(base64.b64decode(public_key), nacl.bindings.crypto_box_PUBLICKEYBYTES)
        encrypted = nacl.bindings.crypto_box_seal(secret_value.encode('utf-8'), pk)
        encrypted_b64 = base64.b64encode(encrypted).decode('utf-8')

        # Update the secret
        url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/secrets/{SECRET_NAME}"
        data = {
            'encrypted_value': encrypted_b64,
            'key_id': key_id
        }

        req = Request(url,
                      data=json.dumps(data).encode('utf-8'),
                      headers={
                          'Authorization': f'Bearer {github_token}',
                          'Accept': 'application/vnd.github+json',
                          'Content-Type': 'application/json',
                          'X-GitHub-Api-Version': '2022-11-28'
                      },
                      method='PUT')

        with urlopen(req) as response:
            if response.status == 204:
                print(f"✓ Successfully updated secret: {SECRET_NAME}")
            else:
                print(f"✗ Failed to update secret. Status: {response.status}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
