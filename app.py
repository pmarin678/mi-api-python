from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import xml.etree.ElementTree as ET

app = Flask(__name__)
CORS(app)

XML_URL = "https://s3.amazonaws.com/bsalemarket/facebook_xml/59518/112_59518.xml"

# Datos técnicos simplificados
CAPACIDADES = [
    {"key": "DELTA PRO", "wh": 3600, "watts": 3600},
    {"key": "DELTA 3", "wh": 1024, "watts": 1800},
    {"key": "DELTA 2", "wh": 1024, "watts": 1800},
    {"key": "RIVER 2 MAX", "wh": 512, "watts": 500},
    {"key": "RIVER 2 PRO", "wh": 768, "watts": 800},
    {"key": "RIVER 2", "wh": 256, "watts": 300}
]

@app.route('/calcular', methods=['POST'])
def calcular():
    try:
        datos = request.json
        w_usuario = float(datos.get('watts', 0))
        h_usuario = float(datos.get('horas', 0))
        
        # Simular navegador para evitar bloqueos de Amazon S3
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(XML_URL, headers=headers, timeout=20)
        
        # Parsear el XML
        root = ET.fromstring(response.content)
        # Namespace de Google
        ns = {'g': 'http://base.google.com/ns/1.0'}
        
        recomendaciones = []
        encontrados_en_xml = 0

        for item in root.findall('.//item'):
            titulo = item.find('title').text.upper() if item.find('title') is not None else ""
            encontrados_en_xml += 1
            
            # Filtro ultra básico: solo buscamos la palabra clave
            if "ECOFLOW" in titulo:
                for mod in CAPACIDADES:
                    if mod["key"] in titulo:
                        # Si encontramos el modelo, calculamos sin filtros de hora para probar
                        if mod["watts"] >= w_usuario:
                            duracion = (mod["wh"] * 0.85) / w_usuario
                            recomendaciones.append({
                                "nombre": item.find('title').text,
                                "duracion_estimada": round(duracion, 1),
                                "precio": item.find('g:price', ns).text if item.find('g:price', ns) is not None else "Ver web",
                                "precio_oferta": item.find('g:sale_price', ns).text if item.find('g:sale_price', ns) is not None else None,
                                "url_imagen": item.find('g:image_link', ns).text if item.find('g:image_link', ns) is not None else "",
                                "url_producto": item.find('link').text if item.find('link') is not None else "#",
                                "wh": mod["wh"]
                            })
                            break

        # Ordenar por capacidad
        recomendaciones.sort(key=lambda x: x['wh'])
        
        # LOG DE DEPURACIÓN (Míralo en Railway)
        print(f"DEBUG: XML leido. Total items: {encontrados_en_xml}. EcoFlows aptos: {len(recomendaciones)}")

        return jsonify({"status": "ok", "recomendaciones": recomendaciones[:3]})

    except Exception as e:
        print(f"ERROR CRITICO: {str(e)}")
        return jsonify({"status": "error", "mensaje": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)