import calendar
from datetime import datetime

from flask import Flask, jsonify, request
from pymongo import MongoClient
from bson import ObjectId
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

now = datetime.now()  # Burada now doğru şekilde datetime'dan alınmalı
current_year = now.year
current_month = now.month

# Ayın ilk günü
first_day = datetime(current_year, current_month, 1)

# Ayın son günü
last_day_of_month = calendar.monthrange(current_year, current_month)[1]  # Ayın son gününü al
last_day = datetime(current_year, current_month, last_day_of_month, 23, 59, 59)


client = MongoClient("mongodb://localhost:27017/")  # Yerel MongoDB sunucusuna bağlan
db = client["HesapKitap"]  # 'mydatabase' adlı veritabanını kullan
fabrika_collection = db["Fabrikalar"]
gelir_collection = db["Gelir"]
gider_collection = db["Gider"]

def convert_objectid(data):
    if isinstance(data, list):
        return [convert_objectid(item) for item in data]
    if isinstance(data, dict):
        return {key: (str(value) if isinstance(value, ObjectId) else value) for key, value in data.items()}
    return data

# Basit bir GET isteği (veri çekme)
@app.route('/api/get_data', methods=['GET'])
def get_data():
    data = fabrika_collection.find_one()  # MongoDB'den bir veri çek
    if data:
        # MongoDB ObjectId'sini string'e çevir ve JSON formatında döndür
        data["_id"] = str(data["_id"])
        return jsonify(data), 200
    else:
        return jsonify({"error": "No data found"}), 404

# Basit bir GET isteği
@app.route('/GetDropdownItems', methods=['GET'])
def GetDropdownItems():
    fabrikalar = list(fabrika_collection.find({}, {"_id": 0, "Name": 1}))

    if fabrikalar is not None and len(fabrikalar) > 0:
        array=[]
        for fab in fabrikalar:
            array.append(fab['Name'])
        return array
    else:
        return jsonify({"error": "No data found"}), 404
# Basit bir POST isteği
@app.route('/SaveIncomeData', methods=['POST'])
def gelir_insert():
    data = request.get_json()
    data = convert_to_date(data)
    gelir_collection.insert_one(data)
    return jsonify({"received_data": data}), 201

@app.route('/SaveExpenseData', methods=['POST'])
def gider_insert():
    data = request.get_json()
    data = convert_to_date(data)
    gider_collection.insert_one(data)
    return jsonify({"received_data": data}), 201

@app.route('/GetInvoiceData', methods=['GET'])
def get_inv_data():
    toplam_gelir = 0
    toplam_gider = 0
    gelirler =list(gelir_collection.find({"Date": {
        '$gte': first_day,
        '$lte': last_day
    }}))
    giderler = list(gider_collection.find({"Date": {
        '$gte': first_day,
        '$lte': last_day
    }}))

    for gelir in gelirler:
        toplam_gelir = toplam_gelir + int(gelir["Amount"])

    for gider in giderler:
        toplam_gider = toplam_gider + int(gider["Amount"])

    son_hesap = toplam_gelir - toplam_gider
    return {"gelirler":convert_objectid(gelirler),"giderler":convert_objectid(giderler),"sonhesap":son_hesap,"toplamgelir":toplam_gelir,"toplamgider":toplam_gider}

def convert_to_date(data):
    data['Date'] = datetime(data["Date"]["year"], data["Date"]["month"], data["Date"]["day"])
    return data

if __name__ == '__main__':
    app.run(debug=True)
