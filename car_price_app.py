import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from sqlalchemy import create_engine
import yfinance as yf

# streamlit run app.py --server.port 8524
gold_symbol  = 'GC=F'
usdtry_symbol = 'USDTRY=X'
bist100_symbol = "XU100.IS"
btc_symbol = "BTC-USD"

gold_data  = yf.download(gold_symbol, start='2020-01-01', interval='1mo')
data = yf.download(usdtry_symbol, start='2020-01-01', interval='1mo')
bist100  = yf.download(bist100_symbol, start='2020-01-01', interval='1mo')
btc  = yf.download(btc_symbol, start='2020-01-01', interval='1mo')

bist100.iloc[:6] = bist100.iloc[:6]/10


gold_data['Gram_Altin_Try'] = (gold_data['Close'] / 31.1035) * data['Close'] #TODO buraya bakmalısın
btc["BTC_Try"] = btc["Close"] *data["Close"]

usd_try_monthly = data[['Close']].reset_index()
gold_data_monthly = gold_data.reset_index()
bist100_monthly = bist100[['Close']].reset_index()
btc_monthly = btc.reset_index()

engine = create_engine('sqlite:////home/sabankara/personal_developing/car_price/car_prices_test.db')

st.title('Araç Değerleri, Dolar Bazında Analiz ve Kendi Aralarında Kıyaslama')

years = [str(year) for year in range(2010, 2026)]

if 'selected_vehicles' not in st.session_state:
    st.session_state.selected_vehicles = []

if 'df_combined' not in st.session_state:
    st.session_state.df_combined = pd.DataFrame()

if 'df_combined_dollar' not in st.session_state:
    st.session_state.df_combined_dollar = pd.DataFrame()



col1, col2, col3 = st.columns(3)

with col1:
    selected_year = st.selectbox('Araç Yaşı', years, key='selected_year_1')


with col2:
    query = f"SELECT DISTINCT `Marka Adı` FROM car_prices_test WHERE `{selected_year}` != 0"
    df_filtered = pd.read_sql(query, con=engine)
    brands = df_filtered['Marka Adı'].unique()
    selected_brand = st.selectbox('Araç Markası', brands, key='selected_brand_1')

with col3:
    query = f"SELECT DISTINCT `Tip Adı` FROM car_prices_test WHERE `Marka Adı` = ? AND `{selected_year}` != 0"
    df_filtered = pd.read_sql(query, con=engine, params=(selected_brand,))
    models = np.sort(df_filtered['Tip Adı'].unique())
    selected_model = st.selectbox('Araç Modeli', models, key='selected_model_1')

if st.button('Bu aracı ekle'):
    vehicle_data = (selected_year, selected_brand, selected_model)
    if vehicle_data not in st.session_state.selected_vehicles:
        st.session_state.selected_vehicles.append(vehicle_data)
        st.success(f'{selected_year} {selected_brand} ({selected_model}) eklendi!')

if st.session_state.selected_vehicles:
    st.markdown("### Seçilen Araçlar:")

    for i, (year, brand, model) in enumerate(st.session_state.selected_vehicles):
        col1, col2, col3, col4 = st.columns([7, 1, 1, 1])
        with col1:
            st.markdown(f"""
            <div style='background-color: #f0f0f5; padding: 10px; margin: 5px; border-radius: 5px; font-size: 14px;'>
                <strong style='font-size: 16px;'>Araba {i+1}:</strong> 
                <span style='color: #0066cc; font-size: 14px;'>{year}</span> 
                <span style='color: #ff6600; font-size: 14px;'>{brand}</span> 
                - <span style='color: #33cc33; font-size: 14px;'>{model}</span>
            </div>
            """, unsafe_allow_html=True)
        
        # Yukarı taşı butonu
        with col2:
            if st.button('⬆️', key=f'up_{i}') and i > 0:
                # Şu anki öğeyi bir üstteki ile değiştir
                st.session_state.selected_vehicles[i], st.session_state.selected_vehicles[i-1] = \
                    st.session_state.selected_vehicles[i-1], st.session_state.selected_vehicles[i]
                st.rerun()
        
        # Aşağı taşı butonu
        with col3:
            if st.button('⬇️', key=f'down_{i}') and i < len(st.session_state.selected_vehicles) - 1:
                # Şu anki öğeyi bir alttaki ile değiştir
                st.session_state.selected_vehicles[i], st.session_state.selected_vehicles[i+1] = \
                    st.session_state.selected_vehicles[i+1], st.session_state.selected_vehicles[i]
                st.rerun()

        # Sil butonu
        with col4:
            if st.button('Sil', key=f'delete_{i}'):
                st.session_state.selected_vehicles.pop(i)
                st.rerun()


