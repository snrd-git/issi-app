"""Bangun data untuk aplikasi Skrining ISSI (index.html).

Hasil (folder data/):
  data/prices.js  harga harian 4 tahun semua saham di issi_list.txt + IHSG
  data/fund.js    data fundamental terbaru (Yahoo Finance) untuk tab Investasi
  data/meta.js    waktu update (dipakai aplikasi untuk cek pembaruan)

Dijalankan otomatis oleh GitHub Actions tiap hari bursa (lihat .github/workflows/update.yml),
atau manual:  python ambil_data.py          (harga + fundamental)
              python ambil_data.py harga    (harga saja, cepat)
Butuh: pip install yfinance pandas
"""
import json
import math
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import yfinance as yf

HERE = Path(__file__).parent
DATA = HERE / "data"
TAHUN = 4
MIN_NILAI_LIKUID = 5e8          # rata-rata nilai transaksi 60 hari; di bawah ini riwayat dipendekkan
HARI_PENDEK = 300


def kode_list():
    txt = (HERE / "issi_list.txt").read_text(encoding="utf-8")
    kode = []
    for line in txt.splitlines():
        line = line.split("#")[0]
        kode += [k.strip().upper().replace(".JK", "") for k in line.replace(",", " ").split() if k.strip()]
    return sorted(set(kode))


def now_wib():
    return pd.Timestamp.now(tz="Asia/Jakarta")


def num(x, nd=2):
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return None
    r = round(float(x), nd)
    return int(r) if r == int(r) else r


def tulis(nama, fungsi, obj):
    DATA.mkdir(exist_ok=True)
    s = json.dumps(obj, separators=(",", ":"), ensure_ascii=False)
    (DATA / nama).write_text(f"{fungsi}({s});\n", encoding="utf-8")
    print(f"  {nama}: {len(s)/1e6:.2f} MB")


def harga(kode):
    tick = ["^JKSE"] + [f"{k}.JK" for k in kode]
    print(f"Mengunduh harga {len(tick)} ticker ({TAHUN} tahun)...")
    raw = yf.download(tick, period=f"{TAHUN}y", interval="1d", auto_adjust=False,
                      group_by="ticker", progress=False, threads=True)
    now = now_wib()
    out, hilang = {}, []
    for t in tick:
        k = "IHSG" if t == "^JKSE" else t[:-3]
        try:
            df = raw[t][["Open", "High", "Low", "Close", "Volume"]].dropna(subset=["Close"])
        except KeyError:
            hilang.append(k)
            continue
        df = df[df.Close > 0]
        if df.empty:
            hilang.append(k)
            continue
        df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
        # candle hari ini belum final sebelum bursa tutup
        if now.strftime("%H:%M") < "16:15" and df.index[-1].date() == now.date():
            df = df.iloc[:-1]
        nilai60 = (df.Close * df.Volume).tail(60).mean()
        if k != "IHSG" and not nilai60 >= MIN_NILAI_LIKUID:
            df = df.tail(HARI_PENDEK)
        d = df.index
        out[k] = {
            "d0": d[0].strftime("%Y-%m-%d"),
            "dd": [0] + [int((d[i] - d[i - 1]).days) for i in range(1, len(d))],
            "o": [num(v) for v in df.Open], "h": [num(v) for v in df.High],
            "l": [num(v) for v in df.Low], "c": [num(v) for v in df.Close],
            "v": [int(v // 100) if k != "IHSG" else int(v // 1000) for v in df.Volume.fillna(0)],
        }
    if hilang:
        print("  tanpa data:", " ".join(hilang))
    last = max((pd.Timestamp(v["d0"]) + pd.Timedelta(days=sum(v["dd"]))).strftime("%Y-%m-%d") for v in out.values())
    return out, last


def dividen(t):
    """DPS 12 bulan terakhir dan jumlah tahun berturut-turut membagi dividen."""
    try:
        s = t.dividends
    except Exception:
        return None, None
    if s is None or s.empty:
        return 0, 0
    s.index = pd.to_datetime(s.index).tz_localize(None)
    dps = float(s[s.index >= pd.Timestamp.now() - pd.Timedelta(days=365)].sum())
    tahun = set(s.index.year)
    y = pd.Timestamp.now().year
    if y not in tahun:
        y -= 1
    n = 0
    while y in tahun:
        n += 1
        y -= 1
    return dps, n


def fundamental(kode, harga_akhir):
    print(f"Mengunduh fundamental {len(kode)} saham...")
    fx = {"IDR": 1.0}
    try:
        fx["USD"] = float(yf.Ticker("USDIDR=X").fast_info["last_price"])
    except Exception:
        fx["USD"] = 16500.0  # cadangan
    out = {}
    for i, k in enumerate(kode):
        t = yf.Ticker(f"{k}.JK")
        try:
            inf = t.info or {}
        except Exception as e:
            print("  gagal", k, str(e)[:60])
            time.sleep(2)
            continue
        p = harga_akhir.get(k) or inf.get("currentPrice")
        if not p:
            continue
        ccy = inf.get("financialCurrency") or "IDR"
        rate = fx.get(ccy, 1.0)
        eps, bv = inf.get("trailingEps"), inf.get("bookValue")
        # Yahoo kadang memberi EPS/BV dalam mata uang laporan (mis. USD); ubah bila jelas terlalu kecil
        if eps and rate > 1 and abs(eps) < p / 1000:
            eps *= rate
        if bv and rate > 1 and bv < p / 1000:
            bv *= rate
        dps, thn = dividen(t)
        der = inf.get("debtToEquity")
        out[k] = {
            "nama": inf.get("shortName") or inf.get("longName"),
            "sektor": inf.get("sector"),
            "keuangan": (inf.get("sector") == "Financial Services"),
            "eps": num(eps), "bvps": num(bv), "dps": num(dps),
            "npm": num(inf.get("profitMargins"), 4), "roe": num(inf.get("returnOnEquity"), 4),
            "der": num(der / 100, 3) if der is not None else None,
            "kas": num(inf.get("totalCash"), 0), "utang": num(inf.get("totalDebt"), 0),
            "cfo": num(inf.get("operatingCashflow"), 0),
            "laba": num(inf.get("netIncomeToCommon"), 0),
            "g_laba": num(inf.get("earningsGrowth"), 4), "g_pend": num(inf.get("revenueGrowth"), 4),
            "thn_div": thn, "mcap": num(inf.get("marketCap"), 0), "ccy": ccy,
        }
        if (i + 1) % 20 == 0:
            print(f"  {i+1}/{len(kode)}")
    return out, fx


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "semua"
    kode = kode_list()
    prices, last = harga(kode)
    stamp = now_wib().strftime("%Y-%m-%d %H:%M WIB")
    tulis("prices.js", "ISSI_PRICES", {"updated": stamp, "last": last, "s": prices})
    if mode != "harga":
        akhir = {k: v["c"][-1] for k, v in prices.items()}
        fund, fx = fundamental(kode, akhir)
        tulis("fund.js", "ISSI_FUND", {"updated": stamp, "fx": fx, "s": fund})
    tulis("meta.js", "ISSI_META", {"updated": stamp, "last": last, "n": len(prices) - 1})
    print("Selesai:", stamp, "data terakhir", last)


if __name__ == "__main__":
    main()
