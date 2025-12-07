"""
Flask Routes
Ana API endpoints
"""

from flask import Blueprint, render_template, request, jsonify, send_file, current_app, redirect, url_for
import pandas as pd
import os
import uuid
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_login import login_user, logout_user, login_required, current_user

from app.models import Campaign, CampaignStore, AnalysisResult, User
from app.services.utm_service import collect_utm_data, process_utm_details
from app.services.reklam_service import enrich_with_ad_details
from app.services.analysis_service import categorize_customers, split_by_category
from app.services.export_service import create_campaign_export, export_to_csv
from app.services.validation_service import validate_analysis, create_validation_report_html

main_bp = Blueprint('main', __name__)
campaign_store = CampaignStore()


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        env_user = os.environ.get('ADMIN_USERNAME', 'admin')
        env_pass = os.environ.get('ADMIN_PASSWORD', 'admin123')
        
        if username == env_user and password == env_pass:
            user = User(id=username, username=username)
            login_user(user)
            return redirect(url_for('main.index'))
        else:
            return render_template('login.html', error="Geçersiz kullanıcı adı veya şifre")
            
    return render_template('login.html')

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))


@main_bp.route('/')
@login_required
def index():
    """Ana sayfa - Kampanya listesi"""
    campaigns = campaign_store.list_all()
    return render_template('index.html', campaigns=campaigns)


@main_bp.route('/campaign/new')
@login_required
def new_campaign():
    """Yeni kampanya oluşturma sayfası"""
    return render_template('campaign.html')


@main_bp.route('/campaign/<campaign_id>')
@login_required
def view_campaign(campaign_id):
    """Kampanya detay ve analiz sonuçları"""
    campaign = campaign_store.get(campaign_id)
    if not campaign:
        return "Kampanya bulunamadı", 404
    
    return render_template('results.html', campaign=campaign)


@main_bp.route('/campaign/<campaign_id>/edit')
@login_required
def edit_campaign(campaign_id):
    """Kampanya verilerini düzenle"""
    campaign = campaign_store.get(campaign_id)
    if not campaign:
        return "Kampanya bulunamadı", 404
    
    return render_template('edit.html', campaign=campaign)


