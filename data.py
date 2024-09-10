import sys
sys.path.insert(0,'lib')
from config import Config
from flask import Flask, request, jsonify, session
from flask_cors import CORS # type: ignore
from supabase import create_client, Client
import secrets
import requests
from datetime import datetime, timedelta
import pandas as pd
import regex as re
import pytz

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
CORS(app)
app.config.from_object(Config)

supabase_url = 'https://edggtblrgdscfjhkznkw.supabase.co'
supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVkZ2d0YmxyZ2RzY2ZqaGt6bmt3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjMwMDUwNzIsImV4cCI6MjAzODU4MTA3Mn0.TtYY0AVPuVbQcJBBTXDvdPxEh6ffiUjL81XqIrHHqb4'
supabase: Client = create_client(supabase_url,supabase_key)         

def calculate_all(data):
    # Data historis harus dalam urutan terbaru ke terlama
    Huma_t1 = data['Huma_1']
    Inte_t1 = data['Inte_1']
    Temp_t1 = data['Temp_1']
    Huma_t2 = data['Huma_2']
    Inte_t2 = data['Inte_2']
    Temp_t2 = data['Temp_2']
    Huma_t3 = data['Huma_3']
    Inte_t3 = data['Inte_3']
    Temp_t3 = data['Temp_3']
    Huma_t4 = data['Huma_4']
    Inte_t4 = data['Inte_4']
    Temp_t4 = data['Temp_4']
    Huma_t5 = data['Huma_5']
    Inte_t5 = data['Inte_5']
    Temp_t5 = data['Temp_5']
    
    # Menghitung prediksi
    Huma_t = (0.671 * Huma_t1 - 4.077e-05 * Inte_t1 - 0.534 * Temp_t1 +
              0.144 * Huma_t2 - 1.296e-05 * Inte_t2 + 0.069 * Temp_t2 +
              0.126 * Huma_t3 - 3.940e-06 * Inte_t3 + 0.102 * Temp_t3 +
              0.0027 * Huma_t4 + 6.476e-06 * Inte_t4 + 0.0708 * Temp_t4 +
              0.051 * Huma_t5 + 1.122e-05 * Inte_t5 + 0.2996 * Temp_t5 +
              0.2837)
    
    Inte_t = (-6.404 * Huma_t1 + 0.446 * Inte_t1 + 68.8115 * Temp_t1 -
              9.968 * Huma_t2 + 0.128 * Inte_t2 + 43.4208 * Temp_t2 +
              13.198 * Huma_t3 + 0.063 * Inte_t3 - 103.112 * Temp_t3 +
              45.8223 * Huma_t4 + 0.124 * Inte_t4 + 1.855 * Temp_t4 -
              45.799 * Huma_t5 + 0.197 * Inte_t5 + 6.622 * Temp_t5 -
              114.5463)
    
    Temp_t = (0.004437 * Huma_t1 + 4.198e-05 * Inte_t1 + 0.922 * Temp_t1 -
              0.01048 * Huma_t2 + 3.844e-06 * Inte_t2 + 0.0034 * Temp_t2 -
              0.0027 * Huma_t3 - 1.118e-05 * Inte_t3 + 0.0568 * Temp_t3 +
              0.00788 * Huma_t4 - 4.808e-06 * Inte_t4 + 0.00651 * Temp_t4 +
              0.001539 * Huma_t5 - 1.604e-05 * Inte_t5 + 0.00365 * Temp_t5 +
              0.1101)
    
    return {"Huma_t": round(Huma_t,2), "Inte_t": round(Inte_t,2), "Temp_t": round(Temp_t,2)}

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


@app.route('/predict/node<int:id_gh>', methods=['GET'])
def predict_node(id_gh):
    # Ambil data historis dari Supabase
    data_sensor = supabase.table('dataNode').select("*").eq("id_gh", id_gh).order("time", desc=True).limit(5).execute()
    data = data_sensor.data

    if len(data) < 5:
        return jsonify({"error": "Not enough data for prediction"}), 400
    
    # Siapkan data untuk prediksi
    prev_data = {
        'Huma_1': data[0]['moist'], 'Inte_1': data[0]['lumen'], 'Temp_1': data[0]['temp'],
        'Huma_2': data[1]['moist'], 'Inte_2': data[1]['lumen'], 'Temp_2': data[1]['temp'],
        'Huma_3': data[2]['moist'], 'Inte_3': data[2]['lumen'], 'Temp_3': data[2]['temp'],
        'Huma_4': data[3]['moist'], 'Inte_4': data[3]['lumen'], 'Temp_4': data[3]['temp'],
        'Huma_5': data[4]['moist'], 'Inte_5': data[4]['lumen'], 'Temp_5': data[4]['temp'],
    }

    print(prev_data)
    # Lakukan prediksi
    prediction = calculate_all(prev_data)

    # Kembalikan hasil prediksi sebagai JSON
    return jsonify(prediction)

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
    
if __name__ == "__main__":
    app.run(debug=True)