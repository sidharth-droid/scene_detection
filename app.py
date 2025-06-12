import os
import argparse
import base64
import numpy as np
import cv2
import onnxruntime as ort
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global variables for model and classes
sess = None
input_name = None
classes = None

def load_classes(classes_path):
    # Read slash-separated classes and strip quotes
    text = open(classes_path, 'r').read()
    return [c.strip().strip("'\"") for c in text.split('/') if c.strip()]

def preprocess(frame, size=(224,224)):
    # BGR→RGB, resize, [0,1], normalize, CHW + batch
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, size, interpolation=cv2.INTER_AREA)
    img = img.astype(np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std  = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    img = (img - mean) / std
    img = img.transpose(2, 0, 1)[None, ...]
    return img

def create_session(model_path):
    # Load classification-only ONNX (single input)
    sess_opts = ort.SessionOptions()
    sess_opts.log_severity_level = 1
    providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
    sess = ort.InferenceSession(model_path, sess_opts, providers=providers)
    input_name = sess.get_inputs()[0].name
    return sess, input_name

def predict(frame):
    global sess, input_name, classes
    tensor = preprocess(frame)
    outputs = sess.run(None, {input_name: tensor})
    logits = outputs[0]
    idx = int(np.argmax(logits, axis=1)[0])
    return classes[idx]

def process_image(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return {"error": f"Cannot read image: {image_path}"}
    
    label = predict(img)
    
    # Convert the image for display
    _, buffer = cv2.imencode('.jpg', img)
    img_str = base64.b64encode(buffer).decode('utf-8')
    
    return {
        "prediction": label,
        "image": img_str
    }

def process_video(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"error": f"Cannot open video: {video_path}"}
    
    frames = []
    predictions = []
    
    # Process first 10 frames (or fewer if the video is shorter)
    frame_count = 0
    while cap.isOpened() and frame_count < 10:
        ret, frame = cap.read()
        if not ret:
            break
        
        label = predict(frame)
        predictions.append(label)
        
        # Add text to frame
        cv2.putText(frame, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        
        # Convert frame for display
        _, buffer = cv2.imencode('.jpg', frame)
        img_str = base64.b64encode(buffer).decode('utf-8')
        frames.append(img_str)
        
        frame_count += 1
    
    cap.release()
    
    return {
        "frames": frames,
        "predictions": predictions
    }

def process_base64_frame(base64_data):
    # Remove the data URL prefix if present
    if ',' in base64_data:
        base64_data = base64_data.split(',')[1]
    
    # Decode base64 to image
    img_data = base64.b64decode(base64_data)
    nparr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Make prediction
    label = predict(img)
    
    return {"prediction": label}
model_path = 'MIT_indoor_vit.onnx'
classes_path = 'indoorSceneClasses.txt'

    # Load model and classes globally
classes = load_classes(classes_path)
sess, input_name = create_session(model_path)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/upload_image', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"})
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    result = process_image(file_path)
    return jsonify(result)

@app.route('/upload_video', methods=['POST'])
def upload_video():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"})
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    result = process_video(file_path)
    return jsonify(result)

@app.route('/process_webcam', methods=['POST'])
def process_webcam():
    data = request.json
    if 'image' not in data:
        return jsonify({"error": "No image data"})
    
    result = process_base64_frame(data['image'])
    return jsonify(result)

if __name__ == '__main__':
    
    print(f"Model loaded with {len(classes)} classes")
    # print("Starting server at http://127.0.0.1:5000")

    app.run(host='0.0.0.0', port=5000, debug=True)