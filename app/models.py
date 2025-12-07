"""
Campaign ve Analysis modelleri
"""
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, List
import json
import os

@dataclass
class Campaign:
    """Kampanya bilgilerini tutar"""
    id: str
    name: str
    start_date: str
    end_date: str
    customer_file: str
    created_at: datetime
    status: str = 'pending'  # pending, processing, completed, error
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'customer_file': self.customer_file,
            'created_at': self.created_at.isoformat(),
            'status': self.status
        }
    
    @classmethod
    def from_dict(cls, data):
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


@dataclass
class AnalysisResult:
    """Analiz sonuçlarını tutar"""
    campaign_id: str
    step: str  # utm_collection, utm_details, reklam_detay, final_analysis
    status: str  # running, completed, error
    output_file: Optional[str] = None
    error_message: Optional[str] = None
    stats: Optional[dict] = None
    
    def to_dict(self):
        return {
            'campaign_id': self.campaign_id,
            'step': self.step,
            'status': self.status,
            'output_file': self.output_file,
            'error_message': self.error_message,
            'stats': self.stats
        }


class CampaignStore:
    """Kampanya verilerini dosya sisteminde saklar (basit JSON store)"""
    
    def __init__(self, store_path='data/campaigns'):
        self.store_path = store_path
        os.makedirs(store_path, exist_ok=True)
    
    def save(self, campaign: Campaign):
        """Kampanya kaydet"""
        file_path = os.path.join(self.store_path, f'{campaign.id}.json')
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(campaign.to_dict(), f, ensure_ascii=False, indent=2)
    
    def get(self, campaign_id: str) -> Optional[Campaign]:
        """Kampanya getir"""
        file_path = os.path.join(self.store_path, f'{campaign_id}.json')
        if not os.path.exists(file_path):
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return Campaign.from_dict(data)
    
    def list_all(self) -> List[Campaign]:
        """Tüm kampanyaları listele"""
        campaigns = []
        for filename in os.listdir(self.store_path):
            if filename.endswith('.json'):
                campaign_id = filename[:-5]
                campaign = self.get(campaign_id)
                if campaign:
                    campaigns.append(campaign)
        
        # En yeni önce
        campaigns.sort(key=lambda x: x.created_at, reverse=True)
        return campaigns
    
    def update_status(self, campaign_id: str, status: str):
        """Kampanya durumunu güncelle"""
        campaign = self.get(campaign_id)
        if campaign:
            campaign.status = status
            self.save(campaign)

