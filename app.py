import streamlit as st
import time

st.set_page_config(page_title="EquiCity AI", page_icon="🏙️")

st.title("🏙️ EquiCity AI - Iskandar Puteri")
st.markdown("### *Bridging the Digital Façade for Urban Justice*")

zone = st.selectbox("Pilih Lokasi:", ["Medini (Core)", "Skudai / Gelang Patah (Periphery)"])
user_input = st.text_area("Masukkan aduan anda:")

if st.button("Hantar ke EquiCity AI"):
    if user_input:
        # FAKE LOADING: Lakonan supaya nampak macam AI tengah berfikir
        with st.spinner("Menganalisis aduan berdasarkan Spatial Justice..."):
            time.sleep(2) 
            
            st.subheader("Respon Pakar Bandar:")
            
            # LOGIK HARDCODE BERDASARKAN PHD AWAK
            if "Periphery" in zone:
                st.write(f"Menganalisis aduan '{user_input}' untuk kawasan **Skudai / Gelang Patah (Periphery)**.\n\nBerdasarkan prinsip *Infrastructural Justice*, cadangan peruntukan untuk aplikasi pintar **MESTI DITANGGUHKAN**. Keutamaan pihak kerajaan mesti memfokuskan kepada pembaikan infrastruktur asas terlebih dahulu seperti menurap jalan dan membaiki sistem bas. Rakyat tidak mahukan 'digital façade'; mereka mahukan hak asas yang berfungsi.")
            else:
                st.write(f"Menganalisis aduan '{user_input}' untuk kawasan **Medini (Core)**.\n\nMemandangkan infrastruktur asas di kawasan ini sudah matang, EquiCity AI mencadangkan pelaksanaan pengoptimuman bandar pintar tahap tinggi seperti **Sistem Parkir AI** dan **Pemantauan Keselamatan IoT**.")
                
            st.divider()
            st.caption("Berdasarkan Framework PhD: Just Smart Mobility (Bakhtiar et al., 2026)")
    else:
        st.warning("Sila tulis sesuatu dalam kotak aduan.")