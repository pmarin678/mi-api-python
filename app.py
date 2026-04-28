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
        h_usuario = float(datos.get('horas', 0))
        
        # 1. Obtener el XML (La parte que ya sabemos que funciona)
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(XML_URL, headers=headers, timeout=15)
        root = ET.fromstring(response.content)
        
        # Namespace de Google que usa Bsale
        ns = {'g': 'http://base.google.com/ns/1.0'}
        
        recomendaciones = []
        
        # 2. Recorrer los 180 productos
        for item in root.findall('.//item'):
            titulo_raw = item.find('title').text if item.find('title') is not None else ""
            titulo = titulo_raw.upper()
            
            # FILTRO MAESTRO: Si menciona EcoFlow, River o Delta, entra a la lista
            if any(key in titulo for key in ["ECOFLOW", "RIVER", "DELTA"]):
                
                # Excluir accesorios para no ensuciar el resultado
                if any(acc in titulo for acc in ["PANEL", "SOLAR", "CABLE", "FUNDA", "BOLSO", "BATERIA EXTRA"]):
                    continue

                # Extraer datos de Bsale
                precio = item.find('g:price', ns).text if item.find('g:price', ns) is not None else "Consultar"
                link = item.find('link').text if item.find('link') is not None else "#"
                imagen = item.find('g:image_link', ns).text if item.find('g:image_link', ns) is not None else ""
                
                # Asignación automática de capacidad según el nombre
                # (Para que el cálculo de horas funcione)
                wh = 256 # Default River 2
                watts_max = 300
                
                if "DELTA PRO" in titulo: wh, watts_max = 3600, 3600
                elif "DELTA 3" in titulo: wh, watts_max = 1024, 1800
                elif "DELTA 2" in titulo: wh, watts_max = 1024, 1800
                elif "MAX" in titulo: wh, watts_max = 512, 500
                elif "PRO" in titulo: wh, watts_max = 768, 800

                # Solo mostrar si la estación soporta los Watts del usuario
                if watts_max >= w_usuario:
                    duracion = (wh * 0.85) / max(w_usuario, 1)
                    
                    recomendaciones.append({
                        "nombre": titulo_raw,
                        "duracion_estimada": round(duracion, 1),
                        "precio": precio,
                        "url_imagen": imagen,
                        "url_producto": link,
                        "wh": wh
                    })

        # Ordenar de menor a mayor capacidad
        recomendaciones.sort(key=lambda x: x['wh'])

        # 3. Log para que veas en Railway si funcionó
        print(f"DEBUG: Detectados {len(recomendaciones)} productos EcoFlow aptos de los 180.")

        return jsonify({
            "status": "ok",
            "recomendaciones": recomendaciones[:3]
        })

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({"status": "error", "mensaje": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)