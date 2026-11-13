import { useEffect, useState } from "react";
import L from "leaflet";

import {
  CircleMarker,
  GeoJSON,
  LayersControl,
  MapContainer,
  Popup,
  TileLayer,
  useMap,
} from "react-leaflet";

import "leaflet/dist/leaflet.css";

import {
  fetchHistorical,
  fetchInfrastructure,
} from "../services/api";


function FixMapSize() {
  const map = useMap();

  useEffect(() => {
    const timer = setTimeout(() => {
      map.invalidateSize();
    }, 100);

    return () => clearTimeout(timer);
  }, [map]);

  return null;
}


function HistoricalLayer({ data }) {
  if (!data?.features?.length) {
    return null;
  }

  return (
    <>
      {data.features.map((feature, index) => {
        if (feature.geometry?.type !== "Point") {
          return null;
        }

        const [longitude, latitude] =
          feature.geometry.coordinates;

        const properties =
          feature.properties ?? {};

        return (
          <CircleMarker
            key={properties.id ?? index}
            center={[
              Number(latitude),
              Number(longitude),
            ]}
            radius={9}
            pathOptions={{
              color: "#ef4444",
              fillColor: "#ef4444",
              fillOpacity: 0.9,
              weight: 2,
            }}
          >
            <Popup>
              <div className="map-popup">
                <strong>
                  Historical Landslide
                </strong>

                <div>
                  Date:{" "}
                  {properties.event_date ?? "Unknown"}
                </div>

                <div>
                  Severity:{" "}
                  {properties.severity ?? "Unknown"}
                </div>

                <div>
                  Source:{" "}
                  {properties.source ?? "Unknown"}
                </div>

                {properties.confidence != null && (
                  <div>
                    Confidence:{" "}
                    {Math.round(
                      Number(properties.confidence) * 100
                    )}
                    %
                  </div>
                )}

                {properties.description && (
                  <p>
                    {properties.description}
                  </p>
                )}
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </>
  );
}


function getInfrastructureStyle(category) {
  switch (category) {
    case "hospital":
      return {
        color: "#ef6666",
        fillColor: "#ef6666",
      };

    case "police":
      return {
        color: "#6fa8ff",
        fillColor: "#6fa8ff",
      };

    case "fire_station":
      return {
        color: "#f09a58",
        fillColor: "#f09a58",
      };

    case "school":
      return {
        color: "#d7c36b",
        fillColor: "#d7c36b",
      };

    default:
      return {
        color: "#9aaab2",
        fillColor: "#9aaab2",
      };
  }
}


function InfrastructureLayer({ data }) {
  if (!data?.features?.length) {
    return null;
  }

  return (
    <GeoJSON
      data={data}
      style={(feature) => {
        const style =
          getInfrastructureStyle(
            feature.properties?.category
          );

        return {
          ...style,
          weight: 3,
          opacity: 0.8,
        };
      }}
      pointToLayer={(feature, latlng) => {
        const style =
          getInfrastructureStyle(
            feature.properties?.category
          );

        return L.circleMarker(
          latlng,
          {
            radius: 5,
            ...style,
            fillOpacity: 0.75,
            weight: 1.5,
          }
        );
      }}
      onEachFeature={(feature, layer) => {
        const properties =
          feature.properties ?? {};

        layer.bindPopup(`
          <strong>
            ${properties.name || "Infrastructure"}
          </strong>
          <br/>
          Category:
          ${properties.category || "Unknown"}
          <br/>
          Source: OpenStreetMap
        `);
      }}
    />
  );
}


function MapView({ region }) {
  const [historical, setHistorical] =
    useState(null);

  const [infrastructure, setInfrastructure] =
    useState(null);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState(null);

  const [visibleCategories, setVisibleCategories] =
    useState({
      hospital: true,
      school: true,
      police: true,
      fire_station: true,
    });


  const latitude = Number(
    region?.center_lat ?? 27.041
  );

  const longitude = Number(
    region?.center_lon ?? 88.266
  );

  const zoom = Number(
    region?.default_zoom ?? 11
  );


  function toggleCategory(category) {
    setVisibleCategories((current) => ({
      ...current,
      [category]: !current[category],
    }));
  }


  useEffect(() => {
    if (!region?.id) {
      console.warn(
        "MapView: no region.id supplied"
      );
      return;
    }

    let cancelled = false;

    async function loadMapData() {
      setLoading(true);
      setError(null);

      try {
        const results =
          await Promise.allSettled([
            fetchHistorical(region.id),
            fetchInfrastructure(region.id),
          ]);

        if (cancelled) {
          return;
        }

        const [
          historicalResult,
          infrastructureResult,
        ] = results;

        if (
          historicalResult.status ===
          "fulfilled"
        ) {
          setHistorical(
            historicalResult.value
          );
        } else {
          console.error(
            "Historical API failed:",
            historicalResult.reason
          );
        }

        if (
          infrastructureResult.status ===
          "fulfilled"
        ) {
          setInfrastructure(
            infrastructureResult.value
          );
        } else {
          console.error(
            "Infrastructure API failed:",
            infrastructureResult.reason
          );
        }

        if (
          historicalResult.status ===
            "rejected" ||
          infrastructureResult.status ===
            "rejected"
        ) {
          setError(
            "Some geospatial layers could not be loaded. Base map is still available."
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadMapData();

    return () => {
      cancelled = true;
    };
  }, [region?.id]);


  const filteredInfrastructure = {
    ...(infrastructure ?? {}),
    features:
      infrastructure?.features?.filter(
        (feature) =>
          visibleCategories[
            feature.properties?.category
          ]
      ) ?? [],
  };


  console.log("MAP REGION:", region);
  console.log(
    "MAP CENTER:",
    latitude,
    longitude
  );


  if (
    !Number.isFinite(latitude) ||
    !Number.isFinite(longitude)
  ) {
    return (
      <div style={{ padding: "20px" }}>
        Invalid map coordinates:{" "}
        {String(region?.center_lat)},{" "}
        {String(region?.center_lon)}
      </div>
    );
  }


  return (
    <section
      className="card map-section"
      style={{ width: "100%" }}
    >

      <div className="map-header">
        <div>
          <div className="eyebrow">
            GEOSPATIAL CONTEXT
          </div>

          <h2>
            {region?.name ?? "Darjeeling"} Risk Map
          </h2>

          <p>
            Historical events and surrounding
            infrastructure.
          </p>
        </div>

        <div className="map-counts">
          <span>
            {historical?.features?.length ?? 0}{" "}
            historical events
          </span>

          <span>
            {infrastructure?.features?.length ?? 0}{" "}
            infrastructure features
          </span>
        </div>
      </div>


      <div className="infra-filter-row">
        {[
          ["hospital", "Hospitals"],
          ["school", "Schools"],
          ["police", "Police"],
          ["fire_station", "Fire Stations"],
        ].map(([key, label]) => (
          <button
            key={key}
            type="button"
            className={
              visibleCategories[key]
                ? "filter-chip active"
                : "filter-chip"
            }
            onClick={() =>
              toggleCategory(key)
            }
          >
            {label} (
            {infrastructure
              ?.category_counts?.[key] ?? 0}
            )
          </button>
        ))}
      </div>


      {loading && (
        <div className="map-message">
          Loading map layers...
        </div>
      )}


      {error && (
        <div className="error-card">
          {error}
        </div>
      )}


      <div
        className="map-wrapper"
        style={{
          width: "100%",
          height: "600px",
          minHeight: "600px",
          position: "relative",
        }}
      >

        <MapContainer
          key={`${latitude}-${longitude}`}
          center={[latitude, longitude]}
          zoom={zoom}
          scrollWheelZoom={true}
          style={{
            width: "100%",
            height: "600px",
            minHeight: "600px",
          }}
        >

          <FixMapSize />

          <TileLayer
            attribution="&copy; OpenStreetMap contributors"
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />


          <LayersControl position="topright">

            <LayersControl.Overlay
              checked
              name="Historical Landslides"
            >
              <HistoricalLayer
                data={historical}
              />
            </LayersControl.Overlay>


            <LayersControl.Overlay
              checked
              name="Infrastructure"
            >
              <InfrastructureLayer
                data={filteredInfrastructure}
              />
            </LayersControl.Overlay>

          </LayersControl>


          <CircleMarker
            center={[latitude, longitude]}
            radius={9}
            pathOptions={{
              color: "#75d9b9",
              fillColor: "#75d9b9",
              fillOpacity: 0.9,
            }}
          >
            <Popup>
              <strong>
                {region?.name ?? "Darjeeling"}
              </strong>

              <br />

              DRISHTI reference region
            </Popup>
          </CircleMarker>

        </MapContainer>

      </div>

    </section>
  );
}


export default MapView;