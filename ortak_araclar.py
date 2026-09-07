import yfinance as yf
import numpy as np
import pandas as pd

MAKS_BEKLEME = 90  # olay-tabanli simulasyonda guvenlik ust siniri (gun)


def veri_indir(ticker, start='2010-01-01'):
    veri = yf.download(ticker, start=start, progress=False)
    if isinstance(veri.columns, pd.MultiIndex):
        veri.columns = veri.columns.get_level_values(0)
    return veri


def ema_golden_cross_sinyalleri(veri):
    veri['EMA50'] = veri['Close'].ewm(span=50, adjust=False).mean()
    veri['EMA200'] = veri['Close'].ewm(span=200, adjust=False).mean()
    veri['EMA50_ustte_mi'] = (veri['EMA50'] > veri['EMA200']).astype(int)
    veri['Kesisim'] = veri['EMA50_ustte_mi'].diff()
    veri.iloc[:200, veri.columns.get_loc('Kesisim')] = np.nan
    return veri[veri['Kesisim'] == 1].index


def breakout_sinyalleri(veri, pencere=20):
    veri['Onceki_Zirve'] = veri['Close'].rolling(pencere).max().shift(1)
    veri['Breakout_Mi'] = (veri['Close'] > veri['Onceki_Zirve']).astype(int)
    veri['Yeni_Breakout'] = (veri['Breakout_Mi'].diff() == 1)
    return veri[veri['Yeni_Breakout']].index


def bollinger_alt_bant_reddi_sinyalleri(veri, pencere=20, std_carpani=2):
    veri['Orta_Bant'] = veri['Close'].rolling(pencere).mean()
    veri['Std_Sapma'] = veri['Close'].rolling(pencere).std()
    veri['Alt_Bant'] = veri['Orta_Bant'] - std_carpani * veri['Std_Sapma']
    veri['Ust_Bant'] = veri['Orta_Bant'] + std_carpani * veri['Std_Sapma']
    veri['Alt_Bant_Reddi'] = (veri['Low'] < veri['Alt_Bant']) & (veri['Close'] > veri['Alt_Bant'])
    return veri[veri['Alt_Bant_Reddi']].index


def olay_tabanli_simule_et(veri, sinyal_tarihleri, hedef_fonksiyonu, maks_bekleme=MAKS_BEKLEME):
    """Her sinyal icin: giris = sinyal gunu kapanisi, stop = sinyal gunu Low'u,
    hedef = hedef_fonksiyonu(veri, konum, giris, stop) ile hesaplanir.
    Her ileri gun icin High/Low'a bakarak once hangisi tetiklenirse (STOP ya da HEDEF)
    onunla kapatir. MAKS_BEKLEME sonunda hicbiri tetiklenmediyse kapanisla kapatir."""
    sonuclar = []
    for tarih in sinyal_tarihleri:
        konum = veri.index.get_loc(tarih)
        giris = veri['Close'].iloc[konum]
        stop = veri['Low'].iloc[konum]
        risk = giris - stop
        if risk <= 0:
            continue

        hedef = hedef_fonksiyonu(veri, konum, giris, stop)
        if pd.isna(hedef) or hedef <= giris:
            continue

        sonuc_tipi, cikis, gecen_gun = None, None, None
        for i in range(1, maks_bekleme + 1):
            ileri_konum = konum + i
            if ileri_konum >= len(veri):
                break
            h, l = veri['High'].iloc[ileri_konum], veri['Low'].iloc[ileri_konum]
            if l <= stop:
                sonuc_tipi, cikis, gecen_gun = 'STOP', stop, i
                break
            elif h >= hedef:
                sonuc_tipi, cikis, gecen_gun = 'HEDEF', hedef, i
                break

        if sonuc_tipi is None:
            son_konum = min(konum + maks_bekleme, len(veri) - 1)
            sonuc_tipi, cikis, gecen_gun = 'ZAMAN_ASIMI', veri['Close'].iloc[son_konum], son_konum - konum

        getiri = (cikis - giris) / giris * 100
        sonuclar.append({
            'tarih': tarih, 'konum': konum, 'cikis_konum': konum + gecen_gun,
            'sonuc_tipi': sonuc_tipi, 'getiri': getiri,
        })
    return sonuclar


def bagimsiz_islemleri_sec(islemler):
    """Cakisan (ayni anda pozisyonda olunan) islemleri eler; sadece bir onceki
    islemin CIKIS konumundan SONRA baslayan islemleri tutar."""
    secilen = []
    son_cikis_konumu = -1
    for row in sorted(islemler, key=lambda r: r['konum']):
        if row['konum'] > son_cikis_konumu:
            secilen.append(row)
            son_cikis_konumu = row['cikis_konum']
    return secilen


# Hazir hedef fonksiyonlari
def hedef_orta_bant(veri, konum, giris, stop):
    return veri['Orta_Bant'].iloc[konum]


def hedef_ust_bant(veri, konum, giris, stop):
    return veri['Ust_Bant'].iloc[konum]


def hedef_r_katli(r_katsayisi):
    def fonksiyon(veri, konum, giris, stop):
        return giris + r_katsayisi * (giris - stop)
    return fonksiyon
