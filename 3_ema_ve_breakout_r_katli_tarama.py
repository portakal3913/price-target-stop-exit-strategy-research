"""EMA Golden Cross ve Breakout sinyallerine de aynı fiyat-bazlı çıkışı uygula.
Hedef, sabit bir R-katı (risk mesafesinin katı) olarak tanımlanıyor çünkü bu
sinyallerde Bollinger'daki gibi doğal bir "bant" hedefi yok."""
import numpy as np
from scipy import stats
from ortak_araclar import (
    veri_indir, ema_golden_cross_sinyalleri, breakout_sinyalleri,
    olay_tabanli_simule_et, hedef_r_katli,
)

varliklar = {'^NDX': 'Nasdaq 100', '^GSPC': 'S&P 500', 'GC=F': 'Altın', 'XU100.IS': 'BIST 100'}

for strateji_adi, sinyal_fn in [('EMA Golden Cross', ema_golden_cross_sinyalleri), ('Breakout', breakout_sinyalleri)]:
    print(f"\n########## {strateji_adi} ##########")
    for R in [1, 2, 3]:
        tum_getiriler = []
        for ticker, isim in varliklar.items():
            veri = veri_indir(ticker)
            sinyal_tarihleri = sinyal_fn(veri)
            islemler = olay_tabanli_simule_et(veri, sinyal_tarihleri, hedef_r_katli(R))
            tum_getiriler.extend([r['getiri'] for r in islemler])

        tum_getiriler = np.array(tum_getiriler)
        if len(tum_getiriler) == 0:
            print(f"R={R}: sinyal yok")
            continue
        t, p = stats.ttest_1samp(tum_getiriler, 0)
        print(f"R={R} | n={len(tum_getiriler):>5} | Ort.Getiri: %{tum_getiriler.mean():>6.3f} | "
              f"Kazanma: %{(tum_getiriler>0).mean()*100:>5.1f} | t={t:.3f} p={p:.4f}")
