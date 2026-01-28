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
            Name, Firma, Position, Email, Telefon, Website.
            Falls ein Feld fehlt, schreibe null."""
            
            # Bild an Gemini senden
            response = model.generate_content([prompt, image])
            
            try:
                # Säuberung des Outputs (entfernt ```json ... ```)
                clean_json = response.text.replace('```json', '').replace('```', '').strip()
                data = json.loads(clean_json)
                
                # In Tabelle anzeigen
                df = pd.DataFrame([data])
                st.success("Daten erfolgreich extrahiert!")
                st.table(df)
                
                # Excel/CSV Download
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("Als CSV speichern", csv, "kontakt.csv", "text/csv")
                
            except Exception as e:
                st.error("Fehler beim Verarbeiten der KI-Antwort. Probiere es nochmal.")
                st.write(response.text)
