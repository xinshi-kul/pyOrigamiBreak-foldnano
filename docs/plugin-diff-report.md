# pyOrigamiBreak Plugin Diff Report

Written on 2026-04-16, when the plugin was still uncommitted work on top of the original code.
Re-checked on 2026-11-02 against plugin version 1.0.5: the line counts, the hashes of the
unchanged files and the options `plugin.py` fixes still match, and the plugin code has not changed
since. The analysis below is kept as written; only the paths and commands were updated.

- Reference source: `autobreak/` on `main` (the upstream command-line version)
- Plugin source: `autobreak/` on `foldnano_plugin`
- Plugin zip: packed from `autobreak/` by the
  [foldnano-plugins](https://github.com/XinShiLab/foldnano-plugins) pack script, and listed there

## Executive Summary

The plugin is not a byte-for-byte copy of the original pyOrigamiBreak package. The thermodynamic helper/data files are identical, and the main optimization flow is structurally preserved. The differences are concentrated in the I/O layer, progress display, plugin entry point, in-memory cadnano JSON loading/writing, and result artifact generation.

The core break-search/scoring classes and methods inside `autobreak.py` appear preserved except where disk output was replaced with in-memory CSV/PNG/JSON buffers. The highest parity risks are:

1. The plugin uses `cadnano.fileio.v2decode.decode()` / `v2encode.encodeDocument()` for in-memory JSON, while the original uses `Document.readFile()` / `doc.writeToFile()`.
2. The plugin removes several original side outputs: Excel workbook, cn2svg heatmap SVG, composite report SVG, copied input files, sequence files, and zipped run directory.
3. The plugin accepts literal DNA sequence strings in `sequence_file`; the original accepts filesystem paths.
4. The plugin adapter exposes only a subset of original CLI options.
5. The plugin always writes the final staple table to `results.csv`; original CSV output depends on `-csv` and also writes a separate summary CSV.

Syntax check passed for all Python files:

```bash
python3 -m py_compile autobreak/*.py
```

## File-Level Comparison

`git diff main foldnano_plugin -- autobreak/`:

```text
Only on main: autobreak/__init__.py  (not included in plugin)
autobreak/autobreak.py differs
Only on main: autobreak/exportoligos.py  (not included in plugin)
autobreak/origamidesign.py differs
Only on foldnano_plugin: autobreak/plugin.py  (plugin entry point)
Only on foldnano_plugin: autobreak/fplugin.json, LICENSE, NOTICE  (plugin manifest and notices)
```

Line counts:

```text
2640 autobreak/autobreak.py  (main, original CLI)
2517 autobreak/autobreak.py  (foldnano_plugin, plugin)
1946 autobreak/origamidesign.py  (main, original CLI)
1949 autobreak/origamidesign.py  (foldnano_plugin, plugin)
```

The following files are identical by SHA-256:

| File | SHA-256 |
| --- | --- |
| `utilities.py` | `c8502321085921174dfd0bf075a7f34a602c23b287c6bb5cd01a1a14c173a833` |
| `validate.py` | `4f84efb8859ee26f0a5d5b6b185742db5d82a04bb2197c00a7c02aec70fca4e9` |
| `scaffolds.py` | `2e1e47056b43b822bfb111399c3a284e4400cdf1c30f51df3f2893386908faac` |

## `autobreak.py` Differences

### Imports and Runtime Environment

Reference imports filesystem/reporting dependencies:

- `glob`
- `copyfile`
- `openpyxl`
- `svgutils`
- `cn2svg`
- package imports from `autobreak import ...`

Plugin changes:

- Uses `io` buffers.
- Forces matplotlib `Agg`.
- Imports `cadnano.fileio.v2encode.encodeDocument`.
- Uses flat imports: `import origamidesign, scaffolds, utilities`.

Assessment: intentional plugin/Pyodide adaptation. It should not alter optimization logic directly.

### Result Export Changes

Reference behavior:

- `OligoBreakSolution.export_staples()` appends Excel sheets.
- `AutoBreak.write_results_summary()` writes Excel `Summary`.
- `AutoBreak.write_results()` and `write_best_result()` write workbook sheets.
- `create_results_excel_file()` creates workbook.
- `export_initial_scores()` writes Excel `Summary` and `Final`, applies heatmap formatting, and conditionally writes `*_autobreak.csv` and `*_summary.csv`.

Plugin behavior:

- `export_staples()` writes CSV to a path or file-like object.
- `write_results_summary()` writes CSV into `_csv_buf`.
- `write_results()` / `write_best_result()` / `create_results_excel_file()` are no-ops.
- `export_initial_scores()` always writes sorted staple rows to `_csv_buf`.

Assessment: output format changed substantially, but the staple row generation is the same call path: `oligo.end_to_end_edge.get_csv_row_object()`.

Parity risk: compare normalized CSV tables, not Excel files. The plugin does not emit the original summary CSV as a separate artifact.

### Filesystem and Report Generation

Reference behavior:

- Creates `{name}_autobreak_0001/{inputs,intermediates,outputs}`.
- Copies input JSON and sequence file.
- Writes args text file.
- Generates cn2svg heatmap SVG.
- Generates matplotlib SVG/PNG plots from the Excel workbook.
- Composes a final report SVG with `svgutils`.
- Zips the result folder.

Plugin behavior:

- `set_output_directory()` stores a design name and output counter only.
- `copy_sequence_file()`, `write_input_args()`, `create_staple_heatmap()`, `create_summary_figure()`, and `zip_results()` are no-ops.
- `define_output_files()` initializes `_csv_buf`, `_plots_buf`, and `_result_json`.
- `create_results_plots()` reads the in-memory `staples_frame` and writes a PNG buffer.

Assessment: intentional plugin adaptation. These removed outputs cannot be parity-tested unless recreated by a harness.

### Cadnano JSON Writing

Reference:

```python
self.origami.doc.writeToFile(self.json_legacy_output, legacy=True)
```

Plugin:

```python
self._result_json = _encodeDocument(self.origami.doc)
```

Assessment: this is a real equivalence boundary. Even if the model state is identical, JSON key ordering, optional fields, colors, or legacy formatting can differ.

Recommended comparison: normalize cadnano JSON into semantic topology/color/sequence structures before comparing.

### `run_plugin()`

The plugin adds `run_plugin(json_dict, args, ctx=None)`. Its main control flow mirrors the reference `run()`:

1. Parse parameters.
2. Seed Python `random`.
3. Create `Origami` and `AutoBreak`.
4. Configure break rules, scoring, min/max lengths, readonly flag.
5. Load design.
6. Prepare/validate origami.
7. Run readonly scoring or autobreak.
8. Determine scores and export rows.
9. Split scaffold, set sequence offset, encode final JSON.
10. Return `{cadnano_json, csv, plots_png, summary}`.

Known intentional divergence:

- `set_write_all_results(False)` is hard-coded, so plugin ignores `args.writeall`.
- Output is returned through plugin artifacts instead of a zipped directory.

## `origamidesign.py` Differences

### Progress Display

Reference uses `fastprogress.master_bar` and `mb.write()`.

Plugin uses plain `range()` and `print()`.

Assessment: presentation-only; optimization loop order is unchanged.

### In-Memory JSON Loading

Plugin adds:

```python
def initialize_from_dict(self, json_dict):
    app = cadnano.app()
    self.doc = app.document = Document()
    self.json_input = json_dict.get('name', 'design') + '.json'
    _v2decode(self.doc, json_dict)
    self.part = self.doc.activePart()
```

Assessment: equivalent only if `Document.readFile()` and `_v2decode()` produce the same cadnano model state. This should be explicitly tested.

### Sequence Input

Reference:

- Known sequence name.
- Existing filesystem path.
- `allT`, `allA`, `allC`, random fallback.

Plugin:

- Known sequence name.
- Literal DNA string of `ACGTacgt` with length > 4.
- `allT`, `allA`, `allC`, random fallback.

Assessment: behavior differs for file paths. This is necessary in browser/Pyodide but not identical to the original CLI.

## `plugin.py`

The plugin wrapper maps Foldnano UI parameters to pyOrigamiBreak args:

- `nsol`
- `scaffold_sequence`
- `break_rules`
- `scoring_function`
- `min_length_after_break`
- `max_length_after_break`
- `min_length_to_process`
- `seed`
- `read_only`

It hard-codes:

- `verbose = 0`
- `sort = False`
- `permute = False`
- `writeall = False`
- `npermute = 0`
- `score = 'sum'`
- `csv = True`

Assessment: plugin behavior is equivalent only for this supported option subset. Original CLI behaviors for custom sequence files, permutation, sorted oligo processing, write-all output, and custom score aggregation are not exposed by the plugin UI.

## Test Strategy

A proposal; none of these tests exist yet. The fixtures named below (`test_files/`) are in the
[Foldnano](https://github.com/XinShiLab/foldnano) repository, not this one.

The goal should be semantic equivalence of the design output and numeric equivalence of staple scores, not byte equivalence of files.

### 1. Unit Parity for Pure Functions

Because `utilities.py`, `validate.py`, and `scaffolds.py` are identical, a lightweight parity suite should still lock them down:

- `sequence_to_Tm()`
- `sequence_to_dG_dH_dS()`
- `parse_break_rule()`
- `parse_score_function()`
- `parse_optim_function()`
- scaffold sequence lookup

Run the same parametrized tests against both import roots and assert exact or tight floating-point equality.

### 2. Cadnano Decode/Encode Parity

For each fixture in `test_files/*.json` / `*.cadnano.json`:

1. Load with original `Origami.initialize(path)`.
2. Load with plugin `Origami.initialize_from_dict(json.loads(path))`.
3. After `prepare_origami()`, compare:
   - scaffold/staple oligo counts
   - oligo lengths
   - strand VH/index spans
   - crossover counts
   - scaffold sequence length and offset
   - staple color entries

This isolates whether plugin in-memory cadnano loading matches the original before running autobreak.

### 3. Golden Output Equivalence for Readonly Mode

Readonly mode is the best first end-to-end test because it scores existing breaks without mutating topology.

For each supported fixture and parameter set:

1. Run original CLI with:
   - fixed `--seed`
   - `--readonly`
   - `--csv`
   - same sequence name, break rule, scoring function, min/max lengths
2. Run plugin `run_plugin()` with the same args and JSON dict.
3. Compare plugin `csv` against original `*_autobreak.csv` after normalization:
   - parse with pandas
   - sort by stable identity columns, not by emitted row order
   - compare string columns exactly
   - compare numeric columns with tolerance, e.g. `rtol=1e-9`, `atol=1e-9`
4. Compare summary values:
   - original `*_summary.csv` or Excel summary
   - plugin returned `summary` plus any summary data exposed by the harness

### 4. Golden Output Equivalence for Autobreak Mode

For mutation mode:

1. Use fixed `--seed`.
2. Keep `nsol` small for CI (`1`, `2`, maybe `5`), then add one slower nightly case with `10`.
3. Run original and plugin with the same params.
4. Normalize both resulting cadnano JSON files and compare:
   - `vstrands[*].scaf`
   - `vstrands[*].stap`
   - `loop`
   - `skip`
   - `stap_colors`
   - sequence-related fields such as `sequenceOffset` if present
5. Compare normalized staple CSV as in readonly mode.

Do not require byte-identical JSON, because original and plugin use different write paths.

### 5. Regression Matrix

Use a compact fixture/parameter matrix:

| Case | Fixture | Mode | Params |
| --- | --- | --- | --- |
| Small honeycomb | `test_files/minitest.json` | readonly + autobreak | default params, seed 0 |
| Small square | `test_files/minitest_square.json` | readonly + autobreak | default params, seed 0 |
| Crossovers | `test_files/test_file_xover_from_adjacent_index_diff_vh.cadnano.json` | autobreak | `nsol=2`, seed 1 |
| Scaffold-only edge | `test_files/only_scaf.json` | readonly | expected validation/failure behavior |
| Larger smoke | `test_files/HaloV2_Tom.json` | autobreak | `nsol=1`, seed 0 |

### 6. Browser/Pyodide Smoke Test

Add one integration smoke test around the actual plugin archive path:

1. Install the plugin requirements from `autobreak/fplugin.json`.
2. Run the packed plugin zip through Foldnano's worker harness.
3. Assert:
   - plugin completes
   - `results.csv` artifact exists and has expected columns
   - `plots.png` artifact starts with PNG magic bytes
   - mutation mode returns cadnano JSON when `read_only=false`
   - readonly mode does not return replacement cadnano JSON

This catches archive packaging, import path, wheel availability, and artifact encoding issues that direct Python tests will miss.

### 7. Practical Harness Shape

Create a Python test helper that runs both implementations in isolated subprocesses to avoid module-name collisions (`autobreak.py` exists in both trees):

- Original runner (a checkout of `main`):
  - set `PYTHONPATH` to that checkout
  - run `python -m autobreak.autobreak ...`
  - capture output directory path or pass `--output` to a temp dir
- Plugin runner:
  - set `PYTHONPATH=autobreak` on `foldnano_plugin`
  - import `autobreak`
  - call `run_plugin(json_dict, args)`
  - write returned artifacts to a temp dir for comparison

Normalize comparison artifacts with helper functions:

- `normalize_cadnano_json(data)`
- `normalize_staple_csv(csv_text_or_path)`
- `assert_numeric_frame_equal(left, right, tol)`

### 8. Acceptance Criteria

Treat the plugin as equivalent to the original for the supported plugin surface if:

- Pure thermodynamic helper tests match exactly/tightly.
- Pre-run decoded model summaries match for supported fixtures.
- Readonly `results.csv` matches original CSV numerically after normalization.
- Autobreak normalized cadnano topology matches for fixed seeds.
- Plugin artifact behavior is stable in the Pyodide worker.

Explicitly document non-equivalent surfaces:

- Original Excel workbook output.
- Original cn2svg heatmap/report SVG generation.
- Original zipped output directory.
- Original sequence file-path input.
- CLI options not exposed by plugin parameters.
