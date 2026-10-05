CREATE TABLE talukas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    district_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,

    FOREIGN KEY (district_id)
        REFERENCES districts(id)
        ON DELETE CASCADE,

    UNIQUE (district_id, name)
);

INSERT INTO talukas (district_id, name) VALUES
(1, 'Ahmedabad'),
(1, 'Dholka'),
(1, 'Sanand'),

(2, 'Rajkot'),
(2, 'Gondal'),
(2, 'Jetpur'),

(3, 'Surat'),
(3, 'Bardoli'),
(3, 'Olpad'),

(4, 'Vadodara'),
(4, 'Padra'),
(4, 'Savli'),

(5, 'Bhavnagar'),
(5, 'Gariadhar'),
(5, 'Mahuva'),

(6, 'Jamnagar'),
(6, 'Dhrol'),
(6, 'Kalavad'),

(7, 'Junagadh'),
(7, 'Keshod'),
(7, 'Mendarda'),

(8, 'Bhuj'),
(8, 'Anjar'),
(8, 'Gandhidham');