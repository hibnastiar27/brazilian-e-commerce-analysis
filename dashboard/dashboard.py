import os
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import folium
from streamlit_folium import st_folium
from folium.plugins import HeatMap

# # CEK ROOT PATH CLOUD ATAU LOCAL
# if "STREAMLIT_SERVER" in os.environ or "STREAMLIT_RUNTIME" in os.environ:  # Cek variabel lingkungan untuk Streamlit Cloud
#     root_folder = "dashboard/data"  # root path folder cloud streamlit
# else:
#     root_folder = "data"  # root path folder local
    
# # DEBUGIG
# print(f"Os Env: {os.environ}")
# print(f"Root folder: {root_folder}")

# FUNGSI UNTUK MENENTUKAN PATH DATASET
def tangkap_path_file(file_name):
  return f"/dasboard/data/{file_name}" if os.path.isfile(f"/dasboard/data/{file_name}") else f"data/{file_name}"

# INISIALISASI DATA
clean_df_geolocation = pd.read_csv("/dashboard/data/clean_df_geolocation.csv")
clean_df_sellers = pd.read_csv("/dashboard/data/clean_df_sellers.csv")
clean_gabung_rating_waktu_pengiriman = pd.read_csv("/dashboard/data/clean_gabung_rating_waktu_pengiriman.csv")
clean_gabung_metode_bayar_kota = pd.read_csv("/dashboard/data/clean_gabung_metode_bayar_kota.csv")
clean_gabung_metode_bayar_nilai_transaksi = pd.read_csv("/dashboard/data/clean_gabung_metode_bayar_nilai_transaksi.csv")

# ---
# MEMBUAT FUNGSI UNTUK MENYIAPKAN DATASET KE VISUAL
# ---
def create_gabung_rating_waktu_pengiriman(df):
  clean_gabung_rating_waktu_pengiriman_cols = [
  'order_purchase_timestamp',
  'order_delivered_customer_date',
  'order_estimated_delivery_date',
  ]

  # Memastikan datanya date bukan string
  df[clean_gabung_rating_waktu_pengiriman_cols] = clean_gabung_rating_waktu_pengiriman[clean_gabung_rating_waktu_pengiriman_cols].apply(
    pd.to_datetime, errors='coerce'
  )
  
  # menghitung waktu_pengiriman dengan satuan hari
  df['waktu_pengiriman'] = (
    df['order_delivered_customer_date'] - df['order_purchase_timestamp']
  ).dt.days
  
  # Korelasi antara waktu pengiriman dengan rating
  korelasi_rating_waktu_pengiriman = df[['waktu_pengiriman', 'review_score']].corr()
  
  return korelasi_rating_waktu_pengiriman

def create_gabung_metode_bayar_kota(df):
  # menggunakan size untuk menghitung metode pembayaran pada setiap kota
  jumlah_pembayaran_kota = df.groupby(
    ['customer_city','payment_type']
  ).size().reset_index(name='jumlah')
  
  # menghitung semua total transaksi di setiapkota dan mengurutkan dari yang terbesar
  total_transaksi_kota = jumlah_pembayaran_kota.groupby('customer_city')['jumlah'].sum().reset_index(name='total_transaksi')
  total_transaksi_kota.sort_values('total_transaksi', ascending=False)
    
  # menggabungkan total trans ke dalam jumlah pembayaran dan disorting tertinggi
  metode_bayar_kota = jumlah_pembayaran_kota.merge(total_transaksi_kota, on='customer_city')
  metode_bayar_kota.sort_values(['jumlah', 'total_transaksi'],ascending=False)
  
  metode_bayar_kota['persentase'] = (
    metode_bayar_kota['jumlah'] / metode_bayar_kota['total_transaksi'] * 100
  ) 

  metode_bayar_kota.sort_values(['jumlah', 'total_transaksi'],ascending=False)
  
  # mengelompokkan kota dengan total transaksi dan hanya mengambil index dari 10 data saja yang tertinggi
  kota_tertinggi = metode_bayar_kota.groupby('customer_city')['total_transaksi'].sum().sort_values(ascending=False).head(10).index

  # Filter data hanya kota kota di varibel 'kota_tertinggi' dengan menggunakan isin()
  kota_tertinggi = metode_bayar_kota[metode_bayar_kota['customer_city'].isin(kota_tertinggi)]
  kota_tertinggi.head()
  
  # Mengurutkan dengan total transaksi dan persentase tertinggi dulu
  metode_bayar_tertinggi = kota_tertinggi.sort_values(
      by=['total_transaksi', 'persentase'], ascending=[False, False]
  ).reset_index(drop=True)

  return metode_bayar_tertinggi

