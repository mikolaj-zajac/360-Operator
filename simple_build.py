import os
import subprocess
import sys


def simple_build():
    """Simple one-command build"""
    print("Building 360 Photo Operator...")

    # Install PyInstaller if not present
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])

    # Simple build command
    cmd = [
        'pyinstaller',
        '--onefile',
        '--console',
        '--name=360PhotoOperator',
        '--clean',
        'main.py'
    ]

    try:
        subprocess.run(cmd, check=True)
        print("Build completed! Check the 'dist' folder.")
    except Exception as e:
        print(f"Build error: {e}")


if __name__ == "__main__":
    simple_build()