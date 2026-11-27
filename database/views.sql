-- Reporting views, (re)created by fast_backend/start.sh after the migrations.

-- Latest reading of every station.
CREATE OR REPLACE VIEW v_station_latest AS
SELECT DISTINCT ON (r.station_code)
       s.station_code, s.name, s.reach, s.chainage_km, r.ts AS last_seen,
       r.ph, r."do", r.ec, r.turbidity, r.temperature, r.ammonium, r.nitrate, r.bod, r.cod, r.water_level, r.flow
FROM river_readings r
JOIN stations s ON s.station_code = r.station_code
ORDER BY r.station_code, r.ts DESC;

-- Daily means per station (handy for exports and QA).
CREATE OR REPLACE VIEW v_station_daily AS
SELECT station_code, date_trunc('day', ts) AS day,
       avg(ph) AS ph, avg("do") AS "do", avg(ec) AS ec, avg(turbidity) AS turbidity, avg(ammonium) AS ammonium,
       avg(bod) AS bod, avg(water_level) AS water_level, avg(flow) AS flow, count(*) AS n
FROM river_readings
GROUP BY station_code, date_trunc('day', ts);
