import math
import random
import datetime
import json
import csv
from typing import List, Dict, Any, Tuple

# ==========================================
# 1. DATA MODELS & SENSOR SCHEMAS
# ==========================================

class WeatherObservation:
    def __init__(self, station_id: str, lat: float, lon: float, timestamp: datetime.datetime,
                 temp_c: float, humidity_pct: float, pressure_hpa: float,
                 wind_speed_kmh: float, wind_dir_deg: float, precip_mm: float):
        self.station_id = station_id
        self.lat = lat
        self.lon = lon
        self.timestamp = timestamp
        self.temp_c = temp_c
        self.humidity_pct = humidity_pct
        self.pressure_hpa = pressure_hpa
        self.wind_speed_kmh = wind_speed_kmh
        self.wind_dir_deg = wind_dir_deg
        self.precip_mm = precip_mm
        self.is_valid = True
        self.qc_flags: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "station_id": self.station_id,
            "lat": self.lat,
            "lon": self.lon,
            "timestamp": self.timestamp.isoformat(),
            "temp_c": round(self.temp_c, 2),
            "humidity_pct": round(self.humidity_pct, 1),
            "pressure_hpa": round(self.pressure_hpa, 2),
            "wind_speed_kmh": round(self.wind_speed_kmh, 2),
            "wind_dir_deg": round(self.wind_dir_deg, 1),
            "precip_mm": round(self.precip_mm, 2),
            "is_valid": self.is_valid,
            "qc_flags": self.qc_flags
        }

# ==========================================
# 2. INGESTION & SYNTHETIC TELEMETRY GENERATOR
# ==========================================

class WeatherTelemetrySimulator:
    STATIONS = [
        {"id": "STN_METRO_01", "name": "Downtown Central", "lat": 40.7128, "lon": -74.0060, "base_temp": 22.0},
        {"id": "STN_COAST_02", "name": "Harbor Pier 4", "lat": 40.6892, "lon": -74.0445, "base_temp": 20.2},
        {"id": "STN_AIRPT_03", "name": "International Airport", "lat": 40.6413, "lon": -73.7781, "base_temp": 21.5},
        {"id": "STN_HILLS_04", "name": "North Ridge Peak", "lat": 40.8500, "lon": -74.1500, "base_temp": 17.8},
        {"id": "STN_SUBRB_05", "name": "East Meadowlands", "lat": 40.7306, "lon": -73.9352, "base_temp": 21.0},
    ]

    @classmethod
    def generate_historical_stream(cls, hours: int = 24, inject_anomalies: bool = True) -> List[WeatherObservation]:
        records = []
        base_time = datetime.datetime.now() - datetime.timedelta(hours=hours)
        
        for h in range(hours):
            current_time = base_time + datetime.timedelta(hours=h)
            solar_cycle = math.sin((h - 8) * math.pi / 12)
            
            for stn in cls.STATIONS:
                temp = stn["base_temp"] + (solar_cycle * 4.5) + random.uniform(-0.8, 0.8)
                humidity = max(20.0, min(95.0, 65.0 - (solar_cycle * 15.0) + random.uniform(-3, 3)))
                pressure = 1013.25 - (solar_cycle * 1.5) + random.uniform(-0.5, 0.5)
                wind_speed = max(2.0, 14.0 + (solar_cycle * 6.0) + random.uniform(-3, 3))
                wind_dir = (220.0 + random.uniform(-25, 25)) % 360.0
                precip = 0.0
                
                # Passing storm front simulation
                if 16 <= h <= 18:
                    precip = random.uniform(8.0, 28.0) if stn["id"] in ["STN_METRO_01", "STN_SUBRB_05"] else random.uniform(1.0, 6.0)
                    pressure -= 8.5
                    wind_speed += 28.0
                    temp -= 4.0

                # Sensor faults injection
                if inject_anomalies and h == 10 and stn["id"] == "STN_HILLS_04":
                    temp = 78.5  # Gross hardware spike
                if inject_anomalies and h == 14 and stn["id"] == "STN_COAST_02":
                    pressure = 850.0  # Barometer blowout

                obs = WeatherObservation(
                    station_id=stn["id"],
                    lat=stn["lat"],
                    lon=stn["lon"],
                    timestamp=current_time,
                    temp_c=temp,
                    humidity_pct=humidity,
                    pressure_hpa=pressure,
                    wind_speed_kmh=wind_speed,
                    wind_dir_deg=wind_dir,
                    precip_mm=precip
                )
                records.append(obs)
        return records

