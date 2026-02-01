"""ZIP code geospatial lookup using SF Open Data polygons."""

from typing import Optional

import requests
from shapely.geometry import Point, shape

ZIP_GEOJSON_URL: str = "https://data.sfgov.org/resource/wg3w-h783.geojson"


class ZipMap:
    """Lookup ZIP code from lat/lon coordinates using GeoJSON polygons."""

    def __init__(self, url: str = ZIP_GEOJSON_URL) -> None:
        """Load ZIP code polygons from GeoJSON.

        Args:
            url: URL to GeoJSON with polygon features.
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Loading ZIP code polygons...")

        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        self._polygons: list[tuple[Optional[str], object]] = []
        for feature in data.get("features", []):
            zipcode = feature.get("properties", {}).get("zipcode")
            geom = shape(feature["geometry"])
            self._polygons.append((zipcode, geom))

    def lookup(self, lat: float, lon: float) -> Optional[str]:
        """Return ZIP code for given coordinates.

        Args:
            lat: Latitude.
            lon: Longitude (Shapely uses x=lon, y=lat).

        Returns:
            ZIP code string or None if not found.
        """
        pt = Point(lon, lat)
        for zipcode, poly in self._polygons:
            if zipcode and poly.contains(pt):
                return zipcode
        return None
