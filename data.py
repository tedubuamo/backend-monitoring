import sys
sys.path.insert(0,'lib')
from config import Config
from flask import Flask, request, jsonify, session
from flask_cors import CORS # type: ignore
from supabase import create_client, Client
import secrets
import requests
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
CORS(app)
app.config.from_object(Config)

supabase_url = 'https://edggtblrgdscfjhkznkw.supabase.co'
supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVkZ2d0YmxyZ2RzY2ZqaGt6bmt3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjMwMDUwNzIsImV4cCI6MjAzODU4MTA3Mn0.TtYY0AVPuVbQcJBBTXDvdPxEh6ffiUjL81XqIrHHqb4'
supabase: Client = create_client(supabase_url,supabase_key)         


@app.route('/')
def index():
    return 'Hello World'

@app.route('/data/node<int:id_gh>', methods=['GET'])
def getDataNode(id_gh):
    data_sensor = supabase.table('dataNode').select("*").eq("id_gh",id_gh).order("time", desc=True).limit(30).execute()
    data = data_sensor.data
    return jsonify(data)

@app.route('/monitoring/node<int:id_gh>',methods =['GET'])
def data_monitoring(id_gh):
    url = f"{app.config['API_URL']}/data/node{id_gh}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        tempData = float(round(data[-1]['temp'],1))
        humidData = float(round(data[-1]['moist'],1))
        soilData = float(round(data[-1]['soil'],1))
        lumenData = float(round(data[-1]['lumen'],1))
        return jsonify({"temp":tempData,
                        "humid":humidData,
                        "soil":soilData,
                        "lumen":lumenData})

@app.route('/line/node<int:id_gh>', methods = ['GET'])
def getdata(id_gh):
    url = f"{app.config['API_URL']}/data/node{id_gh}"
        # Melakukan GET request ke server
    response = requests.get(url)
    
    # Memeriksa apakah request berhasil
    if response.status_code == 200:
        data = response.json()
        data = data[0:9]
        data_sensor = []

        for i in range(len(data)):
            original_time = data[i]['time']
            parsed_time = datetime.fromisoformat(original_time)
            adjusted_time = parsed_time + timedelta(hours=7)
            formatted_time = adjusted_time.strftime("%H:%M")
            data_sensor.append({
                'temp': data[i]['temp'],
                'moist':data[i]['moist'],
                'humid': data[i]['soil'],
                'lumen':data[i]['lumen'],
                'time': formatted_time
            })

        response = {
            "data_sensor" : data_sensor
            }
        return jsonify(response), 200
    else:
        return jsonify({"error": "Failed to retrieve data"}), response.status_code
    
@app.route("/overview/gh_home", methods=["GET"])
def get_overview_gh_home():
    base_url = f"{app.config['API_URL']}/data/node"
    total_nodes = 12

    lumen_series = []
    humid_series = []
    soil_series = []
    temp_series = []

    for i in range(1, total_nodes+1):
        response = requests.get(f"{base_url}{i}")
        if response.status_code == 200:
            data = response.json()
            lumen_series.append(data[-1]['lumen'])
            humid_series.append(data[-1]['moist'])
            soil_series.append(data[-1]['soil'])
            temp_series.append(data[-1]['temp'])
        else:
            lumen_series.append(None)
            humid_series.append(None)
            soil_series.append(None)
            temp_series.append(None)
    
    result = [
        { "type": "lumen", "series": lumen_series },
        { "type": "humid", "series": humid_series },
        { "type": "soil", "series": soil_series },
        { "type": "temp", "series": temp_series }]
    
    return jsonify(result), 200

if __name__ == "__main__":
    app.run(debug=True)