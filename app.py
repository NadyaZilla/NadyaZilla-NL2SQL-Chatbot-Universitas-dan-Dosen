import streamlit as st
import pandas as pd
import sqlite3
import json
import re
import random
import io
import os

import streamlit.components.v1 as components
from streamlit_mic_recorder import speech_to_text

from pathlib import Path

from prompt import SYSTEM_PROMPT
from schema import DATABASE_SCHEMA
from dotenv import load_dotenv
from llama_index.llms.groq import Groq

# ===== CONFIG =====
st.set_page_config(page_title="AI Dosen", page_icon="🎓", layout="wide")

# ===== STATE =====
if "page" not in st.session_state:
    st.session_state.page = "Home"

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_count" not in st.session_state:
    st.session_state.chat_count = 0

# ===== NAVIGASI TAB =====
if "menu" not in st.session_state:
    st.session_state.menu = "🏠 Home"

menu = st.segmented_control(
    "Navigasi",
    ["🤖 Chatbot", "🏠 Home", "ℹ️ About", "🗂️ Sistem AI"],
    default=st.session_state.menu
)
    
st.divider()

# ===== SIDEBAR KHUSUS CHATBOT =====
with st.sidebar:

    col1, col2, col3 = st.columns([1,2,1])

    with col2:
        st.image("logo.png", width=90)

    st.divider()

    # ================= CHATBOT =================
    if menu == "🤖 Chatbot":

        st.caption("AI Dosen Assistant")

        welcome = [
            "Jumlah dosen",
            "Jumlah fakultas",
            "Tampilkan data dosen",
            "Grafik dosen dan gaji"
        ]

        st.success(random.choice(welcome))

        input_suara = speech_to_text(
            language='id',
            start_prompt="🎤 Mulai",
            stop_prompt="⏹ Selesai",
            key=f"tts_{st.session_state.chat_count}",
            use_container_width=True
        )

        model = st.selectbox(
            "Model AI",
            [
                "Llama-3.1-8b-instant",
                "Llama-3.3-70b-versatile",
                "meta-llama/llama-4-scout-17b-16e-instruct",
                "openai/gpt-oss-120b"
            ]
        )

        temperature = st.slider(
            "Temperature",
            0.0,
            1.0,
            0.1,
            0.05
        )

        if st.button("Reset Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    # ================= HOME =================
    elif menu == "🏠 Home":

        st.success("Home Page")

        st.caption("AI Analisis Data Dosen")

    # ================= DATABASE =================
    elif menu == "🗂️ Sistem AI":

        st.info("Database System")

        st.caption("SQLite Connected")


# ===== HOME =====
if menu == "🏠 Home":
    st.title("🎓 AI Analisis Data Dosen Universitas")
    st.write("Asisten AI untuk membantu analisis data dosen secara cepat dan interaktif.")

    st.divider() 
    st.header("🤖 Apa yang Bisa Dilakukan Chatbot?") 
    st.write(""" Chatbot ini dapat membantu Anda untuk:\n 
            - Menampilkan data dosen, fakultas, dan jabatan\n 
            - Menjawab pertanyaan berbasis data (contoh: jumlah dosen, gaji tertinggi)\n
            - Membuat visualisasi data (bar chart, line chart, dll)\n
            - Menampilkan foto dosen\n
            - Mengunduh data dalam format CSV\n
            - Memberikan insight singkat dari data """)
    
    st.header("⚙️ Cara Kerja Chatbot") 
    st.write(""" 1. Anda mengajukan pertanyaan (teks atau suara)\n
            2. AI akan memahami pertanyaan Anda\n
            3. Sistem akan mengubah pertanyaan menjadi query SQL\n
            4. Data diambil dari database universitas\n
            5. Hasil ditampilkan dalam bentuk:\n
                - Teks penjelasan\n
                - Tabel data\n
                - Grafik (jika diperlukan)\n
            6. AI memberikan insight singkat dari data """) 
    
    st.header("🗂️ Data yang Bisa Diakses") 
    st.write(""" Chatbot ini terhubung dengan database universitas yang berisi:\n 
            - Data dosen (nama, status, jabatan)\n 
            - Data fakultas\n
            - Data remunerasi/gaji dosen\n
            - Data foto dosen """) 
    
    st.divider()
    st.header("📊 Contoh Data dari Database")

    try:
        with sqlite3.connect("universitas.db") as conn:

            st.subheader("👨‍🏫 Data Dosen")
            df_dosen = pd.read_sql_query("SELECT * FROM dosen LIMIT 5", conn)
            st.dataframe(df_dosen, use_container_width=True)

            st.subheader("🏫 Data Fakultas")
            df_fakultas = pd.read_sql_query("SELECT * FROM fakultas LIMIT 5", conn)
            st.dataframe(df_fakultas, use_container_width=True)

            st.subheader(" Jabatan Fungsional")
            df_jabatan = pd.read_sql_query("SELECT * FROM jabatan_fungsional LIMIT 5", conn)
            st.dataframe(df_jabatan, use_container_width=True)

            st.subheader("💰 Data Remunerasi")
            df_remun = pd.read_sql_query("SELECT * FROM remunerasi LIMIT 5", conn)
            st.dataframe(df_remun, use_container_width=True)

    except Exception as e:
        st.error(f"Gagal mengambil data: {e}")

    st.info("💡 Contoh pertanyaan: 'Siapa dosen dengan gaji terbesar?'") 
    st.divider()

    if st.button("🚀 Masuk ke Chatbot"):
        st.session_state.menu = "🤖 Chatbot"
        st.rerun()

# ===== CHATBOT =====
if menu == "🤖 Chatbot":
    model = st.session_state.get("model")
    temperature = st.session_state.get("temperature")
    input_suara = st.session_state.get("input_suara")

    load_dotenv()

    @st.cache_data(show_spinner=False)
    def buat_kesimpulan(pertanyaan, data_json, model, temperature):
        tabel_data = pd.read_json(io.StringIO(data_json))
        if tabel_data.empty:
            return "Maaf, data yang dicari tidak ditemukan dalam database kami."
        try:
            contoh_data = tabel_data.to_string(index=False)
            final_prompt = f""" 
    [TUGAS]
    Kamu adalah AI analis data dosen universitas yang teliti, akurat, dan sangat patuh aturan.

    [DATA]
    {contoh_data}
    [AKHIR DATA]

    [PERTANYAAN]
    {pertanyaan}

    [ATURAN KETAT - WAJIB 100% PATUH]

    1. SUMBER DATA:
    - SELALU gunakan data yang ada di [DATA]. 
    - Jika ada data di [DATA], jawab langsung berdasarkan data tersebut. 
    - JANGAN PERNAH bilang "tidak ditemukan" atau "maaf" jika ada minimal 1 baris data.

    2. LOGIKA KHUSUS DOSEN (WAJIB DIPAHAMI DALAM PIKIRAN):
    - "Gaji terbesar" → total_remunerasi paling besar
    - "Gaji terkecil" → total_remunerasi paling kecil

    3. KONDISI DATA KOSONG:
    - Jika [DATA] benar-benar kosong (tidak ada baris data sama sekali) → jawab:
        "Maaf, tidak menemukan data yang sesuai."
        
    4. FORMAT JAWABAN:
    - Hanya 1 kalimat
    - Maksimal 15 kata
    - Bahasa Indonesia santai, tegas, tanpa basa-basi
    - Langsung ke inti (tidak perlu penjelasan)

    5. PRIORITAS JAWABAN:
    - Jika ada nama → fokus ke nama
    - Jika lebih dari 1 hasil → sebut jumlahnya
    
    Contoh jawaban yang benar:
        - Dosen dengan gaji paling besar adalah Hana Kusuma Lestari, S.E., M.M., Dr
        - Dosen dengan gaji paling kecil adalah Prof. Dr. Abdul Rizal Adompo, S.S.T., M.T

    Jawablah sekarang.
    """

            llm = Groq(model=model, api_key=st.secrets["GROQ_API_KEY"], temperature=temperature) 
            # llm = Groq(model=model, api_key=os.getenv("GROQ_API_KEY"), temperature=temperature) ====== untuk .env
            return llm.complete(final_prompt).text.strip()
        except Exception:
            return f"Berhasil menarik {len(tabel_data)} baris data"
        
    def buat_riwayat_chat():
        history = []
        for msg in st.session_state.messages[-16:]:
            if msg["role"] == "user":
                history.append(f"User: {msg['content']}")
            elif msg["role"] == "assistant" and not msg.get("error"):
                sql_part = " (SQL digunakan)" if msg.get('sql') else ""
                history.append(f"Assistant: {msg['content']}{sql_part}")
        return "\n".join(history) if history else "Belum ada percakapan sebelumnya"

    def text_to_speech(text):
        if not text:
            return
        
        clean_text = re.sub(r'[*💡📊\n\r]', ' ', text).replace("'", "'").strip()
        if not clean_text:
            return
        js_code = f"""
        <script>
            (function() {{
                // Hentikan semua speech yang sedang berjalan
                if (window.speechSynthesis) {{
                    window.speechSynthesis.cancel();
                }}
                var msg = new SpeechSynthesisUtterance('{clean_text}');
                msg.lang = 'id-ID'
                window.speechSynthesis.speak(msg);
            }})();
        </script>
        """
        components.html(js_code, height=0)

    st.set_page_config(page_title="AI Analisis Data Dosen", page_icon="🎓", layout="wide")

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "db_path" not in st.session_state:
        st.session_state.db_path = "universitas.db"
    if "last_processed" not in st.session_state:
        st.session_state.last_processed = None
    if "chat_count" not in st.session_state:
        st.session_state.chat_count = 0

    # with st.sidebar:
    #     col1, col2, col3 = st.columns([1, 2, 1])
    #     with col2:
    #         st.image("logo.png", width=100)
        
    #     welcome = [
    #         "Jumlah dosen",
    #         "Jumlah fakultas",
    #         "Tampilkan data dosen",
    #         "Tampilkan grafik barchart dosen beserta gaji",
    #         "Tampilkan data dosen dengan status DPK"
    #     ]
    #     st.info(f"Contoh prompt : '{random.choice(welcome)}'")

    #     st.subheader("Prompt Suara")
    #     input_suara = speech_to_text(
    #         language='id',
    #         start_prompt="Mulai Bicara",
    #         stop_prompt="Selesai",
    #         key=f"tts_{st.session_state.chat_count}",
    #         use_container_width=True
    #     )

    #     model = st.selectbox("Pilih Model AI", ["Llama-3.1-8b-instant", "Llama-3.3-70b-versatile", "meta-llama/llama-4-scout-17b-16e-instruct", "openai/gpt-oss-120b"])
    #     temperature = st.slider("Temperature", 0.0, 1.0, 0.1, 0.05)

    #     if st.button("Reset Chat", use_container_width=True):
    #         st.session_state.messages = []
    #         st.session_state.last_processed = None
    #         st.session_state.chat_count += 1
    #         st.cache_data.clear()
    #         st.rerun()
        
    #     st.caption("Made by Nadya Nurjzillani")

    st.title("🎓 AI Analisis Data Dosen Universitas")
    st.write("Tanyakan apa saja tentang data dosen, fakultas, jabatan, dan remunerasi.")

    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            if message.get("error"):
                st.error(message["content"])
            else:
                st.write(message["content"])
            
            if message["role"] == "assistant" and not message.get("error"):
                df_tabel = message.get("df")
                sql_query = message.get("sql")
                
                if isinstance(df_tabel, pd.DataFrame) and not df_tabel.empty:
                    if message.get("action") != "photo":
                        insight = buat_kesimpulan(
                            message.get("pertanyaan"), 
                            df_tabel.to_json(), 
                            model, 
                            temperature
                        )
                        st.info(f"💡**Insight:** {insight}")
                        if idx == len(st.session_state.messages) - 1:
                            if not message.get("tts_played", False):
                                text_to_speech(insight)
                                st.session_state.messages[idx]["tts_played"] = True
                        
                        if message.get("action") == "barchart" and len(df_tabel.columns) >= 2:
                            st.bar_chart(df_tabel.set_index(df_tabel.columns[0]))
                        if message.get("action") == "linechart" and len(df_tabel.columns) >= 2:
                            st.line_chart(df_tabel.set_index(df_tabel.columns[0]))
                        if message.get("action") == "scatterchart" and len(df_tabel.columns) >= 2:
                            st.scatter_chart(df_tabel.set_index(df_tabel.columns[0]))
                        if message.get("action") == "areachart" and len(df_tabel.columns) >= 2:
                            st.area_chart(df_tabel.set_index(df_tabel.columns[0]))

                    if sql_query:
                        with st.expander("Lihat Query SQL"):
                            st.code(sql_query, language="sql")
                    
                    st.write("**Hasil Data:**")
                    st.dataframe(df_tabel, use_container_width=True)
                    
                    if message.get("action") == "photo":
                        if df_tabel.empty:
                            st.error("Data tidak ditemukan")
                        else:
                            data = df_tabel.iloc[0]

                            filename = Path(str(data["foto"])).name
                            path = Path("foto") / filename

                            nama = data.get("nama_lengkap", "Dosen")

                            if path.exists():
                                st.image(str(path), caption=f"Foto: {nama}")
                            else:
                                st.error(f"Foto tidak ditemukan: {path}")

                    csv_data = df_tabel.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="⬇ Download CSV", 
                        data=csv_data, 
                        file_name=f"data_universitas_{idx}.csv", 
                        key=f"dl_{idx}"
                    )

    input_teks = st.chat_input("Tanya sesuatu...")
    prompt_aktif = input_teks if input_teks else input_suara

    if prompt_aktif and prompt_aktif != st.session_state.last_processed:
        st.session_state.last_processed = prompt_aktif
        st.session_state.chat_count += 1
        st.session_state.messages.append({"role": "user", "content": prompt_aktif})
        st.rerun()

    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        prompt_aktif = st.session_state.messages[-1]["content"]
        with st.chat_message("assistant"):
            with st.spinner("AI sedang memproses..."):
                try:
                    history_text = buat_riwayat_chat()
                    llm = Groq(
                        model=model, 
                        api_key=st.secrets["GROQ_API_KEY"],  
                        temperature=temperature,
                        max_tokens=800
                    )
                    # llm = Groq(
                    #     model=model, 
                    #     api_key=os.getenv("GROQ_API_KEY"), ==== untuk .env
                    #     temperature=temperature,
                    #     max_tokens=800
                    # )
                    full_prompt = SYSTEM_PROMPT.format(
                        schema=DATABASE_SCHEMA,
                        history=history_text,
                        prompt=prompt_aktif
                    )
                    response = llm.complete(full_prompt).text.strip()
                    json_clean = re.sub(r'```json|```', '', response).strip()
                    hasil = json.loads(json_clean)
                    
                    explanation = hasil.get("explanation", "Maaf, saya tidak bisa memproses permintaan ini.")
                    sql = hasil.get("sql", "")
                    action = hasil.get("action", "none")
                    error_msg = hasil.get("error")
                    df = pd.DataFrame()
                    
                    if error_msg and str(error_msg).lower() not in ["null", "none", ""]:
                        explanation = error_msg
                    elif sql:
                        sql_final = sql.strip().rstrip(';')
                        try:
                            with sqlite3.connect(st.session_state.db_path) as koneksi_db:
                                df = pd.read_sql_query(sql_final, koneksi_db)
                        
                        except Exception as db_error:
                            explanation = f"Gagal eksekusi query: {str(db_error)}"

                    st.session_state.messages.append({
                        "pertanyaan": prompt_aktif,
                        "role": "assistant",
                        "content": explanation,
                        "sql": sql,
                        "df": df,
                        "action": action,
                        "error": bool(error_msg and str(error_msg).lower() not in ["null", "none", ""]),
                        "tts_played": False   
                    })
                    st.rerun()
                except json.JSONDecodeError:
                    st.error("AI tidak mengembalikan format JSON yang benar. Silakan coba lagi.")
                except Exception as e:
                    st.error(f"Terjadi kesalahan: {str(e)}")

