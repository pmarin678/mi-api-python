from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# PRODUCTOS FIJOS (Sin depender de XML)
PRODUCTOS_ECOFLOW = [
    {
        "nombre": "EcoFlow River 2 Max",
        "wh": 512,
        "watts_max": 500,
        "url_imagen": "https://dojiw2m9tvv09.cloudfront.net/59518/product/X_river-2-max-ecoflow-ecoflow-chile-chile-estaciones-de-energi-a-respaldo-hogar-respaldo-energi-a-generador-ele-ctrico5806.jpg?498&t=1777408549", 
        "url_producto": "https://www.awl.cl/product/ecoflow-river-max-2"
    },
    {
        "nombre": "EcoFlow Delta 3",
        "wh": 1024,
        "watts_max": 1800,
        "url_imagen": "https://dojiw2m9tvv09.cloudfront.net/59518/product/X_delta-3-ecoflow-ecoflow-chile-estacion-de-energia-respaldo-hogar-respaldo-energia1223.jpg?498&t=1777408536",
        "url_producto": "https://www.awl.cl/product/ecoflow-delta-3"
    },
    {
        "nombre": "EcoFlow Delta Pro 2",
        "wh": 3600,
        "watts_max": 4500,
        "url_imagen": "https://dojiw2m9tvv09.cloudfront.net/59518/product/X_delta-pro-ecoflow-ecoflowchile-serie-delta-ecoflow-delta-deltaecoflow-chile-28302.jpg?498&t=1777408404",
        "url_producto": "https://www.awl.cl/product/ecoflow-delta-pro-2"
    }
]

@app.route('/calcular', methods=['POST'])
def calcular():
    try:
        datos = request.json
        w_usuario = float(datos.get('watts', 0))
        h_usuario = float(datos.get('horas', 0))
        
        recomendaciones = []

        for prod in PRODUCTOS_ECOFLOW:
            # Filtro: ¿La estación aguanta la potencia que pide el usuario?
            if prod["watts_max"] >= w_usuario:
                # Cálculo de autonomía: (Capacidad * Eficiencia 85%) / Consumo
                duracion_real = (prod["wh"] * 0.85) / max(w_usuario, 1)
                
                recomendaciones.append({
                    "nombre": prod["nombre"],
                    "duracion_estimada": round(duracion_real, 1),
                    "url_imagen": prod["url_imagen"],
                    "url_producto": prod["url_producto"],
                    "wh": prod["wh"]
                })

        # Ordenar de menor a mayor capacidad
        recomendaciones.sort(key=lambda x: x['wh'])

        return jsonify({
            "status": "ok",
            "recomendaciones": recomendaciones[:3]
        })

    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)