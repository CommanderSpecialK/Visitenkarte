import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import json
import io

def check_password():
    """Gibt True zurück, wenn der Benutzer das richtige Passwort eingegeben hat."""
    def password_entered():
        """Prüft, ob das eingegebene Passwort korrekt ist."""
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Bitte Passwort eingeben", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Bitte Passwort eingeben", type="password", on_change=password_entered, key="password")
        st.error("😕 Passwort falsch.")
        return False
    else:
        return True

# --- AB HIER STARTET DIE EIGENTLICHE APP ---
if check_password():
    st.success("Anmeldung erfolgreich!")
    
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

    # Spalten helfen beim Zentrieren
    col1, col2, col3 = st.columns([2, 1, 2])  

    with col2:
        # Falls das Logo nicht gefunden wird, fängt dieser Block den Fehler ab
        try:
            st.image("WFL_OS.JPG", use_container_width=True)
        except:
            st.warning("Logo WFL_OS.JPG nicht gefunden.")

    st.title("Pro Visitenkarten-Scanner")

    with st.sidebar:
        try:
            st.image("WFL_OS.JPG", width=80)
        except:
            pass
        st.divider() 

    # 2. Dateiupload
    uploaded_file = st.file_uploader("Bild hochladen", type=['jpg', 'png', 'jpeg'])

    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption='Vorschau', use_container_width=True)
        
        if st.button("🚀 Analyse starten"):
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
                
                st.write("🤖 KI analysiert den Text...")
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
                    
                except Exception as e:
                    status.update(label="❌ Fehler aufgetreten", state="error")
                    st.error(f"Details: {e}")

    # 3. Interaktiver Editor & Export
    if st.session_state.alle_kontakte:
        st.divider()
        st.subheader(f"Gesammelte Kontakte ({len(st.session_state.alle_kontakte)})")
        
        spalten_namen = ["Firma", "Name", "Vorname", "Abteilung", "Adresse", "Telefon", "Mobiltelefon", "Email", "URL"]
        df_editor = pd.DataFrame(st.session_state.alle_kontakte, columns=spalten_namen)

        st.markdown("""
        <style>
        div[data-testid="stDataEditor"] {
            background-color: #293133;
            padding: 10px;
            border-radius: 5px;
        }
        </style>
        """, unsafe_allow_html=True)

        # Editor anzeigen
        editiertes_df = st.data_editor(df_editor, num_rows="dynamic", use_container_width=True)
        st.session_state.alle_kontakte = editiertes_df.values.tolist()

        col_l, col_r = st.columns(2)
        with col_l:
            if st.button("🗑️ Liste leeren"):
                st.session_state.alle_kontakte = []
                st.rerun()
        with col_r:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                editiertes_df.to_excel(writer, index=False)
            st.download_button("📥 Excel Download", buffer.getvalue(), "visitenkarten_sammlung.xlsx")

    # 4. Sidebar Statistik
    with st.sidebar:
        st.header("📊 Statistik")
        st.metric("Verbrauchte Tokens", f"{st.session_state.total_tokens:,}")
        if st.button("Reset Stats"):
            st.session_state.total_tokens = 0
            st.rerun()
