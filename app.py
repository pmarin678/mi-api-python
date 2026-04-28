from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import xml.etree.ElementTree as ET

app = Flask(__name__)
CORS(app)

XML_URL = "https://s3.amazonaws.com/bsalemarket/facebook_xml/59518/112_59518.xml"

@app.route('/calcular', methods=['POST'])
def calcular():
    try:
        response = requests.get(XML_URL, timeout=15)
        root = ET.fromstring(response.content)
        
        todos_los_nombres = []
        for item in root.findall('.//item'):
            titulo = item.find('title').text if item.find('title') is not None else "Sin Titulo"
            todos_los_nombres.append(titulo)

        # IMPRIMIR TODO EN EL LOG DE RAILWAY
        print("--- LISTADO DE PRODUCTOS ENCONTRADOS EN XML ---")
        for nombre in todos_los_nombres:
            print(f"PRODUCTO: {nombre}")
        print("-----------------------------------------------")

        return jsonify({
            "status": "diagnostico",
            "mensaje": "Revisa los logs de Railway para ver la lista de productos",
            "total_leidos": len(todos_los_nombres)
        })

    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)