@main_bp.route('/api/campaign/create', methods=['POST'])
@login_required
def create_campaign():
    """
    Yeni kampanya oluştur
    
    Body:
    - name: Kampanya adı
    - start_date: Başlangıç tarihi (YYYY-MM-DD)
    - end_date: Bitiş tarihi (YYYY-MM-DD)
    - file: Müşteri listesi (CSV)
    """
    
    try:
        # Form verilerini al
        name = request.form.get('name')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        # Dosyayı kontrol et
        if 'file' not in request.files:
            return jsonify({'error': 'Dosya bulunamadı'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'Dosya seçilmedi'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'Sadece CSV dosyası yüklenebilir'}), 400
        
        # Kampanya oluştur
        campaign_id = str(uuid.uuid4())[:8]
        filename = secure_filename(file.filename)
        safe_filename = f"{campaign_id}_{filename}"
        
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], safe_filename)
        file.save(upload_path)
        
        # Campaign kaydet
        campaign = Campaign(
            id=campaign_id,
            name=name,
            start_date=start_date,
            end_date=end_date,
            customer_file=safe_filename,
            created_at=datetime.now(),
            status='pending'
        )
        
        campaign_store.save(campaign)
        
        return jsonify({
            'success': True,
            'campaign_id': campaign_id,
            'message': 'Kampanya oluşturuldu'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main_bp.route('/api/campaign/<campaign_id>/analyze', methods=['POST'])
@login_required
def analyze_campaign(campaign_id):
    """
    Kampanya analizini başlat
    
    Pipeline:
    1. UTM verilerini topla (collect_utm_data)
    2. UTM detaylarını netleştir (process_utm_details)
    3. Reklam detaylarını ekle (enrich_with_ad_details)
    4. Kategorilere ayır (categorize_customers)
    5. Export dosyaları oluştur
    """
    
    try:
        campaign = campaign_store.get(campaign_id)
        if not campaign:
            return jsonify({'error': 'Kampanya bulunamadı'}), 404
        
        # Status güncelle
        campaign_store.update_status(campaign_id, 'processing')
        
        # Müşteri dosyasını oku
        customer_file = os.path.join(current_app.config['UPLOAD_FOLDER'], campaign.customer_file)
        df_customers = pd.read_csv(customer_file)
        
        # Email sütununu bul
        email_column = None
        for col in ['email', 'Email', 'EMAIL', 'MAİL ADRESİ', 'Mail']:
            if col in df_customers.columns:
                email_column = col
                break
        
        if not email_column:
            return jsonify({
                'error': 'Email sütunu bulunamadı',
                'columns': df_customers.columns.tolist()
            }), 400
        
        email_list = df_customers[email_column].dropna().unique().tolist()
        
        results = {}
        
        # STEP 1: UTM verilerini topla
        print("\n" + "="*80)
        print("🔄 STEP 1: UTM VERİLERİ TOPLANIYOR")
        print(f"📧 Email Sayısı: {len(email_list)}")
        print(f"📅 Tarih Aralığı: {campaign.start_date} - {campaign.end_date}")
        print("="*80)
        
        df_all_records, stats1 = collect_utm_data(
            email_list=email_list,
            start_date=campaign.start_date,
            end_date=campaign.end_date,
            campaign_id=campaign_id
        )
        
        print(f"✅ STEP 1 TAMAMLANDI: {len(df_all_records)} kayıt toplandı")
        results['step1'] = stats1
        
        # STEP 2: UTM detaylarını netleştir
        print("\n=== STEP 2: UTM DETAYLARI NETLEŞTİRİLİYOR ===")
        df_utm_details, stats2 = process_utm_details(df_all_records)
        
        results['step2'] = stats2
        
        # STEP 3: Reklam detaylarını ekle
        print("\n=== STEP 3: REKLAM DETAYLARI EKLENİYOR ===")
        df_reklam_detay, stats3 = enrich_with_ad_details(df_utm_details)
        
        results['step3'] = stats3
        
        # STEP 4: Kategorilere ayır
        print("\n=== STEP 4: KATEGORİLERE AYRILIYOR ===")
        df_categorized, stats4 = categorize_customers(df_reklam_detay)
        
        results['step4'] = stats4
        
        # STEP 4.5: Kalite Kontrol
        print("\n=== STEP 4.5: KALİTE KONTROL ===")
        validation_report = validate_analysis(
            input_file=customer_file,
            output_df=df_categorized,
            email_column=email_column
        )
        
        results['validation'] = validation_report
        
        # STEP 5: Export dosyaları oluştur
        print("\n=== STEP 5: DOSYALAR OLUŞTURULUYOR ===")
        output_dir = os.path.join(current_app.config['OUTPUT_FOLDER'], 'final', campaign_id)
        exported_files = create_campaign_export(df_categorized, campaign.name, output_dir)
        
        results['exported_files'] = exported_files

        # Prepare Final Stats for Frontend
        final_stats = {
            'total_emails': len(email_list),
            'match_rate': round(stats4.get('REKLAM (Meta)', {}).get('percentage', 0), 1),
            **{k: v['count'] for k, v in stats4.items()}
        }
        results['final_stats'] = final_stats
        
        # Save Results to JSON file
        results_file = os.path.join(output_dir, 'results.json')
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # Status güncelle
        campaign_store.update_status(campaign_id, 'completed')
        
        print("\n=== ANALİZ TAMAMLANDI! ===\n")
        
        return jsonify({
            'success': True,
            'campaign_id': campaign_id,
            'results': results,
            'message': 'Analiz tamamlandı'
        })
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print("\n" + "="*80)
        print("❌❌❌ HATA DETAYLARI ❌❌❌")
        print("="*80)
        print(f"Hata Mesajı: {str(e)}")
        print(f"Hata Tipi: {type(e).__name__}")
        print("\nStack Trace:")
        print(error_details)
        print("="*80 + "\n")
        
        campaign_store.update_status(campaign_id, 'error')
        return jsonify({
            'error': str(e),
            'type': type(e).__name__,
            'details': error_details
        }), 500


@main_bp.route('/api/campaign/<campaign_id>/files')
@login_required
def list_campaign_files(campaign_id):
    """Kampanya dosyalarını listele"""
    
    try:
        campaign = campaign_store.get(campaign_id)
        if not campaign:
            return jsonify({'error': 'Kampanya bulunamadı'}), 404
            
        output_dir = os.path.join(current_app.config['OUTPUT_FOLDER'], 'final', campaign_id)
        
        files = []
        validation = None
        stats = None
        
        if os.path.exists(output_dir):
            # Load results.json if exists
            results_path = os.path.join(output_dir, 'results.json')
            if os.path.exists(results_path):
                try:
                    with open(results_path, 'r', encoding='utf-8') as f:
                        results = json.load(f)
                        validation = results.get('validation')
                        stats = results.get('final_stats')
                except Exception as e:
                    print(f"Error reading results.json: {e}")

            for filename in os.listdir(output_dir):
                if filename == 'results.json': continue
                
                filepath = os.path.join(output_dir, filename)
                files.append({
                    'filename': filename,
                    'size': os.path.getsize(filepath),
                    'created': datetime.fromtimestamp(os.path.getctime(filepath)).isoformat()
                })
        
        return jsonify({
            'status': campaign.status,
            'files': files,
            'validation': validation,
            'stats': stats
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main_bp.route('/api/campaign/<campaign_id>/download/<filename>')
@login_required
def download_file(campaign_id, filename):
    """Dosya indir"""
    
    try:
        output_dir = os.path.join(current_app.config['OUTPUT_FOLDER'], 'final', campaign_id)
        filepath = os.path.join(output_dir, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'Dosya bulunamadı'}), 404
        
        return send_file(filepath, as_attachment=True)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main_bp.route('/api/campaign/<campaign_id>/preview/<filename>')
@login_required
def preview_file(campaign_id, filename):
    """Dosya önizleme (ilk 50 satır)"""
    
    try:
        output_dir = os.path.join(current_app.config['OUTPUT_FOLDER'], 'final', campaign_id)
        filepath = os.path.join(output_dir, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'Dosya bulunamadı'}), 404
        
        # Sadece CSV dosyaları için önizleme
        if not filename.endswith('.csv'):
            return jsonify({'error': 'Sadece CSV dosyaları önizlenebilir'}), 400
        
        # CSV'yi oku (ilk 50 satır)
        df = pd.read_csv(filepath, nrows=50)
        
        # NaN değerlerini None'a çevir (JSON için)
        df = df.where(pd.notna(df), None)
        
        # Toplam satır sayısı
        total_rows = len(pd.read_csv(filepath))
        
        return jsonify({
            'columns': df.columns.tolist(),
            'data': df.to_dict('records'),
            'total_rows': total_rows,
            'showing': len(df),
            'filename': filename
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main_bp.route('/api/campaign/<campaign_id>/data/<step>')
@login_required
def get_step_data(campaign_id, step):
    """
    Belirli bir adımın verilerini getir (kullanıcı müdahale için)
    
    Steps: utm_collection, utm_details, reklam_detay, final_analysis
    """
    
    try:
        output_dir = os.path.join(current_app.config['OUTPUT_FOLDER'], 'final', campaign_id)
        
        # Step'e göre dosyayı bul
        step_files = {
            'final_analysis': '_TUM_KATEGORILER_'
        }
        
        if step not in step_files:
            return jsonify({'error': 'Geçersiz step'}), 400
        
        # En son dosyayı bul
        pattern = step_files[step]
        files = [f for f in os.listdir(output_dir) if pattern in f and f.endswith('.csv')]
        
        if not files:
            return jsonify({'error': 'Dosya bulunamadı'}), 404
        
        files.sort(reverse=True)
        latest_file = files[0]
        
        # DataFrame'i oku ve JSON'a çevir
        filepath = os.path.join(output_dir, latest_file)
        df = pd.read_csv(filepath)
        
        # NaN değerlerini None'a çevir (JSON için)
        df = df.where(pd.notna(df), None)
        
        # İlk 100 kayıt (performans için)
        data = df.head(100).to_dict('records')
        
        return jsonify({
            'columns': df.columns.tolist(),
            'data': data,
            'total_rows': len(df),
            'showing': len(data)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main_bp.route('/api/campaign/<campaign_id>/update-data', methods=['POST'])
@login_required
def update_campaign_data(campaign_id):
    """
    Kampanya verilerini güncelle (kullanıcı müdahalesi)
    """
    
    try:
        data = request.get_json()
        updated_data = data.get('data', [])
        modified_count = data.get('modified_count', 0)
        
        if not updated_data:
            return jsonify({'error': 'Veri bulunamadı'}), 400
        
        # DataFrame'e çevir ve kaydet
        df = pd.DataFrame(updated_data)
        
        # Yeni dosya olarak kaydet (orijinali korumak için)
        output_dir = os.path.join(current_app.config['OUTPUT_FOLDER'], 'final', campaign_id)
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"EDITED_TUM_KATEGORILER_{timestamp}.csv"
        filepath = os.path.join(output_dir, filename)
        
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        return jsonify({
            'success': True,
            'message': f'{modified_count} değişiklik kaydedildi',
            'filename': filename
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