# ==========================================
# 3. QUALITY CONTROL (QC) & CLEANING ENGINE
# ==========================================

class MeteorologicalQualityControl:
    LIMITS = {
        "temp_min": -50.0, "temp_max": 55.0,
        "humidity_min": 5.0, "humidity_max": 100.0,
        "pressure_min": 920.0, "pressure_max": 1080.0,
        "wind_speed_max": 250.0,
        "precip_max": 150.0
    }

    @classmethod
    def audit_stream(cls, stream: List[WeatherObservation]) -> Tuple[List[WeatherObservation], Dict[str, int]]:
        stats = {"total": len(stream), "valid": 0, "quarantined": 0}
        cleaned_records = []

        for obs in stream:
            if not (cls.LIMITS["temp_min"] <= obs.temp_c <= cls.LIMITS["temp_max"]):
                obs.qc_flags.append(f"ERR_TEMP_OUT_OF_BOUNDS: {obs.temp_c:.1f}C")
                obs.is_valid = False

            if not (cls.LIMITS["pressure_min"] <= obs.pressure_hpa <= cls.LIMITS["pressure_max"]):
                obs.qc_flags.append(f"ERR_PRESSURE_OUT_OF_BOUNDS: {obs.pressure_hpa:.1f}hPa")
                obs.is_valid = False

            if not (cls.LIMITS["humidity_min"] <= obs.humidity_pct <= cls.LIMITS["humidity_max"]):
                obs.qc_flags.append("ERR_HUMIDITY_UNPHYSICAL")
                obs.is_valid = False

            if obs.wind_speed_kmh > cls.LIMITS["wind_speed_max"]:
                obs.qc_flags.append("ERR_WIND_EXTREME_ANOMALY")
                obs.is_valid = False

            if obs.is_valid:
                stats["valid"] += 1
                cleaned_records.append(obs)
            else:
                stats["quarantined"] += 1

        return cleaned_records, stats

# ==========================================
# 4. METEOROLOGICAL METRICS & ANALYTICS
# ==========================================

class AtmosphericAnalytics:
    @staticmethod
    def calculate_heat_index(temp_c: float, humidity_pct: float) -> float:
        if temp_c < 27.0 or humidity_pct < 40.0:
            return temp_c
        T = (temp_c * 9/5) + 32
        R = humidity_pct
        HI = (-42.379 + 2.04901523*T + 10.14333127*R - 0.22475541*T*R 
              - 0.00683783*T*T - 0.05481717*R*R + 0.00122874*T*T*R 
              + 0.00085282*T*R*R - 0.00000199*T*T*R*R)
        return (HI - 32) * 5/9

    @staticmethod
    def calculate_dew_point(temp_c: float, humidity_pct: float) -> float:
        a = 17.27
        b = 237.7
        alpha = ((a * temp_c) / (b + temp_c)) + math.log(max(humidity_pct, 1.0) / 100.0)
        return (b * alpha) / (a - alpha)

    @classmethod
    def aggregate_station_metrics(cls, records: List[WeatherObservation]) -> Dict[str, Dict[str, Any]]:
        by_stn: Dict[str, List[WeatherObservation]] = {}
        for r in records:
            by_stn.setdefault(r.station_id, []).append(r)

        summary = {}
        for stn_id, obs_list in by_stn.items():
            temps = [o.temp_c for o in obs_list]
            winds = [o.wind_speed_kmh for o in obs_list]
            press = [o.pressure_hpa for o in obs_list]
            total_rain = sum(o.precip_mm for o in obs_list)
            
            summary[stn_id] = {
                "sample_count": len(obs_list),
                "avg_temp_c": round(sum(temps) / len(temps), 2),
                "min_temp_c": round(min(temps), 2),
                "max_temp_c": round(max(temps), 2),
                "avg_wind_kmh": round(sum(winds) / len(winds), 2),
                "max_wind_kmh": round(max(winds), 2),
                "total_precip_mm": round(total_rain, 2),
                "current_pressure_hpa": round(press[-1], 2),
                "pressure_tendency_hpa": round(press[-1] - press[0], 2)
            }
        return summary

