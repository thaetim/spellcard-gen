"""Build script for compiling spellcard-generator to EXE with Nuitka."""
import subprocess
import sys
from pathlib import Path


def run_command(cmd, check=True):
    """Run a command and print output."""
    print(f"\n>>> {' '.join(str(c) for c in cmd)}\n")
    result = subprocess.run(cmd, check=check)
    return result.returncode == 0


def is_package_installed(package_name):
    """Check if a package is installed."""
    try:
        subprocess.run([sys.executable, "-m", "pip", "show", package_name],
                       capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def main():
    # Check if nuitka is installed
    try:
        subprocess.run([sys.executable, "-m", "nuitka", "--version"],
                       capture_output=True, check=True)
        print("✓ Nuitka is installed")
    except subprocess.CalledProcessError:
        print("Installing Nuitka...")
        if not run_command([sys.executable, "-m", "pip", "install", "nuitka"]):
            print("Failed to install Nuitka")
            return 1

    # Install/upgrade project dependencies
    script_dir = Path(__file__).parent.absolute()
    requirements_file = script_dir / "requirements.txt"
    if requirements_file.exists():
        print("Installing project dependencies...")
        if not run_command([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]):
            print("Failed to install dependencies")
            return 1
        print("✓ Dependencies installed")

    # Build configuration
    script_dir = Path(__file__).parent.absolute()
    script = script_dir / "generate.py"
    output_dir = script_dir / "build"
    output_dir.mkdir(exist_ok=True)

    # Nuitka compile command
    nuitka_cmd = [
        sys.executable, "-m", "nuitka",

        # Basic options
        "--standalone",                    # Create standalone distribution
        "--onefile",                       # Single executable file
        "--assume-yes-for-downloads",      # Auto-download dependencies
        "--mingw64",                       # Use MinGW64 (Nuitka downloads it)

        # Output
        f"--output-dir={output_dir}",
        "--output-filename=spellcard-generator.exe",

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
        if is_package_installed(package):
            nuitka_cmd.append(f"--include-package={package}")
        else:
            print(f"Warning: {package} not found, skipping explicit include")

    # Add Windows options
    nuitka_cmd.extend([
        # Windows options
        "--windows-console-mode=force",    # Keep console window

        # Optimization
        "--lto=yes",                       # Link-time optimization

        # Additional options to help with resource embedding
        "--show-progress",                 # Show build progress
        "--remove-output",                 # Clean previous build artifacts

        # Main script
        script
    ])

    print("=" * 60)
    print("Building spellcard-generator.exe with Nuitka")
    print("=" * 60)
    print("\n⚠ NOTE: If build fails at 'Failed to add resources', try:")
    print("   1. Add build folder to Windows Defender exclusions")
    print("   2. Temporarily disable antivirus")
    print("   3. The build folder is:", output_dir)
    print("=" * 60)

    if run_command(nuitka_cmd):
        print("\n" + "=" * 60)
        print("✓ Build successful!")
        print(f"Executable: {output_dir / 'spellcard-generator.exe'}")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print("✗ Build failed")
        print("\nTroubleshooting tips:")
        print("1. Add the build folder to Windows Defender exclusions:")
        print(f"   {output_dir}")
        print("2. Try temporarily disabling antivirus during build")
        print("3. Check if the DLL file exists and is not locked:")
        print(f"   {output_dir / 'generate.dist' / 'generate.dll'}")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())

# TODO # DEV
# FATAL: Sorry, non-MSVC is not currently supported with Python 3.13,
# due to differences in layout internal structures of Python.

# Newer Nuitka will work to solve this. Use Python 3.12 or
# option "--msvc=latest" as a workaround for now and wait
# for updates of Nuitka to add MinGW64 support back.
# FATAL: Failed unexpectedly in Scons C backend compilation.
# Nuitka:WARNING:     Complex topic! More information can be found at https://nuitka.net/info/scons-backend-failure.html
# Nuitka-Reports: Compilation crash report written to file 'nuitka-crash-report.xml'
