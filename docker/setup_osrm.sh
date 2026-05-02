#!/bin/bash
# AI-AIDERS OSRM Map Setup Script
# Downloads a lightweight map and processes it for OSRM so it can run offline quickly.

mkdir -p osrm-data
cd osrm-data

echo "Downloading map data (Using a very small map snippet for fast setup - Monaco)..."
curl -O http://download.geofabrik.de/europe/monaco-latest.osm.pbf
mv monaco-latest.osm.pbf map.osm.pbf

echo "Building Routing Graph (Extracting Road Networks)..."
docker run -t -v $(pwd):/data osrm/osrm-backend osrm-extract -p /opt/car.lua /data/map.osm.pbf

echo "Partitioning Graph..."
docker run -t -v $(pwd):/data osrm/osrm-backend osrm-partition /data/map.osrm

echo "Customizing Weights (Speed Limits, Traffic)..."
docker run -t -v $(pwd):/data osrm/osrm-backend osrm-customize /data/map.osrm

echo "Done! You can now launch the tracker by running: docker-compose up -d"
