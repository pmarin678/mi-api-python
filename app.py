from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import xml.etree.ElementTree as ET

app = Flask(__name__)
CORS(app)

# Tu feed de productos de Bsale
XML_URL = "https://s3.amazonaws.com/bsalemarket/facebook_xml/59518/112_59518.xml"

# Base de datos técnica (Capacidades de los modelos)
CAPACIDADES_TECNICAS = {
    "RIVER 2": {"cap_wh": 256, "pot_w": 300},
    "RIVER 2 MAX": {"cap_wh": 512, "pot_w": 500},
    "RIVER 2 PRO": {"cap_wh": 768, "pot_w": 800},
    "DELTA 2": {"cap_wh": 1024, "pot_w": 1800},
    "DELTA MAX": {"cap_wh": 1612, "pot_w": 2000},
    "DELTA PRO": {"cap_wh": 3600, "pot_w": 3600}
}

@app.route('/calcular', methods=['POST'])
def calcular():
    datos = request.json
    # Cambiamos 'valor' por 'watts' y añadimos 'horas'
    watts_usuario = float(datos.get('watts', 0))
    horas_usuario = float(datos.get('horas', 0))
    
    if watts_usuario <= 0 or horas_usuario <= 0:
        return jsonify({"status": "error", "mensaje": "Datos inválidos"}), 400

    energia_necesaria = (watts_usuario * horas_usuario) / 0.85 # 0.85 es margen de eficiencia
    
    try:
        # Leemos el XML de Bsale
        response = requests.get(XML_URL)
        root = ET.fromstring(response.content)
        namespace = {'g': 'http://base.google.com/ns/1.0'}
        
        recomendaciones = []
        
        for item in root.findall('.//item'):
            titulo = item.find('title').text.upper()
            
            for modelo, specs in CAPACIDADES_TECNICAS.items():
                if modelo in titulo:
                    # Si el modelo aguanta los Watts y tiene suficiente energía
                    if specs["pot_w"] >= watts_usuario and specs["cap_wh"] >= energia_necesaria:
                        duracion = (specs["cap_wh"] * 0.85) / watts_usuario
                        
                        recomendaciones.append({
                            "nombre": item.find('title').text,
                            "capacidad_wh": specs["cap_wh"],
                            "duracion_estimada": round(duracion, 1),
                            "precio": item.find('g:price', namespace).text,
                            "precio_oferta": item.find('g:sale_price', namespace).text if item.find('g:sale_price', namespace) is not None else None,
                            "url_imagen": item.find('g:image_link', namespace).text,
                            "url_producto": item.find('link').text
                        })
                        break
        
        # Ordenar por el más económico (menor capacidad)
        recomendaciones.sort(key=lambda x: x['capacidad_wh'])
        
        return jsonify({"status": "ok", "recomendaciones": recomendaciones[:2]})

    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)