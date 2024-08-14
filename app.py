from flask import Flask, request, jsonify, session
from flask_cors import CORS # type: ignore
from datetime import datetime
from psycopg2.extras import RealDictCursor 
from supabase import create_client, Client

import json
import os
import secrets
import pandas as pd
import requests
import re

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
CORS(app)

pump_state = False

supabase_url = 'https://gvbmcluktznlzafloyix.supabase.co'
supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd2Ym1jbHVrdHpubHphZmxveWl4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcyMjM5MzE1NSwiZXhwIjoyMDM3OTY5MTU1fQ.llaf9ziOsLynYi0c-8RzTWBmzk53jpemol92Fdvb2vs'
supabase: Client = create_client(supabase_url,supabase_key)         
    
# def get_db_connection():
#     conn = psycopg2.connect(
#         host="localhost",
#         database="tws",
#         user="postgres",
#         password="ardiansyah29"
#     )
#     return conn

def load_data():
    file_path = os.path.join('dataset', 'data_sensor')
    if os.path.exists(file_path):
        with open(file_path) as f:
            data = json.load(f)
            print("Data Loaded: ", data)  # Debugging log
            return data
    else:
        print("File not found: ", file_path)
        return None

def time_sensor(data):
    time_temp = []
    for item in data:
        date = datetime.strptime(item['datetime'], '%Y-%m-%dT%H:%M:%S.%fZ')
        time = date.strftime('%H:%M')
        time_temp.append({
            'time': time,
            'temp': item['temp']
        })

    return time_temp

def calculate_average_temp(data):
    total_temp = sum(item['temp'] for item in data)
    average_temp = total_temp / len(data)
    return average_temp

def calculate_average_soil(data):
    total_soil = sum(item['soil'] for item in data)
    average_soil = total_soil / len(data)
    return average_soil

def calculate_average_moist(data):
    total_moist = sum(item['moist'] for item in data)
    average_moist = total_moist / len(data)
    return average_moist

def calculate_average_lumen(data):
    total_lumen = sum(item['lumen'] for item in data)
    average_lumen = total_lumen / len(data)
    return average_lumen

@app.route('/user', methods=['GET'])
def user_petani():
    response = supabase.table("petani").select("email_petani","password").execute()
    data = response.data
    return jsonify(data)

# --------------- LOGIN PAGE API FOR USER ---------------

patternEmailUser = r'^[a-zA-Z0-9]+@petani\.com$'
tabel_petani = supabase.table("petani").select("email_petani","password").execute()
data_petani = pd.DataFrame(tabel_petani.data)
userEmailList = data_petani['email_petani'].tolist()

@app.route('/api/login', methods=['POST'])
def login():
    global patternEmailUser, tabel_petani, data_petani, userList
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        # Autentikasi Login Page
        if re.match(patternEmailUser,email):
            if email in userEmailList:
                user_index = data_petani.loc[data_petani['email_petani'] == email].index[0]
                if data_petani.at[user_index,'password'] == password:
                    session['email_petani'] = email
                return jsonify({'message': 'Login successful!','user': email}), 200
        return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/api/register', methods=['POST'])
def register():
    global patternEmailUser, tabel_petani, data_petani, userEmailList
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        confirmPassword = data.get('confirmPassword')
        print()
        print(data)
        print()
        # Autentikasi Register Page
        if re.match(patternEmailUser,email):
            if email in userEmailList:
                return jsonify({'message': 'Username already exists'}), 400
            elif email not in userEmailList:
                if password == confirmPassword:
                    supabase.table("petani").insert({ "nama_petani" : username, "email_petani" : email, "password" : password }).execute()
                    return jsonify({'message': 'Petani added sucessfully'}), 201
            else:
                print("GOBLok")
                return jsonify({'message': 'Invalid credentials'}), 400
    return jsonify({'message': 'Apalah'}), 201

# --------------- THIS ENDING OF LOGIN PAGE API FOR USER ---------------
  
#    --------------- THIS DASHBOARD PAGE API FOR USER ---------------
@app.route('/iot/node1', methods = ['GET'])
def get_data():
    data = load_data()
    return jsonify(data)

@app.route('/node1',methods =['GET'])
def data_monitoring():
    url = 'http://127.0.0.1:5000/iot/node1'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        tempData = float(round(data[-1]['temp'],2))
        moistData = float(round(data[-1]['moist'],2))
        soilData = float(round(data[-1]['soil'],2))
        lumenData = float(round(data[-1]['lumen'],2))
        return jsonify({"temp":tempData,
                        "moist":moistData,
                        "soil":soilData,
                        "lumen":lumenData})

@app.route('/api/node1', methods = ['GET'])
def getdata():
    url = 'http://127.0.0.1:5000/iot/node1'
        # Melakukan GET request ke server
    response = requests.get(url)
    
    # Memeriksa apakah request berhasil
    if response.status_code == 200:
        data = response.json()
        average_temp = calculate_average_temp(data)
        average_soil = calculate_average_soil(data)
        average_moist = calculate_average_moist(data)
        average_lumen = calculate_average_lumen(data)
        time = time_sensor(data)
        response = {
            "data" : data,
            "time_temp" : time,
            "average_temp" : average_temp,
            "average_soil" : average_soil,
            "average_moist" : average_moist,
            "average_lumen" : average_lumen
        }
        return jsonify(response), 200
    else:
        return jsonify({"error": "Failed to retrieve data"}), response.status_code

#--------------- THIS ENDING OF DASHBOARD PAGE API FOR USER ---------------

@app.route('/api/pump', methods=['POST','GET'])
def control_pump():
    global pump_state
    if request.method == 'POST':
        try:
            # Ambil status dari permintaan POST
            content = request.json
            pump_state = content['state']

            # Lakukan aksi untuk menghidupkan atau mematikan pompa
            if pump_state:
                print("Pompa dinyalakan")
                # Tambahkan kode untuk menyalakan pompa
            else:
                print("Pompa dimatikan")
                # Tambahkan kode untuk mematikan pompa

            return jsonify({'success': True, 'pump_state': pump_state}), 200
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400

    elif request.method == 'GET':
        return jsonify({'success': True, 'pump_state':pump_state}), 200

if __name__ == "__main__":
    app.run(debug=True)