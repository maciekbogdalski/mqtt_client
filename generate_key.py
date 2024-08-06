from cryptography.fernet import Fernet

# Generate a key
key = Fernet.generate_key()

# Print the key (you should save it securely instead of printing it)
print(f"Encryption Key: {key.decode()}")

# Save the key to a file
with open('encryption_key.key', 'wb') as key_file:
    key_file.write(key)
