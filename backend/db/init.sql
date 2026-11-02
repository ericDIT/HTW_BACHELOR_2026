-- Stationstabelle
CREATE TABLE IF NOT EXISTS stations (
	station_id VARCHAR(100) PRIMARY KEY,
	station_name VARCHAR(100) NOT NULL,
	lon NUMERIC(9,6),
	lat NUMERIC(9,6),
	elevator BOOLEAN DEFAULT FALSE,
	blind_strip BOOLEAN DEFAULT FALSE
);

-- Linientabelle
CREATE TABLE IF NOT EXISTS lines (
    line_id VARCHAR(100) PRIMARY KEY,
    line_name VARCHAR(20) NOT NULL,
    transport_type VARCHAR(20),
    operator VARCHAR(40)
);

-- Junction-Tabelle da eine station mehrere Linien haben kann und eine Linie mehrere Stationen befährt
CREATE TABLE IF NOT EXISTS line_stations (
    line_id VARCHAR(100) REFERENCES lines(line_id) ON DELETE CASCADE,
    station_id VARCHAR(100) REFERENCES stations(station_id) ON DELETE CASCADE,
    PRIMARY KEY (line_id, station_id)
);

-- Verspätungstabelle (Verspätung für eine Linie an einer Station zu einem bestimmten Zeitpunkt)
CREATE TABLE IF NOT EXISTS delays (
    delay_id SERIAL PRIMARY KEY,
    trip_id VARCHAR(100) NOT NULL,
    station_id VARCHAR(100) NOT NULL REFERENCES stations(station_id),
    line_id VARCHAR(100) NOT NULL REFERENCES lines(line_id),
    delay_day DATE NOT NULL,
    scheduled_time TIMESTAMP NOT NULL,
    cancelled BOOLEAN DEFAULT FALSE,
    actual_time TIMESTAMP,
    delay_minutes INT,
    occupancy VARCHAR(1)
);

CREATE TABLE IF NOT EXISTS delay_facts_daily_by_line (
    station_id VARCHAR(100) NOT NULL REFERENCES stations(station_id),
    line_id VARCHAR(100) NOT NULL REFERENCES lines(line_id),
    fact_date DATE NOT NULL,
    avg_delay NUMERIC(9,2),
    max_delay INT,
    delay_rate NUMERIC, -- Wert zwischen null und eins
    morning_avg_delay NUMERIC(9,2),
    evening_avg_delay NUMERIC(9,2),
    morning_departures INT,
    evening_departures INT,
    total_departures INT,
    occupancy_occurance_l INT,
    occupancy_occurance_m INT,
    occupancy_occurance_h INT,
    PRIMARY KEY (line_id, station_id, fact_date)
);

CREATE TABLE IF NOT EXISTS delay_facts_daily_by_station (
    station_id VARCHAR(100) NOT NULL REFERENCES stations(station_id),
    fact_date DATE NOT NULL,
    avg_delay NUMERIC(9,2),
    delay_rate NUMERIC, -- Wert zwischen null und eins
    morning_avg_delay NUMERIC(9,2),
    evening_avg_delay NUMERIC(9,2),
    morning_departures INT,
    evening_departures INT,
    occupancy_occurance_l INT,
    occupancy_occurance_m INT,
    occupancy_occurance_h INT,
    total_departures INT,
    max_delay INT,
    avg_bus_delay NUMERIC(9,2),
    avg_train_delay NUMERIC(9,2),
    PRIMARY KEY (station_id, fact_date)
);