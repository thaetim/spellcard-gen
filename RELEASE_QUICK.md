# Release Process - Quick Reference

## 🚀 Create a Release in 3 Steps

### Step 1: Build
```bash
python build-pyinstaller.py
```
Creates: `build/spellcard-generator_1.0.0.exe`

### Step 2: Package
```bash
python create_release.py
```
Creates: `release/spellcard-generator-v1.0.0-windows.zip`

### Step 3: Upload to GitHub
1. Go to: https://github.com/YourUsername/spellcard-generator/releases/new
2. Tag: `v1.0.0`
3. Title: `Spellcard Generator v1.0.0`
4. Upload: `release/spellcard-generator-v1.0.0-windows.zip`
5. Click **Publish release**

Done! ✅

---

## 📁 What's Included in the Release ZIP?

```
spellcard-generator-v1.0.0-windows/
├── spellcard-generator_1.0.0.exe    # Main executable
├── INSTALL.txt                       # Quick start guide
├── USAGE.md                          # Full user guide
├── README.md                         # Developer docs
├── LICENSE                           # License file
└── Spells-example.csv               # Example CSV file
```

---

## 📋 Pre-Release Checklist

Before creating a release:

- [ ] Update `VERSION = '1.0.0'` in `generate.py`
- [ ] Update `CHANGELOG.md` with release notes
- [ ] Test the executable thoroughly
- [ ] Run `python build-pyinstaller.py`
- [ ] Test the built executable
- [ ] Run `python create_release.py`
- [ ] Commit all changes
- [ ] Create git tag: `git tag -a v1.0.0 -m "Release v1.0.0"`
- [ ] Push tag: `git push origin v1.0.0`
- [ ] Create GitHub release
- [ ] Upload ZIP file
- [ ] Verify download works

---

## 📝 Release Description Template

```markdown
# Spellcard Generator v1.0.0

Generate beautiful, printable D&D spell cards from CSV data.

## Download

**Windows:** Download `spellcard-generator-v1.0.0-windows.zip` below

## Quick Start
1. Extract ZIP
2. See INSTALL.txt
3. Read USAGE.md for full guide

## What's New
- Initial release
- CSV validation
- Multiple card sizes
- Print-optimized output

See CHANGELOG.md for full details.
```

---

## 🔧 Scripts Reference

| Script | Purpose | Output |
|--------|---------|--------|
| `build-pyinstaller.py` | Compile to exe | `build/*.exe` |
| `build-nuitka.py` | Compile to exe (alternative) | `build/*.exe` |
| `create_release.py` | Package for release | `release/*.zip` |

---

## 🐛 Troubleshooting

**"Executable not found"**
```bash
# Build first
python build-pyinstaller.py
```

**"Version mismatch"**
```python
# Update VERSION in generate.py
VERSION = '1.0.0'
```

**"Tag already exists"**
```bash
# Delete and recreate
git tag -d v1.0.0
git push origin --delete v1.0.0
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

---

## 📚 Full Documentation

- **User Guide:** [USAGE.md](USAGE.md)
- **Release Guide:** [RELEASE_GUIDE.md](RELEASE_GUIDE.md)
- **Changelog:** [CHANGELOG.md](CHANGELOG.md)
- **Developer Docs:** [README.md](README.md)
