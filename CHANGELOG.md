# Changelog

All notable changes to Spellcard Generator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Nothing yet

### Changed
- Nothing yet

### Fixed
- Nothing yet

---

## [1.0.0] - 2024-12-07

### Added
- Initial release of Spellcard Generator
- Generate spell cards from CSV files with D&D spell data
- Support for multiple card sizes (single, double, triple-wide)
- Automatic card layout optimization for printing
- CSV validation with detailed error messages
- Support for all standard D&D spell fields:
  - Name, Level, School, Casting Time, Range, Components, Duration, Text
  - Optional: Source, Page, Classes, Subclasses, At Higher Levels
- Three execution modes:
  - Normal mode: Run once, wait for user input
  - Loop mode (`--loop`): Press ENTER to regenerate, ESC to exit
  - Dev mode (`--dev`): Run once and exit immediately
- Drag-and-drop support for CSV files
- Output files generated in `out/` subdirectory
- Print-optimized HTML output with embedded CSS and JavaScript
- Comprehensive documentation (USAGE.md, RELEASE_GUIDE.md)
- Automated release packaging script (`create_release.py`)

### Technical
- Built with Python 3.12
- Uses PyInstaller for Windows executable compilation
- Dependencies: pandas, watchdog, keyboard
- CSV validation checks:
  - Required columns presence
  - UTF-8 encoding
  - Proper quoting for fields with newlines/commas
  - Valid level values (Cantrip, 1st-9th, or plain numbers)
  - Column count consistency

### Known Issues
- Some antivirus software (e.g., ESET) may flag the executable as suspicious (false positive)
  - Workaround: Add executable to antivirus exceptions
- Very long spell descriptions may need manual adjustment for optimal display

---

## Release Notes Template

When creating a new release, copy this template:

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New features go here

### Changed
- Changes to existing functionality

### Deprecated
- Features that will be removed in future versions

### Removed
- Features that were removed

### Fixed
- Bug fixes

### Security
- Security-related changes
```

---

## Version History

- **1.0.0** (2024-12-07) - Initial release

[Unreleased]: https://github.com/YourUsername/spellcard-generator/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/YourUsername/spellcard-generator/releases/tag/v1.0.0
