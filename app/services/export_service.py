"""
Export Servisi
CSV ve Excel export fonksiyonları
"""

import pandas as pd
import os
from datetime import datetime


def export_to_csv(df, filename, output_dir='data/output'):
    """
    DataFrame'i CSV'ye kaydet
    
    Args:
        df: DataFrame
        filename: Dosya adı (örn: "kampanya_analiz")
        output_dir: Çıktı dizini
    
    Returns:
        str: Oluşturulan dosya yolu
    """
    
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filepath = os.path.join(output_dir, f"{filename}_{timestamp}.csv")
    
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
    
    return filepath


def export_to_excel(df_dict, filename, output_dir='data/output'):
    """
    Birden fazla DataFrame'i Excel'e (çoklu sheet) kaydet
    
    Args:
        df_dict: Dict {sheet_name: DataFrame}
        filename: Dosya adı (örn: "kampanya_analiz")
        output_dir: Çıktı dizini
    
    Returns:
        str: Oluşturulan dosya yolu
    """
    
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filepath = os.path.join(output_dir, f"{filename}_{timestamp}.xlsx")
    
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        for sheet_name, df in df_dict.items():
            # Sheet adını temizle (Excel 31 karakter limiti)
            clean_sheet_name = sheet_name[:31].replace('/', '_').replace('\\', '_')
            df.to_excel(writer, sheet_name=clean_sheet_name, index=False)
    
    return filepath


def create_campaign_export(df_categorized, campaign_name, output_dir='data/output/final'):
    """
    Kampanya için export dosyalarını oluştur (Sadece 2 dosya)
    
    Args:
        df_categorized: Kategorilere ayrılmış DataFrame
        campaign_name: Kampanya adı
        output_dir: Çıktı dizini
    
    Returns:
        dict: Oluşturulan dosya yolları
    """
    
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_name = campaign_name.replace(' ', '_').replace('/', '_')
    
    exported_files = {}
    
    print("\n📦 Export dosyaları oluşturuluyor...")
    
    # 1. TEK CSV - Tüm kategoriler (filtrelenebilir)
    print("   📄 CSV dosyası oluşturuluyor...")
    combined_filename = f"{safe_name}_ANALIZ_{timestamp}.csv"
    combined_filepath = os.path.join(output_dir, combined_filename)
    df_categorized.to_csv(combined_filepath, index=False, encoding='utf-8-sig')
    exported_files['csv'] = combined_filepath
    print(f"   ✅ CSV: {combined_filename}")
    
    # 2. TEK EXCEL - Kategori bazında sheet'ler
    print("   📊 Excel dosyası oluşturuluyor...")
    excel_filename = f"{safe_name}_ANALIZ_{timestamp}.xlsx"
    excel_filepath = os.path.join(output_dir, excel_filename)
    
    with pd.ExcelWriter(excel_filepath, engine='openpyxl') as writer:
        # Tüm veriyi ilk sheet'e ekle
        df_categorized.to_excel(writer, sheet_name='TÜM VERİ', index=False)
        
        # Her kategori için ayrı sheet
        for category in sorted(df_categorized['kategori'].unique()):
            df_category = df_categorized[df_categorized['kategori'] == category]
            clean_sheet_name = category[:31].replace('/', '_').replace('(', '').replace(')', '')
            df_category.to_excel(writer, sheet_name=clean_sheet_name, index=False)
            print(f"      • {category}: {len(df_category)} kayıt")
    
    exported_files['excel'] = excel_filepath
    print(f"   ✅ Excel: {excel_filename}")
    
    print(f"\n✅ {len(exported_files)} dosya oluşturuldu!")
    
    return exported_files

