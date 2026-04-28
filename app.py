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
        productos_descartados = []

        for item in root.findall('.//item'):
            # Buscamos en todas las etiquetas posibles el texto
            texto_todo = " ".join([elem.text for elem in item.iter() if elem.text]).upper()
            
            if "ECOFLOW" in texto_todo or "RIVER" in texto_todo or "DELTA" in texto_todo:
                # 1. Filtro de accesorios
                if any(x in texto_todo for x in ["TERMO", "MUG", "BOLSO", "CABLE", "FUNDA", "BOLSA", "CHASIS"]):
                    continue

                # 2. Captura de precio
                precio_raw = item.find('g:price', ns).text if item.find('g:price', ns) is not None else "0"
                try:
                    # Extraer solo el número (ej: "123456.0 CLP")
                    valor_precio = float(precio_raw.split()[0])
                except:
                    valor_precio = 0

                # 3. Solo productos de más de $100.000 (para asegurar que sean estaciones)
                if valor_precio < 100000:
                    continue

                # 4. Clasificación por modelo
                wh, watts_max, nombre_bonito = 256, 300, "EcoFlow River 2"
                
                if "PRO 2" in texto_todo or "PRO2" in texto_todo: 
                    wh, watts_max, nombre_bonito = 4096, 4000, "EcoFlow Delta Pro 2"
                elif "DELTA 3" in texto_todo: 
                    wh, watts_max, nombre_bonito = 1024, 1800, "EcoFlow Delta 3"
                elif "DELTA 2" in texto_todo: 
                    wh, watts_max, nombre_bonito = 1024, 1800, "EcoFlow Delta 2"
                elif "RIVER 2 PRO" in texto_todo: 
                    wh, watts_max, nombre_bonito = 768, 800, "EcoFlow River 2 Pro"
                elif "RIVER 2 MAX" in texto_todo: 
                    wh, watts_max, nombre_bonito = 512, 500, "EcoFlow River 2 Max"
                elif "DELTA" in texto_todo:
                    wh, watts_max, nombre_bonito = 1024, 1800, "EcoFlow Delta Series"

                # 5. Filtro por potencia del usuario
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
                else:
                    productos_descartados.append(f"{nombre_bonito} (Soporta {watts_max}W)")

        # Limpiar duplicados y ordenar
        recomendaciones.sort(key=lambda x: x['wh'])
        vistos = set()
        unicos = []
        for r in recomendaciones:
            if r['nombre'] not in vistos:
                unicos.append(r)
                vistos.add(r['nombre'])

        print(f"DEBUG: Recomendados: {len(unicos)} | Descartados por potencia: {len(productos_descartados)}")
        
        return jsonify({
            "status": "ok", 
            "recomendaciones": unicos[:3],
            "debug_info": {"descartados": productos_descartados[:5]}
        })

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({"status": "error", "mensaje": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)