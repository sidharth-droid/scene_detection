from flask import Flask, render_template, request, jsonify
import os
from werkzeug.utils import secure_filename
import google.generativeai as genai
from flask import send_from_directory

# from dotenv import load_dotenv

# load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.static_folder = 'static'
app.static_url_path = '/static'

# Configure Gemini API
genai.configure(api_key='YourAPI')
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
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
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
    # Ensure upload directory exists and has write permissions
    upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), app.config['UPLOAD_FOLDER'])
    os.makedirs(upload_dir, exist_ok=True)
    print(f"Upload directory: {upload_dir}")
    print(f"Directory exists: {os.path.exists(upload_dir)}")
    print(f"Directory writable: {os.access(upload_dir, os.W_OK)}")
    
    app.run(debug=True, host='0.0.0.0')