from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Ruta de prueba para saber si el servidor está vivo
@app.route('/')
def home():
    return "Servidor de Energía Online"

@app.route('/calcular', methods=['POST'])
def calcular():
    try:
        datos = request.json
        if not datos:
            return jsonify({"error": "No se recibieron datos"}), 400
            
        # Lógica de cálculo (puedes cambiar este num * 2 por tu fórmula)
        num = datos.get('valor', 0)
        resultado = float(num) * 2 
        
        return jsonify({
            "resultado": resultado,
            "status": "ok",
            "mensaje": "Cálculo realizado con éxito"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Quitamos el app.run() de aquí abajo porque Railway usa Gunicorn
# Solo dejamos esto por si quieres probarlo localmente alguna vez
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

    