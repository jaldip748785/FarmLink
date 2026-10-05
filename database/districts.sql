CREATE TABLE districts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

INSERT INTO districts (name) VALUES
('Ahmedabad'),
('Rajkot'),
('Surat'),
('Vadodara'),
('Bhavnagar'),
('Jamnagar'),
('Junagadh'),
('Kutch');