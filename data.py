import sys
sys.path.insert(0,'lib')
from config import Config
from flask import Flask, request, jsonify, session
from flask_cors import CORS 
from supabase import create_client, Client
import secrets
import requests
from datetime import datetime, timedelta
import pandas as pd
import regex as re
import pytz
import numpy as np
import joblib

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
        if data:  # Pastikan data tidak kosong
            tempData = float(round(data[-1]['temp'], 1))
            humidData = float(round(data[-1]['moist'], 1))
            soilData = float(round(data[-1]['soil'], 1))
            lumenData = float(round(data[-1]['lumen'], 1))
            return jsonify({"temp": tempData,
                            "humid": humidData,
                            "soil": soilData,
                            "lumen": lumenData})
        else:
            return jsonify({"error": "No data found"}), 404
    else:
        # Mengembalikan respons jika gagal mengambil data dari API
        return jsonify({"error": "Failed to fetch data from the API"}), response.status_code

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
                'humid':data[i]['moist'],
                'soil': data[i]['soil'],
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

@app.route("/production/average/node<int:id_gh>", methods=['GET'])
def average_production(id_gh):
    data_sensor = supabase.table('dataNode').select("*").eq("id_gh", id_gh).order("time", desc=True).limit(5).execute()
    data = data_sensor.data
    formatted_data = {
        "type":"celcius",
        "data":[{"x":item['temp'], 
                 "y":item['lumen']} for item in data]
    }
    return jsonify(formatted_data)

# ----------------------------- LOGIN USER -----------------------------

patternEmailUser = r'^[a-zA-Z0-9]+@petani\.com$'
tabel_user = supabase.table("user").select('*').execute()
data_user = pd.DataFrame(tabel_user.data)
userEmailList = data_user['email'].tolist()

@app.route('/user', methods=['GET'])
def user_petani():
    response = supabase.table("user").select('*').execute()
    data = response.data
    return jsonify(data)

@app.route('/api/login', methods=['POST'])
def login():
    global patternEmailUser, tabel_user, data_user, userEmailList
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        user = supabase.table("user").select("*").eq("email", email).eq("password", password).execute()

        if user.data:
            return jsonify({"user": user.data})
        else:
            return jsonify({"error": "Invalid email or password"}), 401


# @app.route('/api/register', methods=['POST'])
# def register():
#     global patternEmailUser, tabel_petani, data_petani, userEmailList
#     if request.method == 'POST':
#         data = request.get_json()
#         username = data.get('username')
#         email = data.get('email')
#         password = data.get('password')
#         confirmPassword = data.get('confirmPassword')
#         print()
#         print(data)
#         print()
#         # Autentikasi Register Page
#         if re.match(patternEmailUser,email):
#             if email in userEmailList:
#                 return jsonify({'message': 'Username already exists'}), 400
#             elif email not in userEmailList:
#                 if password == confirmPassword:
#                     supabase.table("petani").insert({ "nama_petani" : username, "email_petani" : email, "password" : password }).execute()
#                     return jsonify({'message': 'Petani added sucessfully'}), 201
#             else:
#                 print("GOBLok")
#                 return jsonify({'message': 'Invalid credentials'}), 400
#     return jsonify({'message': 'Apalah'}), 201


# ----------------------------- LOGIN ADMIN -----------------------------
patternEmailAdmin = r'^[a-zA-Z0-9]+@admin\.com$'

@app.route('/admin', methods=['GET'])
def admin_petani():
    response = supabase.table("admin").select('*').execute()
    data = response.data
    return jsonify(data)

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    identifier = data.get('identifier')  # Ini bisa berupa email atau username
    password = data.get('password')

    # Cek apakah identifier adalah email
    if re.match(patternEmailAdmin, identifier):
        # Ambil data admin berdasarkan email
        response = supabase.table("admin").select('*').eq('email', identifier).execute()
    else:
        # Ambil data admin berdasarkan username
        response = supabase.table("admin").select('*').eq('username', identifier).execute()

    admin_data = response.data

    if not admin_data:
        return jsonify({'message': 'User not found'}), 404

    admin_data = admin_data[0]  # Mengambil admin data dari list hasil query

    # Verifikasi password
    if admin_data['password'] != password:
        return jsonify({'message': 'Incorrect password'}), 401

    # Jika login berhasil
    session['admin_id'] = admin_data['id_admin']
    session['email'] = admin_data['email']
    session['username'] = admin_data['username']
    
    return jsonify({
        'message': 'Login successful!',
        'admin': {
            'id_admin': admin_data['id_admin'],
            'email': admin_data['email'],
            'username': admin_data['username']
        }
    }), 200
    
@app.route('/production/node<int:id_gh>', methods=['GET'])
def get_production_data(id_gh):
    # Ambil data produksi berdasarkan id_gh
    data_produksi = supabase.table('panen').select("*").eq("id_gh", id_gh).order("waktu_panen", desc=True).execute()
    data = data_produksi.data

    # Cek apakah data ada
    if not data:
        return jsonify({"message": "No production data found for this greenhouse"}), 404

    # Mengembalikan data dalam format JSON
    formatted_data = [
        {
            "id": item['id'],
            "id_gh": item['id_gh'],
            "id_varietas": item['id_varietas'],
            "jumlah_produksi": item['jumlah_produksi'],
            "waktu_panen": item['waktu_panen'],
            "created_at": item['created_at']
        }
        for item in data
    ]

    return jsonify(formatted_data), 200

