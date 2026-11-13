# Changelog

## [0.2.0] — 2026-11-13

### Breaking

- Tool names no longer contain a dot: `legal.clause_tree` → `legal_clause_tree`, and the same for the other six (`legal_playbook`, `legal_playbook_register`, `legal_playbook_check`, `legal_export_tree`, `legal_clause_integrity`, `legal_coverage_check`). Providers validate the `tools[].name` field against `^[a-zA-Z0-9_-]+$`; the dotted names invalidated the whole `tools` array, so the plugin registered but every request carrying its tools was rejected with `Invalid 'tools[N].name'`. Minor bump because tool names are part of the 0.1.0 compatibility promise — update prompts, saved calls and permission rules that still say `legal.*`. Fixes #9.
- `test/tool-name-wire.test.mjs` pins the wire pattern so a new tool cannot reintroduce a dot.

## [0.1.0] — 2026-11-03

### Stable

- First non-alpha release: tool names and the CLI surface are covered by a
  compatibility promise (breaking changes require a minor bump).
- Ships a quickstart sample, a one-line prompt, a permission block and real captures.

## [0.1.0] — 2026-11-01

### Security / Fixes

- Path-traversal guard, bounded clause-number gap detection (a huge clause number no longer expands millions of issues).


### Added

- `legal_coverage_check`: coverage against the 12-key playbook — mapped keys, missing keys and the coverage ratio. Read-only; it does not judge clause quality. Verified by `node --test test/*.test.mjs` (11/11).

## [Unreleased]

### Added

- `legal_clause_integrity`: contract numbering QA — duplicate clause numbers, missing top-level numbers and out-of-order numbering, with stable issue codes. Read-only. Verified by `node --test test/*.test.mjs` (8/8).

## [0.1.0-alpha.8] — 2026-11-01

### Changed

- Documentation: five-language fixture/acceptance links now resolve on npm; added specific related-checker/tool links.
- Marketplace metadata: taxonomy category, archetype, domains and status; docs page now shows the same.
- Added a real terminal hero (and GIF for the active docs set) plus `TROUBLESHOOTING.md`.

All notable changes to `dsh-legal-clause` are documented here. The format follows Keep a Changelog; this project uses alpha versions.

## [0.1.0-alpha.7] — 2026-11-01

### Added

- Five-language READMEs: English, 简体中文, Español, Português, हिन्दी.
- Local workflow SVG at `docs/assets/dsh-legal-clause-flow.svg`.
- Family cross-links (domain index, checker family, `dsh-kit`), compatibility, permissions, and related-work sections.
- Standard repository files: `SECURITY.md`, `PRIVACY.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, and `icon.svg`.

### Changed

- README aligned with the PerryLink DSH checker/plugin family style; package remains public/synthetic, alpha, not GA.

## [Earlier]

Earlier alpha builds are available from npm and GitHub Releases; this file starts at the family-standard documentation wave.
