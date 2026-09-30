CREATE TABLE IF NOT EXISTS `customer` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(120) NOT NULL,
    `phone` VARCHAR(20),
    `email` VARCHAR(120) UNIQUE,
    `password_hash` VARCHAR(128)
);