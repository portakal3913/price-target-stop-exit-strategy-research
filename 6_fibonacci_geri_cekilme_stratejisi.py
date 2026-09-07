"""Fibonacci Geri Çekilme (Retracement) + Uzantı (Extension) Stratejisi.

Giriş: Son 90 günün Dip-Zirve aralığında, fiyatın test ettiği EN DERİN
geri çekilme seviyesinden (%23.6, %38.2, %50, %61.8, %78.6 arasından)
kapanışın üstüne dönmesi (rejection).
Stop: Sinyal günü en düşük fiyatı.
Hedef: Fibonacci UZANTISI (Dip + ext_katsayısı × (Zirve-Dip)) — sabit
R-katı yerine, trendin doğal devamını hedefleyen bir seviye.

Bu strateji tasarımı kullanıcı ile birlikte geliştirildi: "birden fazla
seviyeyi kontrol et, hangisi ret verirse oradan gir" ve "hedefi de
Fibonacci uzantısıyla belirle" fikirleri kullanıcıdan geldi."""
import numpy as np
import pandas as pd
from scipy import stats
from ortak_araclar import veri_indir, bagimsiz_islemleri_sec

varliklar = {'^NDX': 'Nasdaq 100', '^GSPC': 'S&P 500', 'GC=F': 'Altın', 'XU100.IS': 'BIST 100'}
PENCERE = 90
GERI_CEKILME_ORANLARI = [0.236, 0.382, 0.5, 0.618, 0.786]
MAKS_BEKLEME = 90
AYIRMA_TARIHI = pd.Timestamp('2021-01-01')


def fib_sinyalleri_ve_seviyeler(veri, pencere=PENCERE):
    """Her gün için: son `pencere` günün (kendisi hariç, shift(1)) Zirve/Dip'ini
    hesaplar. O gün, test edilen EN DERİN geri çekilme seviyesinden (Low seviyenin
    altına inip Close üstüne dönerse) sinyal üretir."""
    veri['Zirve'] = veri['Close'].rolling(pencere).max().shift(1)
    veri['Dip'] = veri['Close'].rolling(pencere).min().shift(1)
    sinyaller = {}
    for i in range(pencere, len(veri)):
        tarih = veri.index[i]
        zirve, dip = veri['Zirve'].iloc[i], veri['Dip'].iloc[i]
        if pd.isna(zirve) or pd.isna(dip) or zirve <= dip:
            continue
        aralik = zirve - dip
        low, close = veri['Low'].iloc[i], veri['Close'].iloc[i]

        for oran in sorted(GERI_CEKILME_ORANLARI, reverse=True):
            seviye = zirve - oran * aralik
            if low < seviye and close > seviye:
                sinyaller[tarih] = (oran, seviye, zirve, dip)
                break  # o gün için en derin geçerli seviyeyi bulduk, dur
    return sinyaller


def fib_ext_ile_simule_et(veri, sinyaller, ext_katsayisi, maks_bekleme=MAKS_BEKLEME):
    sonuclar = []
    for tarih, (oran, seviye, zirve, dip) in sinyaller.items():
        konum = veri.index.get_loc(tarih)
        giris = veri['Close'].iloc[konum]
        stop = veri['Low'].iloc[konum]
        if stop >= giris:
            continue
        hedef = dip + ext_katsayisi * (zirve - dip)
        if hedef <= giris:
            continue

        sonuc_tipi, cikis, gecen_gun = None, None, None
        for i in range(1, maks_bekleme + 1):
            ik = konum + i
            if ik >= len(veri):
                break
            h, l = veri['High'].iloc[ik], veri['Low'].iloc[ik]
            if l <= stop:
                sonuc_tipi, cikis, gecen_gun = 'STOP', stop, i
                break
            elif h >= hedef:
                sonuc_tipi, cikis, gecen_gun = 'HEDEF', hedef, i
                break
        if sonuc_tipi is None:
            sk = min(konum + maks_bekleme, len(veri) - 1)
            sonuc_tipi, cikis, gecen_gun = 'ZAMAN_ASIMI', veri['Close'].iloc[sk], sk - konum

        getiri = (cikis - giris) / giris * 100
        sonuclar.append({
            'tarih': tarih, 'konum': konum, 'cikis_konum': konum + gecen_gun,
            'getiri': getiri, 'oran': oran,
        })
    return sonuclar


for ext in [1.272, 1.618]:
    print(f"\n=== Fibonacci Uzantısı Hedefi = %{ext*100:.1f} ===")
    tum_getiriler, tum_bagimsiz = [], []
    for ticker, isim in varliklar.items():
        veri = veri_indir(ticker)
        sinyaller = fib_sinyalleri_ve_seviyeler(veri)
        islemler = fib_ext_ile_simule_et(veri, sinyaller, ext)
        bagimsizlar = bagimsiz_islemleri_sec(islemler)
        getiriler = [r['getiri'] for r in islemler]
        if len(getiriler) > 0:
            print(f"{isim:>12} | n={len(getiriler):>4} | Ort: %{np.mean(getiriler):>6.3f} | "
                  f"Kazanma: %{100*np.mean([g>0 for g in getiriler]):>5.1f}")
        tum_getiriler.extend(getiriler)
        tum_bagimsiz.extend([r['getiri'] for r in bagimsizlar])

    tg, tb = np.array(tum_getiriler), np.array(tum_bagimsiz)
    t1, p1 = stats.ttest_1samp(tg, 0)
    t2, p2 = stats.ttest_1samp(tb, 0)
    print(f"Çakışmalı: n={len(tg)}, Ort=%{tg.mean():.3f}, p={p1:.4f} | "
          f"Bağımsız: n={len(tb)}, Ort=%{tb.mean():.3f}, p={p2:.4f}")

print("\n=== In-Sample / Out-of-Sample (Uzantı=%161.8) ===")
is_all, oos_all = [], []
for ticker, isim in varliklar.items():
    veri = veri_indir(ticker)
    sinyaller = fib_sinyalleri_ve_seviyeler(veri)
    islemler = fib_ext_ile_simule_et(veri, sinyaller, 1.618)
    is_all.extend([r['getiri'] for r in islemler if r['tarih'] < AYIRMA_TARIHI])
    oos_all.extend([r['getiri'] for r in islemler if r['tarih'] >= AYIRMA_TARIHI])

is_all, oos_all = np.array(is_all), np.array(oos_all)
t1, p1 = stats.ttest_1samp(is_all, 0)
t2, p2 = stats.ttest_1samp(oos_all, 0)
print(f"In-Sample  (2010-2020) : n={len(is_all):>5}, Ort=%{is_all.mean():.3f}, "
      f"Kazanma=%{(is_all>0).mean()*100:.1f}, p={p1:.6f}")
print(f"Out-of-Sample (2021-26): n={len(oos_all):>5}, Ort=%{oos_all.mean():.3f}, "
      f"Kazanma=%{(oos_all>0).mean()*100:.1f}, p={p2:.6f}")