else:
    st.markdown("### Henüz araç seçilmedi.")

if st.session_state.selected_vehicles:
    selected_data = []
    for year, brand, model in st.session_state.selected_vehicles:
        query = """
        
        SELECT `Marka Adı`, `Tip Adı`, `{}` as price, `date` FROM car_prices_test 
        WHERE `Marka Adı` = ? 
        AND `Tip Adı` = ? 
        AND `{}` != 0
        """.format(year, year)

        df_vehicle = pd.read_sql(query, con=engine, params=(brand, model))
        df_vehicle['date'] = pd.to_datetime(df_vehicle['date'], format='%Y%m')

        df_vehicle['Tip Adı'] = df_vehicle['Tip Adı'] + " (" + year + ")"
        selected_data.append(df_vehicle)

    st.session_state.df_combined = pd.concat(selected_data).sort_values(by="date")
    st.session_state.df_combined_dollar = st.session_state.df_combined.copy()


    usd_try_monthly.rename(columns={'Close': 'Dolar_Close'}, inplace=True)
    

    gold_data_monthly.rename(columns={'Gram_Altin_Try': 'Gold_Close'}, inplace=True)
    gold_data_monthly = gold_data_monthly.drop(columns=['Open', 'High', 'Low', 'Adj Close', 'Volume'])

    bist100_monthly.rename(columns={'Close': 'Bist100_Close'}, inplace=True)

    btc_monthly.rename(columns={'BTC_Try': 'BTC_Close'}, inplace=True)
    btc_monthly = btc_monthly.drop(columns=['Open', 'High', 'Low', 'Adj Close', 'Volume'], errors="ignore")

    # bist100_monthly = bist100_monthly.drop(columns=['Open', 'High', 'Low', 'Adj Close', 'Volume'])



    # USD/TRY kuru ile birleştirme
    st.session_state.df_combined_dollar = pd.merge_asof(
        st.session_state.df_combined_dollar.sort_values('date'), 
        usd_try_monthly.sort_values('Date'), 
        left_on='date', 
        right_on='Date',
        suffixes=('', '_usd')  # USD/TRY için suffix ekledik
    )

    # Gram altın fiyatı ile birleştirme
    st.session_state.df_combined_dollar = pd.merge_asof(
        st.session_state.df_combined_dollar.sort_values('date'), 
        gold_data_monthly.sort_values('Date'), 
        left_on='date', 
        right_on='Date',
        suffixes=('', '_gold')  # Gram altın için suffix ekledik
    )

    # BIST100 fiyatı ile birleştirme
    st.session_state.df_combined_dollar = pd.merge_asof(
        st.session_state.df_combined_dollar.sort_values('date'), 
        bist100_monthly.sort_values('Date'), 
        left_on='date', 
        right_on='Date',
        suffixes=('', '_bist')  # BIST100 için suffix ekledik
    )

    # BTC fiyatı ile birleştirme
    st.session_state.df_combined_dollar = pd.merge_asof(
        st.session_state.df_combined_dollar.sort_values('date'), 
        btc_monthly.sort_values('Date'), 
        left_on='date', 
        right_on='Date',
        suffixes=('', '_btc')  # BTC için suffix ekledik
    )

 
    st.session_state.df_combined_dollar["price$"] = np.where(st.session_state.df_combined_dollar["price"] != 0, st.session_state.df_combined_dollar["price"] / st.session_state.df_combined_dollar['Dolar_Close'], 0)
    st.session_state.df_combined_dollar["gold"] =   np.where(st.session_state.df_combined_dollar["price"] != 0, st.session_state.df_combined_dollar["price"] / st.session_state.df_combined_dollar['Gold_Close'], 0)
    st.session_state.df_combined_dollar["bist100"] = np.where(st.session_state.df_combined_dollar["price"] != 0, st.session_state.df_combined_dollar["price"] / st.session_state.df_combined_dollar['Bist100_Close'], 0)
    st.session_state.df_combined_dollar["btc"] = np.where(st.session_state.df_combined_dollar["price"] != 0, st.session_state.df_combined_dollar["price"] / st.session_state.df_combined_dollar['BTC_Close'], 0)

    base_car = st.session_state.selected_vehicles[0]
    df_pivot = st.session_state.df_combined_dollar.pivot_table(values="price", index="date", columns="Tip Adı", aggfunc="sum")
    tip_list =  st.session_state.df_combined_dollar["Tip Adı"].drop_duplicates().to_list()

    if len(tip_list) > 1:
        for tip in set(tip_list) - {base_car[2] + " (" + base_car[0] + ")"}:
            df_pivot[tip] = df_pivot[tip] / df_pivot[base_car[2] + " (" + base_car[0] + ")"]
    df_pivot[base_car[2] + " (" + base_car[0] + ")"] = 1
    df_pivot_reset = df_pivot.reset_index()

    # Tabları ekrana eklemeden önce DataFrame'lerin boş olmadığını kontrol edin
    if not st.session_state.df_combined.empty and not st.session_state.df_combined_dollar.empty:
        tab_tl, tab_dol, tab_gold, tab_btc, tab_bist, tab_parite = st.tabs(["TL", "Dolar", "Altın","BTC","BIST100", "Parite"])
        
        # TL grafiği
        fig_tl = px.line(st.session_state.df_combined_dollar, x='date', y="price", 
                         title='Price over Time in TL', color="Tip Adı", height=700)
        fig_tl.update_traces(line=dict(width=3))
        
        # Dolar grafiği
        fig_dollar = px.line(st.session_state.df_combined_dollar, x='date', y="price$", 
                             title='Price over Time in Dollar', color="Tip Adı", height=700)
        fig_dollar.update_traces(line=dict(width=3))

        # Altın Grafiği
        fig_gold = px.line(st.session_state.df_combined_dollar, x='date', y="gold", 
                           title='Price over Time in Altın', color="Tip Adı", height=700)
        fig_gold.update_traces(line=dict(width=3))

        # BTC grafiği
        fig_btc = px.line(st.session_state.df_combined_dollar, x='date', y="btc", 
                          title='Price over Time in BTC', color="Tip Adı", height=700)
        fig_btc.update_traces(line=dict(width=3))

        # BIST100 grafiği
        fig_bist = px.line(st.session_state.df_combined_dollar, x='date', y="bist100", 
                           title='Price over Time in BIST100', color="Tip Adı", height=700)
        fig_bist.update_traces(line=dict(width=3))




        # Parite grafiği
        if len(tip_list) > 1:
            fig_parite = px.line(df_pivot_reset, x='date', y=df_pivot_reset.columns[1:], title=f'{base_car[2]} paritesi ref alındı', height=700)
            fig_parite.update_traces(line=dict(width=3))
        
        
        with tab_tl:
            st.plotly_chart(fig_tl)
        with tab_dol:
            st.plotly_chart(fig_dollar)

        with tab_gold:
            st.plotly_chart(fig_gold)

        with tab_btc:
            st.plotly_chart(fig_btc)

        with tab_bist:
            st.plotly_chart(fig_bist)

        with tab_parite:
            if len(tip_list) > 1:
                st.plotly_chart(fig_parite)
            else:
                st.write("Parite grafı, en az iki marka seçilmelidir.")


# col1_1, col2_2 = st.columns(2)


# with col1_1:
#     try:
#         if not st.session_state.df_combined.empty:
#             st.session_state.df_combined
#     except NameError:
#         pass

# with col2_2:
#     try:
#         if not st.session_state.df_combined_dollar.empty:
#             st.session_state.df_combined_dollar

#     except NameError:
#         pass

