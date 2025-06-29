# Fordere den Benutzer auf, das Root-Verzeichnis anzugeben
$rootDirectory = Read-Host "Gib das Verzeichnis ein, in dem nach ZIP-Dateien gesucht werden soll"

# Überprüfen, ob das angegebene Verzeichnis existiert
if (-not (Test-Path -Path $rootDirectory)) {
    Write-Host "Das angegebene Verzeichnis existiert nicht. Bitte überprüfe den Pfad und versuche es erneut."
    exit
}
# Hole alle ZIP-Dateien im angegebenen Verzeichnis und allen Unterordnern
$zipFiles = Get-ChildItem -Path $rootDirectory -Recurse -Filter "*.zip"

foreach ($zipFile in $zipFiles) {
    # Zielverzeichnis für die Entpackung (kann angepasst werden, falls gewünscht)
    $destination = $zipFile.FullName.Replace($zipFile.Extension, "")

    # Falls das Zielverzeichnis noch nicht existiert, erstelle es
    if (-not (Test-Path -Path $destination)) {
        New-Item -ItemType Directory -Path $destination
    }

    # Entpacken der ZIP-Datei
    try {
        Write-Host "Entpacke $($zipFile.FullName) nach $destination"
        Expand-Archive -Path $zipFile.FullName -DestinationPath $destination -Force
    }
    catch {
        Write-Host "Fehler beim Entpacken von $($zipFile.FullName): $_"
    }
}