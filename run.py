#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reklam Analiz Web Uygulaması - Ana Dosya
"""

from app import create_app
import os

# .env dosyasını manuel yükle (Flask'ın otomatik yüklemesi macOS'ta sorun çıkarıyor)
try:
    from dotenv import load_dotenv
    load_dotenv(override=False)
except Exception as e:
    print(f"⚠️  .env yüklenemedi (normal, devam ediliyor): {e}")

app = create_app()

if __name__ == '__main__':
    # Development mode
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'True') == 'True'
    
    print("="*80)
    print("🚀 SATIŞ KAYNAK ANALİZİ WEB UYGULAMASI")
    print("="*80)
    print(f"📍 URL: http://localhost:{port}")
    print(f"🔧 Debug: {debug}")
    print("="*80)
    print()
    
    # Flask'ın .env yüklemesini devre dışı bırak (biz yukarda yükledik)
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        load_dotenv=False
    )

