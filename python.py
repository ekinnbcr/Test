import time
import random
import os
import json
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

# 📂 Çerezleri saklayacağımız dosya
storage_path = "cookies.json"

# 📂 Son seçilen cihazları saklamak için bir JSON dosyası
last_selected_device_path = "last_selected_device.json"

# 📌 **Cihazlar Dengeli Olarak Seçilecek!**
mobile_devices = ['Blackberry PlayBook', 'BlackBerry Z30', 'Galaxy Note 3', 'Galaxy Note II', 'Galaxy S III', 'Galaxy S5', 
                  'Galaxy S8', 'Galaxy S9+', 'Galaxy Tab S4', 'iPad (gen 5)', 'iPad (gen 6)', 'iPad (gen 7)', 'iPad Mini', 
                  'iPad Pro 11', 'iPhone 6', 'iPhone 6 Plus', 'iPhone 7', 'iPhone 7 Plus', 'iPhone 8', 'iPhone 8 Plus', 
                  'iPhone SE', 'iPhone X', 'iPhone XR', 'iPhone 11', 'iPhone 11 Pro', 'iPhone 11 Pro Max', 'iPhone 12', 
                  'iPhone 12 Pro', 'iPhone 12 Pro Max', 'iPhone 12 Mini', 'iPhone 13', 'iPhone 13 Pro', 'iPhone 13 Pro Max', 
                  'iPhone 13 Mini', 'iPhone 14', 'iPhone 14 Plus', 'iPhone 14 Pro', 'iPhone 14 Pro Max', 'iPhone 15', 
                  'iPhone 15 Plus', 'iPhone 15 Pro', 'iPhone 15 Pro Max', 'Kindle Fire HDX', 'LG Optimus L70', 
                  'Microsoft Lumia 550', 'Microsoft Lumia 950', 'Nexus 10', 'Nexus 4', 'Nexus 5', 'Nexus 5X', 'Nexus 6', 
                  'Nexus 6P', 'Nexus 7', 'Nokia Lumia 520', 'Nokia N9', 'Pixel 2', 'Pixel 2 XL', 'Pixel 3', 'Pixel 4', 
                  'Pixel 4a (5G)', 'Pixel 5', 'Pixel 7', 'Moto G4']

# 🛠 Eğer çerez dosyası bozuksa veya yoksa, yüklemeyi atla
if os.path.exists(storage_path):
    try:
        with open(storage_path, "r") as f:
            json.load(f)  # JSON'un bozuk olup olmadığını kontrol et
    except json.JSONDecodeError:
        os.remove(storage_path)  # Bozuksa dosyayı sil


def get_random_mobile_device(p):
    """📱 Playwright’in desteklediği mobil cihazlardan rastgele bir tane seç, önceki cihazlar tekrar seçilmesin."""
    
    # 📌 Son 3 çalıştırmada seçilen cihazları kaydet
    if os.path.exists(last_selected_device_path):
        with open(last_selected_device_path, "r") as f:
            last_selected_devices = json.load(f)
    else:
        last_selected_devices = []

    # 📌 Son 3 cihaz tekrar seçilmesin
    available_devices = [device for device in mobile_devices if device not in last_selected_devices]

    # 📌 Eğer elimizde çok az seçenek kaldıysa, listeyi sıfırla (tekrar seçim yapılabilsin)
    if len(available_devices) < 3:
        available_devices = mobile_devices[:]

    # 📌 Daha önce seçilmemiş cihazlar arasından rastgele bir tane seç
    random_device_name = random.choice(available_devices)

    # 📌 Seçilen cihazı son 3 cihaza ekleyip dosyaya kaydet
    last_selected_devices.append(random_device_name)
    if len(last_selected_devices) > 3:  # Sadece son 3 taneyi tut
        last_selected_devices.pop(0)

    with open(last_selected_device_path, "w") as f:
        json.dump(last_selected_devices, f)

    print(f"📱 **Rastgele Seçilen Cihaz:** {random_device_name}")
    return random_device_name  # **Cihazın ismini döndürüyoruz!**



