from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# --- DATOS DE REFERENCIA ---
MODELOS_ECOFLOW = [
    {"nombre": "EcoFlow RIVER 2", "capacidad_wh": 256, "potencia_max_w": 300},
    {"nombre": "EcoFlow RIVER 2 Max", "capacidad_wh": 512, "potencia_max_w": 500},
    {"nombre": "EcoFlow RIVER 2 Pro", "capacidad_wh": 768, "potencia_max_w": 800},
    {"nombre": "EcoFlow DELTA mini", "capacidad_wh": 882, "potencia_max_w": 1400},
    {"nombre": "EcoFlow DELTA 2", "capacidad_wh": 1024, "potencia_max_w": 1800},
    {"nombre": "EcoFlow DELTA Max (1600)", "capacidad_wh": 1612, "potencia_max_w": 2000},
    {"nombre": "EcoFlow DELTA Pro", "capacidad_wh": 3600, "potencia_max_w": 3600}
]

@app.route('/')
def home():
    return "API de Asesor EcoFlow Online", 200

@app.route('/calcular', methods=['POST'])
def calcular():
    try:
        datos = request.json
        # 'equipos' será una lista de objetos: [{"watts": 10, "cantidad": 2}, ...]
        equipos = datos.get('equipos', [])
        horas_deseadas = float(datos.get('horas', 1))
        
        # 1. Calcular consumo total en Watts
        total_watts = sum(float(e['watts']) * int(e['cantidad']) for e in equipos)
        
        if total_watts == 0:
            return jsonify({"error": "No hay consumo detectado"}), 400

        # 2. Buscar mejores estaciones
        margen_eficiencia = 0.85
        energia_requerida_wh = (total_watts * horas_deseadas) / margen_eficiencia
        
        opciones = []
        for estacion in MODELOS_ECOFLOW:
            puede_potencia = estacion['potencia_max_w'] >= total_watts
            capacidad_suficiente = estacion['capacidad_wh'] >= energia_requerida_wh
            
            if puede_potencia and capacidad_suficiente:
                # Calcular duración real para esta estación específica
                duracion_real = (estacion['capacidad_wh'] * margen_eficiencia) / total_watts
                
                opciones.append({
                    "nombre": estacion['nombre'],
                    "capacidad_wh": estacion['capacidad_wh'],
                    "potencia_max_w": estacion['potencia_max_w'],
                    "duracion_estimada": round(duracion_real, 1)
                })
        
        # Ordenar por la más económica/pequeña que sirva
        opciones.sort(key=lambda x: x['capacidad_wh'])

        return jsonify({
            "status": "ok",
            "consumo_total_w": total_watts,
            "horas_solicitadas": horas_deseadas,
            "recomendaciones": opciones[:2] # Devolvemos las 2 mejores
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)