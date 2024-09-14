import pickle
from datetime import datetime, timedelta
import numpy as np
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
supabase: Client = create_client(supabase_url,supabase_key)  

# Load your machine learning model (assuming it's serialized with pickle)
with open('model_replon.pkl', 'rb') as f:
    model = pickle.load(f)

def fetch_hourly_data(id_gh, hours=24):
    """
    Fetch hourly data for the past `hours` hours.
    """
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    
    # Query Supabase to get data from `start_time` to `end_time`
    response = supabase.table('dataNode') \
        .select("*") \
        .eq("id_gh", id_gh) \
        .gte("time", start_time.isoformat()) \
        .lte("time", end_time.isoformat()) \
        .order("time", desc=False) \
        .execute()
    
    return response.data

def make_predictions(data):
    """
    Generate predictions for the next 24 hours based on the given data.
    The data should contain hourly entries for the past 24 hours.
    """
    # Assume the model takes the past 24 hours as input to predict the next 24
    # Process your data into a suitable input for the model
    X = np.array([[
        entry['temp'], 
        entry['moist'], 
        entry['lumen'],
        entry['soil']] for entry in data])
    
    # Make predictions
    predictions = model.predict(X)
    
    # Create a list of timestamps for the next 24 hours
    start_time = datetime.now()
    future_times = [start_time + timedelta(hours=i) for i in range(1, 25)]
    
    # Format the results as a list of dictionaries
    results = []
    for i, pred in enumerate(predictions):
        results.append({
            'time': future_times[i].strftime('%Y-%m-%d %H:%M:%S'),
            'pred_temp': pred[0],
            'pred_moist': pred[1],
            'pred_lumen': pred[2],
            'pred_soil': pred[3]
        })
    
    return results

@app.route('/predict/node<int:id_gh>', methods=['GET'])
def predict_next_24_hours(id_gh):
    # Fetch hourly data for the past 24 hours
    historical_data = fetch_hourly_data(id_gh, hours=24)
    
    if len(historical_data) < 24:
        return jsonify({"error": "Not enough data for prediction"}), 400

    # Generate predictions for the next 24 hours
    predictions = make_predictions(historical_data)
    
    # Return the predictions as JSON
    return jsonify(predictions), 200

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
