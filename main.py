import ctypes
import json
import subprocess
import sys
import os
import csv
import time
import threading
import re
from os import mkdir

from pymsgbox import alert

from hardware_handler import HardwareManager, logger
from webp_handler import process_all
from uploader import upload_files

from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QFileDialog, QTextEdit, QVBoxLayout, QWidget,
                             QHBoxLayout, QLabel, QGridLayout, QTreeView, QMessageBox, QLineEdit, QSizePolicy, QFrame)
from PyQt6.QtGui import QColor, QFileSystemModel
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal


class FileDialogExample(QMainWindow):
    def __init__(self):
        super().__init__()
        self.selected_path = ""
        self.capture_in_progress = False
        self.camera_busid = None
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        self.target_folder = os.path.join(desktop, "Zdjecia360")
        # Create folder if it doesn't exist
        if not os.path.exists(self.target_folder):
            os.makedirs(self.target_folder)

        # Initialize hardware manager
        self.hardware_manager = None
        self.capture_in_progress = False
        self.camera_busid = None  # Store detected camera bus ID

        self.last_errors = {'Table360': '', 'Camera': '', 'System': ''}

        self.initUI()
        self.init_wsl_environment()

    def show_error_message(self, device, message):
        """Show error message in UI and log"""
        print(f"❌ {device} Error: {message}")
        self.last_errors[device] = message

        # Update UI based on device type
        if device == "Table360":
            self.update_status_label(self.table_label, "Error")
            self.device_states['Table360'] = 'Error'
        elif device == "Camera":
            self.update_status_label(self.camera_label, "Error")
            self.device_states['Camera'] = 'Error'

        # Show alert for critical errors
        if "failed" in message.lower() or "error" in message.lower():
            QMessageBox.critical(self, f"{device} Error", message)

    def update_status_label(self, label: QLabel, state: str):
        """Update status label with detailed error info if available"""
        title = label.property('device_title') or label.text().split(':')[0]

        if state == 'Error':
            # Get the last error for this device
            device_name = "Table360" if "Table360" in title else "Camera"
            error_msg = self.last_errors.get(device_name, 'Unknown error')
            label.setText(f"{title}: Error - {error_msg[:30]}...")
            label.setStyleSheet('color: #c62828; font-weight: 700;')
        else:
            label.setText(f"{title}: {state}")
            if state == 'Connected':
                label.setStyleSheet('color: #2e7d32; font-weight: 700;')
            else:
                label.setStyleSheet('color: #606060; font-weight: 700;')

    def init_wsl_environment(self):
        """Initialize WSL 2 environment and ensure a distribution is running"""

        def setup_wsl():
            try:
                # Check if any WSL 2 distribution is running
                result = subprocess.run(
                    ['wsl', '--list', '--verbose'],
                    capture_output=True, text=True, timeout=10
                )

                if result.returncode == 0:
                    # Check if any distribution is running
                    lines = result.stdout.split('\n')
                    distribution_running = False
                    default_distro = None

                    for line in lines:
                        if 'Running' in line:
                            distribution_running = True
                            print("WSL 2 distribution is already running")
                            break
                        if 'Default' in line and not default_distro:
                            # Extract default distribution name
                            parts = line.split()
                            if len(parts) > 0:
                                default_distro = parts[0]

                    if not distribution_running:
                        # Start the default distribution
                        if default_distro:
                            print(f"Starting WSL 2 distribution: {default_distro}")
                            subprocess.run(
                                ['wsl', '-d', default_distro, 'echo', 'WSL started'],
                                timeout=10
                            )
                        else:
                            # Try to start Ubuntu (most common)
                            print("Starting Ubuntu distribution")
                            subprocess.run(
                                ['wsl', '-d', 'Ubuntu', 'echo', 'WSL started'],
                                timeout=10
                            )

                        time.sleep(3)

                # Check if gPhoto2 is installed
                install_check = subprocess.run(
                    ['wsl', 'which', 'gphoto2'],
                    capture_output=True, text=True, timeout=10
                )

                if install_check.returncode != 0:
                    print("gPhoto2 not found in WSL, attempting to install...")
                    subprocess.run(
                        ['wsl', 'sudo', 'apt-get', 'update', '-y'],
                        capture_output=True, timeout=120
                    )
                    subprocess.run(
                        ['wsl', 'sudo', 'apt-get', 'install', '-y', 'gphoto2'],
                        capture_output=True, timeout=180
                    )
                    print("gPhoto2 installation completed")

            except Exception as e:
                print(f"Failed to initialize WSL: {e}")
                # Try alternative approach
                self.setup_wsl_alternative()

        thread = threading.Thread(target=setup_wsl, daemon=True)
        thread.start()

    def setup_wsl_alternative(self):
        """Alternative method to setup WSL if the first one fails"""
        try:
            # Start WSL with a simple command to ensure it's running
            subprocess.run(['wsl', 'echo', 'WSL initializing...'], timeout=10)

            # Install gPhoto2 if needed
            subprocess.run(
                ['wsl', 'sudo', 'apt-get', 'update', '-y'],
                capture_output=True, timeout=120
            )
            subprocess.run(
                ['wsl', 'sudo', 'apt-get', 'install', '-y', 'gphoto2'],
                capture_output=True, timeout=180
            )

            print("WSL setup completed via alternative method")
        except Exception as e:
            print(f"Alternative WSL setup also failed: {e}")
            self.show_wsl_help_message()

    def show_wsl_help_message(self):
        """Show help message for WSL setup"""
        message = """
    WSL 2 Setup Required

    To use this application, you need to have a WSL 2 distribution running.

    Please follow these steps:

    1. Open Windows Terminal or Command Prompt as Administrator
    2. Run: wsl --install
       (This will install Ubuntu by default)
    3. Wait for the installation to complete and set up a username/password
    4. Restart this application

    If you already have WSL installed but it's not running, try:
    1. Open Windows Terminal
    2. Type 'wsl' and press Enter to start the default distribution
    3. Then run this application again

    Alternatively, you can manually start WSL with:
    wsl -d Ubuntu
    """
        QMessageBox.warning(self, "WSL Setup Required", message)

    def bind_usb_device(self, busid):
        """Bind USB device for sharing with WSL (requires admin privileges)"""
        try:
            # Try to bind the USB device
            result = subprocess.run(
                ["powershell", "-Command", f"usbipd bind --busid={busid}"],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                print(f"USB device {busid} bound successfully")
                return True
            else:
                print(f"Failed to bind USB device: {result.stderr}")

                # If binding fails due to admin rights, try with runas
                if "access denied" in result.stderr.lower() or "administrator" in result.stderr.lower():
                    print("Attempting to bind with administrator privileges...")
                    return self.bind_usb_device_as_admin(busid)
                return False

        except Exception as e:
            print(f"USB binding error: {e}")
            return False

    def bind_usb_device_as_admin(self, busid):
        """Attempt to bind USB device with administrator privileges"""
        try:
            # Create a PowerShell script to run as admin
            ps_script = f"""
            $psi = New-Object System.Diagnostics.ProcessStartInfo
            $psi.FileName = "usbipd"
            $psi.Arguments = "bind --busid={busid}"
            $psi.Verb = "runas"
            $psi.WindowStyle = "Hidden"
            $process = [System.Diagnostics.Process]::Start($psi)
            $process.WaitForExit()
            exit $process.ExitCode
            """

            # Save the script to a temporary file
            script_path = os.path.join(os.getenv('TEMP'), 'bind_usb.ps1')
            with open(script_path, 'w') as f:
                f.write(ps_script)

            # Execute the script
            result = subprocess.run(
                ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path],
                capture_output=True, text=True, timeout=15
            )

            # Clean up the script
            try:
                os.remove(script_path)
            except:
                pass

            if result.returncode == 0:
                print(f"USB device {busid} bound with admin privileges")
                return True
            else:
                print(f"Admin binding failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"Admin binding error: {e}")
            return False

    def detect_camera_busid(self):
        """Detect the camera's USB bus ID using usbipd"""
        try:
            # List all USB devices
            result = subprocess.run(
                ["powershell", "-Command", "usbipd list"],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode != 0:
                print("Failed to list USB devices")
                return None

            # Parse the output to find camera devices
            lines = result.stdout.split('\n')
            camera_busid = None

            # Look for common camera vendors or PTP devices
            camera_keywords = ['canon', 'nikon', 'sony', 'fuji', 'olympus', 'panasonic',
                               'ptp', 'picture transfer', 'camera', 'dslr']

            for line in lines:
                if re.match(r'^\d+-\d+\s+', line):  # Line with bus ID
                    parts = line.split()
                    if len(parts) >= 3:
                        busid = parts[0]
                        description = ' '.join(parts[2:]).lower()

                        # Check if this looks like a camera
                        if any(keyword in description for keyword in camera_keywords):
                            print(f"Found potential camera: {description} at {busid}")
                            camera_busid = busid
                            break

            return camera_busid

        except Exception as e:
            print(f"USB detection error: {e}")
            return None

    def attach_usb_to_wsl(self, busid=None):
        """Attach USB device to WSL with automatic binding"""
        if busid is None:
            # Try to detect camera bus ID
            busid = self.detect_camera_busid()
            if busid is None:
                print("Could not detect camera bus ID")
                return False

        # First, check if device is already bound
        state = self.get_usb_device_state(busid)
        if state == "not shared":
            print(f"Device {busid} is not shared. Attempting to bind...")
            if not self.bind_usb_device(busid):
                # If automatic binding fails, show user instructions
                self.show_bind_instructions(busid)
                return False
            # Wait a moment after binding
            time.sleep(2)

        try:
            # Detach first if already attached
            subprocess.run(
                ["powershell", "-Command", f"usbipd detach --busid={busid}"],
                capture_output=True, timeout=5
            )
            time.sleep(1)

            # Attach to WSL
            result = subprocess.run(
                ["powershell", "-Command", f"usbipd attach --wsl --busid={busid}"],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                print(f"USB device {busid} attached to WSL")
                self.camera_busid = busid
                return True
            else:
                print(f"Failed to attach USB: {result.stderr}")
                return False

        except Exception as e:
            print(f"USB attachment error: {e}")
            return False

    def get_usb_device_state(self, busid):
        """Check if USB device is shared"""
        try:
            result = subprocess.run(
                ["powershell", "-Command", "usbipd list"],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                # Parse the output to find the device state
                for line in result.stdout.split('\n'):
                    if busid in line:
                        if "not shared" in line.lower():
                            return "not shared"
                        elif "shared" in line.lower():
                            return "shared"
                return "not found"
            return "error"
        except Exception as e:
            print(f"Error checking USB state: {e}")
            return "error"

    def show_bind_instructions(self, busid):
        """Show instructions for manual USB binding"""
        message = f"""
    USB Device Needs to be Shared Manually

    The camera at bus ID {busid} is not shared with WSL.

    To fix this, please run the following command as Administrator:

    1. Press Win + X and select "Windows Terminal (Admin)" or "Command Prompt (Admin)"
    2. Run this command: usbipd bind --busid={busid}
    3. Then try connecting the camera again in this application.

    Alternatively, you can run this application as Administrator.
    """
        QMessageBox.warning(self, "USB Sharing Required", message)

    def check_camera_connection(self):
        """Check if camera is connected via gPhoto2"""
        try:
            result = subprocess.run(
                ['wsl', 'gphoto2', '--auto-detect'],
                capture_output=True, text=True, timeout=15
            )

            if result.returncode == 0 and 'usb' in result.stdout.lower():
                print("Camera detected via gPhoto2")
                return True
            else:
                print("Camera not detected via gPhoto2")
                print(f"gPhoto2 output: {result.stdout}")
                if result.stderr:
                    print(f"gPhoto2 error: {result.stderr}")
                return False

        except Exception as e:
            print(f"Camera check failed: {e}")
            return False

    def initUI(self):
        from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                     QPushButton, QLineEdit, QFrame, QProgressBar)
        from PyQt6.QtCore import Qt, QTimer
        from PyQt6.QtGui import QFont

        self.setWindowTitle("360 Operator")
        self.resize(400, 300)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # --- Main layout ---
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(12)

        # --- Name input + Start button (horizontal) ---
        name_row = QHBoxLayout()
        name_row.setSpacing(10)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter name...")
        self.name_input.textChanged.connect(self.toggle_start_button)
        self.name_input.setMinimumWidth(220)
        self.name_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.start_button = QPushButton("Start Capture")
        self.start_button.setEnabled(False)
        self.start_button.clicked.connect(self.start_capture_process)
        # Make font bigger for start button
        font = self.start_button.font()
        font.setPointSize(font.pointSize() + 2)
        font.setBold(True)
        self.start_button.setFont(font)

        name_row.addWidget(self.name_input)
        name_row.addWidget(self.start_button)
        main_layout.addLayout(name_row)

        # --- Helper to create framed connection rows ---
        def make_connection_row(title: str):
            frame = QFrame()
            frame.setFrameShape(QFrame.Shape.StyledPanel)
            frame_layout = QHBoxLayout()
            frame_layout.setContentsMargins(10, 8, 10, 8)
            frame_layout.setSpacing(8)
            frame.setLayout(frame_layout)

            label = QLabel(f"{title}: Not connected")
            label.setProperty('device_title', title)
            label.setMinimumWidth(220)
            label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

            btn = QPushButton("Connect")
            btn.setProperty('device', title)

            frame_layout.addWidget(label)
            frame_layout.addStretch()
            frame_layout.addWidget(btn)

            return frame, label, btn

        # create rows
        table_frame, self.table_label, self.table_button = make_connection_row("Table360")
        camera_frame, self.camera_label, self.camera_button = make_connection_row("Camera")

        main_layout.addWidget(table_frame)
        main_layout.addWidget(camera_frame)
        main_layout.addStretch()

        # Progress bar section
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(8)

        # Progress bar label
        self.progress_label = QLabel("Ready")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self.progress_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.progress_bar)

        # Add progress section to main layout
        main_layout.addLayout(progress_layout)

        # track states for demo/testing
        self.device_states = {'Table360': 'Not connected', 'Camera': 'Not connected'}

        # Track progress state
        self.current_stage = "ready"

        # connect signals
        self.table_button.clicked.connect(lambda: self.cycle_connect('Table360'))
        self.camera_button.clicked.connect(lambda: self.cycle_connect('Camera'))

        # --- Pastel stylesheet with enhanced button styles ---
        self.setStyleSheet("""
        QWidget { 
            background-color: #f6f8fb; 
            font-family: Arial, Helvetica, sans-serif; 
            font-size: 13px; 
            color: #333; 
        }
        QFrame { 
            background-color: #ffffff; 
            border-radius: 10px; 
            border: 1px solid rgba(163,201,199,0.12); 
        }
        QLineEdit { 
            border: 2px solid #e6eef0; 
            border-radius: 8px; 
            padding: 7px; 
            background-color: #ffffff; 
            height: 32px;
        }
        QPushButton { 
            background-color: #a3c9c7; 
            border: none; 
            border-radius: 8px; 
            padding: 6px 12px; 
            color: #ffffff; 
            font-weight: 600;
            min-width: 80px;
            height: 32px;
        }
        QPushButton:disabled { 
            background-color: #e6e6e6; 
            color: #9a9a9a; 
        }
        QPushButton:hover:enabled { 
            background-color: #8fb8b6; 
        }
        QPushButton#start_button { 
            background-color: #ff9f43; 
            font-size: 14px;
            font-weight: bold;
        }
        QPushButton#start_button:hover:enabled { 
            background-color: #ed8624; 
        }
        QLabel { 
            padding: 2px; 
        }
        QProgressBar {
            border: 2px solid #e6eef0;
            border-radius: 5px;
            text-align: center;
            height: 20px;
        }
        QProgressBar::chunk {
            background-color: #a3c9c7;
            border-radius: 3px;
        }
        """)

        # Apply special style to start button
        self.start_button.setObjectName("start_button")

    def toggle_start_button(self):
        text = self.name_input.text().strip()
        # Only enable if name is entered and both devices are connected
        devices_connected = (self.device_states.get('Table360') == 'Connected' and
                             self.device_states.get('Camera') == 'Connected')
        self.start_button.setEnabled(bool(text) and devices_connected and not self.capture_in_progress)

    def cycle_connect(self, device: str):
        if device == 'Table360':
            if self.device_states[device] == 'Not connected':
                # Initialize hardware manager if not already done
                if self.hardware_manager is None:
                    self.hardware_manager = HardwareManager()

                # Try to connect to serial
                connected = self.hardware_manager.initialize_serial()
                new_state = 'Connected' if connected else 'Error'
                self.device_states[device] = new_state
                self.update_status_label(self.table_label, new_state)
            else:
                # Disconnect
                if self.hardware_manager and self.hardware_manager.serial_conn:
                    self.hardware_manager.serial_conn.close()
                    self.hardware_manager.serial_conn = None
                self.device_states[device] = 'Not connected'
                self.update_status_label(self.table_label, 'Not connected')

        # In your cycle_connect method for Camera:
        elif device == 'Camera':
            if self.device_states[device] == 'Not connected':
                # Try to attach USB and check camera
                attached = self.attach_usb_to_wsl()  # This now includes binding
                if attached:
                    # Give it time to initialize
                    time.sleep(4)
                    connected = self.check_camera_connection()

                    if connected:
                        # Try to prepare camera
                        preparation_success = self.hardware_manager.prepare_canon_camera()
                        new_state = 'Connected'
                        if not preparation_success:
                            print("Camera connected but some settings couldn't be configured")
                    else:
                        new_state = 'Error'

                    self.device_states[device] = new_state
                    self.update_status_label(self.camera_label, new_state)
                else:
                    new_state = 'Error'
                    self.device_states[device] = new_state
                    self.update_status_label(self.camera_label, new_state)
            else:
                # Disconnect camera
                if self.camera_busid:
                    try:
                        subprocess.run(["powershell", "-Command", f"usbipd detach --busid={self.camera_busid}"],
                                       timeout=5)
                    except:
                        pass
                self.device_states[device] = 'Not connected'
                self.update_status_label(self.camera_label, 'Not connected')
                self.camera_busid = None

    def update_status_label(self, label: QLabel, state: str):
        title = label.property('device_title') or label.text().split(':')[0]
        label.setText(f"{title}: {state}")
        if state == 'Connected':
            label.setStyleSheet('color: #2e7d32; font-weight: 700;')
        elif state == 'Error':
            label.setStyleSheet('color: #c62828; font-weight: 700;')
        else:
            label.setStyleSheet('color: #606060; font-weight: 700;')

    def start_capture_process(self):
        """Start the photo capture and processing workflow"""
        folder_name = self.name_input.text().strip()
        if not folder_name:
            return

        # Clear previous errors
        self.last_errors = {'Table360': '', 'Camera': '', 'System': ''}

        # Create the directory path
        self.selected_path = os.path.join(self.target_folder, folder_name)
        os.makedirs(self.selected_path, exist_ok=True)

        # Reset progress
        self.current_stage = "capturing"
        self.update_progress(0, "Taking photos 0/20")

        # Disable start button during capture
        self.capture_in_progress = True
        self.toggle_start_button()

        # Start the capture process in a separate thread
        self.capture_thread = self.CaptureThread(
            self.selected_path,
            self.hardware_manager,
            self.update_progress_callback,
            self.camera_busid
        )
        self.capture_thread.finished.connect(self.on_capture_finished)
        self.capture_thread.error_occurred.connect(self.show_error_message)  # Connect error signal
        self.capture_thread.start()

    def update_progress_callback(self, current, total, stage):
        """Update progress from capture thread"""
        progress_percent = int((current / total) * 100)
        self.update_progress(progress_percent, f"{stage.capitalize()} {current}/{total}")

    def on_capture_finished(self, success):
        """Handle completion of capture thread"""
        self.capture_in_progress = False
        self.toggle_start_button()

        if success:
            self.process_photos()
        else:
            self.update_progress(0, "Capture failed")

    # Thread class for capturing photos
    # Thread class for capturing photos
    # Thread class for capturing photos
    class CaptureThread(QThread):
        finished = pyqtSignal(bool)
        error_occurred = pyqtSignal(str, str)

        def __init__(self, save_path, hardware_manager, progress_callback, camera_busid):
            super().__init__()
            self.save_path = save_path
            self.hardware_manager = hardware_manager
            self.progress_callback = progress_callback
            self.camera_busid = camera_busid
            self.hardware_manager.save_folder = save_path

        def run(self):
            try:
                # Turn off laser
                if not self.hardware_manager.send_command(self.hardware_manager.COMMANDS["laser off"], "laser off"):
                    self.error_occurred.emit("Table360", "Failed to turn off laser")
                    self.finished.emit(False)
                    return

                num_photos = 20

                # Reset camera connection before starting sequence
                self.hardware_manager.reset_usb_connection(self.camera_busid)
                time.sleep(3)

                for i in range(1, num_photos + 1):
                    logger.info(f"▶ Obrót {i}/{num_photos}")

                    # Report progress
                    self.progress_callback(i, num_photos, "capturing")

                    # Start movement
                    movement_success = self.hardware_manager.send_command(
                        self.hardware_manager.COMMANDS["Lewo trzymanie"],
                        "Lewo trzymanie"
                    )

                    if not movement_success:
                        self.error_occurred.emit("Table360", "Movement command failed")
                        self.finished.emit(False)
                        return

                    # Wait for movement to complete
                    time.sleep(0.8)  # Reduced movement time

                    # Stop movement
                    if not self.hardware_manager.send_command(self.hardware_manager.COMMANDS["Stop"], "Stop"):
                        self.error_occurred.emit("Table360", "Stop command failed")
                        self.finished.emit(False)
                        return

                    # Short delay before capture
                    time.sleep(0.2)

                    # Capture photo
                    filename = f"zdjecie_{i:02d}.jpg"
                    success = self.hardware_manager.capture_dslr_photo(filename=filename)

                    if not success:
                        # Reset USB and try one more time
                        self.hardware_manager.reset_usb_connection(self.camera_busid)
                        time.sleep(3)
                        success = self.hardware_manager.capture_dslr_photo(filename=filename)

                        if not success:
                            self.error_occurred.emit("Camera", f"Failed to capture photo {i} after reset")
                            self.finished.emit(False)
                            return

                logger.info(f"✅ Completed capturing {num_photos} photos")

                # Turn laser back on
                self.hardware_manager.send_command(self.hardware_manager.COMMANDS["laser on"], "laser on")

                self.finished.emit(True)

            except Exception as e:
                logger.error(f"Capture error: {e}")
                self.error_occurred.emit("System", f"Unexpected error: {str(e)}")
                self.finished.emit(False)

    def process_photos(self):
        """Process the captured photos"""
        self.current_stage = "processing"
        self.update_progress(0, "Processing photos...")

        # Start processing in a separate thread
        self.process_thread = self.ProcessThread(self.selected_path, self.update_progress)
        self.process_thread.finished.connect(self.on_processing_finished)
        self.process_thread.start()

    def on_processing_finished(self, success):
        """Handle completion of processing"""
        if success:
            self.upload_photos()
        else:
            self.update_progress(0, "Processing failed")

    # Thread class for processing photos
    class ProcessThread(QThread):
        finished = pyqtSignal(bool)

        def __init__(self, folder_path, progress_callback):
            super().__init__()
            self.folder_path = folder_path
            self.progress_callback = progress_callback

        def run(self):
            try:
                # Update progress
                self.progress_callback(50, "Running Photoshop automation...")

                # Run Photoshop automation
                win_path = os.path.abspath(self.folder_path).replace('/', '\\')
                with open("folder_path.txt", "w") as f:
                    f.write(win_path)

                jsx_script = "auto_process.jsx"
                photoshop_exe = r"C:\Program Files\Adobe\Adobe Photoshop 2024\Photoshop.exe"

                subprocess.run([photoshop_exe, jsx_script], check=True, timeout=300)

                # Update progress
                self.progress_callback(75, "Converting to WebP...")

                # Process to WebP
                process_all(self.folder_path)

                self.progress_callback(100, "Processing complete!")
                self.finished.emit(True)
            except Exception as e:
                logger.error(f"Processing error: {e}")
                self.finished.emit(False)

    def upload_photos(self):
        """Upload the processed photos"""
        self.current_stage = "uploading"
        self.update_progress(0, "Uploading photos...")

        # Get the product ID from the text input
        product_id = self.name_input.text().strip()

        # Start upload in a separate thread
        self.upload_thread = self.UploadThread(self.selected_path, product_id, self.update_progress)
        self.upload_thread.finished.connect(self.on_upload_finished)
        self.upload_thread.start()

    def on_upload_finished(self, success):
        """Handle completion of upload"""
        if success:
            self.update_progress(100, "Upload complete!")
            # Show success message
            QMessageBox.information(self, "Success", "Upload completed successfully!")
        else:
            self.update_progress(0, "Upload failed!")
            # Show error message
            QMessageBox.critical(self, "Error", "Upload failed. Please check the logs for details.")

        # Re-enable start button
        self.start_button.setEnabled(True)
    # Thread class for uploading photos
    class UploadThread(QThread):
        finished = pyqtSignal(bool)

        def __init__(self, folder_path, product_id, progress_callback):
            super().__init__()
            self.folder_path = folder_path
            self.product_id = product_id
            self.progress_callback = progress_callback

        def run(self):
            try:
                # Update progress
                self.progress_callback(10, "Starting upload...")

                # Import and call the uploader
                from uploader import upload_files
                success = upload_files(self.folder_path, self.product_id)

                if success:
                    self.progress_callback(100, "Upload complete!")
                    self.finished.emit(True)
                else:
                    self.progress_callback(0, "Upload failed!")
                    self.finished.emit(False)

            except Exception as e:
                logger.error(f"Upload error: {e}")
                self.progress_callback(0, f"Upload error: {e}")
                self.finished.emit(False)

    def update_progress(self, value, text):
        """Update progress bar and label"""
        self.progress_bar.setValue(value)
        self.progress_label.setText(text)

    def show_alert_with_buttons(self, title, message, buttons=None, icon=None):
        """Show message box with buttons"""
        if buttons is None:
            buttons = QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
        if icon is None:
            icon = QMessageBox.Icon.Question

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(buttons)
        msg_box.setIcon(icon)
        result = msg_box.exec()
        return result


def main():
    def is_admin():
        """Check if the application is running with administrator privileges"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def main():
        # Request admin privileges if not already running as admin
        if not is_admin():
            try:
                # Re-run the program with admin rights
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
                sys.exit(0)
            except Exception as e:
                print(f"Failed to elevate privileges: {e}")
                # Continue without admin rights (user will see instructions if needed)

        app = QApplication(sys.argv)
        window = FileDialogExample()
        window.show()
        sys.exit(app.exec())
    app = QApplication(sys.argv)
    window = FileDialogExample()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()