# Build the standalone single-file ChunkCompass.exe with PyInstaller.
# Usage:  .\build_exe.ps1
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$py = Join-Path $root ".venv\Scripts\python.exe"

Write-Host "Building ChunkCompass.exe ..." -ForegroundColor Cyan
& $py -m PyInstaller --noconfirm --onefile --windowed `
    --name ChunkCompass `
    --add-data "$root\chunkcompass\lib\cubiomes.dll;chunkcompass/lib" `
    --distpath "$root\dist" `
    --workpath "$root\build" `
    --specpath "$root" `
    "$root\main.py"

Write-Host "`nDone. Output: $root\dist\ChunkCompass.exe" -ForegroundColor Green
