# PARSE_NOTES

The canonical Autodesk PDF URL in the issue (`damassets.autodesk.net`) was unreachable from this sandbox (DNS resolution failure), so extraction used best-effort parsed shortcut-guide content from accessible sources.

Entries needing manual verification against the official Autodesk PDF:

- `PROPERTIES` command alias appears as `CH` in parsed content, while other datasets often use `PR`.
- One parsed source mixed platform hints in function-key rows (for example, `F10 or CMD+U`); only the Windows-style shortcut was retained.
- OCR-like fragments in one source had row boundary ambiguity (examples: `R / SHADEMODE`, and merged lines around `SCRIPT`, `DSETTINGS`, and `SECTION`).
- Validate whether any missing aliases from the official PDF should be added for full parity.

All AutoCAD entries merged in this update are marked with `source: "autodesk-shortcut-guide-2024"` to make later reconciliation straightforward.
