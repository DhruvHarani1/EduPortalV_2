-- Initial Seed Data
-- Note: Passwords must be hashed in the actual application. These are placeholders.

INSERT INTO users (email, password_hash, role) VALUES
('admin@edu.com', 'scrypt:32768:8:1$7fM3D8uG$f3f...', 'admin'),
('faculty@edu.com', 'scrypt:32768:8:1$7fM3D8uG$f3f...', 'faculty'),
('student@edu.com', 'scrypt:32768:8:1$7fM3D8uG$f3f...', 'student');

INSERT INTO course (name, code, department, duration_years, total_semesters) VALUES
('Bachelor of Technology', 'B.Tech', 'Computer Science', 4, 8),
('Master of Business Administration', 'MBA', 'Management', 2, 4),
('Bachelor of Computer Applications', 'BCA', 'Information Technology', 3, 6);
