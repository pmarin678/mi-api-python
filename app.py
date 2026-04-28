from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import xml.etree.ElementTree as ET

app = Flask(__name__)
CORS(app)

XML_URL = "https://s3.amazonaws.com/bsalemarket/facebook_xml/59518/112_59518.xml"

# Diccionario técnico con los nombres estándar
CAPACIDADES = [
    {"key": "DELTA PRO", "wh": 3600, "watts": 3600},
    {"key": "DELTA MAX", "wh": 1612, "watts": 2000},
    {"key": "DELTA 2", "wh": 1024, "watts": 1800},
    {"key": "RIVER 2 PRO", "wh": 768, "watts": 800},
    {"key": "RIVER 2 MAX", "wh": 512, "watts": 500},
    {"key": "RIVER 2", "wh": 256, "watts": 300}
]

@app.route('/calcular', methods=['POST'])
def calcular():
    try:
        datos = request.json
        w_usuario = float(datos.get('watts', 0))
        h_usuario = float(datos.get('horas', 0))
        
        # Simular un navegador para que S3/Bsale no nos bloquee
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(XML_URL, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return jsonify({"status": "error", "mensaje": "Bsale bloqueo la conexion"}), 500

        root = ET.fromstring(response.content)
        namespace = {'g': 'http://base.google.com/ns/1.0'}
        
        recomendaciones = []
        productos_revisados = 0

        for item in root.findall('.//item'):
            titulo = item.find('title').text.upper()
            productos_revisados += 1
            
            # Buscamos coincidencias
            for mod in CAPACIDADES:
                if mod["key"] in titulo and "PANEL" not in titulo:
                    duracion = (mod["wh"] * 0.85) / w_usuario
                    if mod["watts"] >= w_usuario:
                        recomendaciones.append({
                            "nombre": item.find('title').text,
                            "duracion_estimada": round(duracion, 1),
                            "precio": item.find('g:price', namespace).text if item.find('g:price', namespace) is not None else "Consultar",
                            "precio_oferta": item.find('g:sale_price', namespace).text if item.find('g:sale_price', namespace) is not None else None,
                            "url_imagen": item.find('g:image_link', namespace).text,
                            "url_producto": item.find('link').text,
                            "wh": mod["wh"]
                        })
                        break

        recomendaciones.sort(key=lambda x: x['wh'])
        
        # Imprimir en consola de Railway para saber si encontro algo
        print(f"Productos analizados: {productos_revisados} | Encontrados: {len(recomendaciones)}")
        
        return jsonify({"status": "ok", "recomendaciones": recomendaciones[:3]})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "mensaje": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)