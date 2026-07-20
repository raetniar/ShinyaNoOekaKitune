import os
import shutil
import subprocess
import PyInstaller.__main__

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(root_dir)

# Define build paths
dist_dir = "dist"
build_dir = "build"
icon_path = "system_files/icon.ico"
main_py = "system_files/main.py"

# Cleanup previous build folders if any
for folder in [dist_dir, build_dir]:
    if os.path.exists(folder):
        try: shutil.rmtree(folder)
        except Exception: pass

print("1. Compressing/Compiling long video tool with new icon...")
PyInstaller.__main__.run([
    '--noconfirm',
    '--onedir',
    '--windowed',
    '--name=きりぬきつーる_長尺用',
    '--icon=' + icon_path,
    '--distpath=' + dist_dir,
    '--workpath=' + build_dir,
    main_py
])

print("2. Copying ffmpeg.exe to _internal...")
ffmpeg_src = "system_files/ffmpeg.exe"
ffmpeg_dst = "dist/きりぬきつーる_長尺用/_internal/ffmpeg.exe"
if os.path.exists(ffmpeg_src):
    shutil.copy2(ffmpeg_src, ffmpeg_dst)

print("3. Deploying to root directory...")
dest_exe = "きりぬきつーる_長尺用.exe"
dest_internal = "_internal"

# Rename running files/old files to avoid locks
old_exe = "きりぬきつーる_長尺用_old.exe"
if os.path.exists(old_exe):
    try: os.remove(old_exe)
    except Exception: pass

if os.path.exists(dest_exe):
    try: os.rename(dest_exe, old_exe)
    except Exception as e: print("Warning (rename exe):", e)

if os.path.exists(dest_internal):
    try: shutil.rmtree(dest_internal)
    except Exception as e: print("Warning (remove _internal):", e)

# Move new executable and _internal
shutil.move("dist/きりぬきつーる_長尺用/きりぬきつーる_長尺用.exe", dest_exe)
shutil.move("dist/きりぬきつーる_長尺用/_internal", dest_internal)

print("4. Cleaning up build artifacts...")
try: shutil.rmtree(dist_dir)
except Exception: pass
try: shutil.rmtree(build_dir)
except Exception: pass
spec_file = "きりぬきつーる_長尺用.spec"
if os.path.exists(spec_file):
    os.remove(spec_file)

# Cleanup old_exe if successfully replaced
if os.path.exists(old_exe):
    try: os.remove(old_exe)
    except Exception: pass

print("SUCCESS: Long video tool successfully compiled with custom 'L' icon!")
