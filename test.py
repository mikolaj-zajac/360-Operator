# import tkinter as tk
# import serial
# import time
# import cv2
#
# # Połączenie z urządzeniem
# ser = serial.Serial('COM3', 19200, timeout=1)
#
# def send_command(command, description=""):
#     print(f"▶ {description}: {command.hex()}")
#     ser.write(command)
#
# # Komendy
# COMMANDS = {
#     "Stop": bytes.fromhex("010300000000000004"),
#     "Lewo ciągle": bytes.fromhex("010100000000006466"),
#     "Prawo ciągle": bytes.fromhex("010200000000006467"),
#     "Lewo trzymanie": bytes.fromhex("01010000000002373b"),
#     "Prawo trzymanie": bytes.fromhex("01020000000002373c"),
#     "Obrót +90": bytes.fromhex("010401000000f5dfda"),
#     "Obrót -90": bytes.fromhex("01040100ffff0a212f"),
#     "laser on": bytes.fromhex("010e01020000000113"),
#     "laser off": bytes.fromhex("010e01020000000012"),
#     "cos1": bytes.fromhex("010501000000000007"),
#     "cos2": bytes.fromhex("010500000000000006"),
#     "cos3": bytes.fromhex("020400000005319eda"),
#     "cos4": bytes.fromhex("020601000000000009"),
#
# }
#
# # GUI
# root = tk.Tk()
# root.title("Sterowanie TopShow3D")
# root.geometry("300x400")
#
# KOMENDA_LEWO_TRZYMAJ = bytes.fromhex("01010000000002373b")
# KOMENDA_STOP = bytes.fromhex("010300000000000004")
#
# def zrob_zdjecie(nazwa="zdjecie.jpg"):
#     cap = cv2.VideoCapture(0)  # Możesz zmienić na 1, 2, itd. jeśli masz wiele kamer
#     ret, frame = cap.read()
#     if ret:
#         cv2.imwrite(nazwa, frame)
#         print(f"📸 Zapisano: {nazwa}")
#     else:
#         print("❌ Nie udało się zrobić zdjęcia.")
#     cap.release()
#
# def znajdz_kamere():
#     for i in range(5):
#         cap = cv2.VideoCapture(i)
#         if cap.read()[0]:
#             print(f"✅ Kamera znaleziona pod indeksem {i}")
#             cap.release()
#             return i
#         cap.release()
#     print("❌ Nie znaleziono żadnej kamery.")
#     return None
#
# def zrob_obroty_i_zdjecia(ser, czas_obrotu=0.72725, liczba_zdjec=20):
#     for i in range(1, liczba_zdjec + 1):
#         print(f"▶ Obrót {i}/{liczba_zdjec}")
#         ser.write(KOMENDA_LEWO_TRZYMAJ)
#         time.sleep(czas_obrotu)
#         ser.write(KOMENDA_STOP)
#         print(f"📸 Zdjęcie wykonane ({i})")
#         zrob_zdjecie()
#         time.sleep(3)
#
# # Przyciski stałe (klik i gotowe)
# def make_click_button(text, command_name):
#     tk.Button(root, text=text, width=20, height=2, command=lambda: send_command(COMMANDS[command_name], text)).pack(pady=5)
#
# # Przyciski trzymane (press i release)
# def make_hold_button(text, command_name):
#     btn = tk.Button(root, text=text, width=20, height=2)
#     btn.bind("<ButtonPress>", lambda e: send_command(COMMANDS[command_name], f"{text} - START"))
#     btn.bind("<ButtonRelease>", lambda e: send_command(COMMANDS["Stop"], f"{text} - STOP"))
#     btn.pack(pady=5)
#
# # GUI - dodaj przyciski
# make_click_button("Obrót +90", "Obrót +90")
# make_click_button("Obrót -90", "Obrót -90")
# make_click_button("Lewo ciągle", "Lewo ciągle")
# make_click_button("Prawo ciągle", "Prawo ciągle")
# make_hold_button("Lewo (trzymanie)", "Lewo trzymanie")
# make_hold_button("Prawo (trzymanie)", "Prawo trzymanie")
# make_click_button("STOP", "Stop")
# make_click_button("laser on", "laser on")
# make_click_button("laser off", "laser off")
# tk.Button(root, text="text", width=20, height=2, command=lambda: zrob_obroty_i_zdjecia(ser)).pack(pady=5)
# tk.Button(root, text="text", width=20, height=2, command=lambda: zrob_zdjecie()).pack(pady=5)
#
# index = znajdz_kamere()
# print(index)
#
# #
# root.mainloop()
# ser.close()
#
#
import requests
import time


def capture_photo(filename="canon_photo.jpg"):
    # Trigger capture
    requests.get("http://localhost:5513/?CMD=Capture")
    time.sleep(2)  # Wait for camera to save

    # Download the latest photo
    latest_photo = requests.get("http://localhost:5513/?CMD=GetLastCapturedFile").text
    if latest_photo:
        with open(filename, "wb") as f:
            f.write(requests.get(f"http://localhost:5513/{latest_photo}").content)
        print(f"✅ Photo saved as {filename}")
    else:
        print("❌ Failed to capture photo")


capture_photo()