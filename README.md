# 💪 Fitalyze – Kişisel Vücut Analizi ve Diyet Asistanı

*Kullanıcı profili yönetimi, Google’ın Gemini AI’si ile vücut kompozisyonu analizi, diyet planı oluşturma ve Google Takvim entegrasyonu sunan Flask tabanlı bir backend.*

---

## 🚀 Özellikler

- 📸 Fotoğraftan vücut yağ oranı tespiti (Gemini AI)  
- 📏 Kullanıcıdan alınan boy, kilo, bel, kalça vb. ölçümlerle hesaplama  
- 📊 BMI (Vücut Kitle İndeksi) ve BKO (Bel-Kalça Oranı)  
- 🏋️ 7 günlük egzersiz planı önerisi  
- 🍽️ 7 günlük diyet listesi önerisi  
- 📄 Sonuçları PDF olarak dışa aktarma  
- 💳 Abonelik popup bileşeni (Basic / Pro / Premium)  
- 📅 Haftalık kontrol randevusu için Google Takvim entegrasyonu (opsiyonel)

---

## 🛠️ Kullanılan Teknolojiler

**Frontend (React)**  
- React.js  
- Context API  
- html2canvas + jsPDF  
- CSS Modülleri  
- Bileşenler: FormPanel, Results, WeeklyPlan, BmiLevelBar, BkoLevelBar, BodyFatLevelBar, SubscriptionPopup  

**Backend (Flask)**  
- Flask  
- Flask-CORS, Flask-Session  
- Gemini API (Google Generative AI – gemini-1.5-flash)  
- Google Calendar API (opsiyonel)  
- JSON dosyaları ile kullanıcı bazlı veri saklama  

---

## 🔧 Kurulum

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

`.env` dosyasına ekleyin:
```
FLASK_APP=app.py
FLASK_ENV=development
FLASK_RUN_PORT=5000
FLASK_SECRET_KEY=FLASK_SECRET_ANAHTARINIZ

GEMINI_API_KEY=GEMINI_API_ANAHTARINIZ

GOOGLE_CLIENT_CONFIG_JSON='OAUTH_SECRET_DOSYASI_TAM_KONUMU(PATH)'
GOOGLE_CALENDAR_SCOPES='https://www.googleapis.com/auth/calendar'
GOOGLE_REDIRECT_URI='http://localhost:5000/oauth2callback'

USER_DATA_FOLDER=user_data


```

---

## 📌 API Endpointleri

| Yöntem | URL                                           | Açıklama                                    |
|--------|-----------------------------------------------|---------------------------------------------|
| POST   | `/profile/<user_id>`                          | Kullanıcı profilini oluşturur/günceller    |
| POST   | `/analyze-photo/<user_id>`                    | Fotoğrafla analiz ve plan oluşturur         |
| GET    | `/profile/<user_id>`                          | Kullanıcı profili getirir                   |
| POST   | `/generate-diet-plan/<user_id>`               | Gemini ile diyet planı üretir               |
| POST   | `/profile/<user_id>/schedule-checkup`         | Haftalık kontrol için takvim oluşturur      |
| POST   | `/track-progress/<user_id>`                   | Ağırlık ve ölçüm geçmişi takibi yapar       |


---

## 📌 Çalıştırmak İçin

### Back-end
Proje dizinine gelerek:

```bash
python app.py
```

### Front-end
Proje Dizinine Gelerek:

```bash
cd frontend
npm install
npm start
```

---

## 📑 Dosya & Mantık Özeti

Aşağıdaki Python modüllerinin sorumlulukları:

- **`backend/app.py`**  
  - Flask uygulamasını başlatır, CORS ve session yapılandırmasını yapar.  
  - Kullanıcı profilleri için JSON dosyaları yönetimi.  
  - Google OAuth2 akışını (`/authorize-google-calendar`, `/oauth2callback`, `/auth_status`) ve API uç noktalarını (`/profile`, `/analyze-photo`, `/generate-diet-plan`, `/schedule-checkup`, `/track-progress`, `/test-gemini`) tanımlar.  

- **`backend/utils/calculations.py`**  
  - `calculate_bmi`, `calculate_whr`, `calculate_body_fat_navy`, `calculate_all_metrics` fonksiyonlarıyla sağlık metriklerini hesaplar.  

- **`backend/gemini_integration/fat_analyzer.py`**  
  - BMI, BKO hesaplama ve Gemini AI ile vücut yağ analizi, egzersiz ve diyet önerisi üretir.  

- **`backend/gemini_integration/meal_planner.py`**  
  - Gemini için diyet planı oluşturma stub'u; gerçek API entegrasyonu burada yapılmalı.  

- **`backend/google_calendar_service.py`**  
  - Google OAuth2 kimlik doğrulama akışını ve Calendar API etkileşimlerini yönetir.  

---
