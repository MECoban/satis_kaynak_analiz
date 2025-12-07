"""
UTM Analiz Servisi
check_email_forms.py ve utm_details.py mantığını kullanarak modüler analiz fonksiyonları
"""

import pandas as pd
import os
from datetime import datetime
import sys

# Database bağlantısı
from app.utils.db_connection import DatabaseConnection


def collect_utm_data(email_list, start_date, end_date, campaign_id):
    """
    1. ADIM: Email listesi için veritabanından UTM bilgilerini topla
    
    Args:
        email_list: Liste veya email adresleri
        start_date: Başlangıç tarihi (YYYY-MM-DD)
        end_date: Bitiş tarihi (YYYY-MM-DD)
        campaign_id: Kampanya ID (dosya adı için)
    
    Returns:
        DataFrame: Tüm form kayıtları
    """
    
    print(f"📂 {len(email_list)} email için UTM bilgileri toplanıyor...")
    print(f"📅 Tarih Aralığı: {start_date} - {end_date}")
    
    # Database bağlantısı
    db = DatabaseConnection()
    if not db.connect():
        raise Exception("❌ Veritabanına bağlanılamadı! Lütfen bağlantı bilgilerini kontrol edin.")
    
    db.create_engine()  # Engine'i oluştur
    
    all_results = []
    
    for idx, email in enumerate(email_list, 1):
        email = str(email).strip()
        
        print(f"[{idx}/{len(email_list)}] {email}... ", end='', flush=True)
        
        # Bu email için form kayıtlarını getir
        query = f"""
        SELECT 
            email,
            created_at,
            utm_source,
            utm_medium,
            utm_campaign,
            utm_content,
            utm_term
        FROM iframe_form_submissions
        WHERE LOWER(TRIM(email)) = LOWER(TRIM('{email}'))
          AND created_at >= '{start_date} 00:00:00'
          AND created_at <= '{end_date} 23:59:59'
        ORDER BY created_at ASC
        """
        
        df_forms = db.query_to_dataframe(query)
        
        if df_forms is None or df_forms.empty:
            print("❌ Kayıt yok")
            # Kayıt yok da listeye ekle
            all_results.append({
                'email': email,
                'kayit_sayisi': 0,
                'durum': 'KAYIT YOK',
                'created_at': None,
                'utm_source': None,
                'utm_medium': None,
                'utm_campaign': None,
                'utm_content': None,
                'utm_term': None
            })
        else:
            # Her kaydı ekle
            for _, row in df_forms.iterrows():
                # UTM durumu kontrol et
                has_utm = False
                utm_fields = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term']
                
                for field in utm_fields:
                    val = row[field]
                    if pd.notna(val) and str(val).strip() != '' and str(val).strip().lower() != 'nan':
                        has_utm = True
                        break
                
                all_results.append({
                    'email': email,
                    'kayit_sayisi': len(df_forms),
                    'durum': 'UTM VAR' if has_utm else 'BOŞ',
                    'created_at': row['created_at'],
                    'utm_source': row['utm_source'],
                    'utm_medium': row['utm_medium'],
                    'utm_campaign': row['utm_campaign'],
                    'utm_content': row['utm_content'],
                    'utm_term': row['utm_term']
                })
            
            print(f"✅ {len(df_forms)} kayıt")
    
    db.close()
    
    # DataFrame oluştur
    df_results = pd.DataFrame(all_results)
    
    # İstatistikler
    total = len(df_results)
    kayit_yok = len(df_results[df_results['durum'] == 'KAYIT YOK'])
    utm_var = len(df_results[df_results['durum'] == 'UTM VAR'])
    bos = len(df_results[df_results['durum'] == 'BOŞ'])
    
    stats = {
        'total_records': total,
        'total_customers': len(email_list),
        'kayit_yok': kayit_yok,
        'utm_var': utm_var,
        'bos': bos
    }
    
    print(f"\n📊 ÖZET: {utm_var} UTM VAR, {bos} BOŞ, {kayit_yok} KAYIT YOK")
    
    return df_results, stats


def process_utm_details(df_all_records):
    """
    2. ADIM: Çoklu kayıtları netleştir, her email için en doğru UTM kaydını seç
    
    Args:
        df_all_records: collect_utm_data'dan dönen DataFrame
    
    Returns:
        DataFrame: Her email için tek bir kayıt
    """
    
    print("\n🔍 Her email için en doğru UTM kaydı seçiliyor...")
    
    def has_placeholder_values(row):
        """UTM alanlarında {{}} placeholder var mı"""
        utm_fields = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term']
        
        for field in utm_fields:
            val = row[field]
            if pd.notna(val):
                val_str = str(val)
                if '{{' in val_str or '}}' in val_str:
                    return True
        return False
    
    def is_valid_utm_record(row):
        """Geçerli bir UTM kaydı mı?"""
        if row['durum'] != 'UTM VAR':
            return False
        if has_placeholder_values(row):
            return False
        return True
    
    def select_best_utm_record(group_df):
        """Bir email için en doğru UTM kaydını seç"""
        
        # KAYIT YOK durumu
        if group_df['durum'].iloc[0] == 'KAYIT YOK':
            return group_df.iloc[0]
        
        # Tarihe göre sırala (en eski önce)
        group_df = group_df.sort_values('created_at').reset_index(drop=True)
        
        # İlk geçerli kaydı bul
        for idx, row in group_df.iterrows():
            if is_valid_utm_record(row):
                return row
        
        # Hiçbirinde geçerli UTM yok → BOŞ
        best_record = group_df.iloc[0].copy()
        best_record['durum'] = 'BOŞ'
        best_record['utm_source'] = None
        best_record['utm_medium'] = None
        best_record['utm_campaign'] = None
        best_record['utm_content'] = None
        best_record['utm_term'] = None
        
        return best_record
    
    # Her email için en iyi kaydı seç
    result_list = []
    for email, group in df_all_records.groupby('email'):
        best_record = select_best_utm_record(group)
        result_list.append(best_record)
    
    df_result = pd.DataFrame(result_list)
    
    # İstatistikler
    total = len(df_result)
    utm_var = len(df_result[df_result['durum'] == 'UTM VAR'])
    bos = len(df_result[df_result['durum'] == 'BOŞ'])
    kayit_yok = len(df_result[df_result['durum'] == 'KAYIT YOK'])
    
    stats = {
        'total_customers': total,
        'utm_var': utm_var,
        'bos': bos,
        'kayit_yok': kayit_yok
    }
    
    print(f"✅ {total} email netleştirildi")
    print(f"   📊 {utm_var} UTM VAR, {bos} BOŞ, {kayit_yok} KAYIT YOK")
    
    return df_result, stats

