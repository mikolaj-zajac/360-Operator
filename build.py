import os
import sys
import subprocess
import shutil
from pathlib import Path


def build_application():
    """Build the application using PyInstaller"""
    print("Building 360 Photo Operator...")

    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])

    # Create build directory
    build_dir = Path('build')
    dist_dir = Path('dist')

    # Clean previous builds
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if dist_dir.exists():
        shutil.rmtree(dist_dir)

    # Run PyInstaller
    result = subprocess.run([
        sys.executable, '-m', 'PyInstaller',
        'build.spec',
        '--clean',
        '--noconfirm'
    ])

    if result.returncode == 0:
        print("Build completed successfully!")
        print(f"Executable location: {dist_dir / '360PhotoOperator'}")

        # Create distribution package
        create_distribution_package()
    else:
        print("Build failed!")
        return False


def create_distribution_package():
    """Create a zip file with the application and required files"""
    print("Creating distribution package...")

    dist_dir = Path('dist')
    package_dir = Path('360PhotoOperator_Package')

    # Create package directory
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir()

    # Copy files
    files_to_copy = [
        'installer.py',
        'README.txt',
        'LICENSE'
    ]

    for file in files_to_copy:
        if Path(file).exists():
            shutil.copy2(file, package_dir / file)

    # Copy the built application
    app_dir = package_dir / 'Application'
    app_dir.mkdir()

    if (dist_dir / '360PhotoOperator').exists():
        for item in (dist_dir / '360PhotoOperator').iterdir():
            if item.is_file():
                shutil.copy2(item, app_dir / item.name)

    # Create zip file
    import zipfile
    with zipfile.ZipFile('360PhotoOperator_v1.0.0.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in package_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(package_dir)
                zipf.write(file_path, arcname)

    # Clean up
    shutil.rmtree(package_dir)

    print("Distribution package created: 360PhotoOperator_v1.0.0.zip")


def create_readme():
    """Create README file"""
    readme_content = """360 Photo Operator
===================

A professional application for automated 360-degree product photography.

System Requirements:
- Windows 10/11 64-bit
- 8GB RAM minimum, 16GB recommended
- USB ports for camera and turntable
- Internet connection for initial setup

Supported Cameras:
- Canon EOS series (tested with EOS RP)
- Other cameras supported by gPhoto2

Installation:
1. Run installer.py as Administrator
2. Follow the on-screen instructions
3. Restart your computer when prompted
4. Run the application from the desktop shortcut

First Time Setup:
1. Connect your DSLR camera via USB
2. Connect your turntable to COM port
3. Set camera to Manual mode and Manual focus
4. Disable auto power-off on camera

Usage:
1. Enter product name in the text field
2. Click "Connect" for both Table360 and Camera
3. Click "Start Capture" to begin the process
4. The application will automatically capture, process, and upload photos

Troubleshooting:
- Ensure WSL 2 is installed and running
- Run application as Administrator for USB access
- Check camera connection in Device Manager
- Verify COM port settings for turntable

Support:
For technical support, please contact your system administrator.
"""

    with open('README.txt', 'w', encoding='utf-8') as f:
        f.write(readme_content)


if __name__ == "__main__":
    create_readme()
    build_application()