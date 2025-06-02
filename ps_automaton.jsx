// ===== KONFIGURACJA ===== //
var ACTION_NAME = "Wycięcie Buty";
var ACTION_SET = "Buty.atn";
var OUTPUT_FORMAT = "PNG"; // Zapisz jako PNG

// ===== GŁÓWNA FUNKCJA ===== //
function main() {
    var mainFolder = Folder.selectDialog("Wybierz folder GŁÓWNY");
    if (!mainFolder) return;

    var totalProcessed = processAllSubfolders(mainFolder);
    alert("Gotowe!\nPrzetworzono zdjęć: " + totalProcessed);
}

// ===== PRZETWARZANIE REKURENCYJNE ===== //
function processAllSubfolders(folder) {
    var files = folder.getFiles();
    var imageCount = 0;

    var images = [];
    for (var i = 0; i < files.length; i++) {
        if (files[i] instanceof Folder) {
            imageCount += processAllSubfolders(files[i]);
        } else if (isImageFile(files[i])) {
            images.push(files[i]);
        }
    }

    if (images.length > 0) {
        var outputFolder = new Folder(folder + "/" + OUTPUT_FORMAT + " Files");
        if (!outputFolder.exists) outputFolder.create();

        for (var i = 0; i < images.length; i++) {
            if (processSingleFile(images[i], outputFolder)) {
                imageCount++;
            }
        }
    }

    return imageCount;
}

// ===== PRZETWARZANIE POJEDYNCZEGO ZDJĘCIA ===== //
function processSingleFile(file, outputFolder) {
    try {
        var doc = app.open(file);

        app.doAction(ACTION_NAME, ACTION_SET);

        var originalName = decodeURI(file.name).replace(/\.[^\.]+$/, "");
        var outputFile = new File(outputFolder + "/" + originalName + ".png");

        var saveOptions = new PNGSaveOptions();
        doc.saveAs(outputFile, saveOptions);

        doc.close(SaveOptions.DONOTSAVECHANGES);
        return true;
    } catch (e) {
        alert("Błąd podczas przetwarzania: " + file.name + "\n" + e);
        return false;
    }
}

// ===== SPRAWDZANIE TYPU PLIKU ===== //
function isImageFile(file) {
    return /\.(jpg|jpeg|png|tiff|psd)$/i.test(file.name);
}

// ===== URUCHOMIENIE ===== //
main();
