import matplotlib
matplotlib.use('Agg')  # Use Agg backend for rendering plots
import matplotlib.pyplot as plt
import io
import base64
import json
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from datetime import datetime
import time
import firebase_admin
from firebase_admin import credentials, db
from flask import Flask, render_template, Response
from mess import send_alert_email, send_alert_sms

app = Flask(__name__)

# Firebase configuration
SERVICE_ACCOUNT_KEY = '/Users/saimaster/Desktop/Programs/Mini/Mini pro/serviceAccountKey.json'
DATABASE_URL = 'https://air-check-f96be-default-rtdb.firebaseio.com'

def initialize_firebase():
    cred = credentials.Certificate(SERVICE_ACCOUNT_KEY)
    firebase_admin.initialize_app(cred, {
        'databaseURL': DATABASE_URL
    })

def fetch_data_from_firebase():
    ref = db.reference('/Data')
    return ref.get()

def create_plot(timestamps, values, xlabel, ylabel, title):
    plt.figure(figsize=(6, 4))
    plt.plot(timestamps, values, marker='*', linestyle='dotted')
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=45)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()  # Close the figure after saving
    return base64.b64encode(buf.getvalue()).decode('utf8')

def determine_air_quality_message(co2_value):
    try:
        co2_value = int(co2_value)
    except ValueError:
        return "Error: CO2 value is not a valid number"

    if co2_value > 1500:
        return "Bad (heavily contaminated indoor air, ventilation required)"
    elif 1100 <= co2_value <= 1500:
        return "Moderate (contaminated indoor air, ventilation recommended)"
    elif 700 <= co2_value < 1100:
        return "Good"
    else:
        return "Excellent"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def data():
    def generate():
        while True:
            raw_data = fetch_data_from_firebase()

            timestamps = []
            co2_values = []
            temp_c_values = []
            temp_f_values = []
            humidity_values = []
            pressure_values = []
            air_quality_messages = []

            if raw_data:
                for timestamp, values in raw_data.items():
                    timestamps.append(timestamp)
                    co2_value = values.get('CO2')
                    co2_values.append(co2_value)
                    air_quality_messages.append(determine_air_quality_message(co2_value))
                    temp_c_values.append(values.get('Temp(C)'))
                    temp_f_values.append(values.get('Temp(F)'))
                    humidity_values.append(values.get('Humidity'))
                    pressure_values.append(values.get('Pressure'))

                    # Check if the air quality is bad and send an alert
                    if determine_air_quality_message(co2_value) == "Bad (heavily contaminated indoor air, ventilation required)":
                        send_alert_email("CO2 Alert", f"CO2 levels are too high: {co2_value} ppm, ventilation required")
                        send_alert_sms(f"CO2 levels are too high: {co2_value} ppm, ventilation required")

            # Keep only the last 10 values for a smooth graph
            if len(timestamps) > 10:
                timestamps = timestamps[-10:]
                co2_values = co2_values[-10:]
                air_quality_messages = air_quality_messages[-10:]
                temp_c_values = temp_c_values[-10:]
                temp_f_values = temp_f_values[-10:]
                humidity_values = humidity_values[-10:]
                pressure_values = pressure_values[-10:]

            # Create plots
            co2_plot = create_plot(timestamps, co2_values, 'Timestamp', 'CO2 (ppm)', 'CO2 Levels')
            temp_c_plot = create_plot(timestamps, temp_c_values, 'Timestamp', 'Temp (°C)', 'Temperature (°C)')
            temp_f_plot = create_plot(timestamps, temp_f_values, 'Timestamp', 'Temp (°F)', 'Temperature (°F)')
            humidity_plot = create_plot(timestamps, humidity_values, 'Timestamp', 'Humidity (%)', 'Humidity Levels')
            pressure_plot = create_plot(timestamps, pressure_values, 'Timestamp', 'Pressure (hPa)', 'Atmospheric Pressure')

            # Send the data as a JSON response
            yield f"data:{json.dumps({'co2_plot': co2_plot, 'temp_c_plot': temp_c_plot, 'temp_f_plot': temp_f_plot, 'humidity_plot': humidity_plot, 'pressure_plot': pressure_plot, 'air_quality_message': air_quality_messages[-1]})}\n\n"
            
            time.sleep(10)  # Update every 10 seconds

    return Response(generate(), content_type='text/event-stream')

@app.route('/predict')
def predict():
    raw_data = fetch_data_from_firebase()

    df = pd.DataFrame(raw_data).T
    df.index = pd.to_datetime(df.index, format='%Y-%m-%d_%H-%M-%S')
    df = df.apply(pd.to_numeric, errors='coerce')
    df = df.dropna()

    # Convert datetime to int64 for modeling
    X = df.index.astype('int64').values.reshape(-1, 1)
    y = df['CO2'].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = LinearRegression()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    mse = mean_squared_error(y_test, y_pred)
    print(f"Mean Squared Error: {mse}")

    plt.figure(figsize=(10, 6))
    plt.plot(X_test, y_test, 'b.', label='Actual CO2')
    plt.plot(X_test, y_pred, 'r-', label='Predicted CO2')
    plt.xlabel('Timestamp')
    plt.ylabel('CO2 (ppm)')
    plt.title('Actual vs Predicted CO2 Levels')
    plt.legend()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()  # Close the figure after saving
    graph_url = base64.b64encode(buf.getvalue()).decode('utf8')

    return render_template('predict.html', graph_url=graph_url)

if __name__ == "__main__":
    initialize_firebase()
    app.run(debug=True, threaded=True, port=5010)
