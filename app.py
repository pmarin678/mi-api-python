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
        datos = request.json
        w_usuario = float(datos.get('watts', 0))
        
        response = requests.get(XML_URL, timeout=15)
        root = ET.fromstring(response.content)
        ns = {'g': 'http://base.google.com/ns/1.0'}
        
        recomendaciones = []

        for item in root.findall('.//item'):
            # Capturamos todo el texto para identificar el modelo
            texto_todo = " ".join([elem.text for elem in item.iter() if elem.text]).upper()
            
            # Filtro estricto: Debe ser EcoFlow y NO ser accesorio/merchandising
            if "ECOFLOW" in texto_todo:
                if any(x in texto_todo for x in ["TERMO", "MUG", "BOLSO", "CABLE", "FUNDA", "PANEL", "SOLAR", "ADAPTADOR", "CHASIS"]):
                    continue

                # Extraer Precio para filtrar por valor (las estaciones valen más de 100.000 generalmente)
                precio_raw = item.find('g:price', ns).text if item.find('g:price', ns) is not None else "0"
                # Limpiamos el precio para convertirlo a número (ej: "24990.0 CLP" -> 24990)
                try:
                    valor_precio = float(precio_raw.split()[0])
                except:
                    valor_precio = 0

                if valor_precio < 150000: # Si vale menos de 150k, probablemente no es una estación
                    continue

                # Identificación de Capacidad
                wh, watts_max, nombre_bonito = 256, 300, "EcoFlow River 2"
                
                if "PRO 2" in texto_todo or "PRO2" in texto_todo: wh, watts_max, nombre_bonito = 4096, 4000, "EcoFlow Delta Pro 2"
                elif "DELTA 3" in texto_todo: wh, watts_max, nombre_bonito = 1024, 1800, "EcoFlow Delta 3"
                elif "DELTA 2" in texto_todo: wh, watts_max, nombre_bonito = 1024, 1800, "EcoFlow Delta 2"
                elif "RIVER 2 PRO" in texto_todo: wh, watts_max, nombre_bonito = 768, 800, "EcoFlow River 2 Pro"
                elif "RIVER 2 MAX" in texto_todo: wh, watts_max, nombre_bonito = 512, 500, "EcoFlow River 2 Max"

                if watts_max >= w_usuario:
                    duracion = (wh * 0.85) / max(w_usuario, 1)
                    recomendaciones.append({
                        "nombre": nombre_bonito,
                        "duracion_estimada": round(duracion, 1),
                        "precio": precio_raw,
                        "url_imagen": item.find('g:image_link', ns).text if item.find('g:image_link', ns) is not None else "",
                        "url_producto": item.find('link').text,
                        "wh": wh
                    })

        # Ordenar por capacidad y eliminar duplicados de nombre
        recomendaciones.sort(key=lambda x: x['wh'])
        
        # Filtrar duplicados (por si el XML tiene el mismo producto dos veces)
        vistos = set()
        unicos = []
        for r in recomendaciones:
            if r['nombre'] not in vistos:
                unicos.append(r)
                vistos.add(r['nombre'])

        return jsonify({"status": "ok", "recomendaciones": unicos[:3]})

    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)