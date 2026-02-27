# CNC Plotter G-code Dönüştürücü

JSCut'tan gelen G-code dosyalarını servo motorlu Z ekseni için dönüştürür.

## 🎯 Ne Yapar?

JSCut programı 3 step motorlu CNC makineler için tasarlanmıştır. Z ekseni hareketlerini step motor komutları olarak üretir:
- `G1 Z5.5000` - Z eksenini yukarı kaldır
- `G1 Z-0.5000` - Z eksenini aşağı indir

Bu program bu komutları **servo motor** komutlarına dönüştürür:
- **M3 S45** → Kalem aşağı (çizim yapıyor)
- **M5** → Kalem yukarı (çizim yapmıyor)
- **G4 P0.2** → Servo'nun pozisyona ulaşması için 0.2 saniye bekle

### 🔄 Y Ekseni Ters Çevirme (YENİ!)

JSCut ve Inkscape gibi programlar **sol üst köşeden** (0,0) başlar ve Y ekseni **aşağı doğru** pozitiftir.  
CNC makineler ise genellikle **sol alt köşeden** (0,0) başlar ve Y ekseni **yukarı doğru** pozitiftir.

Bu program **otomatik olarak Y eksenini ters çevirerek** koordinat sistemlerini uyumlu hale getirir! 🎯

### ⏱️ Servo Bekleme Süresi (YENİ!)

Servo motorlar pozisyona ulaşmak için zamana ihtiyaç duyar. Program her servo hareketinden sonra **G4 (dwell)** komutuyla bekler:
- Varsayılan: **0.2 saniye**
- Ayarlanabilir: 0.1 - 0.5 saniye arası önerilir
- Çok hızlı servo → daha kısa süre (0.1s)
- Yavaş servo veya ağır kalem → daha uzun süre (0.3-0.5s)

## 📦 Gereksinimler

- Python 3.6 veya üzeri
- Windows için GUI versiyonunda tkinter (Python ile birlikte gelir)

## 🚀 Kullanım

### 1️⃣ GUI Versiyonu (Windows - Önerilen)

```bash
python gcode_converter.py
```

**Adımlar:**
1. Program çalıştırılır
2. **Y Eksenini Ters Çevir** seçeneğini işaretleyin (JSCut için önerilen)
3. **Servo Bekleme Süresi** girin (varsayılan 0.2 saniye)
4. **Dosya Seç ve Dönüştür** butonuna tıklayın
5. JSCut'tan gelen G-code dosyanızı seçin
6. Çıkış dosyası için isim belirleyin
7. Program otomatik dönüştürür ve sonucu gösterir

### 2️⃣ Komut Satırı Versiyonu (Her Platform)

```bash
# Y eksenini ters çevirerek (JSCut için önerilen)
python gcode_converter_cli.py jscut_output.gcode --flip-y

# Y flip + özel servo bekleme süresi
python gcode_converter_cli.py jscut_output.gcode --flip-y --dwell 0.3

# Hem giriş hem çıkış dosyası + Y flip + hızlı servo (0.15s)
python gcode_converter_cli.py jscut_output.gcode servo_output.gcode --flip-y --dwell 0.15

# Y flip olmadan (eğer zaten doğru koordinat sistemi kullanıyorsanız)
python gcode_converter_cli.py jscut_output.gcode
```

**Yardım için:**
```bash
python gcode_converter_cli.py --help
```

## 📋 Örnek Dönüşüm

**JSCut Orijinal:**
```gcode
G1 X20.0000 Y15.0000 F2540
G1 Z0.5000
G1 Z-0.5000 F127      ; Kalem aşağı
G1 X31.2303 Y-52.0896 F1016
G1 Z5.5000 F2540      ; Kalem yukarı
```

**Dönüştürülmüş (Servo + Y Flip + Dwell):**
```gcode
G1 X20.0000 Y0.0000 F2540      ; Y ters çevrildi (15→0)
; G1 Z0.5000 (orijinal - kalem zaten yukarıda)
; G1 Z-0.5000 F127 (orijinal)
M3 S45  ; Kalem aşağı
G4 P0.2  ; Servo bekleme süresi (servo'nun yerine oturması için)
G1 X31.2303 Y67.0896 F1016     ; Y ters çevrildi (-52→67)
; G1 Z5.5000 F2540 (orijinal)
M5  ; Kalem yukarı
G4 P0.2  ; Servo bekleme süresi
```

**Y Ekseni Nasıl Ters Çevrilir?**
- Program otomatik olarak max Y değerini bulur (örn: 15.0000)
- Her Y koordinatı: `new_Y = max_Y - old_Y` formülüyle dönüştürülür
- Örnek: Y15.0000 → 15-15 = Y0.0000 (üst köşe → alt köşe)
- Örnek: Y-52.0896 → 15-(-52.0896) = Y67.0896

**G4 (Dwell) Komutu Neden Gerekli?**
- Servo motorlar hareket ettikten sonra pozisyona ulaşmak için zamana ihtiyaç duyar
- G4 P0.2 = 0.2 saniye bekle (200 milisaniye)
- Bu bekleme olmadan kalem tam inmeden çizim başlar → bozuk çizim
- Çok hızlı hareket ederse kalem kağıda tam değmez veya çok bastırır

## ⚙️ Çalışma Mantığı

### Z Ekseni (Servo Motor):
1. **Z Pozitif veya Sıfır** (`Z >= 0`) → `M5` (Kalem Yukarı)
2. **Z Negatif** (`Z < 0`) → `M3 S45` (Kalem Aşağı)
3. **Gereksiz Tekrarları Önler**: Kalem zaten aşağıdaysa tekrar M3 S45 göndermez
4. **Orijinal Koruma**: Z komutları yorum satırı olarak saklanır