def create_gabung_metode_bayar_nilai_transaksi(df):
  # menggabungkan menghitung rata rata
  rata_transaksi = df.groupby(
    ['customer_city', 'payment_type']
  )['payment_value'].mean().reset_index()

  rata_transaksi.head()
  # mengelompokan tipe pembayaran dengan nilai transaksi
  kota_tertinggi_nilai_transaksi = rata_transaksi.loc[rata_transaksi.groupby('payment_type')['payment_value'].idxmax()]
  return kota_tertinggi_nilai_transaksi.sort_values(
    'payment_value',
    ascending=False
  )
  
def create_jumlah_seller_koordinat(df_seller,df_geo):
  # menghitung jumlah seller pada setiap kota
  jumlah_seller = df_seller['seller_city'].value_counts().reset_index()
  jumlah_seller.columns = ['city', 'jumlah_seller']
  
  # Menggabungkan jumlah seller dengan geolocation yang sudah di cleaning dan dmemastikan bahwa seluruh data tidak ada null nya dengan dropna()
  jumlah_seller_koordinat = pd.merge(
    jumlah_seller,
    df_geo[['geolocation_city', 'geolocation_lat', 'geolocation_lng']],
    left_on='city',
    right_on='geolocation_city',
    how='left'
  ).dropna().reset_index()
  
  return jumlah_seller_koordinat

# ---
# SETUP JUDUL TITLE PAGE DAN TITLE KONTEN
# ---
st.set_page_config(page_title="Dashboard E-Commerce By Aria :sparkles:")
st.title('Dashboard E-Commerce By Aria :sparkles:')

# ---
# Sidebar
# ---
with st.sidebar:
  st.sidebar.title("Tentang Saya")
  st.sidebar.markdown("Nur Aria Hibnastiar")
  st.sidebar.markdown("[nurhibnastiar1@gmail.com](nurhibnastiar1@gmail.com)")
  
  st.sidebar.title("Menu")
  
  # mengambil seluruh payment type yg unik
  list_payment_type = clean_gabung_metode_bayar_kota['payment_type'].unique()
  # Mengambil tipe pembayaran dari multiselect
  select_payment_type = st.multiselect(
    label="Tipe Pembayaran",
    placeholder="Pilih tipe pembayaran",
    options=(list_payment_type),
    default=list_payment_type
  )
  
  # order_estimated_delivery_date
  waktu_min = clean_gabung_rating_waktu_pengiriman['order_estimated_delivery_date'].min()
  waktu_max = clean_gabung_rating_waktu_pengiriman['order_estimated_delivery_date'].max()
  
  # Mengambil awal_waktu & akhir_waktu dari date_input
  awal_waktu, akhir_waktu = st.date_input(
    label='Rentang Waktu (estimated_delivery_date)',
    min_value=waktu_min,
    max_value=waktu_max,
    value=[waktu_min, waktu_max]
  )
# ---
# Filtering Data supaya dinamis mengikuti input user 
# ---
fix_gabung_rating_waktu_pengiriman = clean_gabung_rating_waktu_pengiriman[
  (clean_gabung_rating_waktu_pengiriman["order_estimated_delivery_date"] >= str(awal_waktu)) & 
  (clean_gabung_rating_waktu_pengiriman["order_estimated_delivery_date"] <= str(akhir_waktu))
]
fix_gabung_metode_bayar_kota = clean_gabung_metode_bayar_kota[clean_gabung_metode_bayar_kota['payment_type'].isin(select_payment_type)]
fix_gabung_metode_bayar_nilai_transaksi = clean_gabung_metode_bayar_nilai_transaksi[clean_gabung_metode_bayar_nilai_transaksi['payment_type'].isin(select_payment_type)]

