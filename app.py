import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import json
import io

# 1. API Konfiguration
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Bitte 'GEMINI_API_KEY' in den Streamlit Secrets hinterlegen!")

model = genai.GenerativeModel('gemini-2.5-flash-lite')

# Initialisierung des Speichers (Kurzzeitgedächtnis)
if 'alle_kontakte' not in st.session_state:
    st.session_state.alle_kontakte = []

st.title("📇 Multi-Scan Visitenkarten-Sammler")
st.info("Tipp: Du kannst auch Bilder mit mehreren Visitenkarten gleichzeitig hochladen!")

uploaded_file = st.file_uploader("Bild auswählen", type=['jpg', 'png', 'jpeg'])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption='Hochgeladenes Bild', use_container_width=True)
    
    if st.button("Bild analysieren und Karten hinzufügen"):
        with st.spinner('KI scannt das Bild nach einer oder mehreren Karten...'):
            # HIER wird die Variable 'prompt' definiert
            prompt = """
            Analysiere dieses Bild. Es enthält eine oder mehrere Visitenkarten.
            Extrahiere die Daten von JEDER einzelnen erkennbaren Karte.
            Gib mir NUR eine LISTE von JSON-Objekten zurück.
            Jedes Objekt muss exakt diese Schlüssel haben: 
            Firma, Name, Vorname, Abteilung, Adresse, Telefon, Mobiltelefon, Email, URL.
            Falls ein Feld fehlt, setze es auf null.
            Beispiel-Format: [{"Firma": "A", "Name": "B", ...}, {"Firma": "C", "Name": "D", ...}]
            """
            
            try:
                # Bild an Gemini senden
                response = model.generate_content([prompt, image])
                
                # JSON-Text säubern und laden
                clean_json = response.text.replace('```json', '').replace('```', '').strip()
                extrakt = json.loads(clean_json)
                
                # Falls die KI nur ein einzelnes Objekt statt einer Liste schickt
                if isinstance(extrakt, dict):
                    extrakt = [extrakt]
                
                spalten = ["Firma", "Name", "Vorname", "Abteilung", "Adresse", "Telefon", "Mobiltelefon", "Email", "URL"]
                
                # Alle gefundenen Karten verarbeiten
                gefundene_anzahl = 0
                for eintrag in extrakt:
                    sortierte_werte = [eintrag.get(col, "") for col in spalten]
                    st.session_state.alle_kontakte.append(sortierte_werte)
                    gefundene_anzahl += 1
                
                st.success(f"Erfolgreich {gefundene_anzahl} Karte(n) zur Liste hinzugefügt!")
                
            except Exception as e:
                st.error(f"Fehler bei der Analyse: {e}")
                st.write("KI-Antwort zur Fehlersuche:", response.text if 'response' in locals() else "Keine Antwort")

# Anzeige der gesammelten Liste
# --- INTERAKTIVER EDITOR ---
if st.session_state.alle_kontakte:
    st.divider()
    st.subheader(f"Daten bearbeiten & kontrollieren ({len(st.session_state.alle_kontakte)} Einträge)")
    st.info("Du kannst direkt in die Zellen klicken, um Texte zu korrigieren.")

    # 1. Spaltenüberschriften definieren
    spalten_namen = ["Firma", "Name", "Vorname", "Abteilung", "Adresse", "Telefon", "Mobiltelefon", "Email", "URL"]
    
    # 2. DataFrame erstellen
    df_editor = pd.DataFrame(st.session_state.alle_kontakte, columns=spalten_namen)
    
    # 3. Den interaktiven Editor anzeigen
    # num_rows="dynamic" erlaubt es dir, Zeilen direkt im Editor zu löschen (Markieren + Entf)
    editiertes_df = st.data_editor(df_editor, num_rows="dynamic", use_container_width=True)
    
    # 4. Den Speicher (session_state) mit den Änderungen aus dem Editor synchronisieren
    st.session_state.alle_kontakte = editiertes_df.values.tolist()

    st.divider()
    
    # --- AKTIONEN ---
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Gesamte Liste leeren"):
            st.session_state.alle_kontakte = []
            st.rerun()
            
    with col2:
        # Excel Export (nimmt die editierten Daten!)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # Hier nutzen wir das editierte_df
            editiertes_df.to_excel(writer, index=False, header=False)
        
        st.download_button(
            label="Als Excel herunterladen",
            data=buffer.getvalue(),
            file_name="visitenkarten_korrigiert.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
