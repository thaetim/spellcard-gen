"""Build script for compiling spellcard-generator to EXE with PyInstaller."""
import subprocess
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path
import shutil


def run_command(cmd, check=True, logger=None):
    """Run a command and capture all output to both console and log."""
    cmd_str = ' '.join(str(c) for c in cmd)
    print(f"\n>>> {cmd_str}\n")
    if logger:
        logger.info(f"Running command: {cmd_str}")

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1,
        encoding='utf-8',
        errors='replace'
    )

    for line in process.stdout:
        print(line, end='')
        if logger:
            logger.info(line.rstrip())

    returncode = process.wait()

    if logger:
        logger.info(f"Command returned: {returncode}")

    if check and returncode != 0:
        raise subprocess.CalledProcessError(returncode, cmd)

    return returncode == 0


def is_package_installed(package_name, python_exe):
    """Check if a package is installed."""
    try:
        subprocess.run([python_exe, "-m", "pip", "show", package_name],
                       capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def setup_logging(script_dir):
    """Set up logging to both console and log file."""
    log_dir = script_dir / "log"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "latest-pyinstaller.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file, mode='w', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("PyInstaller build script started")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    return logger


def main():
    parser = argparse.ArgumentParser(
        description='Build spellcard-generator with PyInstaller')
    parser.add_argument('--standalone', action='store_true',
                        help='Build as standalone folder instead of single exe (better AV compatibility)')
    args = parser.parse_args()

    script_dir = Path(__file__).parent.absolute()
    logger = setup_logging(script_dir)
    
    venv312_python = script_dir / ".venv312" / "Scripts" / "python.exe"

    if venv312_python.exists():
        python_exe = str(venv312_python)
        if sys.executable != python_exe:
            msg = f"⚠ Using venv312 Python: {python_exe} (Current: {sys.executable})"
            print(msg)
            logger.info(msg)
    else:
        python_exe = sys.executable
        msg = f"⚠ Warning: .venv312 not found, using: {python_exe} (Expected: {venv312_python})"
        print(msg)
        logger.warning(msg)

    # Check if PyInstaller is installed
    if not is_package_installed("pyinstaller", python_exe):
        msg = "Installing PyInstaller..."
        print(msg)
        logger.info(msg)
        if not run_command([python_exe, "-m", "pip", "install", "pyinstaller"], logger=logger):
            msg = "Failed to install PyInstaller"
            print(msg)
            logger.error(msg)
            return 1

    msg = "✓ PyInstaller is installed"
    print(msg)
    logger.info(msg)

    # Install project dependencies
    requirements_file = script_dir / "requirements.txt"
    if requirements_file.exists():
        msg = "Installing project dependencies..."
        print(msg)
        logger.info(msg)
        if not run_command([python_exe, "-m", "pip", "install", "-r", str(requirements_file)], logger=logger):
            msg = "Failed to install dependencies"
            print(msg)
            logger.error(msg)
            return 1
        msg = "✓ Dependencies installed"
        print(msg)
        logger.info(msg)

    # Build configuration
    script = script_dir / "generate.py"
    output_dir = script_dir / "build"
    dist_dir = script_dir / "dist"
    
    # Clean previous builds
    for dir_path in [output_dir, dist_dir]:
        if dir_path.exists():
            msg = f"Cleaning {dir_path}..."
            print(msg)
            logger.info(msg)
            shutil.rmtree(dir_path)

    output_dir.mkdir(exist_ok=True)
    dist_dir.mkdir(exist_ok=True)

    # Get version from generate.py
    try:
        generate_content = script.read_text(encoding='utf-8')
        for line in generate_content.split('\n'):
            if line.strip().startswith('VERSION'):
                version = line.split('=')[1].strip().strip("'\"")
                break
        else:
            version = '1.0.0'
            logger.warning("VERSION not found in generate.py, using default: 1.0.0")
    except Exception as e:
        version = '1.0.0'
        logger.warning(f"Could not read VERSION from generate.py: {e}, using default: 1.0.0")

    exe_filename = f"spellcard-generator_{version}.exe"

    # PyInstaller command
    pyinstaller_cmd = [
        python_exe, "-m", "PyInstaller",
        
        # Output options
        f"--distpath={dist_dir}",
        f"--workpath={output_dir}",
        f"--specpath={output_dir}",
        f"--name={exe_filename.replace('.exe', '')}",
        
        # Console mode
        "--console",
        
        # Clean previous build
        "--clean",
        
        # Don't confirm before replacing files
        "--noconfirm",
        
        # Include data directories
        f"--add-data={script_dir / 'templates'}{';' if sys.platform == 'win32' else ':'}templates",
        f"--add-data={script_dir / 'data'}{';' if sys.platform == 'win32' else ':'}data",
        f"--add-data={script_dir / 'assets'}{';' if sys.platform == 'win32' else ':'}assets",
        
        # Hidden imports (modules that PyInstaller might miss)
        "--hidden-import=card_generator",
        "--hidden-import=spell_processing",
        "--hidden-import=text_formatting",
        "--hidden-import=spell_styling",
        "--hidden-import=text_splitting",
        "--hidden-import=pandas",
        "--hidden-import=watchdog",
        "--hidden-import=keyboard",
        
        # Collect all submodules for key packages
        "--collect-all=pandas",
        "--collect-all=keyboard",
    ]

    # Add version info
    pyinstaller_cmd.extend([
        f"--version-file=NONE",  # We'll add metadata manually if needed
    ])

    # Single file vs standalone folder
    if args.standalone:
        msg = "Building as STANDALONE FOLDER (better AV compatibility)"
        print(msg)
        logger.info(msg)
        # No --onefile flag = creates a folder
    else:
        msg = "Building as SINGLE EXE FILE"
        print(msg)
        logger.info(msg)
        pyinstaller_cmd.append("--onefile")

    # Add main script
    pyinstaller_cmd.append(str(script))

    msg = "Building spellcard-generator.exe with PyInstaller"
    print("=" * 60)
    print(msg)
    print("=" * 60)
    logger.info("=" * 60)
    logger.info(msg)
    logger.info("=" * 60)

    if run_command(pyinstaller_cmd, logger=logger):
        # Move final exe to build folder with version in name
        if args.standalone:
            # Standalone mode creates a folder
            standalone_folder = dist_dir / exe_filename.replace('.exe', '')
            if standalone_folder.exists():
                final_path = output_dir / exe_filename.replace('.exe', '')
                if final_path.exists():
                    shutil.rmtree(final_path)
                shutil.move(str(standalone_folder), str(final_path))
                msg = f"✓ Build successful! Standalone folder: {final_path}"
                print("\n" + "=" * 60)
                print("✓ Build successful!")
                print(f"Standalone folder: {final_path}")
                print(f"Run: {final_path / (exe_filename.replace('.exe', '') + '.exe')}")
                print("=" * 60)
                logger.info("=" * 60)
                logger.info(msg)
                logger.info("=" * 60)
            else:
                msg = "Build completed but output folder not found"
                print(msg)
                logger.error(msg)
                return 1
        else:
            # Single exe mode
            exe_in_dist = dist_dir / f"{exe_filename.replace('.exe', '')}.exe"
            if exe_in_dist.exists():
                final_exe = output_dir / exe_filename
                if final_exe.exists():
                    final_exe.unlink()
                shutil.move(str(exe_in_dist), str(final_exe))
                msg = f"✓ Build successful! Executable: {final_exe}"
                print("\n" + "=" * 60)
                print("✓ Build successful!")
                print(f"Executable: {final_exe}")
                print(f"Size: {final_exe.stat().st_size / 1024 / 1024:.2f} MB")
                print("=" * 60)
                logger.info("=" * 60)
                logger.info(msg)
                logger.info("=" * 60)
            else:
                msg = "Build completed but exe not found in dist folder"
                print(msg)
                logger.error(msg)
                return 1
        
        # Clean up dist folder
        if dist_dir.exists():
            shutil.rmtree(dist_dir)
        
        return 0
    else:
        msg = "✗ Build failed"
        print("\n" + "=" * 60)
        print(msg)
        print("=" * 60)
        logger.error("=" * 60)
        logger.error(msg)
        logger.error("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
