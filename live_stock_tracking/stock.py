import os
import numpy as np
from yahoo import data_scraping
from technical_indicators import hmax, hma3
import json
import time

def scale_number_to_three_digits_fixed(number: float) -> float:
    """
    Scale a number so that its integer part has three digits.
    For example:
    - 0.412 -> 412.0
    - 0.025689 -> 259.9
    - 0.000008956 -> 895.6
    - 0.0 -> 0
    :param number: A float number to be scaled.
    :return: The scaled number with three integer digits.
    """
    if number == 0:
        return 0

    # Scale the number to ensure 3 digits before the decimal point
    while number < 100:
        number *= 10

    return round(number, 3)




def generate_signals(ticker_symbols, start_date):
    signals = []
    json_file_path = '/home/sabankara/personal_developing/live_stock_tracking/data/signals.json'

    x = time.time()
    # İlk olarak, start_date'den bugüne kadar olan tüm verileri çek ve sinyalleri hesapla
    combined_df = data_scraping(ticker_symbols, start_date)

    y = time.time()
    print(f"\n\nTime taken to scrape new data: {y - x}\n\n")  # Veri çekme süresini yazdır
    for symbol in ticker_symbols:
        coin_name = symbol.split('-')[0]
        if coin_name not in combined_df.columns:
            continue

        srcx = combined_df[coin_name]
        uptaded_srcx = combined_df[coin_name].apply(scale_number_to_three_digits_fixed)
        lengthx = 36
        a = hmax(uptaded_srcx, lengthx)
        b = hma3(uptaded_srcx, lengthx)

        crossup = (b > a) & (b.shift() < a.shift())
        crossdn = (a > b) & (a.shift() < b.shift())

        combined_df['AL'] = np.where(crossup, 'AL', '')
        combined_df['SAT'] = np.where(crossdn, 'SAT', '')

        for idx, row in combined_df.iterrows():
            if row['AL'] == 'AL' or row['SAT'] == 'SAT':
                signal = {
                    "coin": symbol,
                    "date": row['Date'].strftime('%Y-%m-%d %H:%M:%S'),
                    "signal": "AL" if row['AL'] == 'AL' else "SAT",
                    "price": row[coin_name]
                }
                signals.append(signal)

    # Tüm sinyalleri JSON dosyasına yaz
    with open(json_file_path, 'w') as f:
        json.dump(signals, f, indent=4)

    print(f"Wrote {len(signals)} signals to JSON file.")

    # Artık sonsuz döngüde sadece yeni sinyalleri kontrol edeceğiz
    last_processed_time = combined_df['Date'].max()

    while True:
        time.sleep(60)  # Her 60 saniyede bir kontrol et
 
        z = time.time()
        # last_processed_time'den sonraki verileri çek
        new_data = data_scraping(ticker_symbols, last_processed_time)

        if new_data.empty:
            continue  # Yeni veri yoksa döngünün başına dön

        t = time.time()
        print(f"\n\nTime taken to scrape new data: {t - z}\n\n")


        for symbol in ticker_symbols:
            coin_name = symbol.split('-')[0]
            if coin_name not in new_data.columns:
                continue

            srcx = new_data[coin_name]
            uptaded_srcx = new_data[coin_name].apply(scale_number_to_three_digits_fixed)
            lengthx = 36
            a = hmax(uptaded_srcx, lengthx)
            b = hma3(uptaded_srcx, lengthx)

            crossup = (b > a) & (b.shift() < a.shift())
            crossdn = (a > b) & (a.shift() < b.shift())

            new_data['AL'] = np.where(crossup, 'AL', '')
            new_data['SAT'] = np.where(crossdn, 'SAT', '')

            new_signals = []
            for idx, row in new_data.iterrows():
                if row['AL'] == 'AL' or row['SAT'] == 'SAT':
                    signal = {
                        "coin": symbol,
                        "date": row['Date'].strftime('%Y-%m-%d %H:%M:%S'),
                        "signal": "AL" if row['AL'] == 'AL' else "SAT",
                        "price": row[coin_name]
                    }

                    # Yeni sinyal olup olmadığını kontrol et
                    if signal not in signals:
                        signals.append(signal)
                        new_signals.append(signal)

            # Yeni sinyalleri JSON dosyasına ekle
            if new_signals:
                with open(json_file_path, 'w') as f:
                    json.dump(signals, f, indent=4)
                print(f"Added {len(new_signals)} new signals to JSON file.")

        # last_processed_time'ı güncelle
        last_processed_time = new_data['Date'].max()

# def generate_signals(ticker_symbols, start_date):
#     signals = []