# ==========================================
# 5. NOWCASTING & TIME-SERIES PREDICTOR
# ==========================================

class WeatherNowcaster:
    @staticmethod
    def forecast_series(series: List[float], horizon: int = 4, alpha: float = 0.5, beta: float = 0.2) -> List[float]:
        if not series:
            return [0.0] * horizon
        if len(series) == 1:
            return [series[0]] * horizon

        level = series[0]
        trend = series[1] - series[0]

        for i in range(1, len(series)):
            val = series[i]
            last_level = level
            level = alpha * val + (1 - alpha) * (level + trend)
            trend = beta * (level - last_level) + (1 - beta) * trend

        forecasts = []
        for h in range(1, horizon + 1):
            forecasts.append(round(level + h * trend, 2))
        return forecasts

# ==========================================
# 6. DYNAMIC WEATHER ALERT & RISK ENGINE
# ==========================================

class WeatherAlertEngine:
    @classmethod
    def evaluate_station_risk(cls, obs: WeatherObservation, pressure_drop_3h: float) -> List[Dict[str, Any]]:
        alerts = []
        if obs.wind_speed_kmh >= 45.0 or (obs.precip_mm > 15.0 and pressure_drop_3h < -4.0):
            alerts.append({
                "type": "SEVERE_THUNDERSTORM_WARNING",
                "severity": "WARNING",
                "station_id": obs.station_id,
                "message": f"Convective gust ({obs.wind_speed_kmh:.1f} km/h) & rainfall ({obs.precip_mm:.1f} mm/h). Barometric drop: ({pressure_drop_3h:.1f} hPa).",
                "action": "Issue municipal shelter warning; ground ramp stops for aviation."
            })
        if obs.precip_mm >= 25.0:
            alerts.append({
                "type": "FLASH_FLOOD_EMERGENCY",
                "severity": "EMERGENCY",
                "station_id": obs.station_id,
                "message": f"Rainfall rate ({obs.precip_mm:.1f} mm/h) exceeds urban drainage threshold.",
                "action": "Activate municipal drainage pumps; deploy underpass barriers."
            })
        heat_idx = AtmosphericAnalytics.calculate_heat_index(obs.temp_c, obs.humidity_pct)
        if heat_idx >= 38.0:
            alerts.append({
                "type": "EXCESSIVE_HEAT_ADVISORY",
                "severity": "ADVISORY",
                "station_id": obs.station_id,
                "message": f"Apparent Heat Index at {heat_idx:.1f}C (Dry bulb: {obs.temp_c:.1f}C, RH: {obs.humidity_pct:.0f}%).",
                "action": "Open municipal cooling stations; mandate outdoor hydration breaks."
            })
        return alerts

# ==========================================
# 7. DASHBOARD RUNNER & FILE EXPORTER
# ==========================================

