import os
from tkinter import Tk, filedialog, messagebox
from PIL import Image

def convert_folder(png_folder):
    files = sorted([
        f for f in os.listdir(png_folder)
        if f.lower().endswith(".png")
    ])

    if len(files) != 20:
        print(f"[!] Pomijam: {png_folder} — znaleziono {len(files)} plików, nie 20.")
        return

    output_folder = os.path.join(os.path.dirname(png_folder), "WEBP Files")
    os.makedirs(output_folder, exist_ok=True)

    for i, filename in enumerate(files):
        input_path = os.path.join(png_folder, filename)
        output_filename = f"img_0_0_{i}.webp"
        output_path = os.path.join(output_folder, output_filename)

        try:
            with Image.open(input_path) as img:
                img.save(output_path, "WEBP", quality=100)
            print(f"✓ {output_filename}")
        except Exception as e:
            print(f"[X] Błąd przy {filename}: {e}")

def process_all(root_folder):
    converted_any = False
    for dirpath, dirnames, filenames in os.walk(root_folder):
        for dirname in dirnames:
            if dirname == "PNG Files":
                png_folder = os.path.join(dirpath, dirname)
                print(f"\n== Przetwarzam: {png_folder} ==")
                convert_folder(png_folder)
                converted_any = True

    if converted_any:
        messagebox.showinfo("Gotowe", "Wszystkie konwersje zakończone!")
    else:
        messagebox.showwarning("Brak danych", "Nie znaleziono żadnych folderów 'PNG Files' z dokładnie 20 zdjęciami.")

def select_folder():
    root = Tk()
    root.withdraw()
    folder_selected = filedialog.askdirectory(title="Wybierz folder główny")
    if folder_selected:
        process_all(folder_selected)

if __name__ == "__main__":
    select_folder()
