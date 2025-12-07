# GitHub Release Guide

Step-by-step instructions for creating releases on GitHub.

## Quick Release Process

### 1. Build the Executable

```bash
# Build with PyInstaller (recommended)
python build-pyinstaller.py

# Or build with Nuitka (if you prefer)
python build-nuitka.py
```

This creates: `build/spellcard-generator_1.0.0.exe`

### 2. Create Release Package

```bash
python create_release.py
```

This automatically:
- ✅ Extracts version from `generate.py`
- ✅ Creates a release folder with all necessary files
- ✅ Copies the executable, documentation, and examples
- ✅ Creates a ZIP file ready for upload
- ✅ Shows you exactly what to do next

Output: `release/spellcard-generator-v1.0.0-windows.zip`

### 3. Create GitHub Release

**Option A: Via GitHub Web Interface (Easiest)**

1. Go to your repository on GitHub
2. Click **"Releases"** (right sidebar)
3. Click **"Draft a new release"**
4. Fill in the form:
   - **Tag:** `v1.0.0` (create new tag)
   - **Target:** `main` branch
   - **Title:** `Spellcard Generator v1.0.0`
   - **Description:** See template below
5. **Attach files:** Drag and drop the ZIP file
6. Click **"Publish release"**

**Option B: Via GitHub CLI (Advanced)**

```bash
# Install GitHub CLI first: https://cli.github.com/

# Create release with file
gh release create v1.0.0 \
  release/spellcard-generator-v1.0.0-windows.zip \
  --title "Spellcard Generator v1.0.0" \
  --notes "See CHANGELOG.md for details"
```

---

## Release Description Template

Copy this template when creating your release:

```markdown
# Spellcard Generator v1.0.0

Generate beautiful, printable D&D spell cards from CSV data.

## 🎯 What's New

- Initial release
- Generate spell cards from CSV files
- Support for all D&D spell fields (Name, Level, School, etc.)
- CSV validation with helpful error messages
- Multiple card sizes (single, double, triple-wide)
- Print-optimized HTML output

## 📥 Download

**Windows Users:**
1. Download `spellcard-generator-v1.0.0-windows.zip`
2. Extract the ZIP file
3. See `INSTALL.txt` for quick start
4. Read `USAGE.md` for detailed instructions

**Mac/Linux Users:**
- See [README.md](https://github.com/YourUsername/spellcard-generator) for running from source

## 🚀 Quick Start

1. Place your `Spells.csv` file next to the exe
2. Double-click `spellcard-generator_1.0.0.exe`
3. Open `out/spell_cards.html` in your browser
4. Print your cards!

## 📋 Requirements

- Windows 10 or later
- A CSV file with spell data (format described in USAGE.md)

## 🐛 Known Issues

- Some antivirus software may flag the exe as suspicious (false positive)
  - Add to exceptions if needed
  - The file is safe - built with PyInstaller

## 📚 Documentation

- **Quick Start:** See `INSTALL.txt` in the ZIP
- **Full Guide:** See `USAGE.md` in the ZIP
- **Development:** See [README.md](https://github.com/YourUsername/spellcard-generator)

## 💬 Support

Having issues? [Open an issue](https://github.com/YourUsername/spellcard-generator/issues)

---

**Full Changelog:** [CHANGELOG.md](https://github.com/YourUsername/spellcard-generator/blob/main/CHANGELOG.md)
```

---

## Detailed Release Process

### Step 1: Prepare Your Code

```bash
# Make sure everything is committed
git status

# Run tests (if you have any)
python -m pytest

# Update version in generate.py
# VERSION = '1.0.0'  # Update this

# Update CHANGELOG.md with release notes
```

### Step 2: Build and Package

```bash
# Build the executable
python build-pyinstaller.py

# Test the exe manually
cd build
.\spellcard-generator_1.0.0.exe

# If it works, create release package
cd ..
python create_release.py
```

### Step 3: Create Git Tag

```bash
# Create annotated tag
git tag -a v1.0.0 -m "Release version 1.0.0"

# Push the tag to GitHub
git push origin v1.0.0

# Or push all tags
git push --tags
```

### Step 4: Create GitHub Release

1. **Navigate to Releases**
   - Go to: `https://github.com/YourUsername/spellcard-generator/releases`
   - Click: **"Draft a new release"**

2. **Choose Tag**
   - Select existing tag: `v1.0.0`
   - Or create new tag: Type `v1.0.0` and select "Create new tag"

