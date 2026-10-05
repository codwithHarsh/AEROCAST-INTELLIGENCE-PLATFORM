# AEROCAST INTELLIGENCE PLATFORM
### High-Performance Meteorological Telemetry Ingestion, Quality Control & Nowcasting System

---

## 📌 Project Overview
The **Aerocast Intelligence Platform** is an end-to-end meteorological data processing and nowcasting engine designed to ingest, validate, and analyze real-time observation feeds from distributed weather mesonets.

Built with Python's standard library, the platform runs with zero external runtime dependencies and provides real-time atmospheric intelligence, sensor quality control, and civil defense alerting.

---

## 🚀 Key Features

* **Multi-Station Telemetry Ingestion**: Simulates 24-hour continuous multi-sensor data streams across 5 regional observation stations.
* **Deterministic Quality Control (QC)**: Automatically screens and quarantines physical sensor anomalies (hardware spikes, barometer blowouts).
* **Atmospheric Thermodynamics**: Computes Steadman Heat Index, Magnus-Tetens Dew Point, and 24-hour barometric tendencies.
* **Predictive Nowcasting**: Generates 4-hour forward localized temperature projections using Holt-Winters double exponential smoothing.
* **Civil Defense Alert Engine**: Real-time threshold evaluation for severe thunderstorms, flash flood risks, and excessive heat advisories.
* **Dual Artifact Export**: Persists clean telemetry to `weather_observations_clean.csv` and comprehensive summary metrics to `weather_system_report.json`.

---

## 🛠️ Monitored Stations

| Station ID | Station Name | Latitude | Longitude | Base Temp |
| :--- | :--- | :--- | :--- | :--- |
| `STN_METRO_01` | Downtown Central | 40.7128° N | -74.0060° W | 22.0 °C |
| `STN_COAST_02` | Harbor Pier 4 | 40.6892° N | -74.0445° W | 20.2 °C |
| `STN_AIRPT_03` | International Airport | 40.6413° N | -73.7781° W | 21.5 °C |
| `STN_HILLS_04` | North Ridge Peak | 40.8500° N | -74.1500° W | 17.8 °C |
| `STN_SUBRB_05` | East Meadowlands | 40.7306° N | -73.9352° W | 21.0 °C |

---

## 💻 How to Run

1. **Clone or download the repository**:
   ```bash
   git clone [https://github.com/codwithHarsh/AEROCAST-INTELLIGENCE-PLATFORM.git](https://github.com/codwithHarsh/AEROCAST-INTELLIGENCE-PLATFORM.git)
   cd AEROCAST-INTELLIGENCE-PLATFORM
