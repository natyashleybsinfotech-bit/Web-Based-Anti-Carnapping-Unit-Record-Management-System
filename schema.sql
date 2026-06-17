CREATE DATABASE IF NOT EXISTS carnapping_db;
USE carnapping_db;

-- ============================================================
-- TABLE 1: Users
-- Stores information about system users (admins & officers)
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    User_ID INT AUTO_INCREMENT PRIMARY KEY,
    Fullname VARCHAR(100) NOT NULL,
    Email VARCHAR(150),
    Role ENUM('admin','officer') NOT NULL,
    Password VARCHAR(255) NOT NULL,
    Date_Created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Extra operational fields (not in paper schema but required by app)
    username VARCHAR(50) UNIQUE NOT NULL,
    is_active TINYINT DEFAULT 1,
    force_password_change TINYINT DEFAULT 0
);

-- ============================================================
-- TABLE 2: Complainants
-- Stores contact and personal details of individuals filing complaints
-- ============================================================
CREATE TABLE IF NOT EXISTS complainants (
    Complainant_ID INT AUTO_INCREMENT PRIMARY KEY,
    First_Name VARCHAR(100) NOT NULL,
    Last_Name VARCHAR(100) NOT NULL,
    Contact_Number VARCHAR(30),
    Address VARCHAR(255)
);

-- ============================================================
-- TABLE 3: Cases
-- Central table recording each incident/complaint
-- ============================================================
CREATE TABLE IF NOT EXISTS cases (
    Case_ID INT AUTO_INCREMENT PRIMARY KEY,
    Status ENUM('Pending','Ongoing','Closed') DEFAULT 'Pending',
    Case_Description TEXT NOT NULL,
    Priority ENUM('Low','Normal','High') DEFAULT 'Normal',
    Created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    Case_Title VARCHAR(255),
    Complainant_ID INT NOT NULL,
    User_ID INT NOT NULL,
    -- Extra operational fields required by app
    reference_no VARCHAR(50) UNIQUE NOT NULL,
    incident_date DATE,
    incident_location VARCHAR(255),
    barangay_number INT,
    vehicle_details VARCHAR(255),
    narrative TEXT,
    assigned_officer_id INT NULL,
    created_by INT NOT NULL,
    FOREIGN KEY (Complainant_ID) REFERENCES complainants(Complainant_ID) ON DELETE RESTRICT,
    FOREIGN KEY (User_ID) REFERENCES users(User_ID) ON DELETE CASCADE,
    FOREIGN KEY (assigned_officer_id) REFERENCES users(User_ID) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(User_ID) ON DELETE CASCADE
);

-- ============================================================
-- TABLE 4: Receipts
-- Stores details of receipts generated for a case
-- ============================================================
CREATE TABLE IF NOT EXISTS receipts (
    Receipt_ID INT AUTO_INCREMENT PRIMARY KEY,
    Receipt_Code VARCHAR(50),
    Date_Issued TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    email_sent VARCHAR(150),
    Case_ID INT NOT NULL,
    -- Extra operational fields
    pdf_path VARCHAR(255),
    qr_path VARCHAR(255),
    FOREIGN KEY (Case_ID) REFERENCES cases(Case_ID) ON DELETE CASCADE
);

-- ============================================================
-- TABLE 5: Activity_Logs
-- Records a history of actions taken within the system
-- ============================================================
CREATE TABLE IF NOT EXISTS activity_logs (
    Log_ID INT AUTO_INCREMENT PRIMARY KEY,
    Action_Type VARCHAR(100) NOT NULL,
    Timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Description TEXT,
    User_ID INT NOT NULL,
    FOREIGN KEY (User_ID) REFERENCES users(User_ID) ON DELETE CASCADE
);

-- ============================================================
-- TABLE 6: Hotspot
-- Stores aggregated data summarizing carnapping cases per barangay
-- ============================================================
CREATE TABLE IF NOT EXISTS hotspot (
    Hotspot_ID INT AUTO_INCREMENT PRIMARY KEY,
    barangay_name VARCHAR(100) NOT NULL,
    district_name VARCHAR(100) NOT NULL,
    period_type ENUM('weekly','monthly') DEFAULT 'monthly',
    risk_level VARCHAR(50) NOT NULL,
    total_cases INT DEFAULT 0,
    resolution_rate VARCHAR(50) NOT NULL
);
