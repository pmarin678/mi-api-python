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
        
        # Namespace de Google por si acaso
        ns = {'g': 'http://base.google.com/ns/1.0'}
        
        recomendaciones = []

        for item in root.findall('.//item'):
            # BUSQUEDA AGRESIVA: Extraemos todo el texto del item para encontrar el nombre
            # Bsale a veces pone el título en etiquetas con prefijos
            texto_completo = " ".join([elem.text for elem in item.iter() if elem.text]).upper()
            
            if "ECOFLOW" in texto_completo or "RIVER" in texto_completo or "DELTA" in texto_completo:
                # Si es un accesorio, lo saltamos
                if any(acc in texto_completo for acc in ["PANEL", "SOLAR", "CABLE", "FUNDA", "BOLSO"]):
                    continue

                # Intentamos capturar los datos con o sin el prefijo 'g:'
                nombre = item.find('title').text if item.find('title') is not None else "Estación EcoFlow"
                link = item.find('link').text if item.find('link') is not None else "#"
                
                # Buscamos el precio en cualquier variante de etiqueta
                precio = "Consultar"
                for p_tag in ['g:price', 'price', '{http://base.google.com/ns/1.0}price']:
                    p_elem = item.find(p_tag, ns) if ':' in p_tag else item.find(p_tag)
                    if p_elem is not None:
                        precio = p_elem.text
                        break

                imagen = ""
                for i_tag in ['g:image_link', 'image_link']:
                    i_elem = item.find(i_tag, ns) if ':' in i_tag else item.find(i_tag)
                    if i_elem is not None:
                        imagen = i_elem.text
                        break

                # Asignación de capacidad por palabras clave en el texto completo
                wh, watts_max = 256, 300 # Default
                if "PRO 2" in texto_completo: wh, watts_max = 4096, 4000
                elif "DELTA 3" in texto_completo: wh, watts_max = 1024, 1800
                elif "DELTA 2" in texto_completo: wh, watts_max = 1024, 1800
                elif "PRO" in texto_completo: wh, watts_max = 768, 800
                elif "MAX" in texto_completo: wh, watts_max = 512, 500

                if watts_max >= w_usuario:
                    duracion = (wh * 0.85) / max(w_usuario, 1)
                    recomendaciones.append({
                        "nombre": nombre if nombre != "Sin Titulo" else f"EcoFlow {wh}Wh",
                        "duracion_estimada": round(duracion, 1),
                        "precio": precio,
                        "url_imagen": imagen,
                        "url_producto": link,
                        "wh": wh
                    })

        recomendaciones.sort(key=lambda x: x['wh'])
        
        # Log de éxito
        print(f"DEBUG: ¡Logramos identificar {len(recomendaciones)} productos!")

        return jsonify({"status": "ok", "recomendaciones": recomendaciones[:3]})

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return jsonify({"status": "error", "mensaje": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)