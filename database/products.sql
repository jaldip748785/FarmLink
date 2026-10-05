CREATE TABLE products (

    id INT AUTO_INCREMENT PRIMARY KEY,

    farmer_id INT NOT NULL,

    category_id INT NOT NULL,

    title VARCHAR(150) NOT NULL,

    description TEXT,

    price DECIMAL(10,2) NOT NULL,

    quantity INT NOT NULL,

    unit VARCHAR(20),

    image VARCHAR(255),

    district_id INT,

    taluka_id INT,

    village_id INT,

    status ENUM('Available','Sold') DEFAULT 'Available',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (farmer_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    FOREIGN KEY (category_id)
        REFERENCES categories(id)
        ON DELETE CASCADE,

    FOREIGN KEY (district_id)
        REFERENCES districts(id)
        ON DELETE SET NULL,

    FOREIGN KEY (taluka_id)
        REFERENCES talukas(id)
        ON DELETE SET NULL,

    FOREIGN KEY (village_id)
        REFERENCES villages(id)
        ON DELETE SET NULL
);