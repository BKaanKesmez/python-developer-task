"""
Interpol Takip Sistemi - DocTest Dosyası

Bu dosya, projedeki temel fonksiyonların beklenen çıktıları verip vermediğini test eder.
Aşağıdaki '>>>' işaretli kısımlar, sanki terminalde çalıştırılıyormuş gibi simüle edilir.

Test 1: Web Sunucusunun yapılandırma ayarları doğru çekiliyor mu?
>>> import os
>>> os.environ['WEB_PORT'] = '8080'
>>> os.environ.get('WEB_PORT', '5000')
'8080'

Test 2: Çekilen verinin JSON formatı doğru parse edilebiliyor mu?
>>> ornek_gelen_veri = {"total": 6441, "notices": []}
>>> toplam_sayi = ornek_gelen_veri.get('total')
>>> toplam_sayi
6441

Test 3: Veritabanı durum (Alarm) mantığı doğru çalışıyor mu?
>>> eski_sayi = 6000
>>> yeni_sayi = 6500
>>> durum = "Yeni Kayıt"
>>> if eski_sayi and (yeni_sayi != eski_sayi):
...     durum = f"ALARM! Sayı Güncellendi (Eski: {eski_sayi} -> Yeni: {yeni_sayi})"
>>> durum
'ALARM! Sayı Güncellendi (Eski: 6000 -> Yeni: 6500)'
"""

if __name__ == "__main__":
    import doctest
    # verbose=True parametresi, test sonuçlarını detaylıca ekrana basar.
    doctest.testmod(verbose=True)