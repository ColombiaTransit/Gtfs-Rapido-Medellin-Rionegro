#!/usr/bin/env python3
"""Generate shapes.txt by routing through GraphHopper.

Each shape is routed along a list of waypoints: registry stops (colombia-stops
stop_ids) and fixed via points that keep the route on the right road (autopista,
Santa Elena, Llanogrande). The via points were sampled from the original
hand-made shapes; those for the Llanogrande route were set by hand.

Configuration (environment variables):
    GRAPHHOPPER_URL      base URL of a GraphHopper server, e.g. http://localhost:8989
                         (default: the public API, https://graphhopper.com/api/1)
    GRAPHHOPPER_KEY      API key (required for the public API)
    GRAPHHOPPER_PROFILE  routing profile (default: car)

Usage:
    python build_shapes.py [--stops ../colombia-stops/data/stops.csv]
"""

import argparse
import csv
import json
import math
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PUBLIC_API = "https://graphhopper.com/api/1"

RIONEGRO = "CO001362"
AEROPUERTO = "CO002641"
NORTE = "CO001433"
SUR = "CO001432"

# Waypoints per shape: a registry stop_id or a (lat, lon) via point.
SHAPES = {
    "norte-out": [RIONEGRO, (6.21084, -75.38347), (6.25993, -75.43706), (6.32360, -75.46878),
                  (6.32815, -75.51326), (6.30357, -75.55803), NORTE],
    "norte-in": [NORTE, (6.29859, -75.55962), (6.32756, -75.51753), (6.32505, -75.47321),
                 (6.26406, -75.43843), (6.21571, -75.38573), RIONEGRO],
    "sur-out": [RIONEGRO, (6.14948, -75.43451), AEROPUERTO, (6.17083, -75.45252), (6.17073, -75.50031),
                (6.15307, -75.54487), (6.21412, -75.54686), SUR],
    "sur-in": [SUR, (6.21435, -75.54734), (6.15302, -75.54531), (6.17062, -75.49990), (6.17149, -75.45163),
               AEROPUERTO, (6.14988, -75.43470), RIONEGRO],
    # Hand-set: Llanogrande (approximate, to be checked), then the airport, then the autopista.
    "llanogrande-out": [RIONEGRO, (6.13200, -75.42000), AEROPUERTO, (6.25993, -75.43706), (6.32360, -75.46878),
                        (6.32815, -75.51326), (6.30357, -75.55803), NORTE],
}


def load_registry(stops_csv):
    with open(stops_csv, newline="", encoding="utf-8") as f:
        return {r["stop_id"]: (float(r["lat"]), float(r["lon"])) for r in csv.DictReader(f) if r["lat"] and r["lon"]}


def request(points, base, key, profile, flexible):
    params = [("point", f"{lat},{lon}") for lat, lon in points]
    params += [("profile", profile), ("points_encoded", "false"), ("instructions", "false"), ("calc_points", "true")]
    if flexible:
        params += [("pass_through", "true"), ("ch.disable", "true")]
    if key:
        params.append(("key", key))
    url = f"{base.rstrip('/')}/route?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=120) as resp:
        return json.load(resp)


def route(points, base, key, profile):
    """Route with pass_through (no U-turns at via points); fall back to a plain
    request if the server does not allow flexible mode."""
    try:
        data = request(points, base, key, profile, flexible=True)
    except urllib.error.HTTPError as e:
        print(f"  pass_through refused ({e.code}: {e.read()[:200]!r}), retrying without it")
        data = request(points, base, key, profile, flexible=False)
    path = data["paths"][0]
    return [(lat, lon) for lon, lat, *_ in path["points"]["coordinates"]], path["distance"]


def haversine(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371000 * math.asin(math.sqrt(h))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--stops", default=str(ROOT.parent / "colombia-stops" / "data" / "stops.csv"))
    args = p.parse_args()

    base = os.environ.get("GRAPHHOPPER_URL", PUBLIC_API)
    key = os.environ.get("GRAPHHOPPER_KEY", "")
    profile = os.environ.get("GRAPHHOPPER_PROFILE", "car")
    if base == PUBLIC_API and not key:
        sys.exit("Set GRAPHHOPPER_KEY for the public API, or GRAPHHOPPER_URL for your own server.")

    registry = load_registry(args.stops)
    rows = []
    for shape_id, waypoints in SHAPES.items():
        points = [registry[w] if isinstance(w, str) else w for w in waypoints]
        coords, distance = route(points, base, key, profile)
        dist = 0.0
        for seq, pt in enumerate(coords):
            if seq:
                dist += haversine(coords[seq - 1], pt)
            rows.append([shape_id, seq, f"{pt[0]:.6f}", f"{pt[1]:.6f}", f"{dist:.1f}"])
        print(f"{shape_id}: {len(coords)} points, {distance / 1000:.1f} km")

    with open(ROOT / "shapes.txt", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["shape_id", "shape_pt_sequence", "shape_pt_lat", "shape_pt_lon", "shape_dist_traveled"])
        w.writerows(rows)


if __name__ == "__main__":
    main()