### Y Ekseni (Koordinat Sistemi):
1. **Otomatik Algılama**: Dosyadaki en büyük Y değerini bulur
2. **Ters Çevirme**: `new_Y = max_Y - old_Y` formülü
3. **Koordinat Uyumu**: JSCut (sol üst) → CNC (sol alt)

### Güvenlik:
- Program başlangıcında kalem yukarıda başlar
- Her dosya dönüşümünde durum sıfırlanır

## 🔧 Teknik Detaylar

### Servo Ayarları
```
M3 S45 - Kalem aşağı pozisyonu
M5     - Kalem yukarı pozisyonu
```

Bu değerleri değiştirmek isterseniz, kod içinde `self.pen_down` ve `self.pen_up` değişkenlerini düzenleyin.

### Servo Bekleme Süresi (Dwell Time)

**Varsayılan:** 0.2 saniye (200ms)

**Nasıl Ayarlanır?**
- **Hızlı servo** (SG90, MG90S): 0.1-0.15 saniye
- **Orta hızlı servo** (standart): 0.2 saniye (önerilen)
- **Yavaş servo veya ağır kalem**: 0.3-0.5 saniye

**Test Yöntemi:**
1. 0.2 saniye ile başla
2. Çizim yaparken kalem tam değmiyorsa → süreyi artır (0.3s)
3. Çizim çok yavaşsa → süreyi azalt (0.15s)
4. Kalem titriyor veya çizgiler bozuksa → süreyi artır

**Komut satırında:**
```bash
python gcode_converter_cli.py input.gcode --flip-y --dwell 0.3
```

**GUI'de:**
Input alanına istediğin değeri gir (örn: 0.15, 0.2, 0.3)

### Arduino Nano Uyumluluğu
- ✅ X ve Y eksenleri: Step motorlar (28BYJ-48)
- ✅ Z ekseni: Servo motor
- ✅ UGS Platform ile uyumlu
- ✅ G4 (dwell) komutunu destekleyen firmware gerekli

## 🎨 JSCut İç Dolgu Ayarları

JSCut'ta iç dolguları çizmek için:

1. **Operations** sekmesine gidin
2. **Inside** seçeneğini işaretleyin
3. **Fill** bölümünden dolgu tipini seçin:
   - **Hatch** - Paralel çizgiler
   - **Grid** - Izgara
   - **Offset** - Dıştan içe spiral
4. **Step Over** değerini ayarlayın (çizgiler arası mesafe)
5. **Generate** ile G-code üretin

## 📁 Dosya Yapısı

```
📁 cnc-plotter-tools/
├── gcode_converter.py          # GUI versiyonu (Windows)
├── gcode_converter_cli.py      # Komut satırı versiyonu
├── test_jscut.gcode           # Test için örnek dosya
└── README.md                  # Bu dosya
```

## ⚠️ Önemli Notlar

1. **İlk Çalıştırma**: Dönüştürülmüş dosyayı kullanmadan önce UGS'de simülasyon modunda test edin
2. **Servo Kalibrasyonu**: M3 S45 ve M5 değerlerini kendi servo motorunuza göre ayarlayın
3. **Güvenlik**: Her zaman manuel kontrol ile başlayın
4. **Yedekleme**: Orijinal JSCut dosyalarınızı saklayın

## 🐛 Sorun Giderme

**Problem**: Kalem hiç inmiyor / çıkmıyor
- **Çözüm**: Arduino kodunuzda M3 ve M5 komutlarının doğru tanımlı olduğundan emin olun

**Problem**: Kalem tam değmeden çizim başlıyor
- **Çözüm**: Servo bekleme süresini artırın (--dwell 0.3 veya GUI'de 0.3)

**Problem**: Çizim çok yavaş ilerliyor
- **Çözüm**: Servo bekleme süresini azaltın (--dwell 0.15)

**Problem**: Çizgiler titrek veya bozuk
- **Çözüm**: Servo bekleme süresini artırın, servo'nun tam yerine oturması için daha fazla zaman verin

**Problem**: Arduino "G4 komutunu tanımıyor" hatası
- **Çözüm**: Arduino firmware'inizde G4 (dwell) komutu desteklenmeli. GRBL veya Marlin kullanıyorsanız varsayılan olarak destekler.

**Problem**: Sadece dış hatlar çiziliyor, iç dolgu yok
- **Çözüm**: JSCut'ta "Inside" ve "Fill" seçeneklerini aktif edin

**Problem**: Çizim ters/ayna görünümde
- **Çözüm**: `--flip-y` parametresini kullanın veya GUI'de Y flip seçeneğini işaretleyin

**Problem**: Çizim sol üst köşeden başlıyor, sol alttan başlamalı
- **Çözüm**: Bu normal! `--flip-y` kullanın. JSCut sol üstten, CNC'ler sol alttan başlar.

**Problem**: Python dosyası açılmıyor
- **Çözüm**: Komut satırından çalıştırın veya Python'un yüklü olduğundan emin olun

**Problem**: Y flip sonrası çizim hala doğru değil
- **Çözüm**: Inkscape'te çiziminizi kontrol edin, belki orada da flip yapmanız gerekebilir

## 📞 Destek

Sorunlarınız için:
1. README dosyasını tekrar okuyun
2. Test dosyasıyla deneyin
3. Arduino serial monitöründe G-code komutlarını kontrol edin

## 📝 Lisans

Bu araç kişisel ve eğitim amaçlı kullanım için serbesttir.

---

**İyi çizimler! 🎨**
