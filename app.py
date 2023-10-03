import os
import subprocess
import uuid
import threading
import time
from flask import Flask, render_template, request, send_from_directory
import schedule

app = Flask(__name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
CONVERTED_FOLDER = os.path.join(BASE_DIR, 'converted')
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(CONVERTED_FOLDER):
    os.makedirs(CONVERTED_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CONVERTED_FOLDER'] = CONVERTED_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html', audio_file=None)

@app.route('/convert', methods=['POST'])
def convert():
    if 'file' not in request.files:
        return render_template('index.html', error="No file part")
    file = request.files['file']
    if file.filename == '':
        return render_template('index.html', error="No selected file")
    if file and allowed_file(file.filename):
        filename = str(uuid.uuid4())
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        converted_filepath = os.path.join(app.config['CONVERTED_FOLDER'], f"{filename}.mp3")
        file.save(filepath)

        # Conversion using FFmpeg
        subprocess.run(["ffmpeg", "-i", filepath, "-q:a", "0", converted_filepath])

        return render_template('index.html', audio_file=f"/download/{filename}.mp3")
    else:
        return render_template('index.html', error="Unsupported file format")

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['CONVERTED_FOLDER'], filename, as_attachment=True)

def cleanup_old_files():
    now = time.time()
    for folder in [UPLOAD_FOLDER, CONVERTED_FOLDER]:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            if os.path.getctime(file_path) < now - 1 * 3600:  # older than 1 hour
                os.unlink(file_path)

def run_continuously(interval=1):
    cease_continuous_run = threading.Event()
    while not cease_continuous_run.is_set():
        schedule.run_pending()
        time.sleep(interval)

schedule.every(10).minutes.do(cleanup_old_files)

cleanup_thread = threading.Thread(target=run_continuously)
cleanup_thread.start()

if __name__ == '__main__':
    app.run(debug=True)
