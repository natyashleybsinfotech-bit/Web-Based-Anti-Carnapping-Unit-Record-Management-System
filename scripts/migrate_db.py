"""Migration script: apply all new columns and status changes to existing DB."""

from app import create_app, mysql

app = create_app()
with app.app_context():
    cur = mysql.connection.cursor()

    alters = [
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS complainant_address VARCHAR(255) AFTER complainant_contact",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS place_of_occurrence ENUM('Street','Residential','Commercial') DEFAULT NULL AFTER incident_location",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS station_concern VARCHAR(150) AFTER barangay_number",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS blotter_entry_no VARCHAR(100) AFTER station_concern",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS vehicle_type ENUM('Motor','Vehicle') DEFAULT NULL AFTER blotter_entry_no",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS ioc VARCHAR(150) AFTER assigned_officer_id",
        "ALTER TABLE cases ADD COLUMN IF NOT EXISTS suspect_details TEXT AFTER ioc",
        "ALTER TABLE cases MODIFY COLUMN status ENUM('Unsolved','Solved','Cleared','Pending','Ongoing','Closed') DEFAULT 'Unsolved'",
        "UPDATE cases SET status = 'Unsolved' WHERE status IN ('Pending', 'Ongoing')",
        "UPDATE cases SET status = 'Solved' WHERE status = 'Closed'",
        "ALTER TABLE cases MODIFY COLUMN status ENUM('Unsolved','Solved','Cleared') DEFAULT 'Unsolved'",
        """CREATE TABLE IF NOT EXISTS suspects (
            id INT AUTO_INCREMENT PRIMARY KEY,
            case_id INT NOT NULL,
            full_name VARCHAR(200),
            alias VARCHAR(200),
            address VARCHAR(255),
            gang_affiliation VARCHAR(200),
            other_details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
        )""",
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
