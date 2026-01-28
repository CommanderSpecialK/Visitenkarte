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
    st.error("Bitte 'GEMINI_API_KEY' in den Secrets hinterlegen!")

model = genai.GenerativeModel('gemini-2.5-flash-lite')

# --- NEU: INITIALISIERUNG DES SPEICHERS ---
if 'alle_kontakte' not in st.session_state:
    st.session_state.alle_kontakte = []

st.title("📇 Visitenkarten Scanner")

uploaded_file = st.file_uploader("Visitenkarte hochladen", type=['jpg', 'png', 'jpeg'])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption='Aktueller Scan', use_container_width=True)
    
    if st.button("Karte scannen und zur Liste hinzufügen"):
        with st.spinner('KI analysiert...'):
            prompt = """
Analysiere dieses Bild. Es enthält eine oder mehrere Visitenkarten.
Extrahiere die Daten von JEDER einzelnen Karte.
Gib mir eine LISTE von JSON-Objekten zurück (ein Objekt pro Karte).
Jedes Objekt muss diese Schlüssel haben: 
Firma, Name, Vorname, Abteilung, Adresse, Telefon, Mobiltelefon, Email, URL.
Falls ein Feld nicht auf der Karte steht, setze den Wert auf null.
"""
            
try:
    response = model.generate_content([prompt, image])
    clean_json = response.text.replace('```json', '').replace('```', '').strip()
    
    # Jetzt laden wir eine LISTE statt eines einzelnen Objekts
    daten_liste = json.loads(clean_json) 
    
    # Falls die KI nur ein Objekt statt einer Liste schickt, machen wir eine Liste daraus
    if isinstance(daten_liste, dict):
        daten_liste = [daten_liste]

    spalten = ["Firma", "Name", "Vorname", "Abteilung", "Adresse", "Telefon", "Mobiltelefon", "Email", "URL"]
    
    for eintrag in daten_liste:
        sortierte_werte = [eintrag.get(col, "") for col in spalten]
        st.session_state.alle_kontakte.append(sortierte_werte)
        
    st.success(f"{len(daten_liste)} Karte(n) erfolgreich hinzugefügt!")

except Exception as e:
    st.error(f"Fehler: {e}")


# --- NEU: ANZEIGE UND DOWNLOAD ALLER DATEN ---
if st.session_state.alle_kontakte:
    st.divider()
    st.subheader(f"Gesammelte Kontakte ({len(st.session_state.alle_kontakte)})")
    
    # DataFrame aus allen gespeicherten Kontakten erstellen
    df_gesamt = pd.DataFrame(st.session_state.alle_kontakte)
    st.table(df_gesamt)
    
    if st.button("Liste leeren"):
        st.session_state.alle_kontakte = []
        st.rerun()

    # Excel Export für alle Zeilen
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_gesamt.to_excel(writer, index=False, header=False)
    
    st.download_button(
        label="Alle als Excel herunterladen",
        data=buffer.getvalue(),
        file_name="visitenkarten_liste.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
