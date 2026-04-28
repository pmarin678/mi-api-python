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
            try:
                # --- VALIDACIÓN DE SEGURIDAD ---
                # Si falta el título o el link, saltamos este producto
                el_titulo = item.find('title')
                el_link = item.find('link')
                
                if el_titulo is None or el_link is None:
                    continue
                
                # Extraemos el texto de forma segura
                titulo_raw = el_titulo.text if el_titulo.text else ""
                url_producto = el_link.text if el_link.text else "#"
                
                # Buscamos el texto en todo el bloque del producto para identificarlo
                texto_todo = " ".join([elem.text for elem in item.iter() if elem.text]).upper()
                
                # --- FILTROS DE MARCA Y ACCESORIOS ---
                if "ECOFLOW" in texto_todo or "RIVER" in texto_todo or "DELTA" in texto_todo:
                    if any(x in texto_todo for x in ["TERMO", "MUG", "BOLSO", "CABLE", "FUNDA", "BOLSA", "CHASIS"]):
                        continue

                    # Captura de precio segura
                    precio_elem = item.find('g:price', ns)
                    precio_raw = precio_elem.text if (precio_elem is not None and precio_elem.text) else "0 CLP"
                    
                    try:
                        valor_precio = float(precio_raw.split()[0])
                    except:
                        valor_precio = 0

                    if valor_precio < 100000:
                        continue

                    # --- MAPEO DE CAPACIDADES ---
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

                    # --- FILTRO DE POTENCIA ---
                    if watts_max >= w_usuario:
                        duracion = (wh * 0.85) / max(w_usuario, 1)
                        
                        img_elem = item.find('g:image_link', ns)
                        url_imagen = img_elem.text if (img_elem is not None and img_elem.text) else ""

                        recomendaciones.append({
                            "nombre": nombre_bonito,
                            "duracion_estimada": round(duracion, 1),
                            "precio": precio_raw,
                            "url_imagen": url_imagen,
                            "url_producto": url_producto,
                            "wh": wh
                        })
            except Exception:
                # Si un producto individual falla, lo ignoramos y seguimos con el siguiente
                continue

        # Limpiar duplicados y ordenar
        recomendaciones.sort(key=lambda x: x['wh'])
        vistos = set()
        unicos = []
        for r in recomendaciones:
            if r['nombre'] not in vistos:
                unicos.append(r)
                vistos.add(r['nombre'])

        return jsonify({"status": "ok", "recomendaciones": unicos[:3]})

    except Exception as e:
        print(f"ERROR CRÍTICO: {str(e)}")
        return jsonify({"status": "error", "mensaje": "Error procesando el catálogo"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)