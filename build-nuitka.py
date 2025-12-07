"""Build script for compiling spellcard-generator to EXE with Nuitka."""
import subprocess
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path


def run_command(cmd, check=True, logger=None):
    """Run a command and capture all output to both console and log."""
    cmd_str = ' '.join(str(c) for c in cmd)
    print(f"\n>>> {cmd_str}\n")
    if logger:
        logger.info(f"Running command: {cmd_str}")

    # Run command and capture output in real-time
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1,
        encoding='utf-8',
        errors='replace'
    )

    # Stream output to both console and log in real-time
    for line in process.stdout:
        # Print to console immediately
        print(line, end='')
        # Log to file
        if logger:
            logger.info(line.rstrip())

    # Wait for process to complete
    returncode = process.wait()

    if logger:
        logger.info(f"Command returned: {returncode}")

    # If check=True and command failed, raise exception (matching subprocess.run behavior)
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
    log_file = log_dir / "latest.log"

    # Configure logging
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
    logger.info("Build script started")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    return logger


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Build spellcard-generator with Nuitka')
    parser.add_argument('--no-lto', action='store_true',
                        help='Build without Link-Time Optimization (may reduce AV false positives)')
    args = parser.parse_args()

    # Ensure we're using Python from .venv312
    script_dir = Path(__file__).parent.absolute()

    # Set up logging
    logger = setup_logging(script_dir)
    venv312_python = script_dir / ".venv312" / "Scripts" / "python.exe"

    if venv312_python.exists():
        # Use venv312 Python explicitly
        python_exe = str(venv312_python)
        if sys.executable != python_exe:
            msg = f"⚠ Using venv312 Python: {python_exe} (Current: {sys.executable})"
            print(msg)
            logger.info(msg)
    else:
        # Fallback to sys.executable if venv312 not found
        python_exe = sys.executable
        msg = f"⚠ Warning: .venv312 not found, using: {python_exe} (Expected: {venv312_python})"
        print(msg)
        logger.warning(msg)

    # Check if nuitka is installed
    try:
        subprocess.run([python_exe, "-m", "nuitka", "--version"],
                       capture_output=True, check=True)
        msg = "✓ Nuitka is installed"
        print(msg)
        logger.info(msg)
    except subprocess.CalledProcessError:
        msg = "Installing Nuitka..."
        print(msg)
        logger.info(msg)
        if not run_command([python_exe, "-m", "pip", "install", "nuitka"], logger=logger):
            msg = "Failed to install Nuitka"
            print(msg)
            logger.error(msg)
            return 1

    # Install/upgrade project dependencies
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
    output_dir.mkdir(exist_ok=True)

    # Get version from generate.py
    try:
        # Read VERSION from generate.py
        generate_content = (
            script_dir / "generate.py").read_text(encoding='utf-8')
        for line in generate_content.split('\n'):
            if line.strip().startswith('VERSION'):
                # Extract version value: VERSION = '1.0.0'
                version = line.split('=')[1].strip().strip("'\"")
                break
        else:
            version = '1.0.0'  # Default if not found
            logger.warning(
                "VERSION not found in generate.py, using default: 1.0.0")
    except Exception as e:
        version = '1.0.0'  # Default on error
        logger.warning(
            f"Could not read VERSION from generate.py: {e}, using default: 1.0.0")

    exe_filename = f"spellcard-generator_{version}.exe"

    # Nuitka compile command
    nuitka_cmd = [
        python_exe, "-m", "nuitka",

        # Basic options
        "--standalone",                    # Create standalone distribution
        "--onefile",                       # Single executable file
        "--assume-yes-for-downloads",      # Auto-download dependencies
        "--mingw64",                       # Use MinGW64 (Nuitka downloads it)

        # Output
        f"--output-dir={output_dir}",
        f"--output-filename={exe_filename}",

        # Include data files (must use absolute paths)
        f"--include-data-dir={script_dir / 'templates'}=templates",
        f"--include-data-dir={script_dir / 'data'}=data",
        f"--include-data-dir={script_dir / 'assets'}=assets",

        # Include all project modules
        "--include-module=card_generator",
        "--include-module=spell_processing",
        "--include-module=text_formatting",
        "--include-module=spell_styling",
        "--include-module=text_splitting",
    ]

    # Conditionally include packages if they're installed
    # (Nuitka will auto-detect most, but explicit includes ensure full package inclusion)
    packages_to_check = ["pandas", "watchdog"]
    for package in packages_to_check:
        if is_package_installed(package, python_exe):
            nuitka_cmd.append(f"--include-package={package}")
        else:
            msg = f"Warning: {package} not found, skipping explicit include"
            print(msg)
            logger.warning(msg)

    # Add Windows options
    nuitka_cmd.extend([
        # Windows options
        "--windows-console-mode=force",    # Keep console window

        # Additional options to help with resource embedding
        "--show-progress",                 # Show build progress
        "--remove-output",                 # Clean previous build artifacts
    ])

    # Add optimization (LTO can sometimes trigger AV false positives)
    if not args.no_lto:
        nuitka_cmd.append("--lto=yes")
    else:
        msg = "Building without LTO (Link-Time Optimization) to reduce AV false positives"
        print(msg)
        logger.info(msg)

    # Add main script
    nuitka_cmd.append(script)

    # Get Nuitka cache directory (common location)
    nuitka_cache = Path.home() / "AppData" / "Local" / "Nuitka" / "Nuitka" / "Cache"
    nuitka_gcc_dir = Path.home() / "AppData" / "Local" / "Nuitka" / \
        "Nuitka" / "Cache" / "downloads" / "gcc"

    msg = "Building spellcard-generator.exe with Nuitka"
    print("=" * 60)
    print(msg)
    print("=" * 60)
    logger.info("=" * 60)
    logger.info(msg)
    logger.info("=" * 60)
    eset_warning = "⚠ WAŻNE - ESET ANTIVIRUS - Konfiguracja wykluczeń"
    print("\n" + "=" * 60)
    print(eset_warning)
    print("=" * 60)
    logger.info("=" * 60)
    logger.info(eset_warning)
    logger.info("=" * 60)
    eset_info = "ESET blokuje linker (ld.exe) podczas kompilacji. To jest FAŁSZYWY ALARM - pliki Nuitka są bezpieczne."
    print("\nESET blokuje linker (ld.exe) podczas kompilacji.")
    print("To jest FAŁSZYWY ALARM - pliki Nuitka są bezpieczne.\n")
    logger.info(eset_info)
    print("KROK 1: Dodaj wykluczenia w ESET:")
    print("  1. Otwórz ESET (kliknij prawym na ikonę w zasobniku)")
    print("  2. Naciśnij F5 lub: Ustawienia → Ochrona komputera → Wykluczenia")
    print("  3. Kliknij 'Dodaj' i dodaj WSZYSTKIE poniższe:\n")
    print("  FOLDERY (ścieżki bezwzględne):")
    print(f"    • {output_dir}")
    print(f"    • {nuitka_cache}")
    print(f"    • {script_dir}")
    print("\n  PROCESY (ścieżki do plików .exe):")
    print(f"    • {python_exe}")
    print("    • C:\\Users\\M\\AppData\\Local\\Nuitka\\Nuitka\\Cache\\downloads\\gcc\\**\\ld.exe")
    print("    • C:\\Users\\M\\AppData\\Local\\Nuitka\\Nuitka\\Cache\\downloads\\gcc\\**\\gcc.exe")
    print("\n  WZORCE PLIKÓW:")
    print("    • *.dll (w folderze build)")
    print("    • *.exe (w folderze build)")
    print("    • generate.dll")
    print("\nKROK 2: TYMCZASOWO wyłącz ochronę w czasie rzeczywistym:")
    print("  Ustawienia → Ochrona komputera → Ochrona systemu plików")
    print("  → Tymczasowo wyłącz (tylko na czas kompilacji)")
    print("\nKROK 3: Wyczyść folder build i spróbuj ponownie:")
    print(f"  rmdir /s /q {output_dir}")
    print("\n" + "=" * 60)

    if run_command(nuitka_cmd, logger=logger):
        exe_path = output_dir / exe_filename
        msg = f"✓ Build successful! Executable: {exe_path}"
        print("\n" + "=" * 60)
        print("✓ Build successful!")
        print(f"Executable: {exe_path}")
        print("=" * 60)
        logger.info("=" * 60)
        logger.info(msg)
        logger.info("=" * 60)
        return 0
    else:
        msg = "✗ KOMPILACJA NIEUDANA - ESET zablokował plik"
        print("\n" + "=" * 60)
        print(msg)
        print("=" * 60)
        logger.error("=" * 60)
        logger.error(msg)
        logger.error("=" * 60)
        error_msg = "ESET wykrył plik jako podejrzany (Python/Packed.Nuitka_AGen.CL). To jest FAŁSZYWY ALARM - aplikacje Nuitka są bezpieczne."
        print("\nESET wykrył plik jako podejrzany (Python/Packed.Nuitka_AGen.CL)")
        print("To jest FAŁSZYWY ALARM - aplikacje Nuitka są bezpieczne.\n")
        logger.error(error_msg)
        print("ROZWIĄZANIE - Dodaj wykluczenia w ESET:")
        print("\n1. Otwórz ESET (prawy klik na ikonę w zasobniku)")
        print("2. Naciśnij F5 lub: Ustawienia → Ochrona komputera → Wykluczenia")
        print("3. Kliknij 'Dodaj' i dodaj:\n")
        print("FOLDERY:")
        print(f"  • {output_dir}")
        nuitka_cache = Path.home() / "AppData" / "Local" / "Nuitka" / "Nuitka" / "Cache"
        if nuitka_cache.exists():
            print(f"  • {nuitka_cache}")
        print(f"  • {script_dir}")
        print("\nPROCESY (ścieżki do .exe):")
        print(f"  • {python_exe}")
        print("  • C:\\Users\\M\\AppData\\Local\\Nuitka\\**\\ld.exe")
        print("  • C:\\Users\\M\\AppData\\Local\\Nuitka\\**\\gcc.exe")
        print("\nWZORCE:")
        print("  • *.dll (w folderze build)")
        print("  • generate.dll")
        print("\nLUB tymczasowo wyłącz ochronę w czasie rzeczywistym:")
        print("  Ustawienia → Ochrona komputera → Ochrona systemu plików")
        print("  → Tymczasowo wyłącz (tylko na czas kompilacji)")
        print("\nPo dodaniu wykluczeń, wyczyść i spróbuj ponownie:")
        print(f"  rmdir /s /q {output_dir}")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
