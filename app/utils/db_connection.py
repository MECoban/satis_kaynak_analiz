"""
MySQL Veritabanı Bağlantı Modülü (SSH Tunnel Desteği ile)
"""

import os
import pandas as pd
import pymysql
from sqlalchemy import create_engine
from sshtunnel import SSHTunnelForwarder

# .env dosyasından environment variables'ları yükle (opsiyonel)
try:
    from dotenv import load_dotenv
    load_dotenv(override=False)
except Exception:
    pass  # .env yüklenemezse devam et (hardcoded değerler kullanılacak)


class DatabaseConnection:
    """MySQL veritabanına SSH tunnel üzerinden bağlantı sağlayan sınıf"""
    
    def __init__(self, use_ssh_tunnel=True):
        """Veritabanı bağlantı parametrelerini ayarla"""
        self.use_ssh_tunnel = use_ssh_tunnel
        self.tunnel = None
        
        # SSH bilgileri
        self.ssh_host = os.getenv('SSH_HOST')
        self.ssh_port = int(os.getenv('SSH_PORT', 22))
        self.ssh_user = os.getenv('SSH_USER')
        self.ssh_password = os.getenv('SSH_PASSWORD')
        
        # MySQL bilgileri
        self.db_user = os.getenv('DB_USER')
        self.db_password = os.getenv('DB_PASSWORD')
        self.database = os.getenv('DB_NAME')
        self.db_port = int(os.getenv('DB_PORT', 3306))
        self.db_port = int(os.getenv('DB_PORT', 3306))
        
        # Bağlantı nesneleri
        self.connection = None
        self.engine = None
        self.host = '127.0.0.1'  # SSH tunnel üzerinden localhost
        self.port = None  # SSH tunnel başlatıldığında ayarlanacak
    
    def connect(self):
        """SSH tunnel ve veritabanına bağlan"""
        try:
            # SSH Tunnel başlat
            if self.use_ssh_tunnel:
                print("🔐 SSH Tunnel açılıyor...")
                self.tunnel = SSHTunnelForwarder(
                    (self.ssh_host, self.ssh_port),
                    ssh_username=self.ssh_user,
                    ssh_password=self.ssh_password,
                    remote_bind_address=('127.0.0.1', self.db_port)
                )
                self.tunnel.start()
                self.port = self.tunnel.local_bind_port
                print(f"✓ SSH Tunnel açıldı (Local port: {self.port})")
            else:
                self.host = os.getenv('DB_HOST')
                self.port = self.db_port
            
            # MySQL bağlantısı kur
            print("🔌 MySQL'e bağlanılıyor...")
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.db_user,
                password=self.db_password,
                database=self.database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            print(f"✓ Veritabanına başarıyla bağlanıldı: {self.database}\n")
            return True
        except Exception as e:
            print(f"✗ Bağlantı hatası: {str(e)}")
            if self.tunnel:
                self.tunnel.stop()
            return False
    
    def create_engine(self):
        """SQLAlchemy engine oluştur (pandas ile kullanmak için)"""
        try:
            if not self.port:
                raise Exception("Önce connect() metodunu çağırın!")
            
            connection_string = f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.host}:{self.port}/{self.database}"
            self.engine = create_engine(connection_string)
            print(f"✓ SQLAlchemy engine oluşturuldu")
            return self.engine
        except Exception as e:
            print(f"✗ Engine oluşturma hatası: {str(e)}")
            return None
    
    def execute_query(self, query, params=None):
        """SQL sorgusu çalıştır ve sonuçları döndür"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchall()
                return result
        except Exception as e:
            print(f"✗ Sorgu çalıştırma hatası: {str(e)}")
            return None
    
    def query_to_dataframe(self, query, params=None):
        """SQL sorgusunu çalıştır ve pandas DataFrame olarak döndür"""
        try:
            if self.engine is None:
                self.create_engine()
            
            df = pd.read_sql(query, self.engine, params=params)
            print(f"✓ Sorgu başarılı: {len(df)} satır getirildi")
            return df
        except Exception as e:
            print(f"✗ DataFrame oluşturma hatası: {str(e)}")
            return None
    
    def get_table_list(self):
        """Veritabanındaki tüm tabloları listele"""
        query = "SHOW TABLES"
        result = self.execute_query(query)
        if result:
            tables = [list(row.values())[0] for row in result]
            return tables
        return []
    
    def get_table_info(self, table_name):
        """Belirli bir tablonun yapısını göster"""
        query = f"DESCRIBE {table_name}"
        return self.execute_query(query)
    
    def get_row_count(self, table_name):
        """Tablodaki satır sayısını getir"""
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        result = self.execute_query(query)
        if result:
            return result[0]['count']
        return 0
    
    def close(self):
        """Veritabanı ve SSH tunnel bağlantısını kapat"""
        if self.connection:
            self.connection.close()
            print("✓ Veritabanı bağlantısı kapatıldı")
        if self.tunnel:
            self.tunnel.stop()
            print("✓ SSH Tunnel kapatıldı")


# Test fonksiyonu
def test_connection():
    """Bağlantıyı test et"""
    db = DatabaseConnection()
    
    if db.connect():
        print("\n=== Veritabanı Bilgileri ===")
        print(f"Veritabanı: {db.database}")
        
        # Tabloları listele
        tables = db.get_table_list()
        print(f"\n✓ Toplam {len(tables)} tablo bulundu:")
        for table in tables:
            row_count = db.get_row_count(table)
            print(f"  - {table}: {row_count:,} satır")
        
        db.close()
        return True
    else:
        print("Bağlantı başarısız oldu. Lütfen .env dosyasındaki bilgileri kontrol edin.")
        return False


if __name__ == "__main__":
    test_connection()


