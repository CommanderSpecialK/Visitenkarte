import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import json

# Konfiguriere Gemini
# Statt api_key="DEIN_KEY" nutzt du das Secrets-Objekt von Streamlit
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

model = genai.GenerativeModel('gemini-2.5-flash-lite')

st.title("KI Visitenkarten Scanner")

uploaded_file = st.file_uploader("Visitenkarte hochladen", type=['jpg', 'png', 'jpeg'])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption='Hochgeladenes Bild', use_container_width=True)
    
    if st.button("Daten extrahieren"):
        with st.spinner('KI analysiert das Bild...'):
            # Prompt für die KI
            prompt = """Extrahiere die Daten von dieser Visitenkarte. 
            Gib mir NUR ein JSON-Objekt mit diesen Feldern zurück: 
            Firma, Name, Vorname, Abteilung, Adresse, Telefon, Mobiltelefon, Email, URL.
            Falls ein Feld fehlt, schreibe null."""
            
            # Bild an Gemini senden
            response = model.generate_content([prompt, image])
            
# 1. Definieren der festen Spaltenreihenfolge
ordered_data = ["Firma", "Name", "Vorname", "Abteilung", "Adresse", "Telefon", "Mobiltelefon", "Email", "URL"]

try:
    # Säubern der Ausgabe
    clean_json = response.text.replace('```json', '').replace('```', '').strip()
    data = json.loads(clean_json)
    
    # Sicherstellen, dass alle Felder vorhanden sind (sonst leerer Text "")
    ordered_data = {col: data.get(col, "") for col in COLUMNS_ORDER}
    
    # DataFrame mit fester Reihenfolge erstellen
    df = pd.DataFrame([ordered_data])
    
    # Tabelle zur Kontrolle in der App anzeigen (hier noch mit Spaltennamen)
    st.table(df)

import io
    # EXPORT VORBEREITEN
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # header=False entfernt die Überschriften im Excel-File
        # index=False entfernt die Zeilennummerierung
        df.to_excel(writer, index=False, header=False, sheet_name='Kontakt')

    st.download_button(
        label="Als Excel herunterladen (nur Daten)",
        data=buffer.getvalue(),
        file_name="visitenkarte.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
                
except Exception as e:
    st.error("Fehler beim Sortieren der Daten.")

                
except Exception as e:
    st.error("Fehler beim Verarbeiten der KI-Antwort. Probiere es nochmal.")
    st.write(response.text)
