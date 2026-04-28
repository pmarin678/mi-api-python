from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import xml.etree.ElementTree as ET

app = Flask(__name__)
CORS(app)

XML_URL = "https://s3.amazonaws.com/bsalemarket/facebook_xml/59518/112_59518.xml"

# Diccionario técnico flexible
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
        
        response = requests.get(XML_URL, timeout=15)
        root = ET.fromstring(response.content)
        namespace = {'g': 'http://base.google.com/ns/1.0'}
        
        recomendaciones = []
        
        for item in root.findall('.//item'):
            titulo = item.find('title').text.upper()
            
            # Solo procesar si es una estación de energía (evitar paneles/mochilas)
            if "ECOFLOW" in titulo and any(m in titulo for m in ["RIVER", "DELTA"]):
                for modelo, specs in CAPACIDADES.items():
                    if modelo in titulo:
                        # Cálculo de duración real
                        duracion = (specs["wh"] * 0.85) / w_usuario
                        
                        # CRITERIO: Que la estación soporte los Watts 
                        # y que no sea una duración ridículamente baja (ej. menos de 15 min)
                        if specs["watts"] >= w_usuario and duracion > 0.2:
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
        
        # Ordenar por capacidad (Wh) para mostrar de menor a mayor
        recomendaciones.sort(key=lambda x: x['wh'])
        
        # Si no hay nada, devolvemos un mensaje más amigable o sugerencias
        return jsonify({
            "status": "ok", 
            "recomendaciones": recomendaciones[:3] # Mostramos las 3 mejores opciones
        })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status": "error", "mensaje": "Error al procesar el catálogo"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)