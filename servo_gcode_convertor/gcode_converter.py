#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CNC Plotter G-code Dönüştürücü
JSCut'tan gelen Z ekseni step motor komutlarını servo motor komutlarına dönüştürür
M3 S45 = Kalem Aşağı
M5 = Kalem Yukarı
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import re
import os

class GCodeConverter:
    def __init__(self, flip_y=False, y_max=None, dwell_time=0.2):
        self.pen_down = "M3 S45"  # Kalem aşağı komutu
        self.pen_up = "M5"        # Kalem yukarı komutu
        self.last_z_state = None  # Son Z durumu (up/down)
        self.flip_y = flip_y      # Y eksenini ters çevir
        self.y_max = y_max        # Y ekseni maksimum değeri (flip için)
        self.dwell_time = dwell_time  # Servo bekleme süresi (saniye)
        
    def parse_z_value(self, line):
        """G-code satırından Z değerini çıkarır"""
        # Z değerini bul (Z5.5000, Z-0.5000 gibi)
        z_match = re.search(r'Z(-?\d+\.?\d*)', line, re.IGNORECASE)
        if z_match:
            return float(z_match.group(1))
        return None
    
    def parse_y_value(self, line):
        """G-code satırından Y değerini çıkarır"""
        y_match = re.search(r'Y(-?\d+\.?\d*)', line, re.IGNORECASE)
        if y_match:
            return float(y_match.group(1))
        return None
    
    def flip_y_in_line(self, line):
        """Y değerini ters çevirir (y_max - y)"""
        if not self.flip_y or self.y_max is None:
            return line
        
        y_value = self.parse_y_value(line)
        if y_value is not None:
            new_y = self.y_max - y_value
            # Y değerini değiştir
            line = re.sub(r'Y-?\d+\.?\d*', f'Y{new_y:.4f}', line, flags=re.IGNORECASE)
        
        return line
    
    def convert_line(self, line):
        """Tek bir G-code satırını dönüştürür"""
        line = line.strip()
        
        # Boş satırlar ve yorumlar
        if not line or line.startswith(';'):
            return line
        
        # Y eksenini flip et (gerekirse)
        if self.flip_y and 'Y' in line.upper():
            line = self.flip_y_in_line(line)
        
        # Z hareketi var mı kontrol et
        if 'Z' in line.upper():
            z_value = self.parse_z_value(line)
            
            if z_value is not None:
                # Z pozitif veya sıfır → kalem yukarı
                if z_value >= 0:
                    if self.last_z_state != 'up':
                        self.last_z_state = 'up'
                        dwell_cmd = f"G4 P{self.dwell_time}  ; Servo bekleme süresi"
                        return f"; {line} (orijinal)\n{self.pen_up}  ; Kalem yukarı\n{dwell_cmd}"
                    else:
                        # Zaten yukarıdaysa, komutu tekrar göndermiyoruz
                        return f"; {line} (orijinal - kalem zaten yukarıda)"
                
                # Z negatif → kalem aşağı
                else:
                    if self.last_z_state != 'down':
                        self.last_z_state = 'down'
                        dwell_cmd = f"G4 P{self.dwell_time}  ; Servo bekleme süresi"
                        return f"; {line} (orijinal)\n{self.pen_down}  ; Kalem aşağı\n{dwell_cmd}"
                    else:
                        # Zaten aşağıdaysa, komutu tekrar göndermiyoruz
                        return f"; {line} (orijinal - kalem zaten aşağıda)"
            else:
                # Z var ama değer bulunamadı, satırı olduğu gibi bırak
                return line
        
        # Z hareketi yok, normal X/Y hareketi - olduğu gibi bırak
        return line
    
    def convert_gcode(self, input_file, output_file):
        """G-code dosyasını dönüştürür"""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Eğer flip_y aktif ama y_max verilmemişse, otomatik bul
            if self.flip_y and self.y_max is None:
                y_values = []
                for line in lines:
                    y_val = self.parse_y_value(line)
                    if y_val is not None:
                        y_values.append(y_val)
                
                if y_values:
                    self.y_max = max(y_values)
                else:
                    self.flip_y = False
            
            converted_lines = []
            self.last_z_state = None  # Her yeni dosya için sıfırla
            
            # Başlık ekle
            converted_lines.append("; ==========================================\n")
            converted_lines.append("; CNC Plotter G-code (Servo Motor Z Ekseni)\n")
            converted_lines.append(f"; Orijinal dosya: {os.path.basename(input_file)}\n")
            converted_lines.append("; M3 S45 = Kalem Aşağı | M5 = Kalem Yukarı\n")
            if self.flip_y:
                converted_lines.append(f"; Y Ekseni Ters Çevrildi (Y_max = {self.y_max:.4f} mm)\n")
            converted_lines.append(f"; Servo Bekleme Süresi: {self.dwell_time} saniye\n")
            converted_lines.append("; ==========================================\n\n")
            
            # Güvenlik için başlangıçta kalem yukarı
            converted_lines.append(f"{self.pen_up}  ; Başlangıç - Kalem yukarı\n")
            converted_lines.append(f"G4 P{self.dwell_time}  ; Servo bekleme süresi\n")
            converted_lines.append("G90  ; Absolute positioning\n")
            converted_lines.append("G21  ; mm cinsinden\n\n")
            
            # Her satırı dönüştür
            for line in lines:
                converted = self.convert_line(line)
                if converted:
                    if not converted.endswith('\n'):
                        converted += '\n'
                    converted_lines.append(converted)
            
            # Bitiş komutu
            converted_lines.append(f"\n; Bitti - Kalem yukarı kaldır\n")
            converted_lines.append(f"{self.pen_up}\n")
            converted_lines.append("G28 X Y  ; Home X ve Y eksenleri (opsiyonel)\n")
            
            # Yeni dosyaya yaz
            with open(output_file, 'w', encoding='utf-8') as f:
                f.writelines(converted_lines)
            
            flip_info = f"\n\nY Ekseni ters çevrildi (max = {self.y_max:.4f} mm)" if self.flip_y else ""
            return True, f"Dönüştürme başarılı!{flip_info}\n\nGiriş: {input_file}\nÇıkış: {output_file}"
            
        except Exception as e:
            return False, f"Hata oluştu: {str(e)}"

