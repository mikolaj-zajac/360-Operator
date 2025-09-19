import tkinter as tk
from tkinter import filedialog, messagebox
import serial
import subprocess
import os
import time
import logging
import threading
import queue

# Setup logging for debugging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HardwareManager:
    def __init__(self, save_folder=None):
        self.serial_conn = None
        self.save_folder = save_folder or os.getcwd()
        self.COMMANDS = {
            "Stop": bytes.fromhex("010300000000000004"),
            "Lewo ciągle": bytes.fromhex("010100000000006466"),
            "Prawo ciągle": bytes.fromhex("010200000000006467"),
            "Lewo trzymanie": bytes.fromhex("01010000000002373b"),
            "Prawo trzymanie": bytes.fromhex("01020000000002373c"),
            "Obrót +90": bytes.fromhex("010401000000f5dfda"),
            "Obrót -90": bytes.fromhex("01040100ffff0a212f"),
            "laser on": bytes.fromhex("010e01020000000113"),
            "laser off": bytes.fromhex("010e01020000000012"),
            "cos1": bytes.fromhex("010501000000000007"),
            "cos2": bytes.fromhex("010500000000000006"),
            "cos3": bytes.fromhex("020400000005319eda"),
            "cos4": bytes.fromhex("020601000000000009"),
        }
        # self.initialize_hardware()

    def pre_focus_camera(self):
        """Pre-focus camera to reduce capture time"""
        try:
            # Half-press shutter to focus (simulate with gphoto2)
            result = subprocess.run(
                ['wsl', 'gphoto2', '--trigger-capture'],
                capture_output=True, text=True, timeout=10
            )
            time.sleep(0.5)  # Short delay for focus
            return True
        except:
            return False  # Not critical if this fails

    def initialize_hardware(self):
        """Initialize hardware with UI feedback"""
        success = self.initialize_serial()
        if success:
            success = self.initialize_camera()
        return success

    def initialize_serial(self, preferred_port='COM3'):
        """Initialize serial connection, trying multiple COM ports if needed"""
        # List of COM ports to try, starting with the preferred one
        ports_to_try = [preferred_port] + [f'COM{i}' for i in range(1, 11) if f'COM{i}' != preferred_port]

        for port in ports_to_try:
            try:
                logger.info(f"Attempting to connect to {port}...")
                self.serial_conn = serial.Serial(
                    port=port,
                    baudrate=19200,
                    timeout=1,
                    write_timeout=1
                )
                # Test the connection by sending a stop command
                self.serial_conn.write(self.COMMANDS["Stop"])
                logger.info(f"✅ Serial connection established on {port}")
                return True
            except Exception as e:
                logger.error(f"❌ Serial connection failed on {port}: {str(e)}")
                if self.serial_conn:
                    self.serial_conn.close()
                    self.serial_conn = None

        logger.error("❌ Could not establish serial connection on any port")
        error_msg = (
            "Serial connection failed on all tried ports!\n\n"
            "Possible solutions:\n"
            "1. Check if the device is connected and powered on\n"
            "2. Check Device Manager for the correct COM port\n"
            "3. Try reconnecting the USB cable\n"
            "4. Restart the application after ensuring the device is connected"
        )
        messagebox.showerror("Serial Connection Error", error_msg)
        self.serial_conn = None
        return False

    def prepare_canon_camera(self):
        """Prepare Canon camera for automated capture - simplified version"""
        try:
            logger.info("Preparing Canon camera for capture...")

            # Try to set basic configurations that work for most Canon cameras
            config_commands = [
                # Try common config names for image quality
                ['--set-config', 'imagequality=0'],
                ['--set-config', '/main/imgsettings/quality=0'],
                ['--set-config', 'capturetarget=0'],  # Internal memory
                ['--set-config', '/main/capturesettings/capturetarget=0'],
            ]

            for cmd in config_commands:
                try:
                    subprocess.run(['wsl', 'gphoto2'] + cmd, timeout=5, capture_output=True)
                except:
                    pass  # Ignore errors for configs that don't exist

            # Try to disable auto power off with different config names
            power_commands = [
                ['--set-config', 'autopoweroff=0'],
                ['--set-config', '/main/settings/autopoweroff=0'],
                ['--set-config', 'output=0']  # Some Canons use this
            ]

            for cmd in power_commands:
                try:
                    subprocess.run(['wsl', 'gphoto2'] + cmd, timeout=5, capture_output=True)
                except:
                    pass

            logger.info("Canon camera preparation completed")
            return True

        except Exception as e:
            logger.error(f"Camera preparation failed: {e}")
            return False  # Don't fail completely if preparation fails

    def initialize_camera(self):
        """Initialize DSLR camera using gPhoto2 in WSL"""
        # This will be handled by the main application's WSL setup
        return self.check_dslr_connection()

    def check_dslr_connection(self):
        """Check DSLR connection using gPhoto2 in WSL"""
        try:
            result = subprocess.run(
                ['wsl', 'gphoto2', '--auto-detect'],
                capture_output=True, text=True, timeout=10
            )
            print(f"gPhoto2 auto-detect output: {result.stdout}")
            return 'usb' in result.stdout.lower()
        except Exception as e:
            print(f"❌ DSLR detection failed: {str(e)}")
            return False

    def capture_sequence(self, num_photos=20, move_time=19):
        """Capture a sequence of photos with machine movement and progress updates"""
        self.pre_focus_camera()
        if not self.serial_conn:
            print("❌ Serial connection not established")
            return False

        self.send_command(self.COMMANDS["laser off"], "laser off")

        for i in range(1, num_photos + 1):
            print(f"▶ Obrót {i}/{num_photos}")

            # Send progress update if callback provided
            if self.progress_callback:
                self.progress_callback(i, num_photos, "capturing")

            # Send move command
            self.send_command(self.COMMANDS["Lewo trzymanie"], "Lewo trzymanie")
            time.sleep(move_time / num_photos)
            self.send_command(self.COMMANDS["Stop"], "Stop")

            # Capture photo
            filename = f"zdjecie_{i:02d}.jpg"
            success = self.capture_dslr_photo(filename=filename)
            if not success:
                print(f"❌ Failed to capture photo {i}")
                return False

        print(f"✅ Completed capturing {num_photos} photos")
        self.send_command(self.COMMANDS["laser on"], "laser on")

        # Reset USB connection
        try:
            subprocess.run(["powershell", "-Command", "usbipd detach --busid=2-1;"], timeout=5)
            time.sleep(1)
            subprocess.run(["powershell", "-Command", "usbipd attach --wsl --busid=2-1"], timeout=5)
        except Exception as e:
            print(f"USB reset failed: {e}")

        return True

    def select_folder(self):
        """Open a folder selection dialog and set save_folder"""
        folder = filedialog.askdirectory(title="Select Folder to Save Photos")
        if folder:
            self.save_folder = folder
            logger.info(f"📁 Save folder set to: {self.save_folder}")
            # Ensure folder exists in Windows
            os.makedirs(self.save_folder, exist_ok=True)
            # Ensure folder is accessible in WSL
            wsl_path = self.to_wsl_path(self.save_folder)
            try:
                subprocess.run(['wsl', 'mkdir', '-p', wsl_path], check=True, capture_output=True, text=True, timeout=5)
            except subprocess.TimeoutExpired:
                logger.error("❌ WSL folder creation timed out")
                messagebox.showerror("Error", "Failed to create folder in WSL: Timed out")
                return False
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Failed to create WSL folder: {e.stderr}")
                messagebox.showerror("Error", f"Failed to create folder in WSL: {e.stderr}")
                return False
            return True
        else:
            logger.warning("❌ No folder selected")
            return False

    def to_wsl_path(self, windows_path):
        """Convert Windows path to WSL path"""
        windows_path = os.path.normpath(windows_path)
        if windows_path.startswith('C:\\') or windows_path.startswith('C:/'):
            windows_path = windows_path[2:]
        return f"/mnt/c/{windows_path.replace('\\', '/')}"

    def send_command(self, command, description=""):
        """Send serial command to the machine"""
        if not self.serial_conn:
            logger.error("❌ No serial connection")
            return False
        try:
            logger.info(f"▶ {description}: {command.hex()}")
            self.serial_conn.write(command)
            return True
        except Exception as e:
            logger.error(f"❌ Command failed: {str(e)}")
            return False

    def capture_dslr_photo(self, filename="photo.jpg"):
        """Capture and save a DSLR photo with proper gPhoto2 syntax"""
        # Ensure filename is unique
        base_filename = os.path.splitext(filename)[0]
        ext = os.path.splitext(filename)[1]
        counter = 1
        unique_filename = filename
        while os.path.exists(os.path.join(self.save_folder, unique_filename)):
            unique_filename = f"{base_filename}_{counter:03d}{ext}"
            counter += 1

        windows_path = os.path.join(self.save_folder, unique_filename)
        wsl_dest_path = self.to_wsl_path(windows_path)

        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"📸 Capture attempt {attempt + 1}/{max_retries} for {filename}")

                # Reset USB connection if this is a retry
                if attempt > 0:
                    self.reset_usb_connection()
                    time.sleep(3)

                # FIXED: Use proper gPhoto2 command syntax
                # Method 1: Standard capture and download
                result = subprocess.run(
                    ['wsl', 'gphoto2', '--capture-image-and-download', f'--filename={wsl_dest_path}'],
                    capture_output=True, text=True, timeout=25
                )

                if result.returncode == 0:
                    logger.info(f"✅ Photo saved to {windows_path}")
                    return True
                else:
                    logger.warning(f"Attempt {attempt + 1} failed: {result.stderr}")

                    # Method 2: Alternative approach for Canon
                    if "Device Busy" in result.stderr or "PTP" in result.stderr:
                        logger.info("Trying alternative Canon capture method...")
                        success = self.canon_alternative_capture(wsl_dest_path)
                        if success:
                            return True
                        else:
                            # Wait longer before retry for Canon
                            time.sleep(4)

            except subprocess.TimeoutExpired:
                logger.warning(f"Attempt {attempt + 1} timed out")
                if attempt < max_retries - 1:
                    time.sleep(3)
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} error: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(3)

        logger.error(f"❌ All capture attempts failed for {filename}")
        return False

    def canon_alternative_capture(self, wsl_path):
        """Alternative capture method specifically for Canon cameras"""
        try:
            # Method 1: Separate capture and download
            result1 = subprocess.run(
                ['wsl', 'gphoto2', '--capture-image'],
                capture_output=True, text=True, timeout=15
            )

            if result1.returncode == 0:
                time.sleep(2)  # Wait for camera to process
                # Download the last image
                result2 = subprocess.run(
                    ['wsl', 'gphoto2', '--get-file=0', '--filename', wsl_path],
                    capture_output=True, text=True, timeout=15
                )
                return result2.returncode == 0

            # Method 2: Use trigger capture for some Canon models
            result3 = subprocess.run(
                ['wsl', 'gphoto2', '--trigger-capture'],
                capture_output=True, text=True, timeout=15
            )

            if result3.returncode == 0:
                time.sleep(2)
                result4 = subprocess.run(
                    ['wsl', 'gphoto2', '--get-file=0', '--filename', wsl_path],
                    capture_output=True, text=True, timeout=15
                )
                return result4.returncode == 0

            return False

        except Exception as e:
            logger.error(f"Canon alternative capture failed: {e}")
            return False

    def reset_usb_connection(self, busid="2-1"):
        """Reset USB connection to clear device busy state"""
        try:
            # Detach from WSL
            subprocess.run(["powershell", "-Command", f"usbipd detach --busid={busid}"],
                           timeout=5, capture_output=True)
            time.sleep(2)

            # Reattach to WSL
            subprocess.run(["powershell", "-Command", f"usbipd attach --wsl --busid={busid}"],
                           timeout=10, capture_output=True)
            time.sleep(3)  # Longer wait for Canon cameras to reinitialize
            return True
        except Exception as e:
            logger.error(f"USB reset failed: {e}")
            return False

    def cleanup(self):
        """Clean up resources"""
        if self.serial_conn:
            self.send_command(self.COMMANDS["Stop"], "Stop")
            self.serial_conn.close()
            logger.info("Serial connection closed")
        tk.destroyAllWindows()

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Sterowanie TopShow3D")
        self.root.geometry("300x500")
        self.hardware = HardwareManager()

        # GUI Buttons
        tk.Button(root, text="Select Save Folder", width=20, height=2,
                 command=self.hardware.select_folder).pack(pady=5)
        self.make_click_button("Obrót +90", "Obrót +90")
        self.make_click_button("Obrót -90", "Obrót -90")
        self.make_click_button("Lewo ciągle", "Lewo ciągle")
        self.make_click_button("Prawo ciągle", "Prawo ciągle")
        self.make_hold_button("Lewo (trzymanie)", "Lewo trzymanie")
        self.make_hold_button("Prawo (trzymanie)", "Prawo trzymanie")
        self.make_click_button("STOP", "Stop")
        self.make_click_button("Laser ON", "laser on")
        self.make_click_button("Laser OFF", "laser off")
        tk.Button(root, text="Automatyczne zdjęcia", width=20, height=2,
                 command=self.capture_sequence).pack(pady=5)
        tk.Button(root, text="Test kamery", width=20, height=2,
                 command=self.test_camera).pack(pady=5)

    def make_click_button(self, text, command_name):
        """Create a button that sends a single command"""
        tk.Button(self.root, text=text, width=20, height=2,
                 command=lambda: self.hardware.send_command(self.hardware.COMMANDS[command_name], text)).pack(pady=5)

    def make_hold_button(self, text, command_name):
        """Create a button that sends a command on press and stop on release"""
        btn = tk.Button(self.root, text=text, width=20, height=2)
        btn.bind("<ButtonPress>",
                 lambda e: self.hardware.send_command(self.hardware.COMMANDS[command_name], f"{text} - START"))
        btn.bind("<ButtonRelease>",
                 lambda e: self.hardware.send_command(self.hardware.COMMANDS["Stop"], f"{text} - STOP"))
        btn.pack(pady=5)

    def test_camera(self):
        """Test camera by capturing a single photo"""
        if self.hardware.capture_dslr_photo(filename="test.jpg"):
            # messagebox.showinfo("Success", "Test photo captured successfully")
            cmd = "usbipd detach --busid=3-1;"
            subprocess.run(["powershell", "-Command", cmd])
            time.sleep(1)
            cmd = "usbipd attach --wsl --busid=3-1"
            subprocess.run(["powershell", "-Command", cmd])
        else:
            messagebox.showerror("Error", "Failed to capture test photo")

    def capture_sequence(self):
        """Start 360-degree capture sequence"""
        self.hardware.capture_sequence(num_photos=20)

    def on_closing(self):
        """Handle window closing"""
        self.hardware.cleanup()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()