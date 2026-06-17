-- PNP Case System Database Backup
-- Generated: 2026-04-26 02:32:28
-- Database: carnapping_db

SET FOREIGN_KEY_CHECKS=0;

-- Table: activity_logs
DROP TABLE IF EXISTS `activity_logs`;
CREATE TABLE `activity_logs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `action` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `activity_logs_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=99 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (55, 1, 'Login', 'admin logged in', '2026-04-22 01:55:30');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (56, 1, 'User Created', 'Created new officer: officer', '2026-04-22 01:56:47');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (57, 1, 'Logout', 'admin logged out', '2026-04-22 01:56:56');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (58, 5, 'Login', 'officer logged in', '2026-04-22 01:57:22');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (59, 5, 'Password Change', 'User changed password on first login', '2026-04-22 01:57:57');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (60, 5, 'Login', 'officer logged in', '2026-04-22 02:01:14');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (61, 5, 'Create Case', 'Created case CAR-20260422020822 assigned to officer ID 5', '2026-04-22 02:08:23');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (62, 1, 'Login', 'admin logged in', '2026-04-22 02:11:41');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (63, 1, 'Login', 'admin logged in', '2026-04-22 04:08:09');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (64, 1, 'Login', 'admin logged in', '2026-04-22 04:09:00');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (65, 1, 'Login', 'admin logged in', '2026-04-22 14:03:47');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (66, 1, 'Create Case', 'Created case CAR-20260422141337 assigned to officer ID 5', '2026-04-22 14:13:38');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (67, 1, 'Update Case', 'Updated case CAR-20260422020822 with status Closed', '2026-04-22 14:14:58');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (68, 1, 'User Created', 'Created new officer: officer1', '2026-04-22 14:20:12');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (69, 1, 'Logout', 'admin logged out', '2026-04-22 14:20:18');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (70, 6, 'Login', 'officer1 logged in', '2026-04-22 14:20:37');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (71, 6, 'Password Change', 'User changed password on first login', '2026-04-22 14:21:24');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (72, 1, 'Login', 'admin logged in', '2026-04-22 14:46:10');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (73, 1, 'Login', 'admin logged in', '2026-04-24 00:17:54');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (74, 1, 'Create Case', 'Created case CAR-20260424002129 assigned to officer ID 6', '2026-04-24 00:21:31');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (75, 1, 'Login', 'admin logged in', '2026-04-24 00:50:24');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (76, 1, 'Create Case', 'Created case CAR-20260424005211 assigned to officer ID 5', '2026-04-24 00:52:12');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (77, 1, 'User Created', 'Created new officer: officer2', '2026-04-24 00:53:14');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (78, 1, 'Login', 'admin logged in', '2026-04-25 03:13:12');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (79, 1, 'Create Case', 'Created case CAR-20260425031525 assigned to officer ID 6', '2026-04-25 03:15:26');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (80, 1, 'User Created', 'Created new officer: officer3', '2026-04-25 03:16:58');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (81, 1, 'Login', 'admin logged in', '2026-04-25 03:51:10');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (82, 1, 'Login', 'admin logged in', '2026-04-26 00:57:39');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (83, 1, 'User Created', 'Created new officer: officer4', '2026-04-26 00:58:39');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (84, 1, 'User Created', 'Created new officer: officer5', '2026-04-26 01:02:56');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (85, 1, 'Logout', 'admin logged out', '2026-04-26 01:03:32');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (86, 1, 'Login', 'admin logged in', '2026-04-26 01:03:36');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (87, 1, 'Logout', 'admin logged out', '2026-04-26 01:05:48');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (88, 1, 'Login', 'admin logged in', '2026-04-26 01:08:01');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (89, 1, 'Login', 'admin logged in', '2026-04-26 01:41:22');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (90, 1, 'Login', 'admin logged in', '2026-04-26 01:41:57');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (91, 1, 'Login', 'admin logged in', '2026-04-26 01:48:50');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (92, 1, 'Logout', 'admin logged out', '2026-04-26 01:49:13');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (93, 1, 'Login', 'admin logged in', '2026-04-26 01:50:51');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (94, 1, 'Login', 'admin logged in', '2026-04-26 02:16:40');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (95, 1, 'Login', 'admin logged in', '2026-04-26 02:16:41');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (96, 1, 'Backup Deleted', 'Deleted backup: db_backup_20260426_022404.sql', '2026-04-26 02:29:54');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (97, 1, 'Database Backup', 'Created backup: db_backup_20260426_022957.sql', '2026-04-26 02:29:57');
INSERT INTO `activity_logs` (`id`, `user_id`, `action`, `description`, `created_at`) VALUES (98, 1, 'Backup Deleted', 'Deleted backup: db_backup_20260426_022957.sql', '2026-04-26 02:32:23');

