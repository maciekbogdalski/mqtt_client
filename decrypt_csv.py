import csv
from cryptography.fernet import Fernet

# Load the encryption key from the file
with open('encryption_key.key', 'rb') as key_file:
    encryption_key = key_file.read()

cipher_suite = Fernet(encryption_key)


# Function to decrypt messages
def decrypt_message(encrypted_message):
    return cipher_suite.decrypt(encrypted_message.encode()).decode()


# Function to read and decrypt CSV file
def read_decrypted_csv(file_path):
    try:
        with open(file_path, mode='r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            decrypted_rows = []
            for row in reader:
                decrypted_row = {
                    'topic': row['topic'],
                    'message': decrypt_message(row['message']),
                    'timestamp': row['timestamp']
                }
                decrypted_rows.append(decrypted_row)
            return decrypted_rows
    except Exception as e:
        print(f"Error reading or decrypting CSV file: {e}")
        return []


# Function to save decrypted rows to a new CSV file
def save_decrypted_csv(decrypted_rows, output_file_path):
    try:
        with open(output_file_path, mode='w', newline='') as csvfile:
            fieldnames = ['topic', 'message', 'timestamp']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in decrypted_rows:
                writer.writerow(row)
        print(f"Decrypted CSV saved to {output_file_path}")
    except Exception as e:
        print(f"Error saving decrypted CSV file: {e}")


# Main function to read, decrypt, and save CSV content
def main():
    input_file_path = 'mqtt_messages.csv'
    output_file_path = 'mqtt_messages_decrypted.csv'
    decrypted_rows = read_decrypted_csv(input_file_path)

    if decrypted_rows:
        print(f"Decrypted content of {input_file_path}:")
        for row in decrypted_rows:
            print(row)
        save_decrypted_csv(decrypted_rows, output_file_path)
    else:
        print("No decrypted content available or an error occurred.")


if __name__ == '__main__':
    main()
