import pandas as pd
from sqlalchemy import create_engine
import glob
import os
db_path = '/home/sabankara/personal_developing/car_price/car_prices_test.db'
db_directory = os.path.dirname(db_path)

if not os.path.exists(db_directory):
    os.makedirs(db_directory)

# SQLite veritabanı bağlantısı oluşturma
engine = create_engine(f'sqlite:///{db_path}')
print(engine)
file_paths = glob.glob('/home/sabankara/personal_developing/car_price/data/*.xlsx')


def extract_date(file_path):
    """
    Dosya yolundan dosya adını alır ve ilk 6 karakteri (YYYYMM) 
    çıkararak sayısal bir değer olarak döndürür.
    """
    base = os.path.basename(file_path)
    date_str = base[:6]  # Örnek: "202104"
    return int(date_str)  # int dönüşümü, doğru sıralama için

# Dosya listesini artan tarih sırasına göre sıralama
sorted_files = sorted(file_paths, key=extract_date)

# sorted_files = sorted_files[-3:]

if sorted_files:
    first_file = sorted_files[0]
    df = pd.read_excel(first_file)

    df.columns = df.iloc[0]
    df = df.drop(0).reset_index(drop=True)

    df['date'] = first_file.split('/')[-1][:6]

    df.columns = df.columns.map(str)

    for year in range(2011, 2026):  # 2011-2025 arasındaki tüm yılları dahil et
        year_str = str(year)
        if year_str not in df.columns:
            df[year_str] = 0  # Eksik sütunları 0 ile doldur

    # **Veritabanını oluştururken, ilk dosya ile tüm sütunları belirleyelim**
    df.to_sql('car_prices_test', con=engine, if_exists='replace', index=False)
    print(f"İlk dosya ({first_file}) ile veritabanı oluşturuldu.")


for file_path in sorted_files:
    print(file_path,"\n")


    # Excel dosyasını oku
    df = pd.read_excel(file_path)

    # İlk satırı kolon isimleri olarak al ve sıfırdan indeksle
    df.columns = df.iloc[0]
    df = df.drop(0).reset_index(drop=True)
    
    # Dosya adından tarih bilgisini al ve yeni bir kolon olarak ekle
    year_month = file_path.split('/')[-1][:6]  # Örn: '202303' -> '2023-03'
    df['date'] = year_month
    df.columns = df.columns.map(str)

    df.info()
    # Veriyi SQL tablosuna ekle
    df.to_sql('car_prices_test', con=engine, if_exists='append', index=False)