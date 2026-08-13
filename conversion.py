"""
Core conversion logic: QuPath GeoJSON annotation export -> Leica LMD7 shapes.xml.

Adapted from the CLI script `qupath_to_lmd.py` in the lmd7-shape-cutting repo
(https://git.scicore.unibas.ch/imcf/lmd7-shape-cutting), refactored so it can
be driven from the Streamlit app: functions accept file-like objects (as
produced by `st.file_uploader`) and return structured results/raise
exceptions instead of printing to stdout / calling `sys.exit`.
"""

from __future__ import annotations

import contextlib
import io
from dataclasses import dataclass, field

import geopandas
import numpy as np
import shapely
from lmd.lib import Collection

REQUIRED_CALIBRATION_NAMES = ("T1", "T2", "T3")


class ConversionError(Exception):
    """Raised when the uploaded GeoJSON can't be converted to a shapes.xml."""


@dataclass
class LoadResult:
    points: geopandas.GeoDataFrame
    polygons: geopandas.GeoDataFrame
    annotation_log: list[str] = field(default_factory=list)


def load_geojson(source) -> LoadResult:
    """Read a GeoJSON (path or file-like object) and split it into
    calibration points and polygon shapes.
    """
    df = geopandas.read_file(source)

    annotation_log = [
        f"name={row.get('name', '(unnamed)')!r}  type={type(row['geometry']).__name__}"
        for _, row in df.iterrows()
    ]

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

    return LoadResult(points=points, polygons=polygons, annotation_log=annotation_log)


def get_calibration_points(points_df: geopandas.GeoDataFrame) -> np.ndarray:
    """Read T1, T2, T3 calibration cross positions from QuPath points."""

    def get(name):
        row = points_df[points_df["name"] == name]
        if row.empty:
            raise ConversionError(
                f"No calibration point named '{name}' found in the GeoJSON. "
                f"Expected points named {', '.join(REQUIRED_CALIBRATION_NAMES)}."
            )
        g = row["geometry"].values[0]
        return np.array([g.x, g.y])

    return np.array([get(name) for name in REQUIRED_CALIBRATION_NAMES])


@dataclass
class ConversionResult:
    xml_bytes: bytes
    num_shapes: int
    num_points: int
    calibration_points: np.ndarray
    annotation_log: list[str]
    stats_text: str


def convert_geojson_to_xml(source, output_path: str) -> ConversionResult:
    """Convert an opened/uploaded GeoJSON into an LMD7 shapes XML file on disk.

    `source` is anything `geopandas.read_file` accepts (a path or a
    file-like object). Raises `ConversionError` on invalid input.
    """
    load_result = load_geojson(source)

    if load_result.polygons.empty:
        raise ConversionError("No polygon annotations found in the GeoJSON.")

    calibration_points = get_calibration_points(load_result.points)

    # Y-axis is flipped between image space (y down) and LMD space (y up)
    orientation_transform = np.array([[1, 0], [0, -1]])

    collection = Collection(
        calibration_points=calibration_points,
        orientation_transform=orientation_transform,
    )

    name_col = "name" if "name" in load_result.polygons.columns else None
    collection.load_geopandas(load_result.polygons, name_column=name_col)

    stats_buffer = io.StringIO()
    with contextlib.redirect_stdout(stats_buffer):
        collection.stats()

    collection.save(output_path)
    with open(output_path, "rb") as f:
        xml_bytes = f.read()

    return ConversionResult(
        xml_bytes=xml_bytes,
        num_shapes=len(load_result.polygons),
        num_points=len(load_result.points),
        calibration_points=calibration_points,
        annotation_log=load_result.annotation_log,
        stats_text=stats_buffer.getvalue(),
    )
