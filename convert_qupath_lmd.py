"""
Convert a QuPath GeoJSON annotation export to Leica LMD7 XML.

Adapted from the `qupath_to_lmd.py` script developed by the IMCF, so that it
can be used by the Streamlit app instead of from the command line.
"""

import geopandas
import numpy as np
import shapely

from lmd.lib import Collection


def load_geojson(source):
    """Read a GeoJSON and split it into calibration points and polygons.

    `source` can be a file path or an uploaded file.
    Returns the points, the polygons, and a list describing every annotation.
    """
    df = geopandas.read_file(source)

    descriptions = []
    for _, row in df.iterrows():
        name = row.get("name", "(unnamed)")
        descriptions.append(f"name={name!r}  type={type(row['geometry']).__name__}")

    points = df[df["geometry"].apply(lambda g: isinstance(g, shapely.Point))]

    # Convert closed LineStrings/LinearRings to Polygons, keep Polygon/MultiPolygon
    def to_polygon(g):
        if isinstance(g, (shapely.Polygon, shapely.MultiPolygon)):
            return g
        if isinstance(g, (shapely.LineString, shapely.LinearRing)):
            return shapely.Polygon(g)
        return None

    converted = df["geometry"].apply(to_polygon)
    is_poly = converted.notna()
    polygons = df[is_poly].copy()
    polygons["geometry"] = converted[is_poly]
    polygons = polygons.explode(index_parts=False).reset_index(drop=True)
    polygons = polygons[
        polygons["geometry"].apply(lambda g: isinstance(g, shapely.Polygon))
    ]

    return points, polygons, descriptions


def get_calibration_points(points_df):
    """Read the T1, T2, T3 calibration cross positions from the QuPath points."""

    def get(name):
        row = points_df[points_df["name"] == name]
        if row.empty:
            raise ValueError(f"No point named '{name}' found in the GeoJSON.")
        g = row["geometry"].values[0]
        return np.array([g.x, g.y])

    T1 = get("T1")  # mid-right in image-space
    T2 = get("T2")  # bottom-left
    T3 = get("T3")  # top-right

    return np.array([T1, T2, T3])


def save_as_xml(points_df, polygons_df, output_path):
    """Build the LMD7 collection from the annotations and save it as XML."""
    if polygons_df.empty:
        raise ValueError("No polygon annotations found in the GeoJSON.")

    calibration_points = get_calibration_points(points_df)

    # Y-axis is flipped between image space (y down) and LMD space (y up)
    orientation_transform = np.array([[1, 0], [0, -1]])

    collection = Collection(
        calibration_points=calibration_points,
        orientation_transform=orientation_transform,
    )

    name_col = "name" if "name" in polygons_df.columns else None
    collection.load_geopandas(polygons_df, name_column=name_col)

    collection.save(output_path)
