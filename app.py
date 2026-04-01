#!/usr/bin/env python3
"""
IPL Dashboard - Entry point for Render deployment
"""

import sys
import os

# Add src/server to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'server'))

from server import app

if __name__ == '__main__':
    app.run(debug=True, port=8000)
