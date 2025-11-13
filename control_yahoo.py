import os
from pathlib import Path

import pandas as pd
import numpy as np
import yfinance as yf


# ==========================
#  Yardımcı Fonksiyonlar
# ==========================

def fill_missing_months(obj):
    """
    obj: DateTimeIndex'e sahip Series veya tek/çok kolonlu DataFrame.
    Eksik ayları (MS frekansında) önceki ve sonraki değerlerin ortalamasıyla doldurur.
    İlk/son uçta tek taraf NaN ise sonuç NaN kalır (mantıklı davranış).
    """
    if isinstance(obj, pd.Series):
        s = obj.copy()
        s.index = pd.to_datetime(s.index)
        full_idx = pd.date_range(s.index.min(), s.index.max(), freq="MS")
        s = s.reindex(full_idx)
        f = s.ffill()
        b = s.bfill()
        return (f + b) / 2

    elif isinstance(obj, pd.DataFrame):
        df = obj.copy()
        df.index = pd.to_datetime(df.index)
        full_idx = pd.date_range(df.index.min(), df.index.max(), freq="MS")
        df = df.reindex(full_idx)
        f = df.ffill()
        b = df.bfill()
        return (f + b) / 2

    else:
        raise TypeError("fill_missing_months yalnızca Series veya DataFrame kabul eder.")


def _ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def _ticker_to_filename(symbol: str, interval: str = "1mo") -> str:
    # Dosya ismi olarak kullanırken problem çıkarmasın diye bazı karakterleri değiştiriyoruz
    safe = symbol.replace("=", "_").replace("^", "").replace("/", "_")
    return f"{safe}_{interval}.parquet"


def load_or_update_yahoo_ticker(
    symbol: str,
    start: str = "2020-01-01",
    interval: str = "1mo",
    data_dir: str | Path = "/mnt/c/Users/semih/Desktop/python_project/car_prices/yahoo_cache",
    auto_adjust: bool = False,
) -> pd.DataFrame:
    """
    Tek bir sembol için:
      - Eğer parquet yoksa: Yahoo'dan komple indirip kaydeder.
      - Eğer parquet varsa:
          * Son barın tarihi bu ay ise: direkt parquet'i kullanır.
          * Değilse: eksik ayları Yahoo'dan indirip sonuna ekler, tekrar kaydeder.
    """
    data_dir = Path(data_dir)
    _ensure_dir(data_dir)

    file_path = data_dir / _ticker_to_filename(symbol, interval)
    today = pd.Timestamp.today().normalize()

    if file_path.exists():
        # Önceden indirilmiş veriyi oku
        df_cached = pd.read_parquet(file_path)
        if not isinstance(df_cached.index, pd.DatetimeIndex):
            # Eğer index Date değilse index'i tarihe çevir
            try:
                df_cached.index = pd.to_datetime(df_cached.index)
            except Exception:
                # Bazı parquet yazımları Date kolonunu ayrı tutabilir
                if "Date" in df_cached.columns:
                    df_cached["Date"] = pd.to_datetime(df_cached["Date"])
                    df_cached = df_cached.set_index("Date")
                else:
                    raise ValueError("Parquet dosyasının tarih indexi anlaşılamadı!")

        last_date = df_cached.index.max()

        # Eğer son tarih zaten içinde bulunduğumuz ay ise, yeni veri çekmemize gerek yok
        if last_date.to_period("M") >= today.to_period("M"):
            return df_cached.sort_index()

        # Eksik aylar için başlangıç tarihi: son tarihten bir sonraki ay
        download_start = (last_date + pd.offsets.MonthBegin(1)).strftime("%Y-%m-%d")

        df_new = yf.download(
            symbol,
            start=download_start,
            interval=interval,
            auto_adjust=auto_adjust,
        )

        if df_new.empty:
            # Yahoo’dan yeni veri gelmediyse, eskisini döndür
            return df_cached.sort_index()

        # İndeksin DateTime olduğundan emin ol
        if not isinstance(df_new.index, pd.DatetimeIndex):
            df_new.index = pd.to_datetime(df_new.index)

        # Duplicate tarihleri temizle, birleştir
        df_all = pd.concat([df_cached, df_new])
        df_all = df_all[~df_all.index.duplicated(keep="last")].sort_index()

        df_all.to_parquet(file_path)
        return df_all

    else:
        # Dosya yok, baştan indir
        df = yf.download(
            symbol,
            start=start,
            interval=interval,
            auto_adjust=auto_adjust,
        )

        if df.empty:
            raise ValueError(f"{symbol} için Yahoo'dan veri indirilemedi!")

        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        df.to_parquet(file_path)
        return df.sort_index()


# ===========================================
#  TÜM YAHOO VARLIKLARINI TEK YERDEN YÖNET
# ===========================================

def get_yahoo_market_data(
    start: str = "2020-01-01",
    interval: str = "1mo",
    cache_dir: str | Path = "yahoo_cache",
):
    """
    Tüm Yahoo sembollerini tek fonksiyonda ele alır.
    - Verileri parquet üzerinden cache’ler
    - Eksik ayları tamamlar
    - Gram altın TRY ve BTC TRY hesaplar
    - BIST100'ün ilk 6 satırını /10 düzeltmesini uygular

    Dönüş:
        dict:
            {
              "gold": gold_df,          # GC=F (Gram_Altin_Try kolonu eklenmiş)
              "usdtry": usdtry_df,      # USDTRY=X
              "bist100": bist100_df,    # XU100.IS
              "btc": btc_df             # BTC-USD (BTC_Try kolonu eklenmiş)
            }
    """
    cache_dir = Path(cache_dir)

    gold_symbol = "GC=F"
    usdtry_symbol = "USDTRY=X"
    bist100_symbol = "XU100.IS"
    btc_symbol = "BTC-USD"

    # 1) Temel verileri yükle / güncelle (parquet + Yahoo)
    gold = load_or_update_yahoo_ticker(
        gold_symbol, start=start, interval=interval, data_dir=cache_dir, auto_adjust=False
    )
    usdtry = load_or_update_yahoo_ticker(
        usdtry_symbol, start=start, interval=interval, data_dir=cache_dir, auto_adjust=False
    )
    bist100 = load_or_update_yahoo_ticker(
        bist100_symbol, start=start, interval=interval, data_dir=cache_dir, auto_adjust=False
    )
    btc = load_or_update_yahoo_ticker(
        btc_symbol, start=start, interval=interval, data_dir=cache_dir, auto_adjust=False
    )

    # 2) BIST100 ilk 6 satırı /10 düzeltmesi (senin notuna sadık kalarak)
    #    Not: index tarih sıralı olduğundan ilk 6 satır en eski 6 ay olacak.
    bist100 = bist100.sort_index()
    if len(bist100) >= 6:
        bist100.iloc[:6] = bist100.iloc[:6] / 10.0

    # 3) Gram Altın TRY hesabı
    #    gold_close: ons altın USD cinsinden Close
    gold_close = fill_missing_months(gold["Close"])
    gold_close = gold_close.squeeze("columns")  # Series olarak

    usd_close = usdtry["Close"].squeeze()

    # Gram altın = (ons fiyatı / 31.1035) * USDTRY
    # Indexleri hizalayarak çarpıyoruz
    ons_per_gram = (gold_close / 31.1035)
    g1, u1 = ons_per_gram.align(usd_close, join="inner")
    gram_altin_try = g1 * u1  # gram altın fiyatı (TRY)

    # Gram_Altin_Try kolonunu gold df'ine ekleyelim
    gold = gold.copy()
    gold["Gram_Altin_Try"] = np.nan
    common_idx = gold.index.intersection(gram_altin_try.index)
    gold.loc[common_idx, "Gram_Altin_Try"] = gram_altin_try.loc[common_idx]

    # 4) BTC TRY hesabı
    btc_close = btc["Close"].squeeze()
    b2, u2 = btc_close.align(usd_close, join="inner")
    btc_try = b2 * u2

    btc = btc.copy()
    btc["BTC_Try"] = np.nan
    common_idx_btc = btc.index.intersection(btc_try.index)
    btc.loc[common_idx_btc, "BTC_Try"] = btc_try.loc[common_idx_btc]

    return {
        "gold": gold,
        "usdtry": usdtry,
        "bist100": bist100,
        "btc": btc,
    }


# ==========================
#  Örnek kullanım
# ==========================
if __name__ == "__main__":
    data_dict = get_yahoo_market_data(
        start="2020-01-01",
        interval="1mo",
        cache_dir=".../car_prices/yahoo_cache"  # istersen /mnt/c/... gibi bir yol da verebilirsin
    )

    gold = data_dict["gold"]
    usdtry = data_dict["usdtry"]
    bist100 = data_dict["bist100"]
    btc = data_dict["btc"]

    print("Gold son 5 satır:")
    print(gold.tail())
    print("\nParquet cache klasörü:", Path(".../car_prices/yahoo_cache").resolve())
