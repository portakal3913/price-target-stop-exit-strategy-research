"""Aynı Bollinger alt bant reddi sinyali, ama artık SABİT gün yerine FİYAT
BAZLI çıkış: stop = sinyal günü Low'u, hedef = orta bant ya da üst bant.
Hangisi önce tetiklenirse pozisyon o an kapanır."""
import numpy as np
import pandas as pd
from scipy import stats
from ortak_araclar import (
    veri_indir, bollinger_alt_bant_reddi_sinyalleri, olay_tabanli_simule_et,
    bagimsiz_islemleri_sec, hedef_orta_bant, hedef_ust_bant,
)

varliklar = {'^NDX': 'Nasdaq 100', '^GSPC': 'S&P 500', 'GC=F': 'Altın', 'XU100.IS': 'BIST 100'}

for hedef_adi, hedef_fn in [('ORTA BANT', hedef_orta_bant), ('ÜST BANT', hedef_ust_bant)]:
    print(f"\n########## HEDEF = {hedef_adi} ##########")
    tum_cakismali, tum_bagimsiz = [], []
    for ticker, isim in varliklar.items():
        veri = veri_indir(ticker)
        sinyal_tarihleri = bollinger_alt_bant_reddi_sinyalleri(veri)
        islemler = olay_tabanli_simule_et(veri, sinyal_tarihleri, hedef_fn)
        bagimsizlar = bagimsiz_islemleri_sec(islemler)

        getiriler = [r['getiri'] for r in islemler]
        print(f"{isim:>12} | n={len(getiriler):>4} | Ort.Getiri: %{np.mean(getiriler):>6.2f} | "
              f"Kazanma: %{100*np.mean([g>0 for g in getiriler]):>5.1f}")

        tum_cakismali.extend(getiriler)
        tum_bagimsiz.extend([r['getiri'] for r in bagimsizlar])

    tc, tb = np.array(tum_cakismali), np.array(tum_bagimsiz)
    t1, p1 = stats.ttest_1samp(tc, 0)
    t2, p2 = stats.ttest_1samp(tb, 0)
    print(f"\nÇakışmalı: n={len(tc)}, Ort=%{tc.mean():.3f}, p={p1:.6f}")
    print(f"Bağımsız : n={len(tb)}, Ort=%{tb.mean():.3f}, p={p2:.6f}")
