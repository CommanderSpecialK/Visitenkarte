import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import json
import io
import numpy as np

# 1. API Konfiguration (Nutzt Streamlit Secrets)
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Bitte hinterlege den 'GEMINI_API_KEY' in den Streamlit Secrets!")

model = genai.GenerativeModel('gemini-1.5-flash')

st.title("📇 KI Visitenkarten-Scanner")
st.info("Lade ein Bild hoch, um die Daten direkt in eine Excel-Struktur zu extrahieren.")

# 2. Dateiupload
uploaded_file = st.file_uploader("Visitenkarte auswählen", type=['jpg', 'png', 'jpeg'])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption='Vorschau der Visitenkarte', use_container_width=True)
    
    if st.button("Daten jetzt extrahieren"):
        with st.spinner('KI analysiert das Bild... bitte warten.'):
            # Prompt für die KI
            prompt = """
            Extrahiere die Daten von dieser Visitenkarte. 
            Gib mir NUR ein JSON-Objekt mit genau diesen Schlüsseln zurück: 
            Firma, Name, Vorname, Abteilung, Adresse, Telefon, Mobiltelefon, Email, URL.
            Falls ein Feld nicht auf der Karte steht, setze den Wert auf null.
            """
            
            try:
                # Bild an Gemini senden
                response = model.generate_content([prompt, image])
                
                # JSON-Text säubern
                raw_text = response.text
                clean_json = raw_text.replace('```json', '').replace('```', '').strip()
                data = json.loads(clean_json)
                
                # Deine gewünschte Spaltenreihenfolge
                spalten = ["Firma", "Name", "Vorname", "Abteilung", "Adresse", "Telefon", "Mobiltelefon", "Email", "URL"]
                
                # Daten sortieren und fehlende Felder mit Leerstring füllen
                sortierte_werte = [data.get(col, "") for col in spalten]
                
                # DataFrame erstellen (nur eine Zeile mit Daten)
                df = pd.DataFrame([sortierte_werte])
                
                st.success("Extraktion abgeschlossen!")
                
                # Vorschau-Tabelle (ohne Header im UI zur Kontrolle)
                st.write("Vorschau der Daten:")
                st.table(df)
                
                # 3. EXCEL-EXPORT (ohne Header/Überschriften)
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, header=False)
                
                st.download_button(
                    label="Excel-Datei herunterladen",
                    data=buffer.getvalue(),
                    file_name="visitenkarte_extrakt.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
            except Exception as e:
                st.error(f"Ein Fehler ist aufgetreten: {e}")
                st.info("Tipp: Überprüfe, ob dein Gemini API Key korrekt ist und das Bild lesbar ist.")

# 4. Anleitung für die requirements.txt (als Kommentar)
# Du benötigst in deiner requirements.txt:
# streamlit
# google-generativeai
# pandas
# openpyxl
# Pillow
