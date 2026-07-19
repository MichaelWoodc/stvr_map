import os
import csv
import json
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

# ---------------- CONFIG ----------------

PARCEL_DIR = "data_files/parcels/Parcel_Digest_2025"
AIRBNB_CSV = "data_files/in_process_data/airbnb_master_data_with_type.csv"
OUTPUT_JS = "data_files/in_process_data/locations.js"
MUNICIPALITY_GEOJSON = "data_files/municipality/Municipality.geojson"


# ---------------- SAFE FLOAT PARSER ----------------

def safe_float(value, default=0.0):
    """Convert messy Airbnb numeric fields safely into floats."""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)

    value = str(value).strip()

    if value == "":
        return default
    if value.upper() in ["N/A", "NONE", "NULL"]:
        return default

    # Extract leading number from strings like "3 bedrooms"
    parts = value.split()
    try:
        return float(parts[0])
    except:
        return default


# ---------------- LOAD PARCEL GEOMETRIES ----------------

def load_parcel_geometries(parcel_dir):
    candidates = [
        "Parcel_Digest_2025.geojson",
        "Parcel_Digest_2025.kml",
        "Parcel_Digest_2025.shp"
    ]

    gdf = None
    for fname in candidates:
        path = os.path.join(parcel_dir, fname)
        if os.path.exists(path):
            print(f"Loading parcel geometry from: {path}")
            gdf = gpd.read_file(path)
            break

    if gdf is None:
        raise FileNotFoundError("No parcel geometry file found.")

    if gdf.crs is None:
        raise ValueError("Parcel file has no CRS defined.")

    if gdf.crs.to_epsg() != 4326:
        print(f"Reprojecting from {gdf.crs} → EPSG:4326")
        gdf = gdf.to_crs("EPSG:4326")

    if "PropAddress_Full" not in gdf.columns:
        raise ValueError("PropAddress_Full not found in parcel data.")

    addr_col = "PropAddress_Full"

    gdf["centroid"] = gdf.geometry.centroid

    return gdf, addr_col


# ---------------- LOAD MUNICIPALITIES ----------------

def load_municipalities(path):
    gdf = gpd.read_file(path)
    if gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs("EPSG:4326")
    return gdf


# ---------------- LOAD AIRBNB CSV ----------------

def load_airbnb_csv(path):
    rows = []
    with open(path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for key in ["guests", "bedrooms", "beds", "baths",
                        "latitude", "longitude",
                        "allowed_guests", "over_occupancy", "percent_over"]:
                if key in row:
                    row[key] = safe_float(row[key])
            rows.append(row)
    return rows


# ---------------- MATCH AIRBNB TO PARCELS + MUNICIPALITIES ----------------

def match_airbnb_to_parcels(locations, parcels_gdf, addr_col, muni_gdf):
    valid_locations = []
    skipped_missing_coords = []
    skipped_outside_county = []

    # Only skip rows with missing coordinates. Do NOT drop points just because
    # they don't fall strictly within a parcel polygon — many valid listings are
    # in unplatted or unincorporated areas. We'll use `sjoin_nearest` below to
    # associate the nearest parcel when available.
    for loc in locations:
        lat = loc.get("latitude", "")
        lng = loc.get("longitude", "")

        if lat in ("", None) or lng in ("", None):
            skipped_missing_coords.append(loc)
            continue

        # keep the row; convert to floats later when building GeoDataFrame
        valid_locations.append(loc)

    print(f"[System] Valid coordinate rows: {len(valid_locations)}")
    print(f"[System] Skipped (missing lat/lng): {len(skipped_missing_coords)}")

    airbnb_points = gpd.GeoDataFrame(
        valid_locations,
        geometry=[Point(loc["longitude"], loc["latitude"]) for loc in valid_locations],
        crs="EPSG:4326"
    )

    parcels_gdf = parcels_gdf.to_crs("EPSG:4326")

    centroids = gpd.GeoDataFrame(
        parcels_gdf[[addr_col]],
        geometry=parcels_gdf["centroid"],
        crs="EPSG:4326"
    )

    joined = gpd.sjoin_nearest(
        airbnb_points,
        centroids,
        how="left",
        distance_col="dist_meters"
    )

    # ---- MUNICIPALITY JOIN ----
    muni_join = gpd.sjoin(
        airbnb_points,
        muni_gdf,
        how="left",
        predicate="within"
    )

    updated_locations = []

    for loc, row, muni_row in zip(valid_locations, joined.itertuples(), muni_join.itertuples()):
        loc["approximate_address"] = getattr(row, addr_col)
        loc["approx_distance_meters"] = getattr(row, "dist_meters")

        municipality = getattr(muni_row, "NAME", None)
        if municipality is None:
            municipality = getattr(muni_row, "Municipality", "UNINCORPORATED")
        municipality = str(municipality).strip() or "UNINCORPORATED"
        municipality_clean = municipality.upper()
        loc["municipality"] = municipality

        # ---- OCCUPANCY RULES ----
        bedrooms = safe_float(loc.get("bedrooms", 0))
        guests = safe_float(loc.get("guests", 0))

        # Savannah uses a special rule; all other jurisdictions follow
        # the county rule (2 per bedroom + 2). Tybee Island no longer has
        # a separate exception — treat it like the rest of the county.
        if "SAVANNAH" in municipality_clean:
            if bedrooms <= 2:
                allowed = 4
            else:
                allowed = 2 * bedrooms
        else:
            allowed = 2 * bedrooms + 2

        loc["allowed_guests"] = allowed
        loc["over_occupancy"] = guests - allowed
        loc["percent_over"] = (
            (guests - allowed) / allowed * 100 if allowed > 0 else 0
        )

        updated_locations.append(loc)

    return updated_locations


# ---------------- WRITE locations.js ----------------

def write_locations_js(path, locations):
    js_text = "const locations = " + json.dumps(locations, indent=2) + ";"
    with open(path, "w", encoding="utf-8") as f:
        f.write(js_text)
    print(f"[System] locations.js written to: {path}")


# ---------------- MAIN ----------------

if __name__ == "__main__":
    parcels_gdf, addr_col = load_parcel_geometries(PARCEL_DIR)
    muni_gdf = load_municipalities(MUNICIPALITY_GEOJSON)
    airbnb_rows = load_airbnb_csv(AIRBNB_CSV)
    updated = match_airbnb_to_parcels(airbnb_rows, parcels_gdf, addr_col, muni_gdf)
    write_locations_js(OUTPUT_JS, updated)