class WeatherSystemRunner:
    def __init__(self):
        self.raw_data: List[WeatherObservation] = []
        self.clean_data: List[WeatherObservation] = []
        self.qc_summary: Dict[str, int] = {}
        self.station_metrics: Dict[str, Dict[str, Any]] = {}
        self.alerts: List[Dict[str, Any]] = []

    def execute_pipeline(self):
        print("=" * 80)
        print(">>> AEROCAST WEATHER DATA ANALYSIS SYSTEM: PIPELINE EXECUTION <<<")
        print("=" * 80)

        print("[1/5] Ingesting telemetry stream from 5 regional mesonets (24-hour window)...")
        self.raw_data = WeatherTelemetrySimulator.generate_historical_stream(hours=24, inject_anomalies=True)
        print(f"      [OK] Ingested {len(self.raw_data)} multi-modal observation packets.")

        print("[2/5] Running Quality Control (Plausibility & Anomaly Scrubbing)...")
        self.clean_data, self.qc_summary = MeteorologicalQualityControl.audit_stream(self.raw_data)
        print(f"      [OK] Valid Records: {self.qc_summary['valid']} | Quarantined Faults: {self.qc_summary['quarantined']}")

        print("[3/5] Computing thermodynamic indicators and aggregation statistics...")
        self.station_metrics = AtmosphericAnalytics.aggregate_station_metrics(self.clean_data)

        print("[4/5] Executing Holt-Winters predictive models & Civil Defense Rule Engine...")
        latest_records = [r for r in self.clean_data if r.timestamp == self.clean_data[-1].timestamp]
        for obs in latest_records:
            p_drop = self.station_metrics[obs.station_id]["pressure_tendency_hpa"]
            new_alerts = WeatherAlertEngine.evaluate_station_risk(obs, p_drop)
            self.alerts.extend(new_alerts)

        print("[5/5] Synthesizing executive analytical terminal dashboard...")
        self.render_dashboard()
        self.export_artifacts()

    def render_dashboard(self):
        print("\n" + "=" * 80)
        print("AEROCAST ENTERPRISE METEOROLOGICAL SUMMARY DASHBOARD")
        print("=" * 80)
        
        header = f"{'STATION ID':<16} | {'AVG TEMP':<9} | {'TEMP RANGE':<13} | {'MAX WIND':<9} | {'PRECIP':<8} | {'PRESSURE'}"
        print(header)
        print("-" * 80)
        for stn_id, m in self.station_metrics.items():
            t_range = f"{m['min_temp_c']} - {m['max_temp_c']} C"
            line = f"{stn_id:<16} | {m['avg_temp_c']:>6.1f} C | {t_range:<13} | {m['max_wind_kmh']:>6.1f}kph | {m['total_precip_mm']:>5.1f}mm | {m['current_pressure_hpa']:>7.1f} hPa"
            print(line)
        print("-" * 80)

        metro_records = [r.temp_c for r in self.clean_data if r.station_id == "STN_METRO_01"]
        forecast = WeatherNowcaster.forecast_series(metro_records, horizon=4)
        print(f"\nNOWCAST PREDICTION (STN_METRO_01 - 4-Hour Forward Horizon):")
        print(f"  Current: {metro_records[-1]:.2f} C  -->  T+1h: {forecast[0]} C | T+2h: {forecast[1]} C | T+3h: {forecast[2]} C | T+4h: {forecast[3]} C")

        print(f"\nACTIVE ATMOSPHERIC ALERTS ({len(self.alerts)} ACTIVE):")
        if not self.alerts:
            print("  [ALL CLEAR] No severe weather warnings active across monitoring grids.")
        else:
            for alt in self.alerts:
                print(f"  ! [{alt['severity']}] {alt['type']} at {alt['station_id']}")
                print(f"    Details : {alt['message']}")
                print(f"    Action  : {alt['action']}\n")
        print("=" * 80)

    def export_artifacts(self):
        csv_file = "weather_observations_clean.csv"
        with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "station_id", "lat", "lon", "timestamp", "temp_c", "humidity_pct",
                "pressure_hpa", "wind_speed_kmh", "wind_dir_deg", "precip_mm", "is_valid", "qc_flags"
            ])
            writer.writeheader()
            for r in self.clean_data:
                writer.writerow(r.to_dict())
        
        json_file = "weather_system_report.json"
        report_payload = {
            "generated_at": datetime.datetime.now().isoformat(),
            "quality_control_summary": self.qc_summary,
            "station_metrics": self.station_metrics,
            "active_alerts": self.alerts
        }
        with open(json_file, mode="w", encoding="utf-8") as f:
            json.dump(report_payload, f, indent=4)
            
        print(f"\n[EXPORT COMPLETE] Persisted clean telemetry to '{csv_file}' and executive JSON report to '{json_file}'.\n")

if __name__ == "__main__":
    runner = WeatherSystemRunner()
    runner.execute_pipeline()
