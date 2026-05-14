import os
import json
import sqlite3
import threading
import pika
from flask import Flask, render_template

# ---------------------------------------------------------
# 1. SINIF: VERİTABANI YÖNETİCİSİ (DatabaseManager)
# Görevi: Sadece veritabanına bağlanmak, tablo kurmak, veri yazmak ve okumak.
# ---------------------------------------------------------
class DatabaseManager:
    def __init__(self, db_name='interpol.db'):
        self.db_name = db_name
        self._kurulum() # Nesne üretildiğinde tabloyu otomatik kur

    def _kurulum(self):
        # with bloğu sqlite3 bağlantısını iş bitince otomatik kapatır
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS arananlar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    toplam_sayi INTEGER,
                    zaman TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    durum TEXT
                )
            ''')
            conn.commit()

    def kaydet(self, yeni_sayi):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Son kaydı kontrol et (Alarm durumu için) [cite: 14]
            cursor.execute('SELECT toplam_sayi FROM arananlar ORDER BY id DESC LIMIT 1')
            son_kayit = cursor.fetchone()
            
            durum = "Yeni Kayıt"
            if son_kayit:
                eski_sayi = son_kayit[0]
                if yeni_sayi != eski_sayi:
                    durum = f"ALARM! Sayı Güncellendi (Eski: {eski_sayi} -> Yeni: {yeni_sayi})"
                else:
                    durum = "Değişiklik Yok"
                    
            cursor.execute('INSERT INTO arananlar (toplam_sayi, durum) VALUES (?, ?)', (yeni_sayi, durum))
            conn.commit()

    def tum_kayitlari_getir(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT toplam_sayi, zaman, durum FROM arananlar ORDER BY id DESC')
            return cursor.fetchall()

# ---------------------------------------------------------
# 2. SINIF: KUYRUK TÜKETİCİSİ (QueueConsumer)
# Görevi: Sadece RabbitMQ'yu dinlemek ve gelen veriyi veritabanı nesnesine iletmek.
# ---------------------------------------------------------
class QueueConsumer:
    def __init__(self, db_manager):
        # Bağımlılık Enjeksiyonu (Dependency Injection): Kuyruk, verileri yazmak için DB yöneticisini tanır
        self.db_manager = db_manager 
        self.host = os.environ.get("RABBITMQ_HOST", "localhost") 
        self.queue_name = os.environ.get("RABBITMQ_QUEUE", "interpol_kuyrugu") 

    def _mesaj_geldi_tetikleyicisi(self, ch, method, properties, body):
        veri = json.loads(body)
        toplam_sayi = veri.get('total')
        print(f"[x] RabbitMQ'dan Veri Yakalandı: {toplam_sayi}")
        
        # Gelen veriyi DB nesnesi üzerinden veritabanına kaydet
        self.db_manager.kaydet(toplam_sayi) 

    def dinlemeye_basla(self):
        import time
        import pika
        
        while True:
            try:
                # 1. RabbitMQ'ya bağlanmayı dene
                print(f"[*] RabbitMQ'ya bağlanılmaya çalışılıyor: {self.host}")
                connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host))
                channel = connection.channel()
                channel.queue_declare(queue=self.queue_name, durable=True)
                
                # 2. Bağlantı başarılı olursa döngü burada dinlemede kalır
                print(f"[*] BAĞLANTI BAŞARILI! Web sunucusu '{self.queue_name}' kuyruğunu dinliyor...")
                channel.basic_consume(queue=self.queue_name, on_message_callback=self._mesaj_geldi_tetikleyicisi, auto_ack=True)
                channel.start_consuming()
                
            except pika.exceptions.AMQPConnectionError:
                # RabbitMQ kapalıysa veya hazır değilse buraya düşer
                print("[-] RabbitMQ henüz uyanmadı, 3 saniye bekleniyor...")
                time.sleep(3)
            except Exception as e:
                # Diğer beklenmeyen hatalar için
                print(f"[-] Beklenmeyen Hata: {e}")
                time.sleep(3)

# ---------------------------------------------------------
# 3. SINIF: WEB SUNUCUSU (WebServer)
# Görevi: Flask arayüzünü ayağa kaldırmak ve arayüzü sunmak.
# ---------------------------------------------------------
class WebServer:
    def __init__(self, db_manager):
        self.app = Flask(__name__)
        self.db_manager = db_manager
        self.port = int(os.environ.get('WEB_PORT', 5000)) 
        
        # Flask route'unu OOP içindeki bir metoda (fonksiyona) bağlıyoruz
        self.app.add_url_rule('/', view_func=self.ana_sayfa)

    def ana_sayfa(self):
        # Veritabanı nesnesinden kayıtları çekip HTML'e gönder
        kayitlar = self.db_manager.tum_kayitlari_getir() 
        return render_template('index.html', kayitlar=kayitlar) 

    def baslat(self):
        # Arayüzü paylaşıma açıyoruz
        self.app.run(host='0.0.0.0', port=self.port, debug=False)

# ---------------------------------------------------------
# SİSTEMİN ÇALIŞTIRILMASI (Orkestrasyon)
# ---------------------------------------------------------
if __name__ == '__main__':
    # 1. Veritabanı yöneticisi nesnesini oluştur
    db = DatabaseManager()
    
    # 2. Kuyruk dinleyicisi nesnesini oluştur ve arka planda (thread) başlat
    consumer = QueueConsumer(db_manager=db)
    dinleyici_thread = threading.Thread(target=consumer.dinlemeye_basla, daemon=True )
    dinleyici_thread.start()
    
    # 3. Web sunucusu nesnesini oluştur ve başlat
    server = WebServer(db_manager=db)
    server.baslat()