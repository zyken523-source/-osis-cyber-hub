import streamlit as st
import sqlite3
import phonenumbers
from phonenumbers import carrier, geocoder

# --- KONFIGURASI HALAMAN (BERANDA) ---
st.set_page_config(page_title="GetContact Clone", page_icon="🕵️‍♂️", layout="centered")

# Custom CSS biar tampilannya keren
st.markdown("""
    <style>
    .main-title { font-size: 40px; font-weight: bold; color: #00ff41; text-align: center; }
    .sub-title { text-align: center; color: #888; margin-bottom: 30px; }
    .result-box { padding: 20px; border-radius: 10px; background-color: #1e1e1e; border: 1px solid #333; text-align: center;}
    </style>
""", unsafe_allow_html=True)

# --- SETUP DATABASE SQLITE ---
def init_db():
    conn = sqlite3.connect('database_kontak.db')
    c = conn.cursor()
    # Tabel utama untuk nyimpen nomor dan nama
    c.execute('''CREATE TABLE IF NOT EXISTS buku_telepon
                 (nomor TEXT PRIMARY KEY, nama TEXT, provider TEXT)''')
    conn.commit()
    conn.close()

def simpan_kontak(nomor, nama):
    conn = sqlite3.connect('database_kontak.db')
    c = conn.cursor()
    try:
        # Parse nomor buat dapet provider
        pn = phonenumbers.parse(nomor, "ID")
        if not phonenumbers.is_valid_number(pn):
            return False, "Nomor tidak valid"
            
        e164 = phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.E164)
        noplus = e164.replace("+", "")
        prov = carrier.name_for_number(pn, "en") or "Unknown"
        
        c.execute("INSERT OR REPLACE INTO buku_telepon (nomor, nama, provider) VALUES (?, ?, ?)", (noplus, nama, prov))
        conn.commit()
        return True, e164
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def cari_nomor(nomor):
    conn = sqlite3.connect('database_kontak.db')
    c = conn.cursor()
    try:
        pn = phonenumbers.parse(nomor, "ID")
        e164 = phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.E164)
        noplus = e164.replace("+", "")
        
        c.execute("SELECT nama, provider FROM buku_telepon WHERE nomor=?", (noplus,))
        hasil = c.fetchone()
        return e164, hasil
    except:
        return None, None
    finally:
        conn.close()

init_db()

# --- UI STREAMLIT ---
st.markdown('<div class="main-title">🕵️‍♂️ GetContact Clone</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Sistem Pencarian Identitas Berbasis Crowdsourcing</div>', unsafe_allow_html=True)

# Bikin Tab Menu
tab_cari, tab_upload, tab_info = st.tabs(["🔍 Cari Nama", "📤 Upload Buku Kontak", "ℹ️ Cara Kerja"])

# ================= TAB CARI =================
with tab_cari:
    st.write("Masukkan nomor HP untuk mencari nama pemiliknya.")
    cari_input = st.text_input("Nomor HP (contoh: 08123456789)", key="cari")
    
    if st.button("Cari Sekarang", type="primary", use_container_width=True):
        if cari_input:
            e164, hasil = cari_nomor(cari_input)
            if e164:
                if hasil:
                    nama, provider = hasil
                    st.markdown(f"""
                        <div class="result-box">
                            <h3 style='color: #00ff41;'>{nama}</h3>
                            <p style='color: #aaa;'>Nomor: {e164} ({provider})</p>
                            <p style='color: #888; font-size: 12px;'>Data ini berasal dari kontak yang di-upload ke sistem.</p>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning(f"Nomor {e164} tidak ditemukan di database. (Belum ada yang meng-upload kontak ini).")
            else:
                st.error("Format nomor tidak valid!")
        else:
            st.info("Masukkan nomor dulu bree.")

# ================= TAB UPLOAD =================
with tab_upload:
    st.write("Tambah data nama & nomor ke database. (Simulasi upload buku kontak).")
    
    with st.form("form_upload", clear_on_submit=True):
        nomor_baru = st.text_input("Nomor HP (contoh: 08123456789)")
        nama_baru = st.text_input("Nama Pemilik (contoh: Budi Santoso)")
        submit = st.form_submit_button("Simpan ke Database")
        
        if submit:
            if nomor_baru and nama_baru:
                sukses, pesan = simpan_kontak(nomor_baru, nama_baru)
                if sukses:
                    st.success(f"Berhasil menyimpan! Nomor {pesan} terdaftar sebagai {nama_baru}.")
                else:
                    st.error(f"Gagal menyimpan: {pesan}")
            else:
                st.warning("Isi nomor dan nama dulu bree!")

# ================= TAB INFO =================
with tab_info:
    st.write("### Kenapa GetContact Bisa Tahu Nama?")
    st.write("""
    Aplikasi seperti GetContact tidak menggunakan sihir atau Google. Mereka menggunakan metode **Crowdsourcing (Gotong Royong)**.
    1. Ketika User A menginstall aplikasi, mereka diminta izin mengakses Buku Kontak HP.
    2. Jika User A menyimpan nomor `08123456789` dengan nama **"Budi"**, data itu dikirim ke server.
    3. Saat User B mencari `08123456789`, server akan menampilkan nama **"Budi"**.
    
    **Kenapa sistem ini kosong di awal?** Karena database ini baru dibuat. Kamu harus mengisi (upload) kontak ke sini agar sistem bisa menampilkan nama.
    
    *Catatan: Streamlit Cloud akan mereset database ini jika server tidur terlalu lama. Untuk production, kamu butuh database cloud seperti Supabase.*
    """)