if menu == "ℹ️ About":
    st.title("ℹ️ Tentang Aplikasi")

    # ===== DESKRIPSI =====
    st.write("""
    **AI Analisis Data Dosen** adalah aplikasi berbasis kecerdasan buatan 
    yang dirancang untuk membantu analisis data dosen secara cepat, 
    interaktif, dan mudah digunakan.

    Aplikasi ini mampu mengubah pertanyaan pengguna menjadi query SQL 
    dan menampilkan hasil dalam bentuk tabel, grafik, serta insight otomatis.
    """)

    st.divider()

    col1, col2 = st.columns([1, 2])

    # ===== FOTO / IDENTITAS =====
    with col1:
        st.image("profile.png", width=150)  
        st.caption("Nadya Nurjzillani - Developer")  

    # ===== PROFIL =====
    with col2:
        st.header("Tentang Pembuat")
        st.write("""
        **Nadya Nurjzillani**  
        Siswi / Developer  

        Pengembang aplikasi AI Analisis Data Dosen berbasis Streamlit 
        yang mengintegrasikan teknologi Large Language Model (LLM) 
        untuk analisis data secara otomatis.
        """)

    st.divider()

    # ===== TUJUAN =====
    st.header("Tujuan Aplikasi")
    st.write("""
    - Membantu analisis data dosen secara cepat dan efisien  
    - Mempermudah pengguna dalam memahami data melalui visualisasi  
    - Mengimplementasikan teknologi AI dalam bidang pendidikan  
    """)

    # ===== FITUR =====
    st.header("Fitur Utama")
    st.write("""
    - 🤖 Chatbot AI berbasis data  
    - 📊 Visualisasi data otomatis (chart)  
    - 📂 Export data ke CSV  
    - 🖼️ Menampilkan foto dosen  
    - 🎤 Input suara untuk pertanyaan  
    """)

    # ===== TEKNOLOGI =====
    st.header("Teknologi yang Digunakan")
    st.write("""
    - **Streamlit** → antarmuka aplikasi  
    - **SQLite** → database  
    - **Groq LLM** → pemrosesan AI  
    - **Python** → backend logic  
    """)

    st.divider()

    # ===== KONTAK =====
    st.header("📬 Kontak")
    st.write("""
    📧 Email: nadyanurjzillani@Gmail.com\n
    📱 WhatsApp: +62 857-2855-3651\n
    📷 Instagram: @nadya_zilla\n
    """)

    st.divider()

    # ===== FOOTER =====
    st.caption("© 2026 AI Analisis Data Dosen | Dibuat oleh Nadya Nurjzillani")

