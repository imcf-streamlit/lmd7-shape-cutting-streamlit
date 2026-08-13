"""
Streamlit app: upload a QuPath GeoJSON annotation export, get back a
Leica LMD7 shapes.xml ready for import.
"""

import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import streamlit as st

from conversion import ConversionError, convert_geojson_to_xml, load_geojson

st.set_page_config(page_title="LMD7 Shape Cutting", page_icon="✂️", layout="centered")

st.title("✂️ LMD7 Shape Cutting")
st.write(
    "Upload a GeoJSON exported from QuPath (containing the T1/T2/T3 "
    "calibration points and your drawn shapes) to generate a `shapes.xml` "
    "file ready for import on the LMD7."
)

with st.expander("How to prepare the GeoJSON in QuPath"):
    st.markdown(
        """
        1. Add three **Points** annotations on the calibration crosses,
           named `T1`, `T2`, `T3`.
        2. Draw your shapes with the **Polygon** tool.
        3. `File → Export objects as GeoJSON`, choose **All objects**.
        """
    )

uploaded = st.file_uploader("GeoJSON file", type=["geojson", "json"])

if uploaded is None:
    st.info("Upload a GeoJSON file to get started.")
    st.stop()

try:
    uploaded.seek(0)
    load_result = load_geojson(uploaded)
except Exception as exc:  # noqa: BLE001 - surface any parse error to the user
    st.error(f"Could not read the GeoJSON file: {exc}")
    st.stop()

st.subheader("Annotations found")
st.write(f"{len(load_result.points)} point(s), {len(load_result.polygons)} polygon(s)")
with st.expander("Details"):
    st.code("\n".join(load_result.annotation_log) or "(none)")

point_names = load_result.points["name"].values if "name" in load_result.points else []
missing = [n for n in ("T1", "T2", "T3") if n not in point_names]
if missing:
    st.error(
        f"Missing calibration point(s): {', '.join(missing)}. "
        "Add them in QuPath and re-export."
    )
    st.stop()

if load_result.polygons.empty:
    st.error("No polygon shapes found in the GeoJSON.")
    st.stop()

fig, ax = plt.subplots()
load_result.polygons.plot(ax=ax, edgecolor="black", facecolor="none")
load_result.points.plot(ax=ax, color="red", marker="x")
for _, row in load_result.points.iterrows():
    ax.annotate(row.get("name", ""), (row.geometry.x, row.geometry.y))
ax.set_aspect("equal")
ax.invert_yaxis()  # image-space y is down
ax.set_title("Preview (image space)")
st.pyplot(fig)

if st.button("Convert to shapes.xml", type="primary"):
    with st.spinner("Converting..."):
        uploaded.seek(0)
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = str(Path(tmp_dir) / "shapes.xml")
            try:
                result = convert_geojson_to_xml(uploaded, output_path)
            except ConversionError as exc:
                st.error(str(exc))
                st.stop()

    st.success(f"Converted {result.num_shapes} shape(s).")
    st.code(result.stats_text)
    st.download_button(
        "Download shapes.xml",
        data=result.xml_bytes,
        file_name="shapes.xml",
        mime="application/xml",
    )
