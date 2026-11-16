-- Optional demo data. Run AFTER schema.sql.
USE job_tracker_app;

INSERT INTO companies (company_name, industry, website, city, state, notes) VALUES
('Tech Solutions Inc', 'Technology', 'www.techsolutions.com', 'Miami', 'Florida', 'Referred by a classmate'),
('Data Analytics Corp', 'Data Science', 'www.dataanalytics.com', 'Austin', 'Texas', NULL),
('Cloud Systems LLC', 'Cloud Computing', 'www.cloudsystems.com', 'Seattle', 'Washington', NULL),
('Digital Innovations', 'Software', 'www.digitalinnovations.com', 'San Francisco', 'California', NULL);

INSERT INTO jobs (company_id, job_title, job_type, salary_min, salary_max, job_url, date_posted, requirements) VALUES
(1, 'Software Developer', 'Full-time', 70000, 90000, NULL, '2026-10-15', '{"required_skills": ["Python", "SQL", "Flask"]}'),
(1, 'Database Administrator', 'Full-time', 75000, 95000, NULL, '2026-10-12', '{"required_skills": ["SQL", "MySQL", "Linux"]}'),
(2, 'Data Analyst', 'Full-time', 65000, 85000, NULL, '2026-10-14', '{"required_skills": ["Python", "SQL", "Tableau"]}'),
(3, 'Cloud Engineer', 'Full-time', 80000, 100000, NULL, '2026-10-08', '{"required_skills": ["AWS", "Linux", "Python", "Docker"]}'),
(4, 'Junior Developer', 'Full-time', 55000, 70000, NULL, '2026-10-20', '{"required_skills": ["Python", "JavaScript", "Git"]}'),
(4, 'IT Support Specialist', 'Full-time', 50000, 62000, NULL, '2026-10-25', '{"required_skills": ["Troubleshooting", "Networking", "Windows", "Ticketing"]}');

INSERT INTO applications (job_id, application_date, status, resume_version, cover_letter_sent, interview_data) VALUES
(1, '2026-10-20', 'Applied', 'v2.1', TRUE, NULL),
(3, '2026-10-18', 'Interview', 'v2.1', TRUE, '{"interview_rounds": 2, "interviewers": ["Sarah Johnson", "Mike Chen"], "feedback": "Strong technical skills, good communication", "next_steps": "Final round scheduled"}'),
(4, '2026-10-10', 'Rejected', 'v2.0', FALSE, NULL),
(6, '2026-11-01', 'Screening', 'v3.0', TRUE, NULL),
(5, '2026-11-03', 'Offer', 'v3.0', TRUE, '{"interview_rounds": 3, "interviewers": ["David Brown"], "next_steps": "Review offer"}');

INSERT INTO contacts (company_id, contact_name, title, email, phone, linkedin_url, notes) VALUES
(1, 'Sarah Johnson', 'HR Manager', 'sjohnson@techsolutions.com', '305-555-0101', NULL, NULL),
(2, 'Michael Chen', 'Technical Recruiter', 'mchen@dataanalytics.com', NULL, NULL, 'Met at career fair'),
(3, 'Emily Williams', 'Hiring Manager', 'ewilliams@cloudsystems.com', NULL, NULL, NULL),
(4, 'David Brown', 'Senior Developer', NULL, NULL, NULL, NULL);
