import pickle

import joblib
import numpy as np
import torch
from flask import Flask, jsonify, request

app = Flask(__name__)


def net_process(model_path, scaler_path, json_data):
    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)
    inputs = [
                 json_data.get(f'{i}.{feature}')
                 for i in range(3)
                 for feature in ['X', 'Y', 'Z']
             ] + [
                 json_data.get(feature)
                 for feature in [
            '重力X', '重力Y', '重力Z',
            '翻滚角', '倾斜角', '方位角',
            '温度', '相对方位', '磁倾角',
            '磁总量', '磁场幅值', '北向方位', '高边方位'
        ]
             ]
    numpy_data = np.array(inputs).reshape(1, -1)
    numpy_data = scaler.transform(numpy_data)
    X = torch.from_numpy(numpy_data.astype(np.float32))
    model = torch.load(model_path)
    Y = model(X)
    print(Y)
    return round(float(Y[0]), 3)


def svr_process(model_path, scaler_path, json_data):
    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)
    inputs = [
                 json_data.get(f'{i}.{feature}')
                 for i in range(3)
                 for feature in ['X', 'Y', 'Z']
             ] + [
                 json_data.get(feature)
                 for feature in [
            '重力X', '重力Y', '重力Z',
            '翻滚角', '倾斜角', '方位角',
            '温度', '相对方位', '磁倾角',
            '磁总量', '磁场幅值', '北向方位', '高边方位'
        ]
             ]
    numpy_data = np.array(inputs).reshape(1, -1)
    inputs = scaler.transform(numpy_data)
    model = joblib.load(model_path)
    outputs = model.predict(inputs)
    return round(outputs[0], 3)


@app.route('/1', methods=['POST'])
def predict_mlp1():
    json_data = request.get_json()
    distance = net_process('model/MLP_1_model.pkl', 'scaler/MLP_1_scaler.pkl', json_data)
    return jsonify({'distance': distance})


@app.route('/2', methods=['POST'])
def predict_mlp3():
    json_data = request.get_json()
    distance = net_process('model/MLP_3_model.pkl', 'scaler/MLP_3_scaler.pkl', json_data)
    return jsonify({'distance': distance})


@app.route('/3', methods=['POST'])
def predict_mlp5():
    json_data = request.get_json()
    distance = net_process('model/MLP_5_model.pkl', 'scaler/MLP_5_scaler.pkl', json_data)
    return jsonify({'distance': distance})


@app.route('/4', methods=['POST'])
def predict_svr1():
    json_data = request.get_json()
    distance = svr_process('model/SVR_1_model.pkl', 'scaler/SVR_1_scaler.pkl', json_data)
    return jsonify({'distance': distance})


@app.route('/5', methods=['POST'])
def predict_svr3():
    json_data = request.get_json()
    distance = svr_process('model/SVR_3_model.pkl', 'scaler/SVR_3_scaler.pkl', json_data)
    return jsonify({'distance': distance})


@app.route('/6', methods=['POST'])
def predict_svr5():
    json_data = request.get_json()
    distance = svr_process('model/SVR_5_model.pkl', 'scaler/SVR_5_scaler.pkl', json_data)
    return jsonify({'distance': distance})


@app.route('/7', methods=['POST'])
def predict_cnn1():
    json_data = request.get_json()
    distance = net_process('model/CNN_1_model.pkl', 'scaler/CNN_1_scaler.pkl', json_data)
    return jsonify({'distance': distance})


@app.route('/8', methods=['POST'])
def predict_cnn3():
    json_data = request.get_json()
    distance = net_process('model/CNN_3_model.pkl', 'scaler/CNN_3_scaler.pkl', json_data)
    return jsonify({'distance': distance})


@app.route('/9', methods=['POST'])
def predict_cnn5():
    json_data = request.get_json()
    distance = net_process('model/CNN_5_model.pkl', 'scaler/CNN_5_scaler.pkl', json_data)
    return jsonify({'distance': distance})


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


if __name__ == '__main__':
    app.run()
