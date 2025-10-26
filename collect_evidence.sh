#!/usr/bin/env bash
set -e
echo "=== IMAGE SIZES ==="
docker images enterprise-ai-proxy:latest enterprise-ai-api:latest postgres:15-alpine | awk '{print $1,$2,$7}' || true

echo "=== STARTUP TIME ==="
START=$(date +%s)
docker-compose up -d --build
until curl -k --silent https://localhost/health | grep -q ok; do
  sleep 0.5
done
END=$(date +%s)
echo "startup_seconds=$((END-START))"

echo "=== RUN LOAD TEST ==="
python3 tools/load_test.py

echo "=== DOCKER STATS SNAPSHOT (no-stream) ==="
docker stats --no-stream --format "table {{.Name}}	{{.CPUPerc}}	{{.MemUsage}}" > docker_stats_snapshot.txt
cat docker_stats_snapshot.txt

echo "=== RTO (restart) ==="
TS1=$(date +%s)
docker restart $(docker ps -q --filter ancestor=enterprise-ai-api:latest)
until curl -k --silent https://localhost/ready | grep -q true; do
  sleep 0.5
done
TS2=$(date +%s)
echo "rto_seconds=$((TS2-TS1))"
echo "Evidence files: docker_stats_snapshot.txt"