#     # Eğer JSON dosyası zaten varsa, içeriğini yükle
#     json_file_path = '/home/sabankara/personal_developing/live_stock_tracking/data/signals.json'
#     if os.path.exists(json_file_path):
#         with open(json_file_path, 'r') as f:
#             signals = json.load(f)

#     while True:
#         x = time.time()
#         combined_df = data_scraping(ticker_symbols, start_date)
#         y = time.time()
#         print(f"Time taken to scrape data: {y - x}")  # Veri çekme süresini yazdır

#         new_signals = []  # Sadece yeni sinyaller için liste
#         for symbol in ticker_symbols:
#             coin_name = symbol.split('-')[0]
#             if coin_name not in combined_df.columns:
#                 continue

#             srcx = combined_df[coin_name]
#             uptaded_srcx = combined_df[coin_name].apply(scale_number_to_three_digits_fixed)
#             lengthx = 24
#             a = hmax(uptaded_srcx, lengthx)
#             b = hma3(uptaded_srcx, lengthx)

#             crossup = (b > a) & (b.shift() < a.shift())
#             crossdn = (a > b) & (a.shift() < b.shift())

#             combined_df['AL'] = np.where(crossup, 'AL', '')
#             combined_df['SAT'] = np.where(crossdn, 'SAT', '')

#             for idx, row in combined_df.iterrows():
#                 if row['AL'] == 'AL' or row['SAT'] == 'SAT':
#                     signal = {
#                         "coin": symbol,
#                         "date": row['Date'].strftime('%Y-%m-%d %H:%M:%S'),
#                         "signal": "AL" if row['AL'] == 'AL' else "SAT",
#                         "price": row[coin_name]
#                     }

#                     # Yeni sinyal olup olmadığını kontrol et
#                     if signal not in signals:
#                         new_signals.append(0)

#         # Yeni sinyalleri mevcut listeye ekle
#         signals.extend(new_signals)

#         # Yeni sinyalleri JSON dosyasına yaz
#         with open(json_file_path, 'w') as f:
#             json.dump(signals, f, indent=4)

#         print(f"Added {len(new_signals)} new signals to JSON file.")
#         time.sleep(60)


# def generate_signals(ticker_symbols, start_date):
#     signals = []
#     while True:
#         x = time.time()
#         combined_df = data_scraping(ticker_symbols, start_date)
#         y = time.time()
#         print(f"Time taken to scrape data: {y-x}") # print(y-x)
   
#         for symbol in ticker_symbols:
#             coin_name = symbol.split('-')[0]
#             if coin_name not in combined_df.columns:
#                 continue
            
#             srcx = combined_df[coin_name]
#             uptaded_srcx = combined_df[coin_name].apply(scale_number_to_three_digits_fixed)
#             lengthx = 24
#             a = hmax(uptaded_srcx, lengthx)
#             b = hma3(uptaded_srcx, lengthx)
            
#             crossup = (b > a) & (b.shift() < a.shift())
#             crossdn = (a > b) & (a.shift() < b.shift())
            
#             combined_df['AL'] = np.where(crossup, 'AL', '')
#             combined_df['SAT'] = np.where(crossdn, 'SAT', '')
            
#             for idx, row in combined_df.iterrows():
#                 if row['AL'] == 'AL':
#                     signals.append({
#                         "coin": symbol,
#                         "date": row['Date'].strftime('%Y-%m-%d %H:%M:%S'),
#                         "signal": "AL",
#                         "price": row[coin_name]
#                     })
#                 elif row['SAT'] == 'SAT':
#                     signals.append({
#                         "coin": symbol,
#                         "date": row['Date'].strftime('%Y-%m-%d %H:%M:%S'),
#                         "signal": "SAT",
#                         "price": row[coin_name]
#                     })
        
#         with open('/home/sabankara/personal_developing/live_stock_tracking/data/signals.json', 'w') as f:
#             json.dump(signals, f, indent=4)
        
#         time.sleep(60)



start_date = '2024-06-01'

ticker_symbols = [
    "DOGE-USD",
    "BNB-USD",
    "BTC-USD",
    "ETH-USD",
    "SOL-USD",
    "AVAX-USD",
    "SAND-USD",
    "BONK-USD",
    "JUP29210-USD",
    "PORTAL29555-USD",
    "NFP28778-USD",
    "MAV-USD",
    "ID21846-USD",
    "MEM-USD",
    "PIT-USD",
    "ADA-USD",
    "DOT-USD",
    "SHIB-USD",
    "MATIC-USD",
    "XLM-USD",
    "TRX-USD",
    "FTT-USD",
    "ATOM-USD",
    "AAVE-USD",
    "EGLD-USD",
    "CHZ-USD",
    "OCEAN-USD",
    "XRP-USD"]


# Sinyalleri üretin
x = generate_signals(ticker_symbols, start_date)


