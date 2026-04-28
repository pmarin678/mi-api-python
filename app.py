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
        
        # 1. Descarga del XML
        response = requests.get(XML_URL, timeout=15)
        root = ET.fromstring(response.content)
        
        # 2. Definición del Namespace de Google (CRÍTICO)
        ns = {'g': 'http://base.google.com/ns/1.0'}
        
        recomendaciones = []

        # 3. Buscar todos los <item> dentro de <channel>
        for item in root.findall('.//item'):
            # Obtener título y descripción para identificar el producto
            titulo_elem = item.find('title')
            titulo = titulo_elem.text.upper() if titulo_elem is not None else ""
            
            # Solo procesar si es EcoFlow y NO es un accesorio
            if "ECOFLOW" in titulo:
                # Lista negra de accesorios para limpiar el resultado
                if any(x in titulo for x in ["BOLSO", "FUNDA", "CABLE", "PANEL", "SOLAR", "TERMO", "MUG"]):
                    continue

                # Extraer Link e Imagen (usando el namespace 'g')
                link_elem = item.find('link')
                img_elem = item.find('{http://base.google.com/ns/1.0}image_link')
                precio_elem = item.find('{http://base.google.com/ns/1.0}price')
                stock_elem = item.find('{http://base.google.com/ns/1.0}availability')

                # Validar que existan los datos mínimos
                if link_elem is None or precio_elem is None:
                    continue
                
                # Verificar disponibilidad
                if stock_elem is not None and "OUT OF STOCK" in stock_elem.text.upper():
                    continue

                # --- Lógica de Capacidad Técnica ---
                # Definimos por defecto River 2
                wh, watts_max, nombre_limpio = 256, 300, "EcoFlow River 2"

                if "DELTA PRO 2" in titulo: wh, watts_max, nombre_limpio = 4096, 4000, "EcoFlow Delta Pro 2"
                elif "DELTA 3" in titulo: wh, watts_max, nombre_limpio = 1024, 1800, "EcoFlow Delta 3"
                elif "DELTA 2" in titulo: wh, watts_max, nombre_limpio = 1024, 1800, "EcoFlow Delta 2"
                elif "RIVER 2 PRO" in titulo: wh, watts_max, nombre_limpio = 768, 800, "EcoFlow River 2 Pro"
                elif "RIVER 2 MAX" in titulo: wh, watts_max, nombre_limpio = 512, 500, "EcoFlow River 2 Max"
                elif "DELTA" in titulo: wh, watts_max, nombre_limpio = 1024, 1800, "EcoFlow Delta Series"

                # 4. Filtro por potencia del usuario
                if watts_max >= w_usuario:
                    duracion = (wh * 0.85) / max(w_usuario, 1)
                    
                    recomendaciones.append({
                        "nombre": nombre_limpio,
                        "titulo_original": titulo.title(),
                        "duracion_estimada": round(duracion, 1),
                        "precio": precio_elem.text,
                        "url_imagen": img_elem.text if img_elem is not None else "",
                        "url_producto": link_elem.text,
                        "wh": wh
                    })

        # Ordenar por capacidad y eliminar duplicados de modelos
        recomendaciones.sort(key=lambda x: x['wh'])
        
        finales = []
        vistos = set()
        for r in recomendaciones:
            if r['nombre'] not in vistos:
                finales.append(r)
                vistos.add(r['nombre'])

        return jsonify({"status": "ok", "recomendaciones": finales[:3]})

    except Exception as e:
        print(f"Error analizando XML: {str(e)}")
        return jsonify({"status": "error", "mensaje": "No se pudo procesar el catálogo"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)