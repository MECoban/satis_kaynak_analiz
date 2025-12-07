"""
Veri Doğrulama ve Kalite Kontrol Servisi
Analiz sonrası otomatik kontroller yapar
"""

import pandas as pd
from typing import Dict, List, Tuple


def validate_analysis(input_file: str, output_df: pd.DataFrame, email_column: str = 'MAİL ADRESİ') -> Dict:
    """
    Analiz sonucunu doğrula ve rapor oluştur
    
    Args:
        input_file: Yüklenen müşteri dosyası
        output_df: Analiz sonucu DataFrame
        email_column: Input dosyasındaki email sütunu adı
    
    Returns:
        Dict: Doğrulama raporu
    """
    
    print("\n" + "="*80)
    print("🔍 KALİTE KONTROL BAŞLATILIYOR")
    print("="*80)
    
    report = {
        'status': 'success',
        'errors': [],
        'warnings': [],
        'stats': {},
        'checks': {}
    }
    
    try:
        # Input dosyasını oku
        df_input = pd.read_csv(input_file)
        
        # Email sütununu bul
        if email_column not in df_input.columns:
            # Alternatif email sütunları dene
            for col in ['email', 'Email', 'EMAIL', 'Mail', 'mail']:
                if col in df_input.columns:
                    email_column = col
                    break
        
        input_emails = df_input[email_column].dropna().unique()
        output_emails = output_df['email'].unique()
        
        # 1. Email Sayısı Kontrolü
        print("\n📊 1. Email Sayısı Kontrolü")
        report['stats']['input_total_rows'] = len(df_input)
        report['stats']['input_unique_emails'] = len(input_emails)
        report['stats']['output_emails'] = len(output_emails)
        report['stats']['duplicates'] = len(df_input) - len(input_emails)
        
        print(f"   ✓ Input toplam satır: {len(df_input)}")
        print(f"   ✓ Input unique email: {len(input_emails)}")
        print(f"   ✓ Output email: {len(output_emails)}")
        print(f"   ✓ Duplicate email: {report['stats']['duplicates']}")
        
        report['checks']['email_count'] = 'PASSED'
        
        # 2. Eksik Email Kontrolü
        print("\n📧 2. Eksik Email Kontrolü")
        missing_emails = set(input_emails) - set(output_emails)
        extra_emails = set(output_emails) - set(input_emails)
        
        if len(missing_emails) > 0:
            report['errors'].append(f"{len(missing_emails)} email output'ta eksik!")
            report['checks']['missing_emails'] = 'FAILED'
            print(f"   ❌ {len(missing_emails)} email eksik!")
            for email in list(missing_emails)[:5]:
                print(f"      • {email}")
                report['errors'].append(f"Eksik email: {email}")
        else:
            report['checks']['missing_emails'] = 'PASSED'
            print(f"   ✅ Tüm emailler mevcut (0 eksik)")
        
        if len(extra_emails) > 0:
            report['warnings'].append(f"{len(extra_emails)} fazla email bulundu")
            print(f"   ⚠️  {len(extra_emails)} fazla email var (input'ta yok)")
        
        # 3. Kategori Dağılımı Kontrolü
        print("\n📊 3. Kategori Dağılımı")
        category_dist = output_df['kategori'].value_counts()
        report['stats']['categories'] = category_dist.to_dict()
        
        for category, count in category_dist.items():
            percentage = (count / len(output_df)) * 100
            print(f"   • {category}: {count} ({percentage:.1f}%)")
            report['checks'][f'category_{category}'] = count
        
        # 4. UTM Veri Kalitesi Kontrolü
        print("\n📈 4. UTM Veri Kalitesi")
        utm_var = output_df[output_df['durum'] == 'UTM VAR']
        
        if len(utm_var) > 0:
            # utm_source dolu mu?
            null_source = utm_var['utm_source'].isna().sum()
            null_campaign = utm_var['utm_campaign'].isna().sum()
            
            report['stats']['utm_null_source'] = null_source
            report['stats']['utm_null_campaign'] = null_campaign
            
            if null_source > 0:
                report['warnings'].append(f"{null_source} 'UTM VAR' kaydında utm_source boş")
                print(f"   ⚠️  {null_source} kayıtta utm_source boş")
            else:
                print(f"   ✅ Tüm 'UTM VAR' kayıtlarında utm_source dolu")
            
            if null_campaign > 0:
                report['warnings'].append(f"{null_campaign} 'UTM VAR' kaydında utm_campaign boş")
                print(f"   ⚠️  {null_campaign} kayıtta utm_campaign boş")
            else:
                print(f"   ✅ Tüm 'UTM VAR' kayıtlarında utm_campaign dolu")
        
        # 5. Reklam Detay Kontrolü (Meta reklamları için)
        print("\n🎯 5. Reklam Detay Kontrolü")
        meta_ads = output_df[output_df['kategori'] == 'REKLAM (Meta)']
        
        if len(meta_ads) > 0:
            null_adset = meta_ads['adset_name'].isna().sum()
            report['stats']['meta_null_adset'] = null_adset
            
            if null_adset > 0:
                percentage = (null_adset / len(meta_ads)) * 100
                report['warnings'].append(f"{null_adset} Meta reklamında adset_name bulunamadı")
                print(f"   ⚠️  {null_adset}/{len(meta_ads)} kayıtta adset_name bulunamadı ({percentage:.1f}%)")
            else:
                print(f"   ✅ Tüm Meta reklamlarında adset_name bulundu")
        
        # 6. Tarih Aralığı Kontrolü
        print("\n📅 6. Tarih Aralığı Kontrolü")
        valid_dates = output_df[output_df['created_at'].notna()]
        
        if len(valid_dates) > 0:
            min_date = pd.to_datetime(valid_dates['created_at']).min()
            max_date = pd.to_datetime(valid_dates['created_at']).max()
            report['stats']['date_range'] = f"{min_date.date()} - {max_date.date()}"
            print(f"   ✓ Tarih aralığı: {min_date.date()} - {max_date.date()}")
        
        # Final Durum
        print("\n" + "="*80)
        if len(report['errors']) == 0:
            report['status'] = 'success'
            print("✅ KALİTE KONTROL BAŞARILI - TÜM KONTROLLER GEÇTİ")
        elif len(report['errors']) > 0 and len(missing_emails) == 0:
            report['status'] = 'warning'
            print("⚠️  KALİTE KONTROL UYARI - Bazı uyarılar var ama kritik hata yok")
        else:
            report['status'] = 'failed'
            print("❌ KALİTE KONTROL BAŞARISIZ - Kritik hatalar var!")
        
        print("="*80 + "\n")
        
        # Özet rapor
        print("📋 ÖZET RAPOR:")
        print(f"   • Durum: {report['status'].upper()}")
        print(f"   • Hata sayısı: {len(report['errors'])}")
        print(f"   • Uyarı sayısı: {len(report['warnings'])}")
        print(f"   • Input email: {len(input_emails)}")
        print(f"   • Output email: {len(output_emails)}")
        print(f"   • Eşleşme oranı: {(len(output_emails)/len(input_emails)*100):.2f}%")
        print()
        
    except Exception as e:
        print(f"\n❌ HATA: {e}\n")
        report['status'] = 'error'
        report['errors'].append(str(e))
    
    return report