if menu == "🗂️ Sistem AI":
    st.title("🗂️ Database & Sistem AI")

    tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Data", 
    "🧠 Prompt AI", 
    "🗂️ Schema", 
    "💻 Source Code"
    ])

    with tab1:
        st.header("📊 Isi Database")

        try:
            with sqlite3.connect("universitas.db") as conn:

                subtab1, subtab2, subtab3, subtab4 = st.tabs([
                    "Dosen", "Fakultas", "Remunerasi", "Jabatan Fusional"
                ])

                with subtab1:
                    df = pd.read_sql_query("SELECT * FROM dosen", conn)
                    st.dataframe(df, use_container_width=True)
                    st.caption(f"{len(df)} data dosen")

                with subtab2:
                    df = pd.read_sql_query("SELECT * FROM fakultas", conn)
                    st.dataframe(df, use_container_width=True)
                    st.caption(f"{len(df)} data fakultas")

                with subtab3:
                    df = pd.read_sql_query("SELECT * FROM jabatan_fungsional", conn)
                    st.dataframe(df, use_container_width=True)
                    st.caption(f"{len(df)} data jabatan fungsional")

                with subtab4:
                    df = pd.read_sql_query("SELECT * FROM remunerasi", conn)
                    st.dataframe(df, use_container_width=True)
                    st.caption(f"{len(df)} data remunerasi")

        except Exception as e:
            st.error(f"Gagal load database: {e}")

    with tab2:
        st.header("🧠 SYSTEM PROMPT AI")

        st.info("Prompt ini digunakan AI untuk generate SQL dan jawaban.")

        st.code(SYSTEM_PROMPT, language="python")

    with tab3:
        st.header("🗂️ Struktur Database")

        st.info("Schema ini digunakan AI untuk memahami tabel.")

        st.code(DATABASE_SCHEMA, language="sql")

    with tab4:
        st.header("💻 Source Code Aplikasi")

        st.info("Berikut adalah kode utama aplikasi AI Dosen berbasis Streamlit.")

        show_code = st.checkbox("Tampilkan Source Code")

        if show_code:
            try:
                with open(__file__, "r", encoding="utf-8") as f:
                    code = f.read()

                st.code(code, language="python")

            except Exception:
                st.warning("Tidak bisa membaca file otomatis.")

                st.code("""
    # Tempelkan kode utama di sini jika deploy tidak mendukung __file__
                """, language="python")