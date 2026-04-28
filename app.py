from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import xml.etree.ElementTree as ET

app = Flask(__name__)
CORS(app)

XML_URL = "https://s3.amazonaws.com/bsalemarket/facebook_xml/59518/112_59518.xml"

# Base de datos técnica (Capacidades de los modelos)
CAPACIDADES_TECNICAS = {
    "RIVER 2": {"capacidad_wh": 256, "potencia_max_w": 300},
    "RIVER 2 MAX": {"capacidad_wh": 512, "potencia_max_w": 500},
    "RIVER 2 PRO": {"capacidad_wh": 768, "potencia_max_w": 800},
    "DELTA 2": {"capacidad_wh": 1024, "potencia_max_w": 1800},
    "DELTA MAX": {"capacidad_wh": 1612, "potencia_max_w": 2000},
    "DELTA PRO": {"capacidad_wh": 3600, "potencia_max_w": 3600}
}

def obtener_productos_xml():
    try:
        response = requests.get(XML_URL)
        root = ET.fromstring(response.content)
        productos_encontrados = []

        # El XML usa el namespace de Google (g:)
        namespace = {'g': 'http://base.google.com/ns/1.0'}

        for item in root.findall('.//item'):
            titulo = item.find('title').text.upper()
            
            # Filtramos para que solo entren modelos EcoFlow que tengamos en la base técnica
            for modelo, specs in CAPACIDADES_TECNICAS.items():
                if modelo in titulo:
                    productos_encontrados.append({
                        "nombre": item.find('title').text,
                        "capacidad_wh": specs["capacidad_wh"],
                        "potencia_max_w": specs["potencia_max_w"],
                        "precio": item.find('g:price', namespace).text,
                        "precio_oferta": item.find('g:sale_price', namespace).text if item.find('g:sale_price', namespace) is not None else None,
                        "url_imagen": item.find('g:image_link', namespace).text,
                        "url_producto": item.find('link').text
                    })
                    break
        return productos_encontrados
    except Exception as e:
        print(f"Error leyendo XML: {e}")
        return []

@app.route('/calcular', methods=['POST'])
def calcular():
    datos = request.json
    watts = float(datos.get('watts', 0))
    horas = float(datos.get('horas', 0))
    
    margen_eficiencia = 0.85
    energia_requerida = (watts * horas) / margen_eficiencia
    
    # Obtenemos datos frescos del XML de Bsale
    todos_los_productos = obtener_productos_xml()
    
    recomendaciones = []
    for p in todos_los_productos:
        if p["potencia_max_w"] >= watts and p["capacidad_wh"] >= energia_requerida:
            # Calcular duración real para este modelo específico
            duracion = (p["capacidad_wh"] * margen_eficiencia) / watts
            p["duracion_estimada"] = round(duracion, 1)
            recomendaciones.append(p)
    
    # Ordenar por el más barato/pequeño que sirva
    recomendaciones.sort(key=lambda x: x['capacidad_wh'])
    
    return jsonify({"status": "ok", "recomendaciones": recomendaciones[:2]})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)