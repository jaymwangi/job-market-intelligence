#!/usr/bin/env python
import subprocess
import sys
import os

if __name__ == "__main__":
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Run streamlit with the app.py file
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        os.path.join(script_dir, "app.py"),
        "--server.port", "8501",
        "--server.address", "0.0.0.0"
    ])