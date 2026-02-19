import cv2
import pytesseract
import numpy as np
import re
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# --- ANA SAYFA YÖNLENDİRMESİ (404 ÇÖZÜMÜ) ---
@app.route('/')
def index():
    # Bu dosya mutlaka 'templates/index.html' konumunda olmalı
    return render_template('index.html')

# --- GÖRÜNTÜ ÖN İŞLEME (Tesseract İçin Optimize) ---
def goruntu_iyilestir(file_bytes):
    try:
        nparr = np.frombuffer(file_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Görüntüyü 2 kat büyütmek Tesseract'ın küçük karakterleri tanımasını sağlar
        height, width = gray.shape
        gray = cv2.resize(gray, (width*2, height*2), interpolation=cv2.INTER_CUBIC)
        
        # Keskinleştirme Maskesi
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        processed = cv2.filter2D(gray, -1, kernel)
        
        return processed
    except:
        return None

# --- ESNEK RİSK ANALİZİ (Fuzzy Matching) ---
def esnek_analiz(text):
    risk = 0
    bulgular = []
    t = text.lower()
    
    # OCR bozuk okusa bile karakter dizilimlerinden yakalıyoruz
    tehditler = {
        "Hukuki Baskı": ["icra", "uzla", "ceza", "hukuk", "avukat", "geraic"],
        "Platform Taklidi": ["ins", "tag", "destek", "yard", "telif", "ihlal", "siga"],
        "Finansal Tuzak": ["kredi", "kazan", "hedi", "00", "tl", "₺", "lütia", "calma"]
    }
    
    for kategori, parcalar in tehditler.items():
        if any(p in t for p in parcalar):
            risk += 35
            bulgular.append(f"Tespit: {kategori} şüphesi.")
            
    return min(100, risk), bulgular

@app.route('/analiz', methods=['POST'])
def perform_analysis():
    try:
        if 'image' in request.files:
            file_bytes = request.files['image'].read()
            processed_img = goruntu_iyilestir(file_bytes)
            
            if processed_img is not None:
                # --psm 6: Metni tek bir blok olarak okur (Ekran görüntüleri için ideal)
                custom_config = r'--oem 3 --psm 6'
                input_text = pytesseract.image_to_string(processed_img, lang='tur', config=custom_config)
                
                risk, bulgular = esnek_analiz(input_text)
                return jsonify({"risk": risk, "metin": input_text, "bulgular": bulgular})
        
        return jsonify({"risk": 0, "metin": "Okunamadı", "bulgular": []}), 400
    except Exception as e:
        return jsonify({"risk": 0, "metin": f"Hata: {e}"}), 500

if __name__ == '__main__':
    # Portu 5005 yaptık
    app.run(debug=True, host='0.0.0.0', port=5005)
