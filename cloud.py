import serial
import time
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from datetime import datetime

# Path to your Firebase service account key file
SERVICE_ACCOUNT_KEY = '/Users/saimaster/Desktop/Programs/Mini/Trial graph/serviceAccountKey.json'
DATABASE_URL = 'https://air-check-f96be-default-rtdb.firebaseio.com'

def initialize_firebase():
    # Initialize Firebase
    try:
        cred = credentials.Certificate(SERVICE_ACCOUNT_KEY)
        firebase_admin.initialize_app(cred, {
            'databaseURL': DATABASE_URL
        })
    except Exception as e:
        print(f"Firebase initialization error: {e}")
        raise

def parse_data(data):
    try:
        # Split the data by commas
        parts = [part.strip() for part in data.split(',')]
        # Ensure that the parts list has exactly 5 elements
        if len(parts) != 5:
            raise ValueError("Data does not contain exactly 5 parts")
        # Extract data from each part
        co2 = parts[0]
        temp_dht = float(parts[1])  # Convert to float for temperature conversion
        humidity_dht = parts[2]
        pressure = parts[3]
        temp_bmp = parts[4]
        return co2, temp_dht, humidity_dht, pressure, temp_bmp
    except (IndexError, ValueError) as e:
        print(f"Error parsing data: {e}")
        return None

def celsius_to_fahrenheit(celsius):
    return celsius * 9/5 + 32

def get_timestamp():
    now = datetime.now()
    return now.strftime("%Y-%m-%d_%H-%M-%S")

def send_to_firebase(timestamp, data):
    try:
        ref = db.reference(f'/Data/{timestamp}')
        ref.set(data)
    except Exception as e:
        print(f"Firebase write error: {e}")

def read_serial_data():
    try:
        # Adjust the serial port name for macOS
        ser = serial.Serial('/dev/tty.usbmodem101', 9600)  # Replace with the correct identifier
        time.sleep(2)  # Wait for the serial connection to initialize
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8').strip()
                print(f"Received raw data: {line}")
                parsed_data = parse_data(line)
                if parsed_data:
                    co2, temp_dht, humidity_dht, pressure, temp_bmp = parsed_data
                    temp_dht_fahrenheit = celsius_to_fahrenheit(temp_dht)
                    timestamp = get_timestamp()
                    data = {
                        'CO2': co2,
                        'Temp(C)': temp_dht,
                        'Temp(F)': temp_dht_fahrenheit,
                        'Humidity': humidity_dht,
                        'Pressure': pressure,
                        # 'TempBMP': temp_bmp
                    }
                    send_to_firebase(timestamp, data)
                    print(f"Data sent to Firebase under timestamp {timestamp}: {data}")
                
    except serial.SerialException as e:
        print(f"Serial error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    initialize_firebase()
    read_serial_data()
