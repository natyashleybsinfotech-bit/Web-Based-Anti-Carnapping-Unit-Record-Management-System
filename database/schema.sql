CREATE DATABASE IF NOT EXISTS carnapping_db;
USE carnapping_db;

-- ============================================================
-- TABLE 1: Users
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150),
    role ENUM('admin','officer') NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    is_active TINYINT DEFAULT 1,
    force_password_change TINYINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLE 2: Complainants
-- ============================================================
CREATE TABLE IF NOT EXISTS complainants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    contact_number VARCHAR(30),
    address VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- TABLE 3: Cases
-- Status: Unsolved / Solved / Cleared  (changed from Pending/Ongoing/Closed)
-- New fields: blotter_entry_no, ioc (Investigator of Case), vehicle_type,
--             suspect_details, station_concern, place_of_occurrence,
--             complainant_address
-- ============================================================
CREATE TABLE IF NOT EXISTS cases (
    id INT AUTO_INCREMENT PRIMARY KEY,
    reference_no VARCHAR(50) UNIQUE NOT NULL,

    -- Complainant snapshot (denormalized for quick display)
    complainant_name VARCHAR(200) NOT NULL,
    complainant_email VARCHAR(150),
    complainant_contact VARCHAR(30),
    complainant_address VARCHAR(255),

    -- Incident info
    incident_date DATE,
    incident_time TIME,
    incident_location VARCHAR(255),
    place_of_occurrence ENUM('Street','Residential','Commercial') DEFAULT NULL,
    barangay_number INT,
    station_concern VARCHAR(150),

    -- Blotter reference
    blotter_entry_no VARCHAR(100),

    -- Vehicle info
    vehicle_type ENUM('Motor','Vehicle') DEFAULT NULL,
    vehicle_details VARCHAR(255),

    -- Case management
    status ENUM('Unsolved','Solved','Cleared') DEFAULT 'Unsolved',
    narrative TEXT,
    assigned_officer_id INT NULL,
    ioc VARCHAR(150),

    -- Suspect details (summary — full records in suspects table)
    suspect_details TEXT,

    -- FK references
    created_by INT NOT NULL,
    complainant_id INT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (assigned_officer_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (complainant_id) REFERENCES complainants(id) ON DELETE SET NULL
);

-- ============================================================
-- TABLE 4: Suspects
-- Separate table for detailed suspect records per case
-- ============================================================
CREATE TABLE IF NOT EXISTS suspects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    case_id INT NOT NULL,
    full_name VARCHAR(200),
    alias VARCHAR(200),
    address VARCHAR(255),
    gang_affiliation VARCHAR(200),
    other_details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
);

-- ============================================================
-- TABLE 5: Receipts
-- ============================================================
CREATE TABLE IF NOT EXISTS receipts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Receipt_Code VARCHAR(50),
    Date_Issued TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    email_sent VARCHAR(150),
    Case_ID INT NOT NULL,
    pdf_path VARCHAR(255),
    qr_path VARCHAR(255),
    FOREIGN KEY (Case_ID) REFERENCES cases(id) ON DELETE CASCADE
);

-- ============================================================
-- TABLE 6: Activity_Logs
-- ============================================================
CREATE TABLE IF NOT EXISTS activity_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    action VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ============================================================
-- TABLE 7: Hotspot
-- ============================================================
CREATE TABLE IF NOT EXISTS hotspot (
    id INT AUTO_INCREMENT PRIMARY KEY,
    barangay_name VARCHAR(100) NOT NULL,
    district_name VARCHAR(100) NOT NULL,
    period_type ENUM('weekly','monthly') DEFAULT 'monthly',
    risk_level VARCHAR(50) NOT NULL,
    total_cases INT DEFAULT 0,
    resolution_rate VARCHAR(50) NOT NULL
);

-- ============================================================
-- ALTER scripts — run these on an EXISTING database to add new columns
-- Safe to run multiple times (uses IF NOT EXISTS logic via stored proc)
-- ============================================================

-- Add new columns to cases if upgrading existing DB
ALTER TABLE cases
    ADD COLUMN IF NOT EXISTS complainant_address VARCHAR(255) AFTER complainant_contact,
    ADD COLUMN IF NOT EXISTS place_of_occurrence ENUM('Street','Residential','Commercial') DEFAULT NULL AFTER incident_location,
    ADD COLUMN IF NOT EXISTS station_concern VARCHAR(150) AFTER barangay_number,
    ADD COLUMN IF NOT EXISTS blotter_entry_no VARCHAR(100) AFTER station_concern,
    ADD COLUMN IF NOT EXISTS vehicle_type ENUM('Motor','Vehicle') DEFAULT NULL AFTER blotter_entry_no,
    ADD COLUMN IF NOT EXISTS ioc VARCHAR(150) AFTER assigned_officer_id,
    ADD COLUMN IF NOT EXISTS suspect_details TEXT AFTER ioc;

-- Change status ENUM (preserves existing data, old values map to Unsolved)
ALTER TABLE cases MODIFY COLUMN status ENUM('Unsolved','Solved','Cleared','Pending','Ongoing','Closed') DEFAULT 'Unsolved';
-- After data migration, trim old values:
UPDATE cases SET status = 'Unsolved' WHERE status IN ('Pending', 'Ongoing');
UPDATE cases SET status = 'Solved'   WHERE status = 'Closed';
ALTER TABLE cases MODIFY COLUMN status ENUM('Unsolved','Solved','Cleared') DEFAULT 'Unsolved';

-- Create suspects table if it doesn't exist
CREATE TABLE IF NOT EXISTS suspects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    case_id INT NOT NULL,
    full_name VARCHAR(200),
    alias VARCHAR(200),
    address VARCHAR(255),
    gang_affiliation VARCHAR(200),
    other_details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE
);
