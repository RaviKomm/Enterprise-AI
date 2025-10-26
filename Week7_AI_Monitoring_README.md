# Week 7: AI Application Monitoring with Prometheus, Grafana, and Alertmanager

## 📘 Overview
This project demonstrates end-to-end monitoring and alerting for an AI API service using **Prometheus**, **Grafana**, and **Alertmanager** within Docker containers. Metrics such as total requests, error rates, and request latency percentiles are collected, visualized, and used to trigger alerts.

---

## 🧱 Project Architecture

**Components:**
- **API Service (`api`)** — Python FastAPI app exposing `/metrics` endpoint.
- **PostgreSQL** — Backend database.
- **Prometheus** — Collects metrics and evaluates alert rules.
- **Grafana** — Visualizes metrics using dashboards.
- **Alertmanager** — Handles alert notifications from Prometheus.
- **Nginx** — Reverse proxy (optional).

**Ports:**
| Service | Port | Description |
|----------|------|-------------|
| API | 8000 | Exposes /metrics |
| Prometheus | 9090 | Metrics collection and alerts |
| Grafana | 3000 | Dashboard visualization |
| Alertmanager | 9093 | Alert notifications |
| PostgreSQL | 5432 | Database |

---

## ⚙️ Setup Instructions

### 1️⃣ Clone and Navigate
```bash
git clone <repo-url>
cd WEEK7
```

### 2️⃣ Start Containers
```bash
docker compose up -d
```

### 3️⃣ Verify Containers
```bash
docker ps
```
You should see containers for `api`, `postgres`, `prometheus`, `grafana`, and `alertmanager` running.

---

## 📊 Step 1: Verify Metrics Collection

Open [http://localhost:8000/metrics](http://localhost:8000/metrics).  
Example metrics output:
```
ai_requests_total{outcome="success"} 10
ai_requests_total{outcome="error"} 2
```

To confirm Prometheus scrapes metrics, visit:  
➡️ [http://localhost:9090/targets](http://localhost:9090/targets)

All targets should be **UP**.

---

## 📈 Step 2: Grafana Dashboard Setup

1. Open Grafana → [http://localhost:3000](http://localhost:3000)
2. Add a **Prometheus datasource** with URL `http://prometheus:9090`
3. Import dashboard JSON (`ai_metrics_dashboard.json`)
4. Set metrics for:
   - **AI Requests Total:**  
     ```promql
     sum(rate(ai_requests_total[$__rate_interval])) by (outcome)
     ```
   - **95th Percentile Latency:**  
     ```promql
     histogram_quantile(0.95, sum(rate(ai_request_duration_seconds_bucket[$__rate_interval])) by (le))
     ```
5. Adjust panel units to **seconds (s)** for latency panels.

---

## 🚨 Step 3: Alert Rules

`rules.yml`:
```yaml
groups:
- name: ai_alerts
  rules:
  - alert: HighP95Latency
    expr: histogram_quantile(0.95, sum(rate(ai_request_duration_seconds_bucket[1m])) by (le)) > 0.5
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "p95 latency > 500ms"

  - alert: ElevatedErrorRate
    expr: rate(ai_requests_total{outcome="error"}[1m]) > 0.05
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "Error rate > 5% in last minute"
```

### Prometheus Configuration (`prometheus.yml`)
```yaml
global:
  scrape_interval: 5s

rule_files:
  - /etc/prometheus/rules.yml

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['prometheus:9090']

  - job_name: 'api'
    static_configs:
      - targets: ['api:8000']
```

---

## 🔔 Step 4: Validate Alerts

Visit [http://localhost:9090/alerts](http://localhost:9090/alerts)  
You should see:
- **HighP95Latency**
- **ElevatedErrorRate**

Alerts show **"Inactive"** by default and **"Firing"** when thresholds are exceeded.

---

## 🧩 Step 5: Grafana Visualization Example

Panels in Grafana include:
- **AI Requests Total** (stacked by outcome)
- **95th Percentile Request Duration** (seconds)
- **Real-time Alert Indicators**

---

## 🧠 Troubleshooting

| Issue | Solution |
|-------|-----------|
| No data in Grafana | Check Prometheus datasource and expressions |
| curl not found in Prometheus | Use `apk add curl` inside container |
| Alerts not visible | Verify `rule_files` path and restart Prometheus |

---

## 📜 Summary
This project successfully integrates Prometheus, Grafana, and Alertmanager for real-time AI API monitoring and alerting. It tracks latency, success/error rates, and visualizes performance trends using Grafana dashboards with alert rules defined in Prometheus.

---

**Author:** Ravi Chandra  
**Course:** Cloud Application Infrastructure – Week 7  
**Topic:** AI Metrics Monitoring and Alerting
