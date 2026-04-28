from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import xml.etree.ElementTree as ET

app = Flask(__name__)
CORS(app)

XML_URL = "https://s3.amazonaws.com/bsalemarket/facebook_xml/59518/112_59518.xml"

# Diccionario con palabras clave que REALMENTE están en tu XML
CAPACIDADES = {
    "RIVER 2": {"wh": 256, "watts": 300},
    "RIVER 2 MAX": {"wh": 512, "watts": 500},
    "RIVER 2 PRO": {"wh": 768, "watts": 800},
    "DELTA 2": {"wh": 1024, "watts": 1800},
    "DELTA MAX": {"wh": 1612, "watts": 2000},
    "DELTA PRO": {"wh": 3600, "watts": 3600}
}

@app.route('/calcular', methods=['POST'])
def calcular():
    try:
        datos = request.json
        w_usuario = float(datos.get('watts', 0))
        h_usuario = float(datos.get('horas', 0))
        
        # Consumo real + 15% de pérdida por conversión (inversor)
        energia_necesaria = (w_usuario * h_usuario) / 0.85
        
        response = requests.get(XML_URL, timeout=10)
        root = ET.fromstring(response.content)
        namespace = {'g': 'http://base.google.com/ns/1.0'}
        
        recomendaciones = []
        
        for item in root.findall('.//item'):
            titulo = item.find('title').text.upper()
            
            # Filtramos: Solo si es EcoFlow y NO es un panel solar o cable
            if "ECOFLOW" in titulo and "PANEL" not in titulo and "CABLE" not in titulo:
                for modelo, specs in CAPACIDADES.items():
                    if modelo in titulo:
                        # Si la potencia de la estación aguanta los Watts del usuario
                        if specs["watts"] >= w_usuario:
                            duracion = (specs["wh"] * 0.85) / w_usuario
                            
                            # Si la batería dura al menos lo que el usuario pidió
                            if duracion >= h_usuario:
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
        
        # Ordenamos por la más económica para el cliente
        recomendaciones.sort(key=lambda x: x['wh'])
        
        return jsonify({"status": "ok", "recomendaciones": recomendaciones[:3]})

    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)