# working_build.py
import os
import sys
import subprocess
import shutil
import importlib


def check_dependencies():
    """Check if all required dependencies are available"""
    dependencies = [
        'PyQt6',
        'serial',
        'selenium',
        'webdriver_manager',
        'requests',
        'PIL'  # Pillow
    ]

    missing = []
    for dep in dependencies:
        try:
            importlib.import_module(dep)
            print(f"✓ {dep}")
        except ImportError:
            missing.append(dep)
            print(f"✗ {dep}")

    return missing


def create_data_files():
    """Create a list of data files to include"""
    data_files = []

    # List of files that need to be included
    files_to_include = [
        'auto_process.jsx',
        'hardware_handler.py',
        'webp_handler.py',
        'uploader.py'
    ]

    for file in files_to_include:
        if os.path.exists(file):
            data_files.append((file, '.'))
            print(f"✓ Including {file}")
        else:
            print(f"⚠ Warning: {file} not found")

    return data_files


def build_with_spec():
    """Build using a properly configured spec file"""

    # Create a proper spec file content
    spec_content = '''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas={data_files},
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'serial',
        'selenium.webdriver.common.by',
        'selenium.webdriver.support.ui',
        'selenium.webdriver.support.expected_conditions',
        'webdriver_manager.chrome',
        'requests',
        'queue',
        'logging',
        'json',
        'os',
        'sys',
        'time',
        'threading',
        'subprocess',
        're'
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=['tkinter', 'pymsgbox'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='360PhotoOperator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX to avoid compression issues
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''.format(data_files=create_data_files())

    # Write the spec file
    with open('working_spec.spec', 'w') as f:
        f.write(spec_content)

    # Build using the spec file
    cmd = ['pyinstaller', 'working_spec.spec', '--clean']
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("✓ Build completed successfully")
        return True
    else:
        print("✗ Build failed")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        return False


def test_built_executable():
    """Test the built executable"""
    exe_path = os.path.join('dist', '360PhotoOperator.exe')

    if not os.path.exists(exe_path):
        print("Executable not found at expected location")
        return False

    print("Testing executable...")

    # Create a test script that runs the executable
    test_script = '''
import subprocess
import sys
import time

exe_path = r'{exe_path}'

print(f"Running: {{exe_path}}")
try:
    process = subprocess.Popen(
        [exe_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True
    )

    # Wait and capture output
    time.sleep(10)

    # Try to get output
    try:
        stdout, stderr = process.communicate(timeout=5)
        print("STDOUT:", stdout)
        print("STDERR:", stderr)
    except subprocess.TimeoutExpired:
        print("Application is running (no output captured)")
        process.terminate()

    print(f"Return code: {{process.returncode}}")

except Exception as e:
    print(f"Error: {{e}}")
'''.format(exe_path=exe_path)

    with open('test_executable.py', 'w') as f:
        f.write(test_script)

    # Run the test
    subprocess.run([sys.executable, 'test_executable.py'])

    # Clean up
    if os.path.exists('test_executable.py'):
        os.remove('test_executable.py')

    return True


def main():
    """Main build process"""
    print("360 Photo Operator - Working Build")
    print("=" * 50)

    # Check dependencies
    print("Checking dependencies...")
    missing = check_dependencies()
    if missing:
        print(f"Missing dependencies: {missing}")
        print("Installing missing dependencies...")
        for dep in missing:
            subprocess.run([sys.executable, '-m', 'pip', 'install', dep])

    # Clean previous builds
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    if os.path.exists('build'):
        shutil.rmtree('build')

    # Build with spec file
    print("\\nBuilding executable...")
    if build_with_spec():
        print("\\nTesting executable...")
        test_built_executable()
    else:
        print("Build failed!")


if __name__ == "__main__":
    main()