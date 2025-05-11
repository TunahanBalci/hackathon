# backend/gemini_integration/fat_analyzer.py
import os
import google.generativeai as genai
import base64
import json
import re
from dotenv import load_dotenv

load_dotenv()

def hesapla_bmi(boy_cm, kilo_kg):
    boy_m = boy_cm / 100
    return round(kilo_kg / (boy_m ** 2), 1)

def yorumla_bmi(bmi):
    if bmi < 18.5:
        return "Zayıf"
    elif bmi < 25:
        return "Normal"
    elif bmi < 30:
        return "Fazla kilolu"
    else:
        return "Obez"

def bel_kalca_orani(bel, kalca):
    return round(bel / kalca, 2)

def yorumla_bko(orani, cinsiyet):
    if cinsiyet.lower() == "kadın":
        return "Elma tipi (riskli)" if orani > 0.85 else "Armut tipi (daha az riskli)"
    else:
        return "Elma tipi (riskli)" if orani > 1.0 else "Armut tipi (daha az riskli)"

def normalize_yag_orani(yag_str):
    if not yag_str:
        return None
    match = re.findall(r"%?(\d+(?:\.\d+)?)", yag_str)
    if len(match) == 1:
        return f"%{match[0]}"
    elif len(match) >= 2:
        ortalama = round((float(match[0]) + float(match[1])) / 2, 1)
        return f"%{ortalama}"
    else:
        return None

def extract_json(text):
    match = re.search(r'\{[\s\S]*\}', text)
    return match.group() if match else None

