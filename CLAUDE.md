# CLAUDE.md

## Repository Overview

This is a documentation and scripts repository maintained by davidnudelman. It serves as a collection of technical guides, tips, and utility scripts primarily focused on Windows systems administration.

## Structure

```
scripts/
├── README.md        # Repository introduction
├── CLAUDE.md        # This file - AI assistant guidance
└── map_printer      # Guide: mapping printers on Windows machines
```

## Content Conventions

- Files are plain text or Markdown documentation containing technical procedures and command examples.
- Scripts and commands documented here target **Windows environments** (PowerShell, DOS/batch).
- No executable source code, build systems, or dependency managers are present.
- No testing framework is configured.

## File Format Guidelines

- Use Markdown (`.md`) for new documentation files when formatting (headers, lists, code blocks) adds clarity.
- Use plain text for concise, single-topic reference notes (consistent with existing files like `map_printer`).
- Embed command examples inline within documentation rather than creating separate script files, unless the script is intended to be run directly.

## Git Workflow

- **Primary branch**: `master`
- Commit messages should be short and descriptive (e.g., "Create map_printer", "Update README.md").
- All commits so far have been authored by davidnudelman.

## Key Topics Covered

- Windows printer mapping (Group Policy, PowerShell WMI, DOS `net use`)
- Windows driver compatibility notes (V4 drivers, Windows 10 specifics)

## Notes for AI Assistants

- This is a small, documentation-only repository. There is no code to build, test, or lint.
- When adding new content, match the existing style: concise, practical, and focused on actionable steps.
- Preserve platform-specific details and version caveats (e.g., Windows 10 vs earlier versions).
