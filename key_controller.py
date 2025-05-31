import os
import pyautogui
import keyboard
import time

script_dir = os.path.dirname(os.path.abspath(__file__))
open = os.path.join(script_dir, 'photos', 'open.jpg')
path = os.path.join(script_dir, 'photos', 'path.jpg')
table = os.path.join(script_dir, 'photos', 'table.jpg')
laser = os.path.join(script_dir, 'photos', 'laser.jpg')
project = os.path.join(script_dir, 'photos', 'project.jpg')
fullscreen = os.path.join(script_dir, 'photos', 'fullscreen.jpg')
camera = os.path.join(script_dir, 'photos', 'camera.jpg')
minimalize = os.path.join(script_dir, 'photos', 'minimalize.jpg')
start = os.path.join(script_dir, 'photos', 'start.jpg')
app = os.path.join(script_dir, 'photos', 'app.jpg')
setup_start = os.path.join(script_dir, 'photos', 'setup_start.jpg')
setup_camera = os.path.join(script_dir, 'photos', 'setup_camera.jpg')
setup_table = os.path.join(script_dir, 'photos', 'setup_table.jpg')
number = os.path.join(script_dir, 'photos', 'number.jpg')
windows_search = os.path.join(script_dir, 'photos', 'windows_search.jpg')
windows_obs = os.path.join(script_dir, 'photos', 'windows_obs.jpg')
# obs_capture = os.path.join(script_dir, 'photos', 'obs_capture.jpg')
obs_right_click = os.path.join(script_dir, 'photos', 'obs_right_click.jpg')
obs_full_screen = os.path.join(script_dir, 'photos', 'obs_full_screen.jpg')
obs_select_screen = os.path.join(script_dir, 'photos', 'obs_select_screen.jpg')
def find_and_click():
    try:
        print("Szukam obrazu open.jpg na ekranie...")
        button_location = pyautogui.locateOnScreen(open, confidence=0.8)
        if button_location:
            pyautogui.click(pyautogui.center(button_location))
            print("Kliknięto w znaleziony obraz open.jpg.")
            check_for_path_image()

        else:
            print("Nie znaleziono obrazu open.jpg.")
    except Exception as e:
        print(f"Błąd w find_and_click: {e}")

def check_for_path_image():
    print("Sprawdzam obecność path.jpg...")
    while True:
        time.sleep(1)
        try:
            pyautogui.locateOnScreen(path, confidence=0.8)
        except:
            print("Obraz path.jpg zniknął z ekranu!")
            break

def click_first():
    try:
        images = [table, laser, project, fullscreen, camera]
        for image_path in images:
            print(f"Szukam obrazu {os.path.basename(image_path)}...")
            image_location = pyautogui.locateOnScreen(image_path, confidence=0.8)
            if image_location:
                pyautogui.click(pyautogui.center(image_location))
                print(f"Kliknięto w obraz {os.path.basename(image_path)}.")
            else:
                print(f"Nie znaleziono obrazu {os.path.basename(image_path)}.")
            time.sleep(0.1)
    except Exception as e:
        print(f"Błąd w click_first: {e}")

def click_second():
    try:
        images = [minimalize, start]
        for image_path in images:
            print(f"Szukam obrazu {os.path.basename(image_path)}...")
            image_location = pyautogui.locateOnScreen(image_path, confidence=0.8)
            if image_location:
                pyautogui.click(pyautogui.center(image_location))
                print(f"Kliknięto w obraz {os.path.basename(image_path)}.")
            else:
                print(f"Nie znaleziono obrazu {os.path.basename(image_path)}.")
            time.sleep(0.1)
        time.sleep(85)
        find_and_click()
    except Exception as e:
        print(f"Błąd w click_second: {e}")

def setup():
    try:
        #           0       1           2       3               4           5              6                7          8                9               10                  11
        images = [windows_search, setup_start, number, setup_table, setup_camera, fullscreen, windows_search, windows_obs, obs_right_click, obs_full_screen, obs_select_screen, minimalize]
        count = 0
        for image_path in images:
            print(image_path)
            print(f"Szukam obrazu {os.path.basename(image_path)}...")
            image_location = pyautogui.locateOnScreen(image_path, confidence=0.8)
            if image_location:
                if count == 0:
                    # pyautogui.doubleClick(pyautogui.center(image_location))
                    # print(f"Double Kliknięto w obraz {os.path.basename(image_path)}.")
                    pyautogui.click(pyautogui.center(image_location))
                    pyautogui.write("Object")
                    keyboard.press("Enter")
                elif count == 2:
                    pyautogui.doubleClick(pyautogui.center(image_location))
                    print(f"Double Kliknięto w obraz {os.path.basename(image_path)}.")
                    pyautogui.press('2')
                    pyautogui.press('0')
                elif count == 7:
                    pyautogui.click(pyautogui.center(image_location))
                    print(f"czekam na obs")
                    time.sleep(3)
                elif count == 8:
                    pyautogui.write("Obs")
                    keyboard.press("Enter")

                else:
                    pyautogui.click(pyautogui.center(image_location))
                    print(f"Kliknięto w obraz {os.path.basename(image_path)}.")
            else:
                print(f"Nie znaleziono obrazu {os.path.basename(image_path)}.")
            time.sleep(0.35)
            count+=1
        time.sleep(2)
        find_and_click()
    except Exception as e:
        print(f"Błąd w click_second: {e}")

keyboard.add_hotkey('f13', click_first)
keyboard.add_hotkey('f14', click_second)
keyboard.add_hotkey('home', setup)

print("Czekam na wciśnięcie klawiszy F13 lub F14... ")
keyboard.wait('f15')