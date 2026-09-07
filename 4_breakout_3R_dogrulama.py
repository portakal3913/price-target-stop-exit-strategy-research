"""Kazanan sistem: Breakout + Stop=SinyalGünüLow + Hedef=3R.
Bağımsızlık düzeltmesi ve In-Sample/Out-of-Sample testleriyle sağlamlığını doğrula."""
import numpy as np
import pandas as pd
from scipy import stats
from ortak_araclar import (
    veri_indir, breakout_sinyalleri, olay_tabanli_simule_et,
    bagimsiz_islemleri_sec, hedef_r_katli,
)

varliklar = {'^NDX': 'Nasdaq 100', '^GSPC': 'S&P 500', 'GC=F': 'Altın', 'XU100.IS': 'BIST 100'}
R = 3
AYIRMA_TARIHI = pd.Timestamp('2021-01-01')

print("=== BAĞIMSIZLIK DÜZELTMESİ ===")
tum_cakismali, tum_bagimsiz = [], []
tum_islemler_tarihli = []

for ticker, isim in varliklar.items():
    veri = veri_indir(ticker)
    sinyal_tarihleri = breakout_sinyalleri(veri)
    islemler = olay_tabanli_simule_et(veri, sinyal_tarihleri, hedef_r_katli(R))
    bagimsizlar = bagimsiz_islemleri_sec(islemler)

    print(f"{isim:>12} | Çakışmalı: {len(islemler):>4} | Bağımsız: {len(bagimsizlar):>4} "
          f"(%{100*len(bagimsizlar)/len(islemler):.1f})")

    tum_cakismali.extend([r['getiri'] for r in islemler])
    tum_bagimsiz.extend([r['getiri'] for r in bagimsizlar])
    tum_islemler_tarihli.extend(islemler)

tc, tb = np.array(tum_cakismali), np.array(tum_bagimsiz)
t1, p1 = stats.ttest_1samp(tc, 0)
t2, p2 = stats.ttest_1samp(tb, 0)
print(f"\nÇakışmalı: n={len(tc)}, Ort=%{tc.mean():.3f}, p={p1:.6f}")
print(f"Bağımsız : n={len(tb)}, Ort=%{tb.mean():.3f}, p={p2:.6f}")

print("\n=== IN-SAMPLE / OUT-OF-SAMPLE ===")
is_getiriler = [r['getiri'] for r in tum_islemler_tarihli if r['tarih'] < AYIRMA_TARIHI]
oos_getiriler = [r['getiri'] for r in tum_islemler_tarihli if r['tarih'] >= AYIRMA_TARIHI]
is_getiriler, oos_getiriler = np.array(is_getiriler), np.array(oos_getiriler)

t3, p3 = stats.ttest_1samp(is_getiriler, 0)
t4, p4 = stats.ttest_1samp(oos_getiriler, 0)
print(f"In-Sample  (2010-2020)    : n={len(is_getiriler):>4}, Ort=%{is_getiriler.mean():.3f}, "
      f"Kazanma=%{(is_getiriler>0).mean()*100:.1f}, p={p3:.6f}")
print(f"Out-of-Sample (2021-2026) : n={len(oos_getiriler):>4}, Ort=%{oos_getiriler.mean():.3f}, "
      f"Kazanma=%{(oos_getiriler>0).mean()*100:.1f}, p={p4:.6f}")
