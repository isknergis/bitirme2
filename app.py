import json
import re
import requests
from flask import Flask, render_template, request, jsonify
from bs4 import BeautifulSoup

app = Flask(__name__)

# --- VERİ VE TREND YÖNETİMİ ---
def sozluk_yukle():
    try:
        with open('sozluk.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"kritik_terimler": {}, "supheli_kaliplar": []}

def guncel_sikayet_trendleri():
    url = "https://www.sikayetvar.com/dolandiricilik"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        # Sitedeki canlı şikayet başlıklarını çekiyoruz
        return [b.text.lower() for b in soup.find_all('h2', class_='complaint-title')[:15]]
    except:
        return []

# --- BULUT OCR (Resim Okuma) ---
def bulut_ocr_motoru(file_bytes):
    api_url = "https://api.ocr.space/parse/image"
    payload = {
        'apikey': 'K81736670888957', # Sana e-posta ile gelen kodu buraya yapıştır
        'language': 'tur'
    }
    files = {'file': ('image.jpg', file_bytes, 'image/jpeg')}
    try:
        res = requests.post(api_url, files=files, data=payload, timeout=20)
        result = res.json()
        if result.get('ParsedResults'):
            return result['ParsedResults'][0]['ParsedText']
        return ""
    except:
        return "Bağlantı hatası: OCR servisine ulaşılamadı."

# --- ANALİZ MANTIĞI ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analiz', methods=['POST'])
def analiz():
    metin = ""
    kaynak = "Manuel Giriş"

    # 1. Veri Girişi (Resim veya Metin)
    if 'image' in request.files:
        metin = bulut_ocr_motoru(request.files['image'].read())
        kaynak = "Görüntü Analizi (Cloud OCR)"
    else:
        metin = request.json.get('text', '') if request.is_json else request.form.get('text', '')

    if not metin or "hata" in metin.lower():
        return jsonify({"risk": 0, "metin": metin or "Metin okunamadı.", "bulgular": []})

    metin_lower = metin.lower()
    sozluk = sozluk_yukle()
    trendler = guncel_sikayet_trendleri()
    
    risk_puani = 0
    bulgular = []

    # 2. Sabit Sözlük Kontrolü
    for kelime, puan in sozluk['kritik_terimler'].items():
        if kelime in metin_lower:
            risk_puani += puan
            bulgular.append(f"Sözlük Eşleşmesi: {kelime.upper()}")

    # 3. OTOMATİK DİNAMİK TREND ANALİZİ
    for trend in trendler:
        # Trend başlığındaki önemli kelimeleri (5 harf+) metinde arıyoruz
        anahtar_kelimeler = [k for k in trend.split() if len(k) > 4]
        for ok in anahtar_kelimeler:
            if ok in metin_lower:
                risk_puani += 15 # Her otomatik yakalanan trend için puan ekle
                bulgular.append(f"Otomatik Yakalanan Trend: {ok.upper()}")
                break 

    # 4. Link Kontrolü
    if re.search(r'https?://', metin_lower) or "bit.ly" in metin_lower:
        risk_puani += 40
        bulgular.append("Şüpheli Link/Bağlantı")

    return jsonify({
        "risk": min(100, risk_puani),
        "metin": metin,
        "kaynak": kaynak,
        "bulgular": list(set(bulgular)) # Tekrarları önle
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