-- Table: cases
DROP TABLE IF EXISTS `cases`;
CREATE TABLE `cases` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `reference_no` varchar(50) NOT NULL,
  `complainant_name` varchar(100) NOT NULL,
  `complainant_email` varchar(150) NOT NULL,
  `complainant_contact` varchar(30) DEFAULT NULL,
  `incident_date` date NOT NULL,
  `incident_location` varchar(255) NOT NULL,
  `barangay_number` int(11) DEFAULT NULL,
  `vehicle_details` varchar(255) DEFAULT NULL,
  `narrative` text NOT NULL,
  `status` enum('Pending','Ongoing','Closed') DEFAULT 'Pending',
  `assigned_officer_id` int(11) DEFAULT NULL,
  `created_by` int(11) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `reference_no` (`reference_no`),
  KEY `assigned_officer_id` (`assigned_officer_id`),
  KEY `created_by` (`created_by`),
  CONSTRAINT `cases_ibfk_1` FOREIGN KEY (`assigned_officer_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
  CONSTRAINT `cases_ibfk_2` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO `cases` (`id`, `reference_no`, `complainant_name`, `complainant_email`, `complainant_contact`, `incident_date`, `incident_location`, `barangay_number`, `vehicle_details`, `narrative`, `status`, `assigned_officer_id`, `created_by`, `created_at`, `updated_at`) VALUES (7, 'CAR-20260422020822', 'tututit', 'tututit15@gmail.com', '09919884161', '2026-04-21', 'Manila', 1, '', 'NINAKAW', 'Closed', 5, 5, '2026-04-22 02:08:22', '2026-04-22 14:14:57');
INSERT INTO `cases` (`id`, `reference_no`, `complainant_name`, `complainant_email`, `complainant_contact`, `incident_date`, `incident_location`, `barangay_number`, `vehicle_details`, `narrative`, `status`, `assigned_officer_id`, `created_by`, `created_at`, `updated_at`) VALUES (8, 'CAR-20260422141337', 'Aaron', 'aaron26@gmail.com', '0912345678', '2026-04-22', 'Manila', 1, '', 'NINAKAW KASI PINABAYAAN KO', 'Pending', 5, 1, '2026-04-22 14:13:37', '2026-04-22 14:13:37');
INSERT INTO `cases` (`id`, `reference_no`, `complainant_name`, `complainant_email`, `complainant_contact`, `incident_date`, `incident_location`, `barangay_number`, `vehicle_details`, `narrative`, `status`, `assigned_officer_id`, `created_by`, `created_at`, `updated_at`) VALUES (9, 'CAR-20260424002129', 'Aaron', 'aaron26@gmail.com', '0912345678', '2026-04-22', 'Manila', 2, '', 'ninakaw', 'Pending', 6, 1, '2026-04-24 00:21:29', '2026-04-24 00:21:29');
INSERT INTO `cases` (`id`, `reference_no`, `complainant_name`, `complainant_email`, `complainant_contact`, `incident_date`, `incident_location`, `barangay_number`, `vehicle_details`, `narrative`, `status`, `assigned_officer_id`, `created_by`, `created_at`, `updated_at`) VALUES (10, 'CAR-20260424005211', 'Naty, Ashley B.', 'naty.ashley.bsinfotech@gmail.com', '', '2026-04-24', 'Manila', 2, '', 'NINAKAW', 'Pending', 5, 1, '2026-04-24 00:52:11', '2026-04-24 00:52:11');
INSERT INTO `cases` (`id`, `reference_no`, `complainant_name`, `complainant_email`, `complainant_contact`, `incident_date`, `incident_location`, `barangay_number`, `vehicle_details`, `narrative`, `status`, `assigned_officer_id`, `created_by`, `created_at`, `updated_at`) VALUES (11, 'CAR-20260425031525', 'Naty, Ashley B.', 'naty.ashley.bsinfotech@gmail.com', '09919884161', '2026-04-25', 'Manila', 1, '', 'NINAKAW', 'Pending', 6, 1, '2026-04-25 03:15:25', '2026-04-25 03:15:25');

-- Table: report_exports
DROP TABLE IF EXISTS `report_exports`;
CREATE TABLE `report_exports` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `case_id` int(11) NOT NULL,
  `pdf_path` varchar(255) DEFAULT NULL,
  `qr_path` varchar(255) DEFAULT NULL,
  `emailed_to` varchar(150) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `case_id` (`case_id`),
  CONSTRAINT `report_exports_ibfk_1` FOREIGN KEY (`case_id`) REFERENCES `cases` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO `report_exports` (`id`, `case_id`, `pdf_path`, `qr_path`, `emailed_to`, `created_at`) VALUES (7, 7, 'exports/CAR-20260422020822.pdf', 'qr/CAR-20260422020822.png', 'tututit15@gmail.com', '2026-04-22 02:08:22');
INSERT INTO `report_exports` (`id`, `case_id`, `pdf_path`, `qr_path`, `emailed_to`, `created_at`) VALUES (8, 8, 'exports/CAR-20260422141337.pdf', 'qr/CAR-20260422141337.png', 'aaron26@gmail.com', '2026-04-22 14:13:37');
INSERT INTO `report_exports` (`id`, `case_id`, `pdf_path`, `qr_path`, `emailed_to`, `created_at`) VALUES (9, 9, 'exports/CAR-20260424002129.pdf', 'qr/CAR-20260424002129.png', 'aaron26@gmail.com', '2026-04-24 00:21:29');
INSERT INTO `report_exports` (`id`, `case_id`, `pdf_path`, `qr_path`, `emailed_to`, `created_at`) VALUES (10, 10, 'exports/CAR-20260424005211.pdf', 'qr/CAR-20260424005211.png', 'naty.ashley.bsinfotech@gmail.com', '2026-04-24 00:52:11');
INSERT INTO `report_exports` (`id`, `case_id`, `pdf_path`, `qr_path`, `emailed_to`, `created_at`) VALUES (11, 11, 'exports/CAR-20260425031525.pdf', 'qr/CAR-20260425031525.png', 'naty.ashley.bsinfotech@gmail.com', '2026-04-25 03:15:25');

-- Table: users
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `full_name` varchar(100) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role` enum('admin','officer') NOT NULL,
  `email` varchar(150) DEFAULT NULL,
  `is_active` tinyint(4) DEFAULT 1,
  `force_password_change` tinyint(4) DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO `users` (`id`, `full_name`, `username`, `password_hash`, `role`, `email`, `is_active`, `force_password_change`, `created_at`) VALUES (1, 'ASH NATY', 'admin', 'admin123', 'admin', 'ashnaty1115@gmail.com\r\n', 1, 0, '2026-04-22 01:54:32');
INSERT INTO `users` (`id`, `full_name`, `username`, `password_hash`, `role`, `email`, `is_active`, `force_password_change`, `created_at`) VALUES (5, 'NATY', 'officer', '$2b$12$a0ZGM9z.GreKR3YM0Riwj.Nt9lRw1InCguK2.xu42MjEFr8n.p9Ui', 'officer', 'naty15@gmail.com', 1, 0, '2026-04-22 01:56:47');
INSERT INTO `users` (`id`, `full_name`, `username`, `password_hash`, `role`, `email`, `is_active`, `force_password_change`, `created_at`) VALUES (6, 'Mark Cacho', 'officer1', '$2b$12$DFSGZhbc/YyTN9QYmnxJ3.pfviZaSC1nMU2yRN1mZ8FtTUUn1amxy', 'officer', 'markcacho@gmail.com', 1, 0, '2026-04-22 14:20:12');
INSERT INTO `users` (`id`, `full_name`, `username`, `password_hash`, `role`, `email`, `is_active`, `force_password_change`, `created_at`) VALUES (7, 'Jennifer', 'officer2', '$2b$12$S7MW5qBmJU3Sp0KEgBvL1evaD5AGuF.499a.gCdmmuLMpEkv/H9EG', 'officer', 'jennifer@gmail.com', 1, 1, '2026-04-24 00:53:14');
INSERT INTO `users` (`id`, `full_name`, `username`, `password_hash`, `role`, `email`, `is_active`, `force_password_change`, `created_at`) VALUES (8, 'Arwind Maalat', 'officer3', '$2b$12$diCOcJ2qmeEkDuOy7YZBKeyu/7bIIp6ifwjY1RX.eDHa11PwyhlyC', 'officer', 'arwindmaalat@gmail.com', 1, 1, '2026-04-25 03:16:57');
INSERT INTO `users` (`id`, `full_name`, `username`, `password_hash`, `role`, `email`, `is_active`, `force_password_change`, `created_at`) VALUES (9, 'Martin Gabe', 'officer4', '$2b$12$WWedMejZbs2GNFgOlAiCVeTxoxQBjg4dWrqKsgwWqNblSdU49Kg9e', 'officer', 'martin@gmail.com', 1, 1, '2026-04-26 00:58:39');
INSERT INTO `users` (`id`, `full_name`, `username`, `password_hash`, `role`, `email`, `is_active`, `force_password_change`, `created_at`) VALUES (10, 'ashley', 'officer5', '$2b$12$vtOQ9Imqg.j1pejE3tkkQe85t8BpHd4K3gbpaAC6VDbnOHUjzJipq', 'officer', 'ashley@gmail.com', 1, 1, '2026-04-26 01:02:56');

SET FOREIGN_KEY_CHECKS=1;