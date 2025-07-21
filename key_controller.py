import os
import pyautogui
import keyboard
import time
import subprocess
import pygetwindow as gw

script_dir = os.path.dirname(os.path.abspath(__file__))
# open = os.path.join(script_dir, 'photos', 'open.jpg')
# path = os.path.join(script_dir, 'photos', 'path.jpg')
# table = os.path.join(script_dir, 'photos', 'table.jpg')
# laser = os.path.join(script_dir, 'photos', 'laser.jpg')
# project = os.path.join(script_dir, 'photos', 'project.jpg')
# fullscreen = os.path.join(script_dir, 'photos', 'fullscreen.jpg')
# camera = os.path.join(script_dir, 'photos', 'camera.jpg')
# minimalize = os.path.join(script_dir, 'photos', 'minimalize.jpg')
# start = os.path.join(script_dir, 'photos', 'start.jpg')
# app = os.path.join(script_dir, 'photos', 'app.jpg')
# setup_start = os.path.join(script_dir, 'photos', 'setup_start.jpg')
# setup_camera = os.path.join(script_dir, 'photos', 'setup_camera.jpg')
# setup_table = os.path.join(script_dir, 'photos', 'setup_table.jpg')
# number = os.path.join(script_dir, 'photos', 'number.jpg')
# windows_search = os.path.join(script_dir, 'photos', 'windows_search.jpg')
# windows_obs = os.path.join(script_dir, 'photos', 'windows_obs.jpg')
# # obs_capture = os.path.join(script_dir, 'photos', 'obs_capture.jpg')
# obs_right_click = os.path.join(script_dir, 'photos', 'obs_right_click.jpg')
# obs_full_screen = os.path.join(script_dir, 'photos', 'obs_full_screen.jpg')
# obs_select_screen = os.path.join(script_dir, 'photos', 'obs_select_screen.jpg')
folder_finder = os.path.join(script_dir, 'photos', 'folder_finder.jpg')
set_folder = os.path.join(script_dir, 'photos', 'set_folder.jpg')

image_folder = "photos"

# [table, laser, project, fullscreen, camera]

setting_up_preview = [
    os.path.join(image_folder, "table.jpg"),
    os.path.join(image_folder, "laser.jpg"),
    os.path.join(image_folder, "project.jpg"),
    os.path.join(image_folder, "camera.jpg"),
    os.path.join(image_folder, "fullscreen.jpg")

]

# images = [minimalize, start]

start = [
    os.path.join(image_folder, "minimalize.jpg"),
    os.path.join(image_folder, "start.jpg"),

]

#         images = [ setup_start, number, setup_table, setup_camera, fullscreen,  obs_right_click, obs_full_screen, obs_select_screen, minimalize]

setup_o2vr = [
    os.path.join(image_folder, "setup_start.jpg"),
    os.path.join(image_folder, "number.jpg"),
    os.path.join(image_folder, "setup_table.jpg"),
    os.path.join(image_folder, "setup_camera.jpg"),
    os.path.join(image_folder, "fullscreen.jpg")
]

setup_obs = [
    os.path.join(image_folder, "obs_wtf.jpg"),
    os.path.join(image_folder, "obs_right_click.jpg"),
    os.path.join(image_folder, "obs_full_screen.jpg"),
    os.path.join(image_folder, "obs_select_screen.jpg"),
    os.path.join(image_folder, "minimalize.jpg")
]


def find_and_click(selected):
    try:
        print("Szukam obrazu open.jpg na ekranie...")
        button_location = pyautogui.locateOnScreen(open, confidence=0.75)
        finder_location = pyautogui.locateOnScreen(folder_finder, confidence=0.9)
        if button_location:
            pyautogui.click(pyautogui.center(button_location))
            print("Kliknięto w znaleziony obraz open.jpg.")
            pyautogui.click(pyautogui.center(finder_location))
            keyboard.wait('')
            check_for_path_image()

        else:
            print("Nie znaleziono obrazu open.jpg.")
    except Exception as e:
        print(f"Błąd w find_and_click: {e}")
#
def open_file(selected):
    try:
        images = [open, folder_finder]
        for image_path in images:
            print(f"Szukam obrazu {os.path.basename(image_path)}...")
            image_location = pyautogui.locateOnScreen(image_path, confidence=0.8)
            if image_location:
                pyautogui.click(pyautogui.center(image_location))
                print(f"Kliknięto w obraz {os.path.basename(image_path)}.")
            else:
                print(f"Nie znaleziono obrazu {os.path.basename(image_path)}.")
            time.sleep(1)
        keyboard.write(selected)
        keyboard.press('enter')
        setf = pyautogui.locateOnScreen(set_folder, confidence=0.8)
        pyautogui.click(pyautogui.center(setf))
    except Exception as e:
        print(f"Błąd w click_first: {e}")
#
def check_for_path_image():
    print("Sprawdzam obecność path.jpg...")
    while True:
        time.sleep(1)
        try:
            pyautogui.locateOnScreen(path, confidence=0.8)
        except:
            print("Obraz path.jpg zniknął z ekranu!")
            break

def click_first(path):
    print(path)
    click_images(setting_up_preview)

def click_second():
    click_images(start)

def setup():

    subprocess.Popen('C:\Program Files\Object2VR\object2vr.exe')
    img = os.path.join(image_folder, "setup_start.jpg")
    wait_until_image_appears(img)

    click_images(setup_o2vr)

    subprocess.Popen("C:\ProgramData\Microsoft\Windows\Start Menu\Programs\OBS Studio\OBS Studio (64bit).lnk", shell=True)
    img = os.path.join(image_folder, "obs_right_click.jpg")
    wait_until_image_appears(img)
    click_images(setup_obs)


# keyboard.add_hotkey('f13', click_first)
# keyboard.add_hotkey('f14', click_second)
# keyboard.add_hotkey('home', setup)
#
# print("Czekam na wciśnięcie klawiszy F13 lub F14... ")
# keyboard.wait('f15')


# -=-=-=-==-=-=-=-=-=-=-=-=-=-=-=-=-=



def wait_until_image_appears(image_path, timeout=30, interval=0.5, action=None, confidence=0.9):
    print(f"Waiting for image to appear: {image_path}")
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=confidence)
            if location is not None:
                print("✅ Image found!")
                if action:
                    action()
                return True
        except Exception as e:
            print(f"No image yet")
        time.sleep(interval)

    print("⏰ Timeout: Image not found.")
    return False

def click_images(image_list):
    for image in image_list:
        if image == os.path.join(image_folder, "obs_wtf.jpg"):
            wait_until_image_appears(image,timeout=4 ,confidence=0.75)
        else:
            wait_until_image_appears(image, confidence=0.75)
        try:
            location = pyautogui.locateCenterOnScreen(image, confidence=0.75)
            if location:
                pyautogui.moveTo(location)
                if "right_click" in image:
                    pyautogui.rightClick(location)
                    print("right")
                elif image == os.path.join(image_folder, "number.jpg"):
                    pyautogui.doubleClick(location)
                    pyautogui.write("20")
                else:
                    pyautogui.click(location)

        except Exception as e:
            print(f"Error processing {image}: {e}")


