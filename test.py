import serial
import time

def initialize_ftdi(ser):
    """Inicjalizacja FTDI (DTR, RTS)"""
    print("Inicjalizacja FTDI...")
    ser.setDTR(False)
    ser.setRTS(False)
    time.sleep(0.1)
    ser.setDTR(True)
    ser.setRTS(True)
    time.sleep(0.1)
    print("DTR i RTS ustawione")

def send_command(ser, command, description):
    """Wysyłanie komendy i odczyt odpowiedzi"""
    print(f"Wysyłam {description}: {command.hex()}")
    ser.write(command)
    time.sleep(0.2)  # Zwiększony czas na odpowiedź
    response = ser.read(9)  # Oczekuj 9-bajtowej odpowiedzi
    print(f"Otrzymano odpowiedź: {response.hex() if response else 'Brak odpowiedzi'}")
    return response

try:
    # Otwórz port COM3 z baud rate 19200
    ser = serial.Serial(
        port='COM3',
        baudrate=19200,  # Potwierdzony baud rate
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=1
    )
    print("Port szeregowy otwarty")

    # Inicjalizacja FTDI
    initialize_ftdi(ser)

    # Komendy
    commands = [
        (bytes([0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02]), "Komenda Połącz"),
        (bytes([0x01, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03]), "Komenda Połącz"),
        (bytes([0x01, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x04]), "Obrót 90° w prawo"),
        (bytes([0x01, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x05]), "Obrót 90° w lewo"),

    ]

    for command, desc in commands:
        send_command(ser, command, desc)
        time.sleep(1)  # Odstęp między komendami

except serial.SerialException as e:
    print(f"Błąd: {e}")
finally:
    ser.close()
    print("Port szeregowy zamknięty")

