"""cx_Freeze build script -> produces a Windows .msi installer.

Build the installer with:

    .venv\\Scripts\\python.exe setup.py bdist_msi

The resulting .msi appears in the dist\\ folder. (The standalone single-file
.exe is built separately with PyInstaller - see build_exe.ps1.)
"""

import os

from cx_Freeze import Executable, setup

# Run from this file's directory so relative paths resolve regardless of cwd.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from chunkcompass import __version__  # noqa: E402

# Our compiled world-gen DLL, loaded at runtime via ctypes by engine.py.
_dll_src = os.path.join("chunkcompass", "lib", "cubiomes.dll")

build_exe_options = {
    "packages": ["chunkcompass", "PIL", "tkinter"],
    "excludes": ["test", "unittest", "pydoc_data"],
    # Keep chunkcompass as loose files (not zipped) so engine.py's __file__ path
    # to lib/cubiomes.dll resolves, and copy the DLL into that location.
    "zip_exclude_packages": ["chunkcompass"],
    "include_files": [
        (_dll_src, os.path.join("lib", "chunkcompass", "lib", "cubiomes.dll")),
    ],
    "include_msvcr": True,
}

# Stable upgrade code so future MSIs upgrade in place instead of installing twice.
bdist_msi_options = {
    "upgrade_code": "{3F2C9A17-6E84-4B2D-9A1C-7D5E2F8B0C63}",
    "add_to_path": False,
    "initial_target_dir": r"[ProgramFilesFolder]\Chunk Compass",
    "all_users": False,
}

executables = [
    Executable(
        "main.py",
        base="Win32GUI",              # windowed app, no console
        target_name="ChunkCompass.exe",
        shortcut_name="Chunk Compass",
        shortcut_dir="ProgramMenuFolder",
        copyright="Chunk Compass",
    )
]

setup(
    name="ChunkCompass",
    version=__version__,
    description="Minecraft seed map with custom waypoints",
    options={
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options,
    },
    executables=executables,
)
