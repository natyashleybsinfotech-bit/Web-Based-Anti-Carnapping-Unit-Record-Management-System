"""Migration script: apply all new columns and status changes to existing DB."""

from app import create_app, mysql

app = create_app()
with app.app_context():
    cur = mysql.connection.cursor()

    alters = [
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS complainant_address VARCHAR(255) AFTER complainant_contact",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS place_of_occurrence ENUM('Street','Residential','Commercial') DEFAULT NULL AFTER incident_location",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS station_concern_id INT AFTER barangay_number",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS blotter_entry_no VARCHAR(100) AFTER station_concern_id",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS vehicle_type ENUM('Motor','Vehicle') DEFAULT NULL AFTER blotter_entry_no",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS ioc VARCHAR(150) AFTER assigned_officer_id",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS suspect_details TEXT AFTER ioc",
        "CREATE TABLE IF NOT EXISTS police_stations (\n            id INT AUTO_INCREMENT PRIMARY KEY,\n            station_number INT NOT NULL UNIQUE,\n            station_name VARCHAR(150) NOT NULL,\n            location VARCHAR(255) NOT NULL,\n            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n        )",
        "INSERT IGNORE INTO police_stations (station_number, station_name, location) VALUES (1, 'Balut / Raxabago Police Station', 'Balut, Tondo'), (2, 'Moriones Police Station', 'Moriones, Tondo'), (3, 'Sta. Cruz Police Station', 'Sta. Cruz, Manila'), (4, 'Sampaloc Police Station', 'Sampaloc, Manila'), (5, 'Ermita Police Station', 'Ermita, Manila'), (6, 'Sta. Ana Police Station', 'Sta. Ana, Manila'), (7, 'Jose Abad Santos Police Station', 'Jose Abad Santos, Manila'), (8, 'Sta. Mesa Police Station', 'Sta. Mesa, Manila'), (9, 'Malate Police Station', 'Malate, Manila'), (10, 'Pandacan Police Station', 'Pandacan, Manila'), (11, 'Meisic Police Station', 'Meisic St., Binondo, Manila'), (12, 'Delpan Police Station', 'Delpan, Tondo, Manila'), (13, 'BASECO Police Station', 'BASECO, Port Area, Manila')",
        "ALTER TABLE cases MODIFY COLUMN status ENUM('Unsolved','Solved','Cleared','Pending','Ongoing','Closed') DEFAULT 'Unsolved'",
        "UPDATE cases SET status = 'Unsolved' WHERE status IN ('Pending', 'Ongoing')",
        "UPDATE cases SET status = 'Solved' WHERE status = 'Closed'",
        "ALTER TABLE cases MODIFY COLUMN status ENUM('Unsolved','Solved','Cleared') DEFAULT 'Unsolved'",
        "ALTER TABLE cases ADD CONSTRAINT fk_case_station_concern FOREIGN KEY (station_concern_id) REFERENCES police_stations(id) ON DELETE SET NULL",
        "CREATE TABLE IF NOT EXISTS suspects (\n            id INT AUTO_INCREMENT PRIMARY KEY,\n            case_id INT NOT NULL,\n            full_name VARCHAR(200),\n            alias VARCHAR(200),\n            address VARCHAR(255),\n            gang_affiliation VARCHAR(200),\n            other_details TEXT,\n            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n            FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE\n        )",
    ]

    for sql in alters:
        try:
            cur.execute(sql)
            print("OK:", sql[:80].strip())
        except Exception as e:
            print("SKIP:", str(e)[:120])

    mysql.connection.commit()
    cur.close()
    print("\nMIGRATION COMPLETE")
