CREATE TABLE users (
	id INT AUTO_INCREMENT PRIMARY KEY,
	username VARCHAR(255) UNIQUE NOT NULL,
	email VARCHAR(255),
	password VARCHAR(255)
);

INSERT INTO users (username, email, password)
VALUES ('admin', 'admin@demo.local', 'admin123');
