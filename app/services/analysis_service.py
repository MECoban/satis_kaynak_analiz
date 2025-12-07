"""
Final Analiz ve Kategorilendirme Servisi
Müşterileri kategorilere ayırır: KAYIT YOK, BOŞ, REKLAM (Meta), ORGANİK
"""

import pandas as pd


def categorize_customers(df_reklam_detay):
    """
    4. ADIM: Müşterileri kategorilere ayır
    
    Args:
        df_reklam_detay: enrich_with_ad_details'den dönen DataFrame
    
    Returns:
        DataFrame: Kategori eklenmiş DataFrame ve stats dict
    """
    
    print("\n📊 Müşteriler kategorilere ayrılıyor...")
    
    df = df_reklam_detay.copy()
    
    # utm_term(adset_id) değerlerini string olarak koru
    if 'utm_term(adset_id)' in df.columns:
        df['utm_term(adset_id)'] = df['utm_term(adset_id)'].apply(
            lambda x: '\t' + str(x) if pd.notna(x) and str(x) != 'nan' else x
        )
    
    def determine_category(row):
        """Müşterinin kategorisini belirle"""
        
        # 1. KAYIT YOK
        if row['durum'] == 'KAYIT YOK':
            return 'KAYIT YOK'
        
        # 2. BOŞ
        if row['durum'] == 'BOŞ':
            return 'BOŞ'
        
        # 3. UTM VAR - Reklam mı Organik mi?
        if row['durum'] == 'UTM VAR':
            utm_source = str(row['utm_source']).lower().strip()
            
            # Meta reklamları (fb, ig)
            if utm_source in ['fb', 'ig', 'facebook', 'instagram']:
                return 'REKLAM (Meta)'
            
            # Organik kaynaklar
            else:
                return 'ORGANİK'
        
        return 'BELİRSİZ'
    
    # Kategori sütunu ekle
    df['kategori'] = df.apply(determine_category, axis=1)
    
    # Kategori en başa al
    cols = ['kategori'] + [col for col in df.columns if col != 'kategori']
    df = df[cols]
    
    # İstatistikler
    total = len(df)
    stats = {}
    
    for category in df['kategori'].unique():
        count = len(df[df['kategori'] == category])
        percentage = (count / total) * 100
        stats[category] = {
            'count': count,
            'percentage': percentage
        }
    
    print(f"✅ {total} müşteri kategorilere ayrıldı:")
    for category, data in stats.items():
        print(f"   {category}: {data['count']} kişi ({data['percentage']:.1f}%)")
    
    return df, stats


def split_by_category(df_categorized):
    """
    Kategori bazında ayrı DataFrame'ler oluştur
    
    Args:
        df_categorized: categorize_customers'dan dönen DataFrame
    
    Returns:
        dict: Her kategori için ayrı DataFrame
    """
    
    result = {}
    
    for category in df_categorized['kategori'].unique():
        result[category] = df_categorized[df_categorized['kategori'] == category].copy()
    
    return result

