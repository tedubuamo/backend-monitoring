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

    
if __name__ == "__main__":
    app.run(debug=True)