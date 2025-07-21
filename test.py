import serial
import time
from enum import Enum


class MovementMode(Enum):
    PAN = 1
    TILT = 2
    ROTATE = 3
    RESET = 4


class LightMode(Enum):
    INTENSITY = 1
    RGB = 2
    STROBE = 3


class Show3D360Controller:
    def __init__(self, port='COM3', baudrate=115200):
        """Initialize connection to the rig"""
        self.connection = serial.Serial(port, baudrate=baudrate, timeout=1)
        self._connected = True
        self.presets = {
            'home': {'pan': 127, 'tilt': 127, 'light': 0},
            'center': {'pan': 127, 'tilt': 127, 'light': 100},
            'left': {'pan': 0, 'tilt': 127, 'light': 50},
            'right': {'pan': 255, 'tilt': 127, 'light': 50}
        }

    def send_command(self, command):
        """Send raw command to the rig"""
        if not self._connected:
            raise ConnectionError("Not connected to rig")
        self.connection.write(f"{command}\n".encode())
        return self.connection.readline().decode().strip()

    def close(self):
        """Close connection"""
        self._connected = False
        self.connection.close()

    def move(self, mode: MovementMode, value: int, speed: int = 50):
        """
        Control rig movement
        :param mode: MovementMode enum
        :param value: Target position (0-255) or degrees
        :param speed: Movement speed (1-100)
        """
        cmd_map = {
            MovementMode.PAN: "PAN",
            MovementMode.TILT: "TILT",
            MovementMode.ROTATE: "ROT",
            MovementMode.RESET: "HOME"
        }

        if mode == MovementMode.RESET:
            return self.send_command(f"{cmd_map[mode]}")
        return self.send_command(f"{cmd_map[mode]} {value} {speed}")

    def move_to_position(self, pan: int, tilt: int, speed: int = 50):
        """Move to specific pan/tilt position"""
        self.move(MovementMode.PAN, pan, speed)
        self.move(MovementMode.TILT, tilt, speed)

    def rotate_continuous(self, speed: int):
        """Continuous rotation at specified speed (-100 to 100)"""
        self.move(MovementMode.ROTATE, speed if speed > 0 else 256 + speed, abs(speed))

    def light_control(self, mode: LightMode, **kwargs):
        """
        Control lighting functions
        :param mode: LightMode enum
        :param kwargs:
            - intensity (0-100)
            - rgb (tuple of 0-255 values)
            - strobe_speed (0-100)
        """
        if mode == LightMode.INTENSITY:
            value = kwargs.get('intensity', 100)
            return self.send_command(f"LIGHT {int(value * 2.55)}")

        elif mode == LightMode.RGB:
            r, g, b = kwargs.get('rgb', (255, 255, 255))
            return self.send_command(f"RGB {r} {g} {b}")

        elif mode == LightMode.STROBE:
            speed = kwargs.get('strobe_speed', 50)
            return self.send_command(f"STROBE {speed}")

    def save_preset(self, name, pan=None, tilt=None, light=None, rgb=None):
        """Save current position as preset"""
        self.presets[name] = {
            'pan': pan,
            'tilt': tilt,
            'light': light,
            'rgb': rgb
        }

    def recall_preset(self, name, speed=50):
        """Recall saved preset"""
        preset = self.presets.get(name)
        if not preset:
            raise ValueError(f"Preset {name} not found")

        if preset['pan'] is not None and preset['tilt'] is not None:
            self.move_to_position(preset['pan'], preset['tilt'], speed)

        if preset['light'] is not None:
            self.light_control(LightMode.INTENSITY, intensity=preset['light'])


if __name__ == "__main__":
    # Initialize controller
    try:
        rig = Show3D360Controller(port='COM3')  # Change to your port

        # Example movement sequence
        rig.recall_preset('home')
        time.sleep(1)

        rig.move_to_position(pan=50, tilt=180, speed=30)
        rig.light_control(LightMode.INTENSITY, intensity=75)
        time.sleep(2)



        rig.rotate_continuous(speed=0)  # Stop rotation
        rig.recall_preset('center')

    except serial.SerialException as e:
        print(f"Serial connection error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'rig' in locals():
            rig.close()