import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import json
import io

# Konfiguriere Gemini
# Statt api_key="DEIN_KEY" nutzt du das Secrets-Objekt von Streamlit
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

model = genai.GenerativeModel('gemini-2.5-flash-lite')

st.title("KI Visitenkarten Scanner")

uploaded_file = st.file_uploader("Visitenkarte hochladen", type=['jpg', 'png', 'jpeg'])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption='Hochgeladenes Bild', use_container_width=True)
    
if st.button("Daten extrahiert"):
    with st.spinner('KI analysiert das Bild...'):
        prompt = """Extrahiere die Daten von dieser Visitenkarte. 
            Gib mir NUR ein JSON-Objekt mit diesen Feldern zurück: 
            Firma, Name, Vorname, Abteilung, Adresse, Telefon, Mobiltelefon, Email, URL.
            Falls ein Feld fehlt, schreibe null."""
        
        # HIER wird die Variable 'response' erstellt:
        response = model.generate_content([prompt, image])
        
        try:
            # Jetzt existiert 'response' und wir können darauf zugreifen
            clean_json = response.text.replace('```json', '').replace('```', '').strip()
            data = json.loads(clean_json)

    # Wenn ein Feld fehlt, wird einfach ein leerer Text "" eingefügt.
    spalten = ["Firma", "Name", "Vorname", "Abteilung", "Adresse", "Telefon", "Mobiltelefon", "Email", "URL"]
    sortierte_werte = [data.get(col, "") for col in spalten]
    
    # 3. Wir erstellen den DataFrame aus dieser sortierten Liste
    df = pd.DataFrame([sortierte_werte]) 
    
    # Vorschau in der App
    st.success("Daten extrahiert!")
    st.table(df)
    
    # 4. Excel-Export (ohne Überschriften)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, header=False)

    st.download_button(
        label="Download Excel",
        data=buffer.getvalue(),
        file_name="kontakt.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

except Exception as e:
    st.error(f"Fehler: {e}")

