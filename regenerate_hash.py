from werkzeug.security import generate_password_hash

# Generate a new hash for the password
new_hash = generate_password_hash("admin123", method="pbkdf2:sha256")
print(f"Generated Hash: {new_hash}")
