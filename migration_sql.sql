INSERT INTO
    admin (
        username,
        email,
        password_hash
    )
VALUES (
        'admin',
        'admin@example.com',
        $ (
            SELECT hash_password ('Password123')
        )
    );