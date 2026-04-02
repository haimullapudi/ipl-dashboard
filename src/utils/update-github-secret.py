#!/usr/bin/env python3
"""
Update GitHub secrets from .env file using GitHub CLI.
Reads MY11C_AUTH_TOKEN from .env and updates the GitHub repository secret.

Prerequisites:
- GitHub CLI (gh) installed: brew install gh
"""

import os
import subprocess
from pathlib import Path

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

def update_secret_with_gh_cli(secret_name, secret_value, repo, github_token):
    """Update secret using GitHub CLI."""
    try:
        # Check if gh is installed
        subprocess.run(['gh', '--version'], check=True, capture_output=True)

        # Set the secret using gh CLI with GH_TOKEN
        env = os.environ.copy()
        env['GH_TOKEN'] = github_token

        cmd = ['gh', 'secret', 'set', secret_name, '-b', secret_value, '-R', repo]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)

        if result.returncode == 0:
            print(f"✓ Successfully updated secret: {secret_name}")
            return True
        else:
            error_msg = result.stderr if isinstance(result.stderr, str) else result.stderr.decode()
            print(f"✗ Failed to update secret: {error_msg}")
            return False

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if isinstance(e.stderr, str) else (e.stderr.decode() if e.stderr else str(e))
        print(f"gh CLI error: {error_msg}")
        return False
    except FileNotFoundError:
        print("GitHub CLI (gh) not found. Install with: brew install gh")
        return None  # Return None to indicate fallback needed

def main():
    # Configuration
    GITHUB_REPO = "haimullapudi/ipl-dashboard"
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

    print(f"Updating GitHub secret '{SECRET_NAME}' for {GITHUB_REPO}...")

    # Try using GitHub CLI first
    result = update_secret_with_gh_cli(SECRET_NAME, secret_value, GITHUB_REPO, github_token)

    if result is None:
        # gh CLI not available, would need API fallback
        print("\nFalling back to API requires PyNaCl and a valid GitHub token with repo scope.")
        print("Please install GitHub CLI for easier secret management:")
        print("  brew install gh")
        print("\nThen authenticate with:")
        print("  gh auth login")

if __name__ == '__main__':
    main()
