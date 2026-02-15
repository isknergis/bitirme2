from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    # Bu komut 'templates' içindeki index.html'i ekrana getirir
    return render_template('index.html')

@app.route('/analiz', methods=['POST'])
def analiz():
    data = request.json
    hiz = float(data.get('speed', 0))
    metin = data.get('text', '')
    
    # BASİT MÜHENDİSLİK MANTIĞI:
    # Hem hız yüksekse (stres) hem kelime tehlikeliyse risk artar
    tehlikeli_kelimeler = ["şifre", "acil", "iban", "onay", "hemen"]
    kelime_riski = any(k in metin.lower() for k in tehlikeli_kelimeler)
    
    risk_skoru = 0
    if hiz > 10: risk_skoru += 50
    if kelime_riski: risk_skoru += 50
    
    return jsonify({
        "risk": risk_skoru,
        "mesaj": "Analiz Tamamlandı"
    })

if __name__ == '__main__':
    app.run(debug=True)