def select_and_convert():
    """Dosya seçme ve dönüştürme işlemini başlatır"""
    # Tkinter root penceresi
    root = tk.Tk()
    root.title("CNC Plotter G-code Dönüştürücü")
    root.geometry("500x280")
    root.resizable(False, False)
    
    # Başlık
    title_label = tk.Label(root, text="CNC Plotter G-code Dönüştürücü", 
                          font=("Arial", 14, "bold"))
    title_label.pack(pady=10)
    
    subtitle_label = tk.Label(root, text="JSCut → Servo Motor (Z Ekseni)", 
                             font=("Arial", 10))
    subtitle_label.pack()
    
    # Y flip checkbox
    flip_y_var = tk.BooleanVar(value=False)
    flip_checkbox = tk.Checkbutton(root, 
                                   text="Y Eksenini Ters Çevir (Sol Üst → Sol Alt)",
                                   variable=flip_y_var,
                                   font=("Arial", 10))
    flip_checkbox.pack(pady=10)
    
    # Servo bekleme süresi frame
    dwell_frame = tk.Frame(root)
    dwell_frame.pack(pady=10)
    
    dwell_label = tk.Label(dwell_frame, 
                          text="Servo Bekleme Süresi (saniye):",
                          font=("Arial", 10))
    dwell_label.pack(side=tk.LEFT, padx=5)
    
    dwell_var = tk.StringVar(value="0.2")
    dwell_entry = tk.Entry(dwell_frame, 
                          textvariable=dwell_var,
                          width=10,
                          font=("Arial", 10))
    dwell_entry.pack(side=tk.LEFT, padx=5)
    
    # Bilgi etiketi
    info_label = tk.Label(root, 
                         text="M3 S45 = Kalem Aşağı | M5 = Kalem Yukarı | G4 = Bekleme",
                         font=("Arial", 9),
                         fg="gray")
    info_label.pack(pady=5)
    
    def start_conversion():
        root.withdraw()  # Pencereyi gizle
        
        # Dwell time değerini al
        try:
            dwell_time = float(dwell_var.get())
            if dwell_time < 0:
                dwell_time = 0.2
                messagebox.showwarning("Uyarı", "Bekleme süresi negatif olamaz. Varsayılan 0.2 kullanılıyor.")
        except ValueError:
            dwell_time = 0.2
            messagebox.showwarning("Uyarı", "Geçersiz bekleme süresi. Varsayılan 0.2 kullanılıyor.")
        
        # Dosya seçme diyalogu
        input_file = filedialog.askopenfilename(
            title="JSCut G-code Dosyasını Seçin",
            filetypes=[
                ("G-code dosyaları", "*.gcode *.nc *.ngc *.txt"),
                ("Tüm dosyalar", "*.*")
            ]
        )
        
        if not input_file:
            messagebox.showinfo("İptal", "Dosya seçilmedi.")
            root.destroy()
            return
        
        # Çıkış dosyası adını oluştur
        base_name = os.path.splitext(input_file)[0]
        flip_suffix = "_flipped" if flip_y_var.get() else ""
        output_file = f"{base_name}_servo{flip_suffix}.gcode"
        
        # Kullanıcıya çıkış dosyasını seçme seçeneği sun
        output_file = filedialog.asksaveasfilename(
            title="Dönüştürülmüş Dosyayı Kaydet",
            initialfile=os.path.basename(output_file),
            defaultextension=".gcode",
            filetypes=[
                ("G-code dosyaları", "*.gcode"),
                ("NC dosyaları", "*.nc"),
                ("Tüm dosyalar", "*.*")
            ]
        )
        
        if not output_file:
            messagebox.showinfo("İptal", "Çıkış dosyası seçilmedi.")
            root.destroy()
            return
        
        # Dönüştürme işlemini yap
        converter = GCodeConverter(flip_y=flip_y_var.get(), dwell_time=dwell_time)
        success, message = converter.convert_gcode(input_file, output_file)
        
        if success:
            messagebox.showinfo("Başarılı", message)
        else:
            messagebox.showerror("Hata", message)
        
        root.destroy()
    
    # Başlat butonu
    start_button = tk.Button(root, 
                            text="Dosya Seç ve Dönüştür",
                            command=start_conversion,
                            bg="#4CAF50",
                            fg="white",
                            font=("Arial", 11, "bold"),
                            padx=20,
                            pady=10)
    start_button.pack(pady=15)
    
    root.mainloop()

def main():
    """Ana program"""
    print("=" * 60)
    print("CNC Plotter G-code Dönüştürücü")
    print("JSCut → Servo Motor (Z Ekseni)")
    print("=" * 60)
    print()
    print("Bu program JSCut'tan gelen G-code dosyalarını")
    print("servo motorlu Z ekseni için dönüştürür.")
    print()
    print("M3 S45 = Kalem Aşağı")
    print("M5 = Kalem Yukarı")
    print()
    print("Dosya seçme penceresi açılıyor...")
    print()
    
    select_and_convert()

if __name__ == "__main__":
    main()
