import os
import json
import time 
import pika
from curl_cffi import requests

#NESNE YÖNELİMLİ DÜZENLEME
#1. Sınıf API işlemleri (Veri Çekme)
class InterpolAPI:
    def __init__(self):
        self.url = os.environ.get("INTERPOL_URL", "https://ws-public.interpol.int/notices/v1/red")

    def veri_getir(self):
        print(f"[{time.strftime('%H:%M:%S')}] Interpol API'sine bağlanılıyor...")

        try:
            # impersonate ="chrome120" parametresi ile TLS parmak izi taklit ediliyor
            response = requests.get(self.url, impersonate="chrome120")

            if response.status_code == 200:
                print("Veri başarıyla çekildi! \n")
                data = response.json()
                return data # Verriyi sadece ekrana yazdırmıyor , artık dışarıya (başka kodlara) veriyoruz.
            
            else:
                print(f"Veri çekme başarısız oldu. Durum kodu: {response.status_code}")
                return None
            
        except Exception as hata:
            print(f"Veri çekme sırasında bir hata oluştu: {hata}")
            return None    
         

class KuyrukYönetimi:
    def __init__(self):
        self.host = os.environ.get("RABBITMQ_HOST", "localhost")
        self.queue_name = os.environ.get("RABBITMQ_QUEUE", "interpol_kuyrugu")

    def mesaji_kuyruga_gonder(self, data):
        try:
            #RabbitMQ ile bağlantı kurma
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host))
            channel = connection.channel()

            #Kuyrugun var olduğundan emin oluyoruz, yoksa oluşturuyor 
            channel.queue_declare(queue=self.queue_name, durable=True)

            #Veriyi JSON formatına çevirip kuyruğa gönderiyoruz 
            channel.basic_publish(exchange='', routing_key=self.queue_name, body=json.dumps(data))
            print(f"[{time.strftime('%H:%M:%S')}] Mesaj kuyruğa gönderildi: {data}")
            connection.close()
        except Exception as hata:
            print(f"[{time.strftime('%H:%M:%S')}] Mesaj kuyruğa gönderilirken bir hata oluştu: {hata}")    

# KODUN ÇALIŞTIRILMA KISMI
if __name__ == "__main__":
    # Sınıflardan 'nesne' üretiyoruz
    api = InterpolAPI()
    kuyruk = KuyrukYönetimi()
    
    # Gorev: "Belirli bir periyot sure ile surekli cekilmesi"
    # Saniyeyi environment'tan aliyoruz, yoksa 30 saniyede bir calisacak
    periyot = int(os.environ.get("PERIYOT_SANIYESI", 30))
    print(f"--- URETICI (PRODUCER) BASLATILDI ---")
    print(f"Her {periyot} saniyede bir veri cekilip kuyruga atilacak.\n")
    
    while True:
        cekilen_veri = api.veri_getir()
        
        if cekilen_veri:
            kuyruk.mesaji_kuyruga_gonder(cekilen_veri)
            
        print(f"{periyot} saniye bekleniyor...\n")
        time.sleep(periyot) # Sistemi belirlenen sure kadar uyutuyoruz