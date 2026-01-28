import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import json
import io

# 1. Konfiguration & Speicher initialisieren
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Bitte 'GEMINI_API_KEY' in den Secrets hinterlegen!")

model = genai.GenerativeModel('gemini-2.5-flash-lite')

if 'alle_kontakte' not in st.session_state:
    st.session_state.alle_kontakte = []
if 'total_tokens' not in st.session_state:
    st.session_state.total_tokens = 0

st.title("📇 Pro Visitenkarten-Scanner")

# 2. Dateiupload
uploaded_file = st.file_uploader("Bild hochladen", type=['jpg', 'png', 'jpeg'])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption='Vorschau', use_container_width=True)
    
    if st.button("🚀 Analyse starten"):
        # --- FORTSCHRITTSANZEIGE START ---
        with st.status("Verarbeite Visitenkarte...", expanded=True) as status:
            st.write("🔍 Bereite Bilddaten vor...")
            
            prompt = """
            Analysiere dieses Bild. Es enthält eine oder mehrere Visitenkarten.
            Extrahiere die Daten von JEDER einzelnen erkennbaren Karte.
            Gib mir NUR eine LISTE von JSON-Objekten zurück.
            Jedes Objekt muss exakt diese Schlüssel haben: 
            Firma, Name, Vorname, Abteilung, Adresse, Telefon, Mobiltelefon, Email, URL.
            Falls ein Feld fehlt, setze es auf null.
            Beispiel-Format: [{"Firma": "A", "Name": "B", ...}, {"Firma": "C", "Name": "D", ...}]
            """
            
            st.write("🤖 KI analysiert den Text (Gemini 2.5 Flash Lite)...")
            try:
                response = model.generate_content([prompt, image])
                
                # Token-Verbrauch loggen
                st.session_state.total_tokens += response.usage_metadata.total_token_count
                
                st.write("📝 Daten werden strukturiert...")
                clean_json = response.text.replace('```json', '').replace('```', '').strip()
                extrakt = json.loads(clean_json)
                
                if isinstance(extrakt, dict):
                    extrakt = [extrakt]
                
                spalten = ["Firma", "Name", "Vorname", "Abteilung", "Adresse", "Telefon", "Mobiltelefon", "Email", "URL"]
                
                for eintrag in extrakt:
                    sortierte_werte = [eintrag.get(col, "") for col in spalten]
                    st.session_state.alle_kontakte.append(sortierte_werte)
                
                status.update(label="✅ Analyse erfolgreich!", state="complete", expanded=False)
                #st.balloons() # Kleiner Erfolgseffekt
                
            except Exception as e:
                status.update(label="❌ Fehler aufgetreten", state="error")
                st.error(f"Details: {e}")
        # --- FORTSCHRITTSANZEIGE ENDE ---

# 3. Interaktiver Editor & Export
if st.session_state.alle_kontakte:
    st.divider()
    st.subheader(f"Gesammelte Kontakte ({len(st.session_state.alle_kontakte)})")
    
    spalten_namen = ["Firma", "Name", "Vorname", "Abteilung", "Adresse", "Telefon", "Mobiltelefon", "Email", "URL"]
    df_editor = pd.DataFrame(st.session_state.alle_kontakte, columns=spalten_namen)
    
    # Editor anzeigen
    editiertes_df = st.data_editor(df_editor, num_rows="dynamic", use_container_width=True)
    st.session_state.alle_kontakte = editiertes_df.values.tolist()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Liste leeren"):
            st.session_state.alle_kontakte = []
            st.rerun()
    with col2:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            editiertes_df.to_excel(writer, index=False, header=False)
        st.download_button("📥 Excel Download", buffer.getvalue(), "visitenkarten_sammlung.xlsx")

# 4. Sidebar Statistik
with st.sidebar:
    st.header("📊 Statistik")
    st.metric("Verbrauchte Tokens", f"{st.session_state.total_tokens:,}")
    if st.button("Reset Stats"):
        st.session_state.total_tokens = 0
        st.rerun()