# ---
# Proses membuat data
# ---
df_gabung_rating_waktu_pengiriman = create_gabung_rating_waktu_pengiriman(fix_gabung_rating_waktu_pengiriman)
df_gabung_metode_bayar_kota = create_gabung_metode_bayar_kota(fix_gabung_metode_bayar_kota)
df_gabung_metode_bayar_nilai_transaksi = create_gabung_metode_bayar_nilai_transaksi(fix_gabung_metode_bayar_nilai_transaksi)
df_jumlah_seller_koordinat = create_jumlah_seller_koordinat(clean_df_sellers, clean_df_geolocation)

# ---
# 1. Apakah waktu pengiriman mempengaruhi rating? 
# ---
st.subheader('Korelasi Waktu Pengiriman dan Rating')
plt.figure(figsize=(10, 4))
sns.heatmap(data=df_gabung_rating_waktu_pengiriman, annot=True, cmap='Reds_r', fmt='.2f')
plt.title('Heatmap Hubungan antara Waktu Pengiriman dan Rating')
st.pyplot(plt)

# ---
# 2. Metode pembayaran apa yang sering di gunakan di setiap kota, dan berapa persentase tertinggi di setiap kota?
# ---
st.subheader('Metode Pembayaran Terpopuler di Kota')

plt.figure(figsize=(12, 6))
plt.title('Metode Pembayaran Terpopuler di Kota dengan Transaksi Tertinggi')
plt.xlabel('Nama Kota')
plt.ylabel('Persentase Penggunaan (%)')
plt.xticks(rotation=25)
plt.legend(title='Metode Pembayaran')

sns.barplot(data=df_gabung_metode_bayar_kota, x='customer_city', y='persentase', hue='payment_type', palette='Reds_r')
# menampilkan persentase setiap barnya
for balok in plt.gca().containers:
   plt.gca().bar_label(balok, fmt='%.1f%%', padding=3)
   
st.pyplot(plt)

# ---
# 3. Kota mana yang memiliki rata-rata nilai transaksi tertinggi untuk masing-masing metode pembayaran?
# ---
st.subheader('Kota Dengan Rata Rata Transaksi Tertinggi dengan metode pembayaran')
kota_tertinggi_nilai_transaksi = df_gabung_metode_bayar_nilai_transaksi.sort_values('payment_value',ascending=False).reset_index()

# Visualisasi bar chart horizontal
plt.figure(figsize=(10, 6))
plt.title('Kota Dengan Rata Rata Nilai Transaksi Tertinggi')
plt.xlabel('Rata Rata Nilai Transaksi')
plt.ylabel('Kota')
plt.legend(title='Metode Pembayaran')
plt.tight_layout()

sns.barplot(data=kota_tertinggi_nilai_transaksi, x='payment_value', y='customer_city', hue='payment_type', palette='Reds_r')

st.pyplot(plt)


# ---
# 4. Gimana sebaran seller di berbagai wilayah dan apakah ada area dengan seller terbanyak? (Nomor 4)
# ---
st.subheader('Persebaran Seller di Wilayah Brazil')
# konversi nilai dari latitude, longtitude dan jumlah seller ke dalam format list
heat_data = df_jumlah_seller_koordinat[['geolocation_lat', 'geolocation_lng', 'jumlah_seller']].values.tolist()

# inisilaisasi folum map dengan location sesuai koordinat brazil
map_seller = folium.Map(location=[-22.90, -47.06], zoom_start=5)

# menggunakan heatmap dengan data list dari heat_map dengan radius map hanya 20 dengan max zoom 13x
HeatMap(heat_data, radius=25, max_zoom=13).add_to(map_seller)

# Supaya center ke tengah
with st.container():
  st_folium(map_seller, width="100%", height=500)