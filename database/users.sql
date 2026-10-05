CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,

    full_name VARCHAR(150) NOT NULL,

    email VARCHAR(150) NOT NULL UNIQUE,

    phone VARCHAR(15) NOT NULL UNIQUE,

    password VARCHAR(255) NOT NULL,

    role ENUM('admin','farmer','buyer') DEFAULT 'buyer',

    district_id INT,

    taluka_id INT,

    village_id INT,

    address TEXT,

    profile_image VARCHAR(255),

    is_verified BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_user_district
        FOREIGN KEY (district_id)
        REFERENCES districts(id)
        ON DELETE SET NULL,

    CONSTRAINT fk_user_taluka
        FOREIGN KEY (taluka_id)
        REFERENCES talukas(id)
        ON DELETE SET NULL,

    CONSTRAINT fk_user_village
        FOREIGN KEY (village_id)
        REFERENCES villages(id)
        ON DELETE SET NULL
);