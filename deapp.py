from flask import Flask, request, jsonify, session
from flask_cors import CORS # type: ignore 
from supabase import create_client, Client
import secrets
import pandas as pd
import re

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
CORS(app)

pump_state = False

supabase_url = 'https://gvbmcluktznlzafloyix.supabase.co'
supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imd2Ym1jbHVrdHpubHphZmxveWl4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcyMjM5MzE1NSwiZXhwIjoyMDM3OTY5MTU1fQ.llaf9ziOsLynYi0c-8RzTWBmzk53jpemol92Fdvb2vs'
supabase: Client = create_client(supabase_url,supabase_key)         

# --------------- LOGIN PAGE API FOR USER ---------------

patternEmailUser = r'^[a-zA-Z0-9]+@petani\.com$'
tabel_petani = supabase.table("petani").select("email_petani","password").execute()
data_petani = pd.DataFrame(tabel_petani.data)
userEmailList = data_petani['email_petani'].tolist()

@app.route('/user', methods=['GET'])
def user_petani():
    response = supabase.table("petani").select("email_petani","password").execute()
    data = response.data
    return jsonify(data)

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


if __name__ == "__main__":
    app.run(debug=True)


