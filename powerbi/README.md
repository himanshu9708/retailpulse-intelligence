# Power BI Project

`EcommerceExecutiveDashboard.pbip` is a real **Power BI Project** —
Microsoft's official plain-text project format, not a `.pbix` (see
`docs/powerbi_design_spec.md` for why a `.pbix` specifically can't be
authored outside Power BI Desktop, and why this format is the correct
alternative rather than a workaround).

## To Open

1. **Set the data path first.** Edit
   `EcommerceExecutiveDashboard.SemanticModel/definition/expressions.tmdl`
   and change the `DataFolder` parameter's default value to this project's
   `data/processed/` folder on your machine (absolute path, ending in a
   path separator).
2. In Power BI Desktop: **File → Open → select `EcommerceExecutiveDashboard.pbip`**.
   (If prompted about the Power BI Project preview feature, enable it under
   File → Options and settings → Options → Preview features.)
3. Power BI Desktop will load the full data model — 8 tables, all
   relationships, all 12 DAX measures — and 4 empty report pages already
   named and ready.
4. Go to **Modeling → Mark as Date Table** on `dim_date` (column `DateKey`)
   to enable the time-intelligence measure (`Revenue YoY Growth %`).
5. Build out the 4 pages' visuals following
   `docs/powerbi_design_spec.md` — the model and measures already exist,
   so this is drag-and-drop work.
6. **File → Save As → Power BI Desktop file (.pbix)** to produce a real,
   standalone `.pbix`.

## What's in Each Folder

| Path | Contents |
|---|---|
| `EcommerceExecutiveDashboard.pbip` | Project pointer file |
| `EcommerceExecutiveDashboard.SemanticModel/` | The real data model: TMDL tables, relationships, DAX measures, Power Query sources |
| `EcommerceExecutiveDashboard.Report/` | Report shell: 4 named, empty pages wired to the semantic model |

See `docs/powerbi_design_spec.md` for the full explanation, the DAX
measure reference, and the page-by-page visual layout to build.
