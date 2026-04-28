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
        # 1. Intentar obtener el XML
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(XML_URL, headers=headers, timeout=15)
        
        # 2. Parsear el XML con cuidado de namespaces
        root = ET.fromstring(response.content)
        
        # Lista para ver qué hay adentro si todo falla
        muestreo_titulos = []
        encontrados = []
        
        # El Namespace de Google que usa Bsale
        ns = {'g': 'http://base.google.com/ns/1.0'}

        for item in root.findall('.//item'):
            titulo_raw = item.find('title').text if item.find('title') is not None else "Sin Titulo"
            muestreo_titulos.append(titulo_raw)
            
            # BUSQUEDA ULTRA-SIMPLE: Solo buscamos la palabra "RIVER" o "DELTA"
            # Ignoramos mayúsculas/minúsculas
            t_upper = titulo_raw.upper()
            if "RIVER" in t_upper or "DELTA" in t_upper or "ECOFLOW" in t_upper:
                
                # Si encontramos uno, extraemos sus datos de Bsale
                precio = item.find('g:price', ns).text if item.find('g:price', ns) is not None else "0"
                link = item.find('link').text if item.find('link') is not None else ""
                
                encontrados.append({
                    "nombre": titulo_raw,
                    "precio": precio,
                    "link": link
                })

        # 3. Respuesta inteligente
        if not encontrados:
            # Si no encontró nada, mandamos los primeros 5 títulos del XML para ver qué está pasando
            return jsonify({
                "status": "error",
                "mensaje": "No se reconocieron productos EcoFlow",
                "diagnostico": muestreo_titulos[:10] # Esto nos dirá qué nombres hay en el XML
            })

        return jsonify({
            "status": "ok",
            "productos_detectados": encontrados[:5] # Probamos devolviendo lo que encontró
        })

    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)