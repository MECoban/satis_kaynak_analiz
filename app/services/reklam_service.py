"""
Reklam Detay Servisi
Meta reklamlardan Campaign, Adset, Ad Name bilgilerini ekler
"""

import pandas as pd
import sys
import os

from app.utils.db_connection import DatabaseConnection


def enrich_with_ad_details(df_utm_details):
    """
    3. ADIM: UTM detaylarına Meta reklam bilgilerini ekle
    
    Args:
        df_utm_details: process_utm_details'den dönen DataFrame
    
    Returns:
        DataFrame: Reklam detayları eklenmiş DataFrame
    """
    
    print("\n🔍 Database'den reklam detayları alınıyor...")
    
    # DataFrame'i kopyala
    df = df_utm_details.copy()
    
    # utm_term string olarak oku
    df['utm_term'] = df['utm_term'].astype(str)
    
    # Sadece UTM VAR olanlar için reklam detayı al
    df_utm_var = df[df['durum'] == 'UTM VAR'].copy()
    
    if len(df_utm_var) == 0:
        print("⚠️  UTM bilgisi olan müşteri yok!")
        return df
    
    print(f"✅ {len(df_utm_var)} müşteri için reklam detayları alınacak")
    
    # Database bağlantısı
    db = DatabaseConnection()
    if not db.connect():
        raise Exception("❌ Veritabanına bağlanılamadı! Lütfen bağlantı bilgilerini kontrol edin.")
    
    db.create_engine()  # Engine'i oluştur
    
    # Yeni sütunlar ekle
    df['campaign_name'] = df['utm_campaign']  # Form'dan
    df['ad_name'] = df['utm_content']  # Form'dan
    df['adset_name'] = None  # Database'den gelecek
    
    success_count = 0
    fail_count = 0
    
    for idx, row in df_utm_var.iterrows():
        email = row['email']
        utm_term = str(row['utm_term']).strip()
        
        print(f"[{idx+1}/{len(df_utm_var)}] {email}... ", end='', flush=True)
        
        if not utm_term or utm_term == 'nan' or utm_term == 'None':
            print("⚠️  UTM Term boş")
            fail_count += 1
            continue
        
        # utm_term = meta_adsets.adset_id (numeric)
        query = f"""
        SELECT name as adset_name
        FROM meta_adsets
        WHERE adset_id = '{utm_term}'
        LIMIT 1
        """
        
        result = db.execute_query(query)
        
        if result and len(result) > 0:
            df.at[idx, 'adset_name'] = result[0].get('adset_name')
            print("✅")
            success_count += 1
        else:
            print("❌")
            fail_count += 1
    
    db.close()
    
    # utm_term sütununu yeniden adlandır
    df = df.rename(columns={'utm_term': 'utm_term(adset_id)'})
    
    stats = {
        'total_utm_var': len(df_utm_var),
        'success_count': success_count,
        'fail_count': fail_count
    }
    
    print(f"\n📊 {success_count} başarılı, {fail_count} başarısız")
    
    return df, stats

