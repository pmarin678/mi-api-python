from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import xml.etree.ElementTree as ET

app = Flask(__name__)
CORS(app)

XML_URL = "https://s3.amazonaws.com/bsalemarket/facebook_xml/59518/112_59518.xml"

# BASE DE DATOS ACTUALIZADA SEGÚN TUS LINKS
# Wh = Capacidad | Watts = Potencia de salida
CAPACIDADES = [
    {"key": "DELTA PRO 2", "wh": 4096, "watts": 4000}, # Datos estimados Delta Pro 2
    {"key": "DELTA 3", "wh": 1024, "watts": 1800},     # Datos estimados Delta 3
    {"key": "RIVER 2 MAX", "wh": 512, "watts": 500},
    {"key": "RIVER 2 PRO", "wh": 768, "watts": 800},
    {"key": "RIVER 2", "wh": 256, "watts": 300},
    {"key": "DELTA 2", "wh": 1024, "watts": 1800}
]

@app.route('/calcular', methods=['POST'])
def calcular():
    try:
        datos = request.json
        w_usuario = float(datos.get('watts', 0))
        h_usuario = float(datos.get('horas', 0))
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(XML_URL, headers=headers, timeout=20)
        
        if response.status_code != 200:
            return jsonify({"status": "error", "mensaje": "Error de conexion con Bsale"}), 500

        root = ET.fromstring(response.content)
        namespace = {'g': 'http://base.google.com/ns/1.0'}
        
        recomendaciones = []

        for item in root.findall('.//item'):
            titulo = item.find('title').text.upper()
            
            # Filtro inteligente: debe ser EcoFlow y no ser un accesorio
            if "ECOFLOW" in titulo and not any(x in titulo for x in ["PANEL", "SOLAR", "CABLE", "ESTUCHE", "BATERIA EXTRA"]):
                
                for mod in CAPACIDADES:
                    # Buscamos si el modelo está en el título (ej: "RIVER 2 MAX" en "EcoFlow River 2 Max")
                    if mod["key"] in titulo:
                        duracion = (mod["wh"] * 0.85) / w_usuario
                        
                        # Si la potencia de la estación aguanta el consumo
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

        # Ordenar por capacidad
        recomendaciones.sort(key=lambda x: x['wh'])
        
        return jsonify({"status": "ok", "recomendaciones": recomendaciones[:3]})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "mensaje": "Estamos actualizando el catálogo"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)