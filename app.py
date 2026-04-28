from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import xml.etree.ElementTree as ET

app = Flask(__name__)
CORS(app)

# URL del XML de Bsale
XML_URL = "https://s3.amazonaws.com/bsalemarket/facebook_xml/59518/112_59518.xml"

# Diccionario técnico de EcoFlow
CAPACIDADES = {
    "RIVER 2": {"wh": 256, "watts": 300},
    "DELTA 2": {"wh": 1024, "watts": 1800},
    "DELTA PRO": {"wh": 3600, "watts": 3600}
}

@app.route('/calcular', methods=['POST'])
def calcular():
    try:
        datos = request.json
        w_usuario = float(datos.get('watts', 0))
        h_usuario = float(datos.get('horas', 0))
        
        # Cálculo de energía necesaria con margen de seguridad
        energia_necesaria = (w_usuario * h_usuario) / 0.85
        
        # Leer XML de Bsale
        response = requests.get(XML_URL, timeout=10)
        root = ET.fromstring(response.content)
        namespace = {'g': 'http://base.google.com/ns/1.0'}
        
        recomendaciones = []
        
        for item in root.findall('.//item'):
            titulo = item.find('title').text.upper()
            
            for modelo, specs in CAPACIDADES.items():
                # Si el nombre del modelo está dentro del título del producto
                if modelo in titulo:
                    # Filtramos por potencia y capacidad
                    if specs["watts"] >= w_usuario and specs["wh"] >= energia_necesaria:
                        duracion = (specs["wh"] * 0.85) / w_usuario
                        
                        recomendaciones.append({
                            "nombre": item.find('title').text,
                            "duracion_estimada": round(duracion, 1),
                            "precio": item.find('g:price', namespace).text,
                            "precio_oferta": item.find('g:sale_price', namespace).text if item.find('g:sale_price', namespace) is not None else None,
                            "url_imagen": item.find('g:image_link', namespace).text,
                            "url_producto": item.find('link').text,
                            "wh": specs["wh"]
                        })
                        break
        
        # Ordenamos de la más pequeña a la más grande
        recomendaciones.sort(key=lambda x: x['wh'])
        
        return jsonify({"status": "ok", "recomendaciones": recomendaciones[:2]})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "mensaje": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)