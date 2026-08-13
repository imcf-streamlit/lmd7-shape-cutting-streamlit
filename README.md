# lmd7-shape-cutting-streamlit

A Streamlit app that turns a QuPath GeoJSON annotation export into a
`shapes.xml` file ready for import on the Leica LMD7 laser micro-dissection
microscope.


## Workflow

On the **LMD7**:

Using the LMD7 "**cut text**" option, cut 3 reference points surrounding your tissue section.
Ideally cutting "T"s helps better with calibrating.
Cut 3 strings on the LMD7: "T1", "T2" and "T3", outside of your specimen.

In **QuPath**:

1. Add three **Points** annotations named `T1`, `T2`, `T3` on the
   calibration crosses, then draw your shapes with the **Polygon** tool.
2. `File → Export objects as GeoJSON`, choosing **All objects**.
3. Upload the resulting `.geojson` file to this app.
4. Review the shape/point preview, then click **Convert to shapes.xml** and
   download the result.
5. On the LMD7, `File → Import Shapes`, import all shapes, and set the
   calibration points manually (navigate to T1/T2/T3 on the membrane).

## Running locally

### With pixi

Clone this repository and on the console type the following. This assumes you have an installation of [pixi](https://pixi.prefix.dev/latest/) installed on your system.

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
  (adapted from `qupath_to_lmd.py` in the IMCF infrastructure.).

## Developers

This was developed by the [IMCF](https://github.com/imcf) of the University of Basel.
