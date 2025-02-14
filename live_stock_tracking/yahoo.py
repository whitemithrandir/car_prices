import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import os
import pyarrow.parquet as pq

def data_scraping(ticker_symbols, start_date, parquet_file='/home/sabankara/personal_developing/live_stock_tracking/data/gecmis_veriler.parquet'):
    yesterday = (datetime.now()).strftime('%Y-%m-%d')
    today = (datetime.now() + timedelta(days=+1)).strftime('%Y-%m-%d')
    
    # Boş bir DataFrame başlat
    combined_df = pd.DataFrame()

    # Parquet dosyasını kontrol et
    if os.path.exists(parquet_file):
        historical_df = pd.read_parquet(parquet_file)
        last_historical_date = historical_df['Date'].max()

        crypto_names = [symbol.split('-')[0] for symbol in ticker_symbols]
        missing_cryptos = [crypto for crypto in crypto_names if crypto not in historical_df.columns]

        # Durum kontrolü
        if missing_cryptos:
            print(f"Historical DataFrame eksik kripto isimleri: {missing_cryptos}")

            for crypto in missing_cryptos:
                symbol = next((symbol for symbol in ticker_symbols if symbol.split('-')[0] == crypto), None) # Eksik kripto için doğru sembolü oluştur
                try:
                    stock_data = yf.download(symbol, start=start_date, end=yesterday, progress=False)
        
                    stock_data['Average Price'] = (stock_data['High'] + stock_data['Low']) / 2
                    df_new = stock_data[['Average Price']].rename(columns={'Average Price': crypto})

                    df_new[crypto] = df_new[crypto]
                    df_new.reset_index(inplace=True)
                    
                    # historical_df'yi yeni veriyle birleştir
                    historical_df = pd.merge(historical_df, df_new, on='Date', how='outer')
                    historical_df.to_parquet(parquet_file, index=False)
                except Exception as e:
                    print(f"Error fetching data for {symbol}: {e}")
    
    else:
        last_historical_date = (datetime.now()).strftime('%Y-%m-%d')
        historical_df = pd.DataFrame()
        for symbol in ticker_symbols:
            try:
                stock_data = yf.download(symbol, start=start_date, end=last_historical_date, progress=False)
                coin_name = symbol.split('-')[0]
                df = stock_data[['Close']].rename(columns={'Close': coin_name})
                df[coin_name] = df[coin_name].round(3)
                df.reset_index(inplace=True)
                historical_df = pd.merge(historical_df, df, on='Date', how='outer') if not historical_df.empty else df
            except Exception as e:
                print(e)
                continue
        historical_df.to_parquet(parquet_file, index=False)

    # Bugünün verisini indir
    today_df = pd.DataFrame()
    for symbol in ticker_symbols:
        try:
            stock_data = yf.download(symbol, start=yesterday, end=today, progress=False)
            if stock_data.empty:
                print(f"{today} tarihinde {symbol} için veri yok, atlanıyor.")
                continue
            coin_name = symbol.split('-')[0]
            df = stock_data[['Close']].rename(columns={'Close': coin_name})
            df[coin_name] = df[coin_name].round(3)
            df.reset_index(inplace=True)
            df.rename(columns={'Datetime': 'Date'}, inplace=True)
            today_df = pd.merge(today_df, df, on='Date', how='outer') if not today_df.empty else df
        except Exception as e:
            print(e)
            continue

    # Geçmiş verilerle bugünün verisini birleştir
    if not historical_df.empty:
        combined_df = pd.concat([historical_df, today_df], ignore_index=True)
    else:
        combined_df = today_df

    # Sütunları sıralandır
    cols = ['Date'] + [col for col in combined_df.columns if col != 'Date']
    combined_df = combined_df[cols]

    # Gün sonunda parquet dosyasını güncelle
    last_saved_date = combined_df['Date'].dt.date.max()
    today_date = datetime.now().date()
    if last_saved_date < today_date:
        # Dünün verisini parquet dosyasına ekle
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        yesterday_data = combined_df[pd.to_datetime(combined_df['Date']).dt.strftime('%Y-%m-%d') == yesterday]
        if not yesterday_data.empty:
            # Parquet dosyasına ekleme modu ile kaydet
            combined_df  = pd.concat([historical_df, yesterday_data], ignore_index=True)
            combined_df.to_parquet(parquet_file, index=False)
      

    return combined_df


