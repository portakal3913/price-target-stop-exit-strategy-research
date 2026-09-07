"""İlk (naif) test: Bollinger alt bant reddi sinyali sonrası SABİT N gün bekleyip
kapanış fiyatıyla getiriyi ölçüyoruz. Bu, fiyatın gerçekte NE YAPTIĞINI değil,
sadece "N gün sonra nerede olduğunu" gösteriyor - bir sonraki script'te bunun
neden yanıltıcı olduğunu göreceğiz."""
import numpy as np
import pandas as pd
from scipy import stats
from ortak_araclar import veri_indir, bollinger_alt_bant_reddi_sinyalleri

varliklar = {'^NDX': 'Nasdaq 100', '^GSPC': 'S&P 500', 'GC=F': 'Altın', 'XU100.IS': 'BIST 100'}
N = 30

tum_sinyal, tum_baseline = [], []
for ticker, isim in varliklar.items():
    veri = veri_indir(ticker)
    sinyal_tarihleri = bollinger_alt_bant_reddi_sinyalleri(veri)
    veri['Sonraki_Getiri'] = (veri['Close'].shift(-N) - veri['Close']) / veri['Close'] * 100

    sinyal_getirileri = veri.loc[sinyal_tarihleri, 'Sonraki_Getiri'].dropna()
    tum_getiriler = veri['Sonraki_Getiri'].dropna()

    print(f"{isim:>12} | n={len(sinyal_getirileri):>4} | Sinyal Ort: %{sinyal_getirileri.mean():>6.2f} | "
          f"Baseline Ort: %{tum_getiriler.mean():>6.2f} | Fark: %{sinyal_getirileri.mean()-tum_getiriler.mean():>6.2f}")

    tum_sinyal.extend(sinyal_getirileri.tolist())
    tum_baseline.extend(tum_getiriler.tolist())

tum_sinyal, tum_baseline = np.array(tum_sinyal), np.array(tum_baseline)
t, p = stats.ttest_ind(tum_sinyal, tum_baseline, equal_var=False)
print(f"\n=== BİRLEŞİK (4 Varlık, N={N} gün sabit bekleme) ===")
print(f"n={len(tum_sinyal)}, Sinyal Ort: %{tum_sinyal.mean():.2f}, Baseline Ort: %{tum_baseline.mean():.2f}")
print(f"t={t:.3f}, p={p:.4f}")
