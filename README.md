# 📊 Satış Kaynak Analizi

Satışlarınızın hangi kaynaklardan geldiğini analiz eden profesyonel web uygulaması.

## 🚀 Özellikler

- ✅ Meta ve organik kaynak analizi
- ✅ UTM parametreleri ile detaylı takip
- ✅ Otomatik reklam detayları çekme
- ✅ Excel ve CSV export
- ✅ Kalite kontrol raporları
- ✅ Modern ve temiz arayüz

## 🐳 Docker ile Kurulum

### 1. Gereksinimler
- Docker
- Docker Compose

### 2. Kurulum Adımları

```bash
# 1. Projeyi klonlayın
git clone <repository-url>
cd mezuniyet_reklam_analiz

# 2. .env dosyası oluşturun
cp .env.example .env

# 3. .env dosyasını düzenleyin
nano .env
# SSH ve Database bilgilerini girin

# 4. Docker Compose ile başlatın
docker-compose up -d

# 5. Logları kontrol edin
docker-compose logs -f
```

### 3. Erişim

Uygulama çalıştığında:
- **URL:** `http://localhost:5000`
- **Durum kontrol:** `docker-compose ps`

### 4. Yönetim Komutları

```bash
# Uygulamayı başlat
docker-compose up -d

# Uygulamayı durdur
docker-compose down

# Logları izle
docker-compose logs -f web

# Container içine gir
docker-compose exec web bash

# Yeniden build et
docker-compose up -d --build

# Tüm verileri sil ve yeniden başlat
docker-compose down -v
docker-compose up -d --build
```

## 💻 Manuel Kurulum (Geliştirme)

```bash
# 1. Virtual environment oluştur
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# veya
.venv\Scripts\activate  # Windows

# 2. Bağımlılıkları yükle
pip install -r requirements.txt

# 3. .env dosyasını oluştur
cp .env.example .env
# Gerekli bilgileri girin

# 4. Uygulamayı başlat
python run.py
```

## 📁 Proje Yapısı

```
mezuniyet_reklam_analiz/
├── app/                    # Flask uygulaması
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   └── services/          # İş mantığı servisleri
│       ├── utm_service.py
│       ├── reklam_service.py
│       ├── analysis_service.py
│       ├── export_service.py
│       └── validation_service.py
├── templates/             # HTML şablonları
├── static/               # CSS, JS, resimler
├── src/                  # Veritabanı bağlantı modülleri
├── data/                 # Veri dosyaları
│   ├── input/
│   ├── uploads/
│   ├── output/
│   └── campaigns/
├── Dockerfile            # Docker image tanımı
├── docker-compose.yml    # Docker Compose konfigürasyonu
├── requirements.txt      # Python bağımlılıkları
└── run.py               # Uygulama başlatıcı

```

## 🔧 Konfigürasyon

### Environment Variables (.env)

| Değişken | Açıklama | Varsayılan |
|----------|----------|-----------|
| `SECRET_KEY` | Flask secret key | - |
| `DEBUG` | Debug modu | `False` |
| `PORT` | Port numarası | `5000` |
| `SSH_HOST` | SSH sunucu adresi | - |
| `SSH_PORT` | SSH port | `22` |
| `SSH_USER` | SSH kullanıcı adı | - |
| `SSH_PASSWORD` | SSH şifresi | - |
| `DB_USER` | Database kullanıcı adı | - |
| `DB_PASSWORD` | Database şifresi | - |
| `DB_NAME` | Database adı | - |
| `DB_PORT` | Database port | `3306` |

## 📝 Kullanım

1. **Yeni Kampanya Oluştur**
   - Kampanya adı girin
   - Tarih aralığı seçin
   - Müşteri listesini yükleyin (CSV)

2. **Analizi Başlat**
   - Sistem otomatik olarak:
     - UTM bilgilerini toplar
     - Reklam detaylarını çeker
     - Kategorilere ayırır
     - Kalite kontrolü yapar

3. **Sonuçları İncele**
   - CSV ve Excel dosyalarını indirin
   - Kalite kontrol raporunu inceleyin
   - Gerekirse verileri düzenleyin

## 🛡️ Güvenlik

- ⚠️ `.env` dosyasını asla Git'e eklemeyin
- 🔐 Production'da güçlü `SECRET_KEY` kullanın
- 🔒 SSH ve Database şifrelerini güvenli tutun
- 🚫 Debug modunu production'da kapatın

## 📊 Çıktı Dosyaları

### ANALIZ.csv
Tüm müşterilerin birleştirilmiş analizi

### ANALIZ.xlsx
Multi-sheet Excel dosyası:
- **TÜM VERİ**: Tüm kayıtlar
- **REKLAM (Meta)**: Meta reklamlarından gelenler
- **ORGANİK**: Organik kaynaklardan gelenler
- **BOŞ**: Kayıt açmış ama UTM bilgisi eksik
- **KAYIT YOK**: Hiç form doldurmamış

## 🐛 Sorun Giderme

### Container başlamıyor
```bash
docker-compose logs web
```

### Veritabanına bağlanamıyor
- SSH bilgilerini kontrol edin
- Database şifresini kontrol edin
- Sunucu erişilebilir mi kontrol edin

### Port zaten kullanımda
```bash
# Portu değiştirin (docker-compose.yml)
ports:
  - "8080:5000"  # 5000 yerine 8080 kullan
```

## 📞 Destek

Sorularınız için iletişime geçin.

## 📄 Lisans

Tüm hakları saklıdır © 2025
