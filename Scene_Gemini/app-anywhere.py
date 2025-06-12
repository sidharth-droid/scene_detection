from flask import Flask, render_template, request, jsonify
import os
from werkzeug.utils import secure_filename
import google.generativeai as genai
from flask import send_from_directory

# from dotenv import load_dotenv

# load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)

# Configuration for PythonAnywhere
UPLOAD_FOLDER = os.path.join(os.path.expanduser('~'), 'uploads')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.static_folder = 'static'
app.static_url_path = '/static'

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
print(f"Upload directory set to: {UPLOAD_FOLDER}")
print(f"Directory exists: {os.path.exists(UPLOAD_FOLDER)}")
print(f"Directory writable: {os.access(UPLOAD_FOLDER, os.W_OK)}")

# Configure Gemini API
genai.configure(api_key='AIzaSyBN_F4aGxokneuCJVK4p8jmZBNq83Iq1NM')
model = genai.GenerativeModel('gemini-1.5-flash')

# Scene classes
SCENE_CLASSES = [
    'airport_inside', 'artstudio', 'auditorium', 'bakery', 'bar', 'bathroom', 'bedroom', 'bookstore',
    'bowling', 'buffet', 'casino', 'children_room', 'church_inside', 'classroom', 'cloister',
    'closet', 'clothingstore', 'computerroom', 'concert_hall', 'corridor', 'deli', 'dentaloffice',
    'dining_room', 'elevator', 'fastfood_restaurant', 'florist', 'gameroom', 'garage', 'greenhouse',
    'grocerystore', 'gym', 'hairsalon', 'hospitalroom', 'inside_bus', 'inside_subway', 'jewelleryshop',
    'kindergarden', 'kitchen', 'laboratorywet', 'laundromat', 'library', 'livingroom', 'lobby',
    'locker_room', 'mall', 'meeting_room', 'movietheater', 'museum', 'nursery', 'office',
    'operating_room', 'pantry', 'poolinside', 'prisoncell', 'restaurant', 'restaurant_kitchen',
    'shoeshop', 'stairscase', 'studiomusic', 'subway', 'toystore', 'trainstation', 'tv_studio',
    'videostore', 'waitingroom', 'warehouse', 'winecellar'
]

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    try:
        return send_from_directory(
            app.config['UPLOAD_FOLDER'],
            filename,
            as_attachment=False
        )
    except FileNotFoundError:
        return "File not found", 404

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        try:
            # Read file content into memory
            file_content = file.read()
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Write file to disk
            with open(filepath, 'wb') as f:
                f.write(file_content)
            
            print(f"File saved to: {filepath}")
            print(f"File exists: {os.path.exists(filepath)}")
            print(f"File size: {os.path.getsize(filepath) if os.path.exists(filepath) else 0} bytes")
            # Analyze the image with Gemini
            img = genai.upload_file(filepath)
            
            prompt = f"""Analyze this image and classify it into exactly one of the following scene categories:
            {', '.join(SCENE_CLASSES)}
            
            Return only the most appropriate scene category from the list above, nothing else."""
            
            response = model.generate_content([prompt, img])
            print("Response: ",response.text)
            
            # Clean up the response
            prediction = response.text.strip().lower()
            print("Prediction0: ",prediction)
            if prediction not in SCENE_CLASSES:
                prediction = "unknown"
            print("Prediction: ",prediction)
            return jsonify({
                'prediction': prediction,
                'image_url': f'/uploads/{filename}'
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        
    else:
        return jsonify({'error': 'File type not allowed'}), 400

if __name__ == '__main__':
    # Print configuration for debugging
    print("\n=== Application Configuration ===")
    print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"Static folder: {app.static_folder}")
    print(f"Static URL path: {app.static_url_path}")
    print("==============================\n")
    
    # Create a test file to verify write permissions
    test_file = os.path.join(app.config['UPLOAD_FOLDER'], 'test.txt')
    try:
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print("✓ Write test successful")
    except Exception as e:
        print(f"✗ Write test failed: {e}")
    
    app.run(debug=True, host='0.0.0.0')