3. **Release Title**
   ```
   Spellcard Generator v1.0.0
   ```

4. **Description**
   - Use the template above
   - Customize "What's New" section
   - Update links to match your repository

5. **Upload Files**
   - Click "Attach binaries"
   - Upload: `release/spellcard-generator-v1.0.0-windows.zip`
   - GitHub will show file size and checksum

6. **Release Options**
   - ☐ Set as pre-release (for beta versions)
   - ☐ Set as latest release (usually checked)
   - ☐ Create discussion for this release

7. **Publish**
   - Click **"Publish release"**
   - Your release is now live!

### Step 5: Verify Release

After publishing:

1. **Check the release page**
   - Does it look good?
   - Are all links working?

2. **Download the ZIP**
   - Download as a user would
   - Extract and test the exe
   - Make sure all files are included

3. **Test on a clean machine** (if possible)
   - Copy ZIP to a different computer
   - Extract and run
   - Verify it works without dependencies

---

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):

```
MAJOR.MINOR.PATCH

1.0.0 → First stable release
1.1.0 → New features (backward compatible)
1.1.1 → Bug fixes only
2.0.0 → Breaking changes
```

**Examples:**
- `v1.0.0` - Initial release
- `v1.1.0` - Added loop mode, CSV validation
- `v1.1.1` - Fixed antivirus false positive
- `v2.0.0` - Changed CSV format (breaking change)

---

## Pre-Releases / Beta Versions

For testing before official release:

```bash
# Tag as pre-release
git tag -a v1.1.0-beta.1 -m "Beta release"
git push origin v1.1.0-beta.1
```

On GitHub:
- Tag: `v1.1.0-beta.1`
- Title: `v1.1.0 Beta 1`
- ✅ Check **"Set as a pre-release"**
- Description: Note it's a beta and what's being tested

---

## Multiple Platform Releases

If you support multiple platforms:

```
Release files:
- spellcard-generator-v1.0.0-windows.zip
- spellcard-generator-v1.0.0-macos.zip
- spellcard-generator-v1.0.0-linux.tar.gz
- spellcard-generator-v1.0.0-source.zip
```

Upload all files to the same release.

---

## Automating with GitHub Actions

Create `.github/workflows/release.yml`:

```yaml
name: Create Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pyinstaller
      
      - name: Build with PyInstaller
        run: python build-pyinstaller.py
      
      - name: Create release package
        run: python create_release.py
      
      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: release/*.zip
          draft: false
          prerelease: false
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

Now releases are automatic when you push a tag:
```bash
git tag v1.0.0
git push origin v1.0.0
# GitHub Actions automatically builds and creates release
```

---

## Best Practices

### Before Every Release

- [ ] Update `VERSION` in `generate.py`
- [ ] Update `CHANGELOG.md`
- [ ] Test the executable thoroughly
- [ ] Check all documentation is current
- [ ] Verify links in README.md
- [ ] Build and test the release package
- [ ] Create git tag
- [ ] Write good release notes

### Release Notes Should Include

- **What's new** - New features
- **Bug fixes** - What was broken and is now fixed
- **Breaking changes** - Things that might break existing usage
- **Known issues** - Problems users should be aware of
- **Installation** - How to install/upgrade
- **Thanks** - Credit contributors

### Security

- **Scan for malware** before releasing
- **Sign executables** if possible (reduces false positives)
- **Include checksums** for verification
- **Document security practices** in README

---

## Troubleshooting

### "Tag already exists"

```bash
# Delete local tag
git tag -d v1.0.0

# Delete remote tag
git push origin --delete v1.0.0

# Create new tag
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

### "Release not showing up"

- Tags must be pushed: `git push --tags`
- Check you're on the right branch
- Refresh the releases page

### "ZIP file too large"

GitHub has a 2GB limit per file. If your ZIP is too large:
- Remove unnecessary files
- Compress more aggressively
- Split into multiple files
- Use external hosting for large files

---

## Useful Commands

```bash
# List all tags
git tag -l

# Show tag details
git show v1.0.0

# Delete local tag
git tag -d v1.0.0

# Delete remote tag
git push origin --delete v1.0.0

# Push specific tag
git push origin v1.0.0

# Push all tags
git push --tags

# Checkout specific version
git checkout v1.0.0
```

---

## Additional Resources

- [GitHub Releases Documentation](https://docs.github.com/en/repositories/releasing-projects-on-github)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [GitHub CLI Releases](https://cli.github.com/manual/gh_release)
