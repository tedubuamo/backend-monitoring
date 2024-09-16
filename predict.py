import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import numpy as np
import joblib
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
import secrets

# Flask setup
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
CORS(app)

# Supabase setup
supabase_url = 'https://edggtblrgdscfjhkznkw.supabase.co'
supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVkZ2d0YmxyZ2RzY2ZqaGt6bmt3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjMwMDUwNzIsImV4cCI6MjAzODU4MTA3Mn0.TtYY0AVPuVbQcJBBTXDvdPxEh6ffiUjL81XqIrHHqb4'
supabase: Client = create_client(supabase_url, supabase_key)

# Load the models (assuming models are saved as separate files for each variable)
lumen_model = joblib.load('lumen_model.pkl')
humid_model = joblib.load('humid_model.pkl')
temp_model = joblib.load('temp_model.pkl')

def fetch_hourly_data(id_gh, hours=24):
    """
    Fetch hourly data for the past hours hours at specific hours (e.g., 01:00, 02:00, etc.).
    """
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    
    # Query Supabase to get data from start_time to end_time
    response = supabase.table('dataNode') \
        .select("*") \
        .eq("id_gh", id_gh) \
        .gte("time", start_time.isoformat()) \
        .lte("time", end_time.isoformat()) \
        .execute()
    
    if not response.data:
        return []

    # Convert the data to a DataFrame
    df = pd.DataFrame(response.data)
    
    # Convert the time column to datetime
    df['time'] = pd.to_datetime(df['time'])
    
    # Filter to get data only at specific hours
    df_filtered = df[df['time'].dt.hour.isin(range(1, 25))]
    
    # Sort by time
    df_filtered.sort_values(by='time', inplace=True)
    
    # Reset index to convert back to a list of dictionaries
    df_filtered.reset_index(drop=True, inplace=True)
    
    # Convert DataFrame back to list of dictionaries
    data_filtered = df_filtered.to_dict(orient='records')
    
    return data_filtered

def make_predictions(models, data):
    """
    Generate predictions for the next 24 hours based on the given data and models.
    """
    # Forecast the values for the next 24 hours using the models
    predictions = {'lumen': [], 'humid': [], 'temp': []}
    
    # Set future times to the next full hour from now
    current_time = datetime.now()
    next_full_hour = (current_time + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    
    # Generate future times for the next 24 hours starting from the next full hour
    future_times = [next_full_hour + timedelta(hours=i) for i in range(24)]

    for column, model in models.items():
        if model:
            try:
                forecast = model.forecast(24)
                if len(forecast) != 24:
                    print(f"Warning: Model for {column} did not produce 24 forecasts.")
                # Round the predictions to 2 decimal places
                predictions[column] = [round(f, 2) for f in forecast]
            except Exception as e:
                print(f"Error making forecast for {column}: {e}")

    # Format the results as a list of dictionaries
    results = {
        'lumen': [],
        'humid': [],
        'temp': []
    }

    for i in range(24):
        time = future_times[i].strftime('%Y-%m-%d %H:%M:%S')
        for column in results.keys():
            if i < len(predictions[column]):
                results[column].append({f'time': time, f'pred_{column}': predictions[column][i]})
            else:
                results[column].append({f'time': time, f'pred_{column}': None})

    return results

@app.route('/predict/node<int:id_gh>', methods=['GET'])
def predict_next_24_hours(id_gh):
    # Fetch hourly data for the past 24 hours
    historical_data = fetch_hourly_data(id_gh, hours=24)
    
    if len(historical_data) < 24:
        return jsonify({"error": "Not enough data for prediction"}), 400

    # Prepare models for prediction
    models = {
        'lumen': lumen_model,
        'humid': humid_model,
        'temp': temp_model
    }

    # Generate predictions for the next 24 hours
    predictions = make_predictions(models, historical_data)
    
    # Return the predictions as JSON
    return jsonify(predictions), 200

# Run the app
if __name__ == '__main__':
    app.run(debug=True)