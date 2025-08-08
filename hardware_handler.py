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
        self.initialize_hardware()

    def initialize_hardware(self):
        self.initialize_serial()
        self.initialize_camera()

    def initialize_serial(self):
        """Initialize serial connection on COM3"""
        try:
            logger.info("Attempting to connect to COM3...")
            self.serial_conn = serial.Serial(
                port='COM3',
                baudrate=19200,
                timeout=1,
                write_timeout=1
            )
            self.serial_conn.write(self.COMMANDS["Stop"])
            logger.info("✅ Serial connection established on COM3")
        except Exception as e:
            logger.error(f"❌ Serial connection failed: {str(e)}")
            error_msg = (
                "Serial connection failed on COM3!\n\n"
                "Possible solutions:\n"
                "1. Close all programs using COM3 (e.g., PuTTY, Arduino IDE)\n"
                "2. Check device connection and try a different USB port\n"
                "3. Run PyCharm as Administrator\n"
                "4. Verify the device driver in Device Manager\n"
                f"Error details: {str(e)}"
            )
            messagebox.showerror("Serial Connection Error", error_msg)
            self.serial_conn = None

    def initialize_camera(self):
        """Initialize DSLR camera using gPhoto2 in WSL"""
        if self.check_dslr_connection():
            logger.info("✅ DSLR camera initialized")
            return True
        logger.error("❌ DSLR camera not detected. Please ensure:")
        logger.error("1. Camera is connected via USB and in PTP mode")
        logger.error("2. USB is attached to WSL: usbipd attach --wsl --busid=<BUSID>")
        logger.error("3. gPhoto2 is installed in WSL")
        return False

    def check_dslr_connection(self):
        """Check DSLR connection using gPhoto2 in WSL"""
        try:
            result = subprocess.run(
                ['wsl', 'gphoto2', '--auto-detect'],
                capture_output=True, text=True, check=True, timeout=10
            )
            logger.debug(f"gPhoto2 auto-detect output: {result.stdout}")
            return 'usb' in result.stdout.lower()
        except subprocess.TimeoutExpired:
            logger.error("❌ gPhoto2 auto-detect timed out")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ gPhoto2 error: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"❌ DSLR detection failed: {str(e)}")
            return False

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
        """Capture and save a DSLR photo to the selected folder using gPhoto2 in WSL"""
        if not self.check_dslr_connection():
            logger.error("❌ DSLR not available")
            return False

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

        def run_subprocess(cmd, timeout=10):
            """Run subprocess with timeout and queue for non-blocking execution"""
            result_queue = queue.Queue()

            def target():
                try:
                    result = subprocess.run(
                        cmd, capture_output=True, text=True, check=True
                    )
                    result_queue.put(('success', result))
                except Exception as e:
                    result_queue.put(('error', e))

            thread = threading.Thread(target=target)
            thread.start()
            thread.join(timeout)
            if thread.is_alive():
                logger.error(f"Subprocess timed out: {cmd}")
                return False, None
            result_type, result = result_queue.get()
            if result_type == 'error':
                raise result
            return True, result

        try:
            # Capture image directly into WSL-accessible Windows path
            logger.debug(f"Capturing photo in WSL: {wsl_dest_path}")
            success, result = run_subprocess(
                ['wsl', 'gphoto2', '--capture-image-and-download', f'--filename={wsl_dest_path}'], timeout=30
            )

            if not success:
                logger.error("❌ gPhoto2 capture failed")
                return False
            logger.debug(f"gPhoto2 capture output: {result.stdout}")

            logger.info(f"📸 DSLR photo saved to {windows_path}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ gPhoto2 error: stdout={e.stdout}, stderr={e.stderr}")
            return False
        except Exception as e:
            logger.error(f"❌ Capture error: {str(e)}")
            return False

    def capture_sequence(self, num_photos=20, move_time=19):
        """Capture a sequence of photos with machine movement"""
        self.send_command(self.COMMANDS["laser off"], "laser off")

        for i in range(1, num_photos + 1):
            logger.info(f"▶ Obrót {i}/{num_photos}")
            # Send move command
            self.send_command(self.COMMANDS["Lewo trzymanie"], "Lewo trzymanie")

            time.sleep(move_time / num_photos)

            self.send_command(self.COMMANDS["Stop"], "Stop")
            # Capture photo
            filename = f"zdjecie_{i:02d}.jpg"
            self.capture_dslr_photo(filename=filename)

        logger.info(f"✅ Completed capturing {num_photos} photos")
        self.send_command(self.COMMANDS["laser on"], "laser on")
        cmd = "usbipd detach --busid=2-1;"
        subprocess.run(["powershell", "-Command", cmd])
        time.sleep(1)
        cmd = "usbipd attach --wsl --busid=2-1"
        subprocess.run(["powershell", "-Command", cmd])
        return True

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