import os
import sys
import subprocess
import shutil
from pathlib import Path


def clean_build():
    """Clean previous build artifacts"""
    build_dirs = ['build', 'dist', '__pycache__']
    for dir_name in build_dirs:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"Cleaned {dir_name}")

    # Clean pycache in subdirectories
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in root:
            shutil.rmtree(root)
            print(f"Cleaned {root}")


def install_dependencies():
    """Install required packages for building"""
    packages = [
        'pyinstaller==5.13.2',
        'PyQt6==6.6.1',
        'pyserial==3.5',
        'selenium==4.15.2',
        'webdriver-manager==4.0.1',
        'requests==2.31.0',
        'pillow==10.1.0'
    ]

    print("Installing build dependencies...")
    for package in packages:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', package], check=True)
            print(f"✓ {package}")
        except subprocess.CalledProcessError:
            print(f"✗ Failed to install {package}")


def build_executable():
    """Build the executable using PyInstaller"""
    print("Building executable...")

    # Use direct PyInstaller command instead of spec file for simplicity
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        'main.py',
        '--name=360PhotoOperator',
        '--onefile',
        '--console',
        '--add-data=auto_process.jsx;.',
        '--add-data=hardware_handler.py;.',
        '--add-data=webp_handler.py;.',
        '--add-data=uploader.py;.',
        '--hidden-import=PyQt6.QtCore',
        '--hidden-import=PyQt6.QtGui',
        '--hidden-import=PyQt6.QtWidgets',
        '--hidden-import=serial',
        '--hidden-import=selenium',
        '--hidden-import=webdriver_manager',
        '--hidden-import=requests',
        '--hidden-import=queue',
        '--exclude-module=tkinter',
        '--exclude-module=pymsgbox',
        '--clean'
    ]

    try:
        result = subprocess.run(cmd, check=True)
        if result.returncode == 0:
            print("✓ Build completed successfully!")
            return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Build failed: {e}")
        return False


def create_distribution_package():
    """Create a distribution package with all required files"""
    print("Creating distribution package...")

    dist_dir = Path('dist')
    package_dir = Path('360PhotoOperator_Package')

    # Create package directory
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir()

    # Copy the main executable
    exe_source = dist_dir / '360PhotoOperator.exe'
    if exe_source.exists():
        shutil.copy2(exe_source, package_dir / '360PhotoOperator.exe')
        print("✓ Copied executable")
    else:
        print("✗ Executable not found!")
        return False

    # Copy required support files
    support_files = [
        'auto_process.jsx',
        'README.txt',
        'LICENSE'
    ]

    for file in support_files:
        if Path(file).exists():
            shutil.copy2(file, package_dir / file)
            print(f"✓ Copied {file}")

    # Create a simple installer script
    create_installer_script(package_dir)

    # Create zip file
    import zipfile
    zip_filename = '360PhotoOperator_v1.0.0.zip'
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in package_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(package_dir)
                zipf.write(file_path, arcname)

    print(f"✓ Created distribution package: {zip_filename}")

    # Clean up
    shutil.rmtree(package_dir)

    return True


def create_installer_script(package_dir):
    """Create a simple installer script"""
    installer_content = """@echo off
chcp 65001 >nul
title 360 Photo Operator Setup

echo ==================================
echo   360 Photo Operator Installation
echo ==================================
echo.

:: Check if running as admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo This application requires Administrator privileges.
    echo.
    echo Please right-click and "Run as Administrator" or
    echo press any key to exit and restart with admin rights.
    pause >nul
    exit /b 1
)

echo Administrator privileges confirmed.
echo.
echo This package contains a standalone executable.
echo.
echo To use the application:
echo 1. Extract all files to a folder of your choice
echo 2. Run 360PhotoOperator.exe as Administrator
echo 3. Follow the on-screen setup instructions
echo.
echo Required system components:
echo - Windows 10/11 64-bit
echo - WSL 2 (will be installed automatically)
echo - USB ports for camera and turntable
echo.
echo Press any key to open the extraction folder...
pause >nul

start "" "%CD%"

exit /b 0
"""

    installer_file = package_dir / 'Installation_Instructions.bat'
    with open(installer_file, 'w', encoding='utf-8') as f:
        f.write(installer_content)


def create_readme():
    """Create README file"""
    readme_content = """360 Photo Operator
===================

A professional application for automated 360-degree product photography.

QUICK START:
1. Run 360PhotoOperator.exe as Administrator
2. The application will guide you through setup
3. Connect your camera and turntable when prompted

SYSTEM REQUIREMENTS:
- Windows 10/11 64-bit
- 8GB RAM minimum
- USB ports for camera and turntable
- Internet connection for initial setup

SUPPORTED HARDWARE:
- Canon EOS series cameras (tested with EOS RP)
- Compatible turntables with serial control

FIRST TIME SETUP:
The application will automatically:
1. Install WSL 2 (if not present)
2. Setup gPhoto2 for camera control
3. Configure USB device sharing

MANUAL SETUP (if automatic fails):
1. Install WSL 2: Open PowerShell as Admin and run: wsl --install
2. Install USBIPD: Download from GitHub releases
3. Run the application as Administrator

TROUBLESHOOTING:
- Always run as Administrator
- Ensure camera is in Manual mode
- Check USB connections
- Restart application if devices aren't detected

SUPPORT:
Contact your system administrator for technical support.

Version 1.0.0
"""

    with open('README.txt', 'w', encoding='utf-8') as f:
        f.write(readme_content)


def main():
    """Main build process"""
    print("360 Photo Operator - Build System")
    print("=" * 40)

    # Create README
    create_readme()
    print("✓ Created README.txt")

    # Clean previous builds
    clean_build()

    # Install dependencies
    install_dependencies()

    # Build executable
    if build_executable():
        # Create distribution package
        if create_distribution_package():
            print("\n" + "=" * 40)
            print("BUILD COMPLETED SUCCESSFULLY!")
            print("Distribution package: 360PhotoOperator_v1.0.0.zip")
            print("\nThe package contains:")
            print("- 360PhotoOperator.exe (standalone executable)")
            print("- auto_process.jsx (Photoshop automation)")
            print("- Installation instructions")
        else:
            print("\nFailed to create distribution package!")
    else:
        print("\nBuild failed!")


if __name__ == "__main__":
    main()