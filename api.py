from flask import Flask, request, jsonify, render_template
import os
from flask_cors import CORS
import whisper
import io
import base64
import requests
from openai import OpenAI

client = OpenAI(api_key="your_key")

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load the Whisper model
audio_to_text_model = whisper.load_model("small")  # Choose from tiny, base, small, medium, large

# Directory where uploaded files will be saved
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configuring the upload folder in the Flask app
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed extensions
ALLOWED_EXTENSIONS = {'mp3'}

# Function to check if the file has the allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to censor lyrics using GPT API
def censor_lyrics(lyrics):
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": f"Please censor any explicit or inappropriate language in the following lyrics, and then condense the lyrics to their most essential parts that can best represent the mood and theme for generating a music cover (max 25 tokens). Focus on keeping parts that are most relevant for a visual interpretation using DALL·E-3. Return as an output only the extracted lyrics! Here are the lyrics: '{lyrics}'"
            }
        ]
    )

    print(completion.choices[0].message)
    return completion.choices[0].message.content

# Route to upload the mp3 file
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Transcribe audio (MP3)
        lyrics = audio_to_text_model.transcribe(file_path)['text']

        # Censor the lyrics using GPT-4
        censored_lyrics = censor_lyrics(lyrics)

        prompt = f"Based on the following lyrics '{censored_lyrics}' generate a cover image. Requirements are: 1. Don't include text in the image. 2. Use few objects 3. Style should be like a music cover."

        # Use OpenAI DALL·E API to generate the image
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )

        print(response)
        # Get the image URL
        image_url = response.data[0].url

        # Download the image and convert it to base64
        image_data = requests.get(image_url,timeout=30)
        img_str = base64.b64encode(image_data.content).decode("utf-8")

        return jsonify({
            "message": f"File {filename} uploaded and processed successfully!",
            "image": img_str  # Base64 encoded image
        }), 200
    else:
        return jsonify({"error": "File type not allowed. Please upload an mp3 file."}), 400

# Route to serve index.html
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