def analyze_fat_percentage_with_gemini(user_data, image_path=None):
    """
    Analyze body fat percentage and generate recommendations using Gemini AI.
    
    Args:
        user_data (dict): Dictionary containing user measurements and information
        image_path (str, optional): Path to the user's body photo
    
    Returns:
        dict: Analysis results including BMI, BKO, fat percentage, and recommendations
    """
    # Configure Gemini API
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    
    genai.configure(api_key=api_key)
    try:
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    except Exception as e:
        print(f"Error initializing Gemini model: {str(e)}")
        raise ValueError(f"Failed to initialize Gemini model: {str(e)}")
    
    # Extract user data
    boy = user_data.get('measurements', {}).get('height_cm')
    kilo = user_data.get('measurements', {}).get('weight_kg')
    yas = user_data.get('age')
    cinsiyet = user_data.get('gender')
    bel = user_data.get('measurements', {}).get('waist_cm')
    kalca = user_data.get('measurements', {}).get('hip_cm')
    
    if not all([boy, kilo, yas, cinsiyet, bel, kalca]):
        missing_fields = []
        if not boy: missing_fields.append('height_cm')
        if not kilo: missing_fields.append('weight_kg')
        if not yas: missing_fields.append('age')
        if not cinsiyet: missing_fields.append('gender')
        if not bel: missing_fields.append('waist_cm')
        if not kalca: missing_fields.append('hip_cm')
        raise ValueError(f"Missing required user measurements: {', '.join(missing_fields)}")
    
    # Calculate basic metrics
    bmi = hesapla_bmi(boy, kilo)
    bmi_yorum = yorumla_bmi(bmi)
    bko = bel_kalca_orani(bel, kalca)
    bko_yorum = yorumla_bko(bko, cinsiyet)
    
    # Prepare prompts
    prompt_text = (
        f"Aşağıdaki kişi bilgilerini ve görselini değerlendir. "
        f"Sadece aşağıdaki JSON formatında cevap ver:\n\n"
        f"- Boy: {boy} cm\n"
        f"- Kilo: {kilo} kg\n"
        f"- Yaş: {yas}\n"
        f"- Cinsiyet: {cinsiyet}\n"
        f"- Bel çevresi: {bel} cm\n"
        f"- Kalça çevresi: {kalca} cm\n"
        f"- Vücut Kitle Endeksi (BMI): {bmi} → {bmi_yorum}\n"
        f"- Bel/Kalça Oranı (BKO): {bko} → {bko_yorum}\n\n"
        "JSON formatı:\n"
        "{\n"
        '  "bmi": <float>,\n'
        '  "bmi_yorum": "<string>",\n'
        '  "bko": <float>,\n'
        '  "bko_yorum": "<string>",\n'
        '  "yag_orani": "<string, % cinsinden>",\n'
        '  "analiz": "<string, 3 cümlelik kısa değerlendirme>"\n'
        "}\n\n"
        "Yalnızca bu JSON'u döndür. Başka açıklama, format, etiket veya markdown (```json gibi) kullanma. "
        "Lütfen yağ oranını yalnızca % cinsinden tek bir sayı olarak döndür (örneğin \"%17.5\"). Diyetisyen(motive edici ve destekleyici) gibi önerilerde bulun."
    )
    
    egzersiz_prompt = (
        f"Aşağıdaki kişinin bilgilerine göre, kişiye özel 7 günlük egzersiz programı oluştur:\n"
        f"- Yaş: {yas}\n"
        f"- Cinsiyet: {cinsiyet}\n"
        f"- BMI: {bmi} ({bmi_yorum})\n"
        f"- BKO: {bko} ({bko_yorum})\n"
        "Program; kardiyo, esneme ve ağırlık çalışmaları içersin. Cinsiyete uygun egzersiz türleri öner.\n"
        "Çıktıyı şu şekilde JSON formatında ver:\n"
        "{\n  \"gunler\": [\n"
        "    {\"gun\": \"Pazartesi\", \"egzersiz\": \"<string>\"},\n"
        "    ...\n"
        "  ]\n}"
    )
    
    diyet_prompt = (
        "Amaç: Kilo vermek ve sağlıklı yaşam tarzı geliştirmektir. Liste; protein, lif, karbonhidrat ve sağlıklı yağ açısından dengeli olmalıdır.\n"
        "Her gün için şu alanları mutlaka ver:\n"
        "- Kahvaltı\n"
        "- Öğle Yemeği\n"
        "- Akşam Yemeği\n"
        "- Ara Öğün\n"
        "- Günlük toplam kalori (kcal) değeri. Bu alanın adı **toplam_kalori** olmalı ve bir sayı içermelidir. Örneğin: 1800.0\n\n"
        "Yalnızca aşağıdaki JSON formatında cevap ver:\n"
        "{\n"
        "  \"gunler\": [\n"
        "    {\n"
        "      \"gun\": \"Pazartesi\",\n"
        "      \"kahvalti\": \"<string>\",\n"
        "      \"ogle\": \"<string>\",\n"
        "      \"aksam\": \"<string>\",\n"
        "      \"ara_ogun\": \"<string>\",\n"
        "      \"toplam_kalori\": <float>\n"
        "    },\n"
        "    ...\n"
        "  ]\n"
        "}\n"
        "Sadece geçerli bir JSON döndür. `toplam_kalori` her gün için zorunludur ve 1500–2200 kcal arasında olmalıdır."
    )
    
    # Process image if provided
    image_data = None
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()
            image_data = {
                "inline_data": {
                    "mime_type": "image/webp",
                    "data": base64.b64encode(image_bytes).decode("utf-8")
                }
            }
    
    # Generate health analysis
    contents = [{"text": prompt_text}]
    if image_data:
        contents.append(image_data)
    
    response = model.generate_content(
        contents=contents,
        generation_config={"temperature": 0.3}
    )
    
    raw_json = extract_json(response.text.strip())
    try:
        gemini_json = json.loads(raw_json)
    except Exception as e:
        print("JSON ayrıştırma hatası:", e)
        gemini_json = {}
    
    # Generate exercise program
    exercise_response = model.generate_content(
        contents=[{"text": egzersiz_prompt}],
        generation_config={"temperature": 0.3}
    )
    
    exercise_raw = extract_json(exercise_response.text.strip())
    try:
        egzersiz_programi = json.loads(exercise_raw).get("gunler", [])
    except Exception as e:
        egzersiz_programi = []
    
    # Generate diet plan
    diyet_response = model.generate_content(
        contents=[{"text": diyet_prompt}],
        generation_config={"temperature": 0.3}
    )
    
    diyet_raw = extract_json(diyet_response.text.strip())
    try:
        diyet_listesi = json.loads(diyet_raw).get("gunler", [])
    except Exception as e:
        print("Diyet listesi ayrıştırılamadı:", e)
        diyet_listesi = []
    
    # Prepare final result
    sonuc_json = {
        "adSoyad": user_data.get('fullName', ''),
        "imageUrl": user_data.get('avatarUrl', ''),
        "boy": boy,
        "kilo": kilo,
        "yas": yas,
        "cinsiyet": cinsiyet,
        "bel": bel,
        "kalca": kalca,
        "bmi": gemini_json.get("bmi", bmi),
        "bmi_yorum": gemini_json.get("bmi_yorum", bmi_yorum),
        "bko": gemini_json.get("bko", bko),
        "bko_yorum": gemini_json.get("bko_yorum", bko_yorum),
        "yag_orani": normalize_yag_orani(gemini_json.get("yag_orani")),
        "analiz": gemini_json.get("analiz"),
        "egzersiz_programi": egzersiz_programi,
        "diyet_listesi": diyet_listesi
    }
    
    return sonuc_json