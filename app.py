"""
Streamlit app to convert a QuPath GeoJSON export into a Leica LMD7 shapes.xml.
"""

import os
import tempfile

import streamlit as st

from convert_qupath_lmd import load_geojson, save_as_xml

st.set_page_config(page_title="LMD7 Shape Cutting", page_icon="✂️")

st.title("✂️ LMD7 Shape Cutting")
st.write(
    "Upload a GeoJSON exported from QuPath (containing the T1/T2/T3 "
    "calibration points and your drawn shapes) to generate a `shapes.xml` "
    "file ready for import on the LMD7. This app was developedby the IMCF of the University of Basel." \
    "More detailed instructions can be found in the [README](https://github.com/imcf-streamlit/lmd7-shape-cutting-streamlit)"
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
    points, polygons, descriptions = load_geojson(uploaded)
except Exception as error:
    st.error(f"Could not read the GeoJSON file: {error}")
    st.stop()

st.subheader("Annotations found")
st.write(f"{len(points)} point(s), {len(polygons)} polygon(s)")
with st.expander("Details"):
    st.code("\n".join(descriptions) or "(none)")

# Check the three calibration points are present before going further
point_names = list(points["name"]) if "name" in points else []
missing = [name for name in ("T1", "T2", "T3") if name not in point_names]
if missing:
    st.error(
        f"Missing calibration point(s): {', '.join(missing)}. "
        "Add them in QuPath and export again."
    )
    st.stop()

if polygons.empty:
    st.error("No polygon shapes found in the GeoJSON.")
    st.stop()

if st.button("Convert to shapes.xml", type="primary"):
    with tempfile.TemporaryDirectory() as folder:
        output_path = os.path.join(folder, "shapes.xml")
        try:
            save_as_xml(points, polygons, output_path)
        except ValueError as error:
            st.error(str(error))
            st.stop()

        with open(output_path, "rb") as xml_file:
            xml_content = xml_file.read()

    st.success(f"Converted {len(polygons)} shape(s).")
    st.download_button(
        "Download shapes.xml",
        data=xml_content,
        file_name="shapes.xml",
        mime="application/xml",
    )
