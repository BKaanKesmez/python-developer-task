import os
from curl_cffi import requests

#NESNE YÖNELİMLİ DÜZENLEME
class InterpolAPI:
    def __init__(self):
        self.url = os.environ.get("INTERPOL_URL", "https://ws-public.interpol.int/notices/v1/red")

    def veri_getir(self):
        print(f"{self.url} adresine TLS Parmak izi taklit edilerek bağlanılıyor...")

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
        

# KODUN ÇALIŞTIRILMA KISMI
if __name__ == "__main__":
    # Sınıfımızdan bir 'nesne' üretiyoruz
    interpol_botu = InterpolAPI()
    
    # Nesnemizin içindeki fonksiyonu çağırıyoruz
    cekilen_veri = interpol_botu.veri_getir()
    
    if cekilen_veri:
        toplam_aranan = cekilen_veri.get('total')
        print(f"Şu an kırmızı bültende toplam {toplam_aranan} kişi bulunuyor.")        
        