def setup_browser():
    """Playwright ile Stealth modda rastgele bir mobil emülasyon ile tarayıcı başlatır."""
    p = sync_playwright().start()

    # 📱 Rastgele Mobil Cihaz Seç
    random_device_name = get_random_mobile_device(p)  # **Şimdi sadece adını döndürüyor!**
    random_device = p.devices.get(random_device_name)  # **Cihaz ayarlarını burada al!**

    if not random_device:
        print(f"❌ Hata: '{random_device_name}' cihazı Playwright tarafından desteklenmiyor!")
        p.stop()
        return None, None, None, None, None

    # Çerez dosyası varsa kullan, yoksa temiz başlat
    storage_state = storage_path if os.path.exists(storage_path) else None

    browser = p.webkit.launch(headless=False)  # WebKit tarayıcıyı kullan (Safari'yi taklit etmek için)
    context = browser.new_context(**random_device, storage_state=storage_state)
    page = context.new_page()

    # 🚀 Stealth Mode etkinleştir (Bot tespiti önleme)
    stealth_sync(page)

    # 🤖 Bot tespiti önleme (Ekstra önlemler)
    page.evaluate("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    # 🚀 Google’ın botları algılamasını önleyecek ekstra önlemler
    page.evaluate("""
        Object.defineProperty(navigator, 'platform', { get: () => 'iPhone' });
        Object.defineProperty(navigator, 'maxTouchPoints', { get: () => 5 });
        Object.defineProperty(navigator, 'vendor', { get: () => 'Apple Computer, Inc.' });
        Object.defineProperty(navigator, 'connection', { get: () => ({ downlink: 10, effectiveType: "4g", rtt: 50 }) });
        Object.defineProperty(navigator, 'mediaCapabilities', { get: () => ({ smooth: true, powerEfficient: true }) });
        document.visibilityState = 'visible';
        document.hidden = false;
        window.onfocus = function() {};
        window.onblur = function() {};
    """)

    return p, browser, context, page, random_device_name

 


def search_google(page, keyword, device_name):
    """Google'da arama yaparak ilk reklamın HTML elementini bulur."""
    page.goto("https://www.google.com/")
    time.sleep(random.uniform(5, 8))  # Sayfanın tam yüklenmesi için bekleme

    # 📌 CAPTCHA Kontrolü ve Yeniden Yükleme
    if "our systems have detected unusual traffic" in page.content().lower():
        print("⚠️ CAPTCHA algılandı! Sayfa yeniden yükleniyor...")
        page.reload()
        time.sleep(random.uniform(5, 10))

    # 🍪 Çerezleri Kabul Et
    try:
        accept_button = page.locator("text=Kabul Et")
        if accept_button.is_visible():
            accept_button.tap()  # Mobilde tıklamak yerine tap() kullan
            time.sleep(random.uniform(3, 5))
    except:
        pass  # Eğer çerez butonu yoksa devam et

    # ✅ **Farklı Google arayüzleri için birden fazla arama kutusu seçici kullan!**
    search_box_selectors = [
        "textarea[name='q']",  # **Standart Google arama kutusu**
        "input[name='q']",  # **Bazı cihazlarda input olabilir**
        "input[title='Ara']",  # **Bazı eski cihazlarda title kullanılabilir**
        "input[aria-label='Search']",  # **Bazı Google temalarında olabilir**
        "form[role='search'] input"  # **Bazı Google temalarında farklı HTML olabilir**
    ]

    search_box = None
    for selector in search_box_selectors:
        try:
            search_box = page.wait_for_selector(selector, timeout=5000)
            if search_box:
                print(f"✅ Arama kutusu bulundu: {selector}")
                break
        except:
            continue  # Eğer bu seçici bulunamazsa bir sonrakine geç

    if not search_box:
        print(f"❌ Arama kutusu bulunamadı! Sayfa yapısı farklı olabilir. Cihaz: {device_name}")
        return None

    # ✅ **Mobil klavye açılmasını sağlamak için TAP yerine FOCUS kullan**
    search_box.tap()
    time.sleep(random.uniform(2, 5))  # Mobil klavye açılma süresi simülasyonu

    # 📌 **BOŞ KARAKTER YAZ VE KLAVYEYİ AÇMAYA ZORLA**
    page.keyboard.type(" ", delay=random.uniform(50, 100))  # Boşluk karakteri ekle
    page.keyboard.press("Backspace")  # Boşluğu sil
    time.sleep(1)

    # 📌 **GERÇEK KELİMEYİ HARF HARF YAZ (Mobil Klavyeyi Simüle Et)**
    page.keyboard.type(keyword, delay=random.uniform(50, 150))

    time.sleep(random.uniform(2, 4))  
    page.keyboard.press("Enter")

    # ✅ **Sayfanın tamamen yüklenmesini bekle**
    page.wait_for_load_state("domcontentloaded")
    time.sleep(random.uniform(5, 10))

    # 🚨 CAPTCHA Kontrolü ve Yeniden Yükleme
    if "captcha" in page.content().lower():
        print("🚨 CAPTCHA algılandı! Sayfa tekrar yükleniyor...")
        page.reload()
        time.sleep(random.uniform(5, 10))
        return search_google(page, keyword, device_name)  # CAPTCHA varsa fonksiyonu tekrar çalıştır

    return page





def main():
    keyword = input("🔎 Aramak istediğiniz kelimeyi girin: ")
    p, browser, context, page, device_name = setup_browser()

    if not page:
        print("❌ Tarayıcı başlatılamadı! Çıkılıyor...")
        return

    try:
        page = search_google(page, keyword, device_name)

    finally:
        # Çerezleri kaydet
        context.storage_state(path=storage_path)
        browser.close()
        p.stop()

if __name__ == "__main__":
    main()

