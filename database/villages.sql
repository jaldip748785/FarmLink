CREATE TABLE villages (
    id INT AUTO_INCREMENT PRIMARY KEY,

    district_id INT NOT NULL,

    taluka_id INT NOT NULL,

    name VARCHAR(100) NOT NULL,

    CONSTRAINT fk_village_district
        FOREIGN KEY (district_id)
        REFERENCES districts(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_village_taluka
        FOREIGN KEY (taluka_id)
        REFERENCES talukas(id)
        ON DELETE CASCADE,

    UNIQUE (taluka_id, name)
);

INSERT INTO villages (district_id, taluka_id, name) VALUES
(2, 4, 'Madhapar'),
(2, 4, 'Kothariya'),
(2, 4, 'Munjka'),
(2, 4, 'Kuvadva'),
(2, 4, 'Vavdi'),
(2, 5, 'Lodhika'),
(2, 6, 'Kotda Sangani');