def create_validation_report_html(report: Dict, campaign_name: str) -> str:
    """
    Doğrulama raporunu HTML formatında oluştur
    """
    
    status_color = {
        'success': 'success',
        'warning': 'warning',
        'failed': 'danger',
        'error': 'danger'
    }
    
    status_icon = {
        'success': '✅',
        'warning': '⚠️',
        'failed': '❌',
        'error': '❌'
    }
    
    color = status_color.get(report['status'], 'secondary')
    icon = status_icon.get(report['status'], '❓')
    
    html = f"""
    <div class="alert alert-{color}">
        <h5>{icon} Kalite Kontrol: {report['status'].upper()}</h5>
        <hr>
        <p><strong>Kampanya:</strong> {campaign_name}</p>
        <p><strong>Input Email:</strong> {report['stats'].get('input_unique_emails', 0)}</p>
        <p><strong>Output Email:</strong> {report['stats'].get('output_emails', 0)}</p>
        <p><strong>Eşleşme:</strong> %{(report['stats'].get('output_emails', 0) / max(report['stats'].get('input_unique_emails', 1), 1) * 100):.2f}</p>
    """
    
    if report['errors']:
        html += "<hr><h6>❌ Hatalar:</h6><ul>"
        for error in report['errors'][:5]:
            html += f"<li>{error}</li>"
        html += "</ul>"
    
    if report['warnings']:
        html += "<hr><h6>⚠️ Uyarılar:</h6><ul>"
        for warning in report['warnings'][:5]:
            html += f"<li>{warning}</li>"
        html += "</ul>"
    
    html += "</div>"
    
    return html

