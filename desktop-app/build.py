"""
Build script to create standalone .exe using PyInstaller.
"""
import PyInstaller.__main__
import os
import shutil

# Get the directory of this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Clean previous builds
for folder in ['build', 'dist']:
    path = os.path.join(BASE_DIR, folder)
    if os.path.exists(path):
        shutil.rmtree(path)

# PyInstaller arguments
args = [
    os.path.join(BASE_DIR, 'main.py'),
    '--name=LeadsCheckerPro',
    '--onefile',
    '--windowed',
    '--noconfirm',
    '--clean',
    f'--distpath={os.path.join(BASE_DIR, "dist")}',
    f'--workpath={os.path.join(BASE_DIR, "build")}',
    f'--specpath={BASE_DIR}',
    f'--add-data={os.path.join(BASE_DIR, "Logo")}{os.pathsep}Logo',
    '--collect-all=customtkinter',
    '--hidden-import=PIL',
    '--hidden-import=PIL._tkinter_finder',
    '--hidden-import=requests',
]

print("Building Leads Checker Pro...")
print("This may take a few minutes...")

PyInstaller.__main__.run(args)

print("\n" + "="*50)
print("Build complete!")
print(f"Executable: {os.path.join(BASE_DIR, 'dist', 'LeadsCheckerPro.exe')}")
print("="*50)
