# lmd7-shape-cutting-streamlit

A Streamlit app that turns a QuPath GeoJSON annotation export into a
`shapes.xml` file ready for import on the Leica LMD7 laser microdissection
microscope.

This is the browser-based counterpart to the CLI tool in
[lmd7-shape-cutting](https://git.scicore.unibas.ch/imcf/lmd7-shape-cutting):
upload a `.geojson` file, and download the converted `shapes.xml`.

## Workflow

1. In QuPath, add three **Points** annotations named `T1`, `T2`, `T3` on the
   calibration crosses, then draw your shapes with the **Polygon** tool.
2. `File → Export objects as GeoJSON`, choosing **All objects**.
3. Upload the resulting `.geojson` file to this app.
4. Review the shape/point preview, then click **Convert to shapes.xml** and
   download the result.
5. On the LMD7, `File → Import Shapes`, import all shapes, and set the
   calibration points manually (navigate to T1/T2/T3 on the membrane).

See the [lmd7-shape-cutting README](https://git.scicore.unibas.ch/imcf/lmd7-shape-cutting)
for the full end-to-end workflow (microscope setup, slide scanning, etc.).

## Running locally

### With pip

```bash
python -m venv .venv
source .venv/bin/activate  # .venv\Scripts\activate on Windows
pip install -r requirements.txt
streamlit run app.py
```

### With pixi

```bash
pixi run app
```

## Deployment

This app is deployable on [Streamlit Community Cloud](https://streamlit.io/cloud)
(or any host that runs `streamlit run app.py`) using `requirements.txt`.
`pixi.toml`/`pixi.lock` are kept for local/reproducible development but are
not required for the pip-based deployment path.

## Files

- [`app.py`](app.py) — Streamlit UI.
- [`conversion.py`](conversion.py) — GeoJSON → LMD7 XML conversion logic
  (adapted from `qupath_to_lmd.py` in lmd7-shape-cutting).
