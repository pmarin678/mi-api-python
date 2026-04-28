from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import xml.etree.ElementTree as ET

app = Flask(__name__)
CORS(app)

XML_URL = "https://s3.amazonaws.com/bsalemarket/facebook_xml/59518/112_59518.xml"

# Base de datos con palabras clave simplificadas para asegurar el match
CAPACIDADES = [
    {"search": ["DELTA", "PRO", "2"], "wh": 4096, "watts": 4000, "label": "Delta Pro 2"},
    {"search": ["DELTA", "3"], "wh": 1024, "watts": 1800, "label": "Delta 3"},
    {"search": ["RIVER", "MAX"], "wh": 512, "watts": 500, "label": "River 2 Max"},
    {"search": ["RIVER", "PRO"], "wh": 768, "watts": 800, "label": "River 2 Pro"},
    {"search": ["RIVER", "2"], "wh": 256, "watts": 300, "label": "River 2"},
    {"search": ["DELTA", "2"], "wh": 1024, "watts": 1800, "label": "Delta 2"}
]

@app.route('/calcular', methods=['POST'])
def calcular():
    try:
        datos = request.json
        w_usuario = float(datos.get('watts', 0))
        h_usuario = float(datos.get('horas', 0))
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(XML_URL, headers=headers, timeout=20)
        root = ET.fromstring(response.content)
        ns = {'g': 'http://base.google.com/ns/1.0'}
        
        recomendaciones = []

        for item in root.findall('.//item'):
            # Obtenemos el título y lo limpiamos
            titulo_raw = item.find('title').text if item.find('title') is not None else ""
            titulo = titulo_raw.upper()
            
            # FILTRO: Si el título contiene "ECOFLOW" o "RIVER" o "DELTA"
            if any(word in titulo for word in ["ECOFLOW", "RIVER", "DELTA"]):
                # Ignorar accesorios obvios
                if any(acc in titulo for acc in ["PANEL", "CABLE", "BOLSO", "SOLAR", "FUNDA"]):
                    continue
                
                for mod in CAPACIDADES:
                    # Si todas las palabras de búsqueda están en el título
                    if all(k in titulo for k in mod["search"]):
                        duracion = (mod["wh"] * 0.85) / w_usuario
                        
                        if mod["watts"] >= w_usuario:
                            recomendaciones.append({
                                "nombre": titulo_raw,
                                "duracion_estimada": round(duracion, 1),
                                "precio": item.find('g:price', ns).text if item.find('g:price', ns) is not None else "Ver web",
                                "precio_oferta": item.find('g:sale_price', ns).text if item.find('g:sale_price', ns) is not None else None,
                                "url_imagen": item.find('g:image_link', ns).text if item.find('g:image_link', ns) is not None else "",
                                "url_producto": item.find('link').text if item.find('link') is not None else "#",
                                "wh": mod["wh"]
                            })
                            break

        recomendaciones.sort(key=lambda x: x['wh'])
        
        # Este print es vital para ver qué pasó en los logs
        print(f"DEBUG: Encontrados {len(recomendaciones)} productos EcoFlow aptos.")
        
        return jsonify({"status": "ok", "recomendaciones": recomendaciones[:3]})

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({"status": "error", "mensaje": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)