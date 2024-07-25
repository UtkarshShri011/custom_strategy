from flask import Flask, request, jsonify
import random

app = Flask(__name__)

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    if data:
        result = random.choice([0, 1])
        return jsonify({"result": result})
    else:
        return jsonify({"error": "No data provided"}), 400

if __name__ == '__main__':
    app.run(debug=True)
