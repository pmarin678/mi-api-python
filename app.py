from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route('/calcular', methods=['POST'])
def calcular():
    datos = request.json
    # Aquí pondremos tu lógica de energía luego
    num = datos.get('valor', 0)
    return jsonify({"resultado": num * 2, "status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

    