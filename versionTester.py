from flask import Flask, jsonify, request
from flask_cors import CORS
from tensorflow import keras
from tensorflow.keras.models import load_model
import numpy as np
import pandas as pd


app = Flask(__name__)
CORS(app)

@app.route('/predict')
def predict():
    model = load_model('model1.keras')
    weights_dict = {}
    
    for layer in model.layers:
        weights = layer.get_weights()
        if weights:
            weights_dict[layer.name] = [w.tolist() for w in weights]
    return jsonify(weights_dict)

@app.route('/predict2')
def predict2():
    model = load_model('model1.keras')
    train_predictions = model.predict()
    train_results = pd.DataFrame(data={'Train Predictions': train_predictions})
    return train_results.to_json(orient='records')
    

if __name__ == '__main__':
    app.run(debug=True)
    
