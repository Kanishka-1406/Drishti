from app.ingestion.fetch_osm import RegionBounds, build_overpass_query, classify, element_geojson, fetch_overpass, make_osm_id


class FakeResponse:
    def __init__(self, payload=None, error=None): self.payload, self.error = payload or {}, error
    def raise_for_status(self):
        if self.error: raise self.error
    def json(self): return self.payload


class FakeClient:
    def __init__(self, response): self.response, self.data = response, None
    def post(self, url, data): self.data = data; return self.response


def test_query_contains_required_osm_categories_and_bbox():
    query = build_overpass_query(RegionBounds(1, "Test", 10, 20, 11, 21))
    for value in ("hospital", "school", "police", "fire_station", "primary", "secondary", "trunk", "10,20,11,21"):
        assert value in query


def test_classification_and_unique_ids():
    assert classify({"amenity": "hospital"}) == "hospital"
    assert classify({"highway": "primary"}) == "road"
    assert classify({"amenity": "cafe"}) is None
    assert make_osm_id({"type": "node", "id": 7}) != make_osm_id({"type": "way", "id": 7})


def test_geometry_keeps_roads_as_lines_and_amenities_as_points():
    assert element_geojson({"type": "node", "lat": 1, "lon": 2}) == {"type": "Point", "coordinates": [2, 1]}
    result = element_geojson({"type": "way", "geometry": [{"lat": 1, "lon": 2}, {"lat": 3, "lon": 4}]})
    assert result == {"type": "LineString", "coordinates": [[2, 1], [4, 3]]}


def test_fetch_overpass_fails_open():
    bounds = RegionBounds(1, "Test", 10, 20, 11, 21)
    result = fetch_overpass(bounds, FakeClient(FakeResponse(error=RuntimeError("offline"))))
    assert result["status"] == "unavailable"
    assert result["elements"] == []


def test_fetch_overpass_returns_elements():
    bounds = RegionBounds(1, "Test", 10, 20, 11, 21)
    client = FakeClient(FakeResponse({"elements": [{"type": "node", "id": 1}]}))
    result = fetch_overpass(bounds, client)
    assert result["status"] == "ok"
    assert len(result["elements"]) == 1
    assert "hospital" in client.data["data"]
