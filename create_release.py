"""Create a release package for spellcard-generator."""
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
import subprocess
import sys


def get_version():
    """Extract version from generate.py."""
    generate_file = Path(__file__).parent / "generate.py"
    try:
        content = generate_file.read_text(encoding='utf-8')
        for line in content.split('\n'):
            if line.strip().startswith('VERSION'):
                version = line.split('=')[1].strip().strip("'\"")
                return version
    except Exception as e:
        print(f"Warning: Could not read VERSION from generate.py: {e}")
        return "1.0.0"


def create_release_package():
    """Create a release ZIP package with executable and documentation."""
    print("=" * 70)
    print("Creating Release Package for Spellcard Generator")
    print("=" * 70)
    
    script_dir = Path(__file__).parent.absolute()
    version = get_version()
    
    # Paths
    build_dir = script_dir / "build"
    exe_name = f"spellcard-generator_{version}.exe"
    exe_path = build_dir / exe_name
    
    # Release directory and ZIP name
    release_name = f"spellcard-generator-v{version}-windows"
    release_dir = script_dir / "release" / release_name
    zip_path = script_dir / "release" / f"{release_name}.zip"
    
    # Check if exe exists
    if not exe_path.exists():
        print(f"\n❌ ERROR: Executable not found: {exe_path}")
        print("\nPlease build the executable first:")
        print("  python build-pyinstaller.py")
        return False
    
    print(f"\n📦 Creating release package for version {version}")
    print(f"   Executable: {exe_path.name}")
    
    # Clean and create release directory
    if release_dir.exists():
        print(f"   Cleaning existing release directory...")
        shutil.rmtree(release_dir)
    release_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy executable
    print(f"   Copying executable...")
    shutil.copy2(exe_path, release_dir / exe_name)
    
    # Copy documentation files
    docs_to_include = [
        ("README.md", "README.md"),
        ("USAGE.md", "USAGE.md"),
        ("LICENSE", "LICENSE"),
    ]
    
    print(f"   Copying documentation...")
    for src_name, dst_name in docs_to_include:
        src_path = script_dir / src_name
        if src_path.exists():
            shutil.copy2(src_path, release_dir / dst_name)
            print(f"     ✓ {src_name}")
        else:
            print(f"     ⚠ {src_name} not found, skipping")
    
    # Copy example CSV if exists
    example_csv = script_dir / "Spells.csv"
    if example_csv.exists():
        print(f"   Copying example Spells.csv...")
        shutil.copy2(example_csv, release_dir / "Spells-example.csv")
    
    # Create a simple INSTALL.txt with quick start instructions
    install_txt = release_dir / "INSTALL.txt"
    install_content = f"""Spellcard Generator v{version} - Quick Start
{"=" * 70}

INSTALLATION:
1. Extract this ZIP file to any folder on your computer
2. Place your Spells.csv file in the same folder as the exe

USAGE:
1. Double-click {exe_name}
2. Find your generated cards in the 'out' folder
3. Open spell_cards.html in your web browser

For detailed instructions, see USAGE.md

REQUIREMENTS:
- Windows 10 or later
- A CSV file with spell data (see USAGE.md for format)

TROUBLESHOOTING:
- If your antivirus flags the exe, add it to your exceptions
  (This is a false positive - the file is safe)
- If the program closes immediately, make sure Spells.csv exists
- For detailed help, see USAGE.md

{"=" * 70}
Spellcard Generator - A tool for D&D players
Website: https://github.com/YourUsername/spellcard-generator
"""
    install_txt.write_text(install_content, encoding='utf-8')
    print(f"     ✓ INSTALL.txt")
    
    # Create ZIP file
    print(f"\n   Creating ZIP archive...")
    if zip_path.exists():
        zip_path.unlink()
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in release_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(release_dir.parent)
                zipf.write(file_path, arcname)
                print(f"     + {arcname}")
    
    # Get ZIP file size
    zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
    
    print("\n" + "=" * 70)
    print("✓ Release package created successfully!")
    print("=" * 70)
    print(f"\n📁 Release folder: {release_dir}")
    print(f"📦 ZIP file: {zip_path}")
    print(f"💾 ZIP size: {zip_size_mb:.2f} MB")
    
    print("\n" + "=" * 70)
    print("NEXT STEPS - Creating a GitHub Release:")
    print("=" * 70)
    print("\n1. Go to your GitHub repository")
    print("2. Click 'Releases' → 'Create a new release'")
    print(f"3. Tag version: v{version}")
    print(f"4. Release title: Spellcard Generator v{version}")
    print("5. Description: Add release notes (what's new, bug fixes, etc.)")
    print(f"6. Attach file: {zip_path.name}")
    print("7. Click 'Publish release'")
    
    print("\n" + "=" * 70)
    print("RELEASE CHECKLIST:")
    print("=" * 70)
    print(f"  [ ] Test the exe: {exe_name}")
    print(f"  [ ] Verify ZIP contents: {zip_path.name}")
    print("  [ ] Update CHANGELOG.md with version notes")
    print("  [ ] Create git tag: git tag -a v{} -m 'Release v{}'".format(version, version))
    print("  [ ] Push tag: git push origin v{}".format(version))
    print("  [ ] Create GitHub release")
    print(f"  [ ] Upload ZIP file: {zip_path.name}")
    print("  [ ] Verify download link works")
    
    return True


if __name__ == "__main__":
    success = create_release_package()
    sys.exit(0 if success else 1)
