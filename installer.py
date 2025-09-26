import os
import sys
import subprocess
import requests
import zipfile
import tempfile
import ctypes
import winreg
from pathlib import Path


class PhotoOperatorInstaller:
    def __init__(self):
        self.app_name = "360 Photo Operator"
        self.version = "1.0.0"
        self.install_dir = Path.home() / "AppData" / "Local" / "360PhotoOperator"
        self.desktop_dir = Path.home() / "Desktop"

    def is_admin(self):
        """Check if running as administrator"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def run_as_admin(self):
        """Restart the script with admin privileges"""
        if not self.is_admin():
            script = os.path.abspath(sys.argv[0])
            params = ' '.join([script] + sys.argv[1:])
            try:
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
                sys.exit(0)
            except Exception as e:
                print(f"Failed to elevate privileges: {e}")
                return False
        return True

    def check_wsl_installation(self):
        """Check if WSL is installed"""
        try:
            result = subprocess.run(['wsl', '--status'], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False

    def install_wsl(self):
        """Install WSL 2"""
        print("Installing WSL 2...")
        try:
            # Enable WSL feature
            subprocess.run([
                'dism.exe', '/online', '/enable-feature',
                '/featurename:Microsoft-Windows-Subsystem-Linux',
                '/all', '/norestart'
            ], check=True)

            # Enable Virtual Machine Platform
            subprocess.run([
                'dism.exe', '/online', '/enable-feature',
                '/featurename:VirtualMachinePlatform',
                '/all', '/norestart'
            ], check=True)

            # Set WSL 2 as default
            subprocess.run(['wsl', '--set-default-version', '2'], check=True)

            # Install Ubuntu
            subprocess.run(['wsl', '--install', '-d', 'Ubuntu'], check=True)

            print("WSL 2 installation completed. Please restart your computer.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"WSL installation failed: {e}")
            return False

    def install_usbipd(self):
        """Install USBIPD for USB device sharing"""
        print("Installing USBIPD...")
        try:
            # Download and install USBIPD
            url = "https://github.com/dorssel/usbipd-win/releases/latest/download/usbipd-win.msi"
            temp_file = tempfile.NamedTemporaryFile(suffix='.msi', delete=False)

            response = requests.get(url, stream=True)
            with open(temp_file.name, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Install MSI
            subprocess.run(['msiexec', '/i', temp_file.name, '/quiet', '/norestart'], check=True)

            # Clean up
            os.unlink(temp_file.name)

            print("USBIPD installed successfully")
            return True
        except Exception as e:
            print(f"USBIPD installation failed: {e}")
            return False

    def install_python_dependencies(self):
        """Install required Python packages"""
        print("Installing Python dependencies...")
        requirements = [
            "PyQt6==6.6.1",
            "pyserial==3.5",
            "selenium==4.15.2",
            "webdriver-manager==4.0.1",
            "requests==2.31.0",
            "pillow==10.1.0"
        ]

        for package in requirements:
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', package], check=True)
                print(f"✓ {package}")
            except subprocess.CalledProcessError:
                print(f"✗ Failed to install {package}")

    def setup_wsl_environment(self):
        """Setup WSL environment with gPhoto2"""
        print("Setting up WSL environment...")
        wsl_commands = [
            "sudo apt-get update -y",
            "sudo apt-get install -y gphoto2",
            "sudo apt-get install -y python3 python3-pip",
            "sudo apt-get install -y usbip"
        ]

        for cmd in wsl_commands:
            try:
                subprocess.run(['wsl', 'bash', '-c', cmd], check=True, timeout=300)
                print(f"✓ {cmd}")
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                print(f"✗ Failed: {cmd}")
                print(f"Error: {e}")

    def create_desktop_shortcut(self):
        """Create desktop shortcut"""
        print("Creating desktop shortcut...")
        shortcut_path = self.desktop_dir / "360 Photo Operator.lnk"

        # Simple batch file to start the application
        batch_content = f'''@echo off
cd /d "{self.install_dir}"
python main.py
pause
'''

        batch_file = self.install_dir / "start_app.bat"
        with open(batch_file, 'w') as f:
            f.write(batch_content)

        # Create shortcut using PowerShell
        ps_script = f'''
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{batch_file}"
$Shortcut.WorkingDirectory = "{self.install_dir}"
$Shortcut.Save()
'''

        try:
            subprocess.run(['powershell', '-Command', ps_script], check=True)
            print("Desktop shortcut created")
        except:
            print("Failed to create desktop shortcut")

    def copy_application_files(self):
        """Copy application files to install directory"""
        print("Copying application files...")

        # Create install directory
        self.install_dir.mkdir(parents=True, exist_ok=True)

        # List of required files
        required_files = [
            'main.py',
            'hardware_handler.py',
            'webp_handler.py',
            'uploader.py',
            'auto_process.jsx'
        ]

        # Copy files
        for file in required_files:
            if os.path.exists(file):
                import shutil
                shutil.copy2(file, self.install_dir / file)
                print(f"✓ {file}")
            else:
                print(f"✗ Missing: {file}")

    def create_config_file(self):
        """Create configuration file"""
        config = {
            "version": self.version,
            "install_path": str(self.install_dir),
            "photo_directory": str(self.desktop_dir / "Zdjecia360"),
            "wsl_distro": "Ubuntu"
        }

        config_file = self.install_dir / "config.json"
        import json
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def install(self):
        """Main installation procedure"""
        print(f"=== {self.app_name} Installer ===")
        print(f"Version: {self.version}")
        print("=" * 40)

        # Request admin privileges
        if not self.run_as_admin():
            print("Administrator privileges are required for installation.")
            input("Press Enter to exit...")
            return False

        # Check WSL
        if not self.check_wsl_installation():
            print("WSL 2 is not installed.")
            response = input("Do you want to install WSL 2? (y/n): ")
            if response.lower() == 'y':
                if not self.install_wsl():
                    print("WSL installation failed. Please install manually.")
                    return False
            else:
                print("WSL 2 is required for this application.")
                return False

        # Install USBIPD
        if not self.install_usbipd():
            print("USBIPD installation failed. Please install manually.")
            return False

        # Setup WSL environment
        self.setup_wsl_environment()

        # Install Python dependencies
        self.install_python_dependencies()

        # Copy application files
        self.copy_application_files()

        # Create configuration
        self.create_config_file()

        # Create desktop shortcut
        self.create_desktop_shortcut()

        print("\n" + "=" * 40)
        print("Installation completed successfully!")
        print(f"Application installed to: {self.install_dir}")
        print("A shortcut has been created on your desktop.")
        print("\nBefore first use, please:")
        print("1. Restart your computer")
        print("2. Connect your camera and turntable")
        print("3. Run the application from the desktop shortcut")

        input("\nPress Enter to exit...")
        return True


if __name__ == "__main__":
    installer = PhotoOperatorInstaller()
    installer.install()