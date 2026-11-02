# pyOrigamiBreak for Foldnano

A [Foldnano](https://github.com/XinShiLab/foldnano) plugin that optimizes staple break positions in
caDNAno designs with thermodynamic scoring. It is adapted from
[pyOrigamiBreak](https://github.com/douglaslab/pyOrigamiBreak) by the
[Douglas Lab](https://bionano.ucsf.edu/), with the authors' permission, under the original MIT
License.

Install it in Foldnano from the plugin Hub's **Community Plugins** section.

## Branches

- `main` tracks the upstream project unchanged.
- `foldnano_plugin` holds the plugin. The changes from upstream are in-memory input and output
  instead of files, flat imports and Pyodide compatibility; see `docs/plugin-diff-report.md`. The
  command-line tool and its helper scripts are not part of this branch.

## Layout

`autobreak/` holds exactly the files of the plugin zip: `fplugin.json` (the plugin manifest),
`plugin.py` (the Foldnano entry point), the adapted modules, `LICENSE` and `NOTICE`.

## Releasing a version

1. Change the plugin files and bump `version` in `autobreak/fplugin.json`.
2. Pack the zip with the
   [foldnano-plugins](https://github.com/XinShiLab/foldnano-plugins) repo, checked out next to this
   one:

   ```sh
   cd ../foldnano-plugins
   npm run pack -- ../pyOrigamiBreak_mini/autobreak
   ```

   Packing is reproducible: the same files always give the same SHA-256, so anyone can check a
   listed zip against this branch.

3. Add the printed entry to the listing there, following its `CONTRIBUTING.md`.

## How to cite

If you use this plugin in published work, please cite:

```
Aksel, T., Navarro, E. J., Fong, N. and Douglas, S. M.
Design principles for accurate folding of DNA origami.
Proceedings of the National Academy of Sciences 121(48), e2406769121 (2024).
https://doi.org/10.1073/pnas.2406769121
```

```
Rapid prototyping of 3D DNA-origami shapes with caDNAno
Douglas et al. Nucleic Acids Res: 37(15):5001–6 (2009)
https://doi.org/10.1093/nar/gkp436
```

## License

MIT, as the original project. See `LICENSE`.