@app.route('/pump/node<int:id_gh>', methods=['GET'])
def get_pump_data(id_gh):
    # Ambil data pompa berdasarkan id_gh
    data_pompa = supabase.table('pompa').select("id, time, status_pompa, id_gh").eq("id_gh", id_gh).order("time", desc=True).execute()
    data = data_pompa.data

    # Cek apakah data ada
    if not data:
        return jsonify({"message": "No pump data found for this greenhouse"}), 404

    # Mengembalikan data dalam format JSON
    formatted_data = [
        {
            "id": item['id'],
            "time": item['time'],
            "status_pompa": item['status_pompa'],
            "id_gh": item['id_gh']
        }
        for item in data
    ]

    return jsonify(formatted_data), 200


#-------Notifikasi--------
# Tentukan rentang ideal untuk masing-masing parameter
IDEAL_TEMP_RANGE = (20, 38)   # Suhu ideal antara 20°C - 30°C
IDEAL_HUMID_RANGE = (20, 85)  # Kelembapan ideal antara 50% - 70%
IDEAL_SOIL_RANGE = (1, 85)   # Kelembapan tanah ideal antara 30% - 60%
IDEAL_LUMEN_RANGE = (1, 40000)  # Intensitas cahaya ideal antara 300 - 700 lumen

# Variabel untuk menyimpan data outlier secara global
outlier_data = {}

# Fungsi untuk mendeteksi apakah data keluar dari batas ideal
def is_outlier(value, ideal_range):
    return value < ideal_range[0] or value > ideal_range[1]

@app.route('/detect_outliers/node<int:id_gh>', methods=['GET'])
def detect_outliers_node(id_gh):
    global outlier_data

    # Ambil data historis dari Supabase
    data_sensor = supabase.table('dataNode').select("*").eq("id_gh", id_gh).order("time", desc=True).limit(10).execute()
    data = data_sensor.data

    # Variabel sementara untuk menyimpan data outlier per request
    temp_outliers = []
    humid_outliers = []
    soil_outliers = []
    lumen_outliers = []

    # Periksa setiap data sensor dan bandingkan dengan nilai ideal
    for record in data:
        temp = record['temp']
        humid = record['moist']
        soil = record['soil']
        lumen = record['lumen']

        # Jika nilai keluar dari rentang ideal, simpan sebagai outlier
        if is_outlier(temp, IDEAL_TEMP_RANGE):
            temp_outliers.append({
                "id_gh": id_gh,
                "time": record['time'],
                "value": temp
            })

        if is_outlier(humid, IDEAL_HUMID_RANGE):
            humid_outliers.append({
                "id_gh": id_gh,
                "time": record['time'],
                "value": humid
            })

        if is_outlier(soil, IDEAL_SOIL_RANGE):
            soil_outliers.append({
                "id_gh": id_gh,
                "time": record['time'],
                "value": soil
            })

        if is_outlier(lumen, IDEAL_LUMEN_RANGE):
            lumen_outliers.append({
                "id_gh": id_gh,
                "time": record['time'],
                "value": lumen
            })

    # Simpan atau update data outlier di variabel global hanya untuk id_gh yang terdeteksi
    outlier_data[id_gh] = {
        "temp_outliers": temp_outliers,
        "humid_outliers": humid_outliers,
        "soil_outliers": soil_outliers,
        "lumen_outliers": lumen_outliers,
    }

    # Mengembalikan hasil deteksi outlier
    return jsonify({
        "temp_outliers": temp_outliers,
        "humid_outliers": humid_outliers,
        "soil_outliers": soil_outliers,
        "lumen_outliers": lumen_outliers
    }), 200

@app.route('/outliers/notifications', methods=['GET'])
def get_outlier_notifications():
    # Mengembalikan data outlier yang sudah disimpan
    # Hanya data terbaru dari setiap id_gh yang ditampilkan
    return jsonify(list(outlier_data.values())), 200


#-------cek kondisi GH 1 jam terakhir------
# Mengatur zona waktu Jakarta
jakarta_tz = pytz.timezone('Asia/Jakarta')

@app.route('/check_all_gh', methods=['GET'])
def check_all_greenhouses():
    # Daftar ID greenhouse yang ingin dicek
    gh_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]  # Contoh ID greenhouse

    notifikasi = []

    for id_gh in gh_ids:
        # Waktu sekarang dan waktu 1 jam yang lalu di zona waktu Jakarta
        current_time = datetime.now(jakarta_tz)
        one_hour_ago = current_time - timedelta(hours=1)

        # Konversi waktu ke format string yang sesuai dengan database (misalnya ISO 8601)
        one_hour_ago_str = one_hour_ago.isoformat()

        # Ambil data dari Supabase untuk setiap gh berdasarkan id_gh dalam waktu 1 jam terakhir
        data_sensor = supabase.table('dataNode').select("*").eq("id_gh", id_gh).gt("time", one_hour_ago_str).execute()
        data = data_sensor.data

        if len(data) == 0:
            # Jika tidak ada data, tambahkan notifikasi
            notifikasi.append(f"Tidak ada data dari greenhouse {id_gh} dalam 1 jam terakhir.")
    
    if len(notifikasi) > 0:
        # Jika ada notifikasi error, return notifikasi tersebut
        return jsonify({
            "status": "error",
            "notifikasi": notifikasi
        }), 404
    else:
        # Tidak memberikan respon apapun jika semua data berhasil diambil
        return '', 204  # No Content
    
#---------Predict---------
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

    
if __name__ == "__main__":
    app.run(debug=True)