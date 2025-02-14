import numpy as np
import pandas as pd

def ta_wma(series, length):
    length = int(length)
    if length <= 0:
        raise ValueError("window must be an integer greater than 0")
    # weights = np.arange(length, 0, -1)  # Ağırlıklar ters sırada azalır
    weights = np.arange(1, length + 1)
    return series.rolling(length).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)

# HMAX fonksiyonu
def hmax(src, length):
    half_length = length // 2
    sqrt_length = int(np.sqrt(length))
    wma_half = ta_wma(src, half_length)
    wma_full = ta_wma(src, length)
    return ta_wma(2 * wma_half - wma_full, sqrt_length)

# HMA3 fonksiyonu
def hma3(src, length):
    p = length / 2
    wma_1 = ta_wma(src, int(p / 3))
    wma_2 = ta_wma(src, int(p / 2))
    wma_3 = ta_wma(src, int(p))
    return ta_wma(wma_1 * 3 - wma_2 - wma_3, int(p))


# def hmax(src, length):
#     half_length = length // 2
#     sqrt_length = int(np.sqrt(length))
#     wma_half = ta_wma(src, half_length)
#     wma_full = ta_wma(src, length)
#     return ta_wma(2 * wma_half - wma_full, sqrt_length)

# def hma3(src, length):
#     p = int(length / 2)
#     wma_1 = ta_wma(src, int(p / 3))
#     wma_2 = ta_wma(src, int(p / 2))
#     wma_3 = ta_wma(src, p)
#     return ta_wma(wma_1 * 3 - wma_2 - wma_3, p)

# def ta_wma(series, length):
#     length = int(length)
#     if length <= 0:
#         raise ValueError("window must be an integer greater than 0")
#     weights = np.arange(1, length + 1)
#     return series.rolling(length).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)

def adx_smoothing(high, low, close, lensig=14, len_=14):
    up = high.diff()
    down = -low.diff()
    plus_dm = np.where((up > down) & (up > 0), up, 0)
    minus_dm = np.where((down > up) & (down > 0), down, 0)
    trur = true_range(high, low, close).rolling(len_).mean()
    plus_di = 100 * pd.Series(plus_dm).rolling(len_).mean() / trur
    minus_di = 100 * pd.Series(minus_dm).rolling(len_).mean() / trur
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di) * 100).replace([np.inf, -np.inf], 0).fillna(0)
    adx = dx.rolling(lensig).mean()  # lensig burada ADX değerini düzleştirmek için kullanılıyor
    return plus_di, minus_di, adx

def true_range(high, low, close):
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return true_range
