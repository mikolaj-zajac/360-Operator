// ===== KONFIGURACJA ===== //
var ACTION_NAME = "Otwarty";
var ACTION_SET = "Zestaw 1.atn";
var OUTPUT_FORMAT = "PNG"; // Zapisz jako PNG
var mainFolder = null; // Declare globally


// ===== GŁÓWNA FUNKCJA ===== //
function main() {
    var pathFile = File("C:/Users/Cinek/PycharmProjects/360-Operator/folder_path.txt");
    pathFile.open("r");
    var folderPath = pathFile.read();
    pathFile.close();
    var mainFolder = new Folder(folderPath);

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
var pathFile = File("C:/Users/Cinek/PycharmProjects/360-Operator/folder_path.txt");
pathFile.open("r");
var folderPath = pathFile.read();
pathFile.close();
var mainFolder = new Folder(folderPath);
var outputFolder = new Folder(mainFolder + "/" + OUTPUT_FORMAT + " Files");

if (outputFolder.exists) {
    var pngs = outputFolder.getFiles("*.png");
    alert("Znaleziono plików PNG: " + pngs.length);

    for (var i = 0; i < pngs.length; i++) {
        app.open(pngs[i]);
    }
} else {
    alert("Folder nie istnieje: " + outputFolder.fsName);
}

if (outputFolder.exists) {
    var pngs = outputFolder.getFiles("*.png");
    for (var i = 0; i < pngs.length; i++) {
        app.open(pngs[i]);
    }
}