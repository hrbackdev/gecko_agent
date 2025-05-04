import base64
import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)

@app.route('/analyze', methods=['POST'])
def analyze_image():
    if 'image' not in request.files or 'prompt' not in request.form:
        return jsonify({'error': 'Falta la imagen o el prompt'}), 400

    image_file = request.files['image']
    prompt = request.form['prompt']

    # Convertir imagen a base64
    image_bytes = image_file.read()
    b64_image = base64.b64encode(image_bytes).decode('utf-8')

    try:
        # Consulta a GPT-4 Vision
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"¿La imagen muestra esto?: {prompt}. Solo responde con 'Sí' o 'No' y una frase explicativa si es sí."},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}
                        }
                    ]
                }
            ],
            max_tokens=100
        )

        content = response.choices[0].message.content.lower()

        if content.startswith("sí") or content.startswith("yes"):
            return jsonify({"match": True, "response": response.choices[0].message.content})
        else:
            return jsonify({"match": False})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
