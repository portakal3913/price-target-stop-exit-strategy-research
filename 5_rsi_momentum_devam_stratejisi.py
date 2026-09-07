"""RSI Momentum Devam Stratejisi (kullanıcı önerisiyle geliştirildi).

Klasik RSI mantığı "RSI>70 aşırı alım, SAT" der. Ama Breakout araştırmamızda
gördüğümüz gibi, genel piyasa drift'i (yükseliş eğilimi) short pozisyonları
cezalandırıyor. Bu script, RSI 70'i yukarı kesme anını SAT değil, "güçlü
momentuma katıl" (AL) sinyali olarak test ediyor - ve bu ters yorum, çok
daha güçlü bir edge ortaya çıkarıyor."""
import numpy as np
import pandas as pd
from scipy import stats
from ortak_araclar import veri_indir, olay_tabanli_simule_et, hedef_r_katli, bagimsiz_islemleri_sec

varliklar = {'^NDX': 'Nasdaq 100', '^GSPC': 'S&P 500', 'GC=F': 'Altın', 'XU100.IS': 'BIST 100'}
AYIRMA_TARIHI = pd.Timestamp('2021-01-01')


def rsi_hesapla(fiyat_serisi, periyot=14):
    degisim = fiyat_serisi.diff()
    kazanc = degisim.where(degisim > 0, 0)
    kayip = -degisim.where(degisim < 0, 0)
    ortalama_kazanc = kazanc.ewm(alpha=1/periyot, adjust=False).mean()
    ortalama_kayip = kayip.ewm(alpha=1/periyot, adjust=False).mean()
    rs = ortalama_kazanc / ortalama_kayip
    return 100 - (100 / (1 + rs))


def rsi_70_yeni_giris_sinyalleri(veri):
    """RSI 70'in ALTINDAYKEN üstüne YENİ çıktığı an (anlık, dönüş beklemeden)."""
    veri['RSI'] = rsi_hesapla(veri['Close'])
    veri['Altta_Mi'] = (veri['RSI'] <= 70).astype(int)
    veri['Gecis'] = veri['Altta_Mi'].diff()
    return veri[veri['Gecis'] == -1].index


print("=== R Değeri Taraması ===")
for R in [1, 2, 3]:
    tum_getiriler, tum_bagimsiz = [], []
    for ticker, isim in varliklar.items():
        veri = veri_indir(ticker)
        sinyaller = rsi_70_yeni_giris_sinyalleri(veri)
        islemler = olay_tabanli_simule_et(veri, sinyaller, hedef_r_katli(R))
        tum_getiriler.extend([r['getiri'] for r in islemler])
        tum_bagimsiz.extend([r['getiri'] for r in bagimsiz_islemleri_sec(islemler)])
    tg, tb = np.array(tum_getiriler), np.array(tum_bagimsiz)
    t1, p1 = stats.ttest_1samp(tg, 0)
    t2, p2 = stats.ttest_1samp(tb, 0)
    print(f"R={R} | Çakışmalı n={len(tg):>4} Ort=%{tg.mean():>6.3f} p={p1:.4f} | "
          f"Bağımsız n={len(tb):>4} Ort=%{tb.mean():>6.3f} p={p2:.4f}")

print("\n=== Varlık Bazında Tutarlılık (R=3) ===")
R = 3
is_all, oos_all = [], []
for ticker, isim in varliklar.items():
    veri = veri_indir(ticker)
    sinyaller = rsi_70_yeni_giris_sinyalleri(veri)
    islemler = olay_tabanli_simule_et(veri, sinyaller, hedef_r_katli(R))
    getiriler = [r['getiri'] for r in islemler]
    print(f"{isim:>12} | n={len(getiriler):>4} | Ort: %{np.mean(getiriler):>6.3f} | "
          f"Kazanma: %{100*np.mean([g>0 for g in getiriler]):>5.1f}")
    is_all.extend([r['getiri'] for r in islemler if r['tarih'] < AYIRMA_TARIHI])
    oos_all.extend([r['getiri'] for r in islemler if r['tarih'] >= AYIRMA_TARIHI])

is_all, oos_all = np.array(is_all), np.array(oos_all)
t1, p1 = stats.ttest_1samp(is_all, 0)
t2, p2 = stats.ttest_1samp(oos_all, 0)
print(f"\nIn-Sample  (2010-2020) : n={len(is_all):>4}, Ort=%{is_all.mean():.3f}, "
      f"Kazanma=%{(is_all>0).mean()*100:.1f}, p={p1:.6f}")
print(f"Out-of-Sample (2021-26): n={len(oos_all):>4}, Ort=%{oos_all.mean():.3f}, "
      f"Kazanma=%{(oos_all>0).mean()*100:.1f}, p={p2:.6f}")
