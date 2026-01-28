import streamlit as st
import easyocr
import pandas as pd
from PIL import Image

st.title("Visitenkarten Scanner")

# Datei-Upload im Webinterface
uploaded_file = st.file_uploader("Bild hochladen", type=['jpg', 'png', 'jpeg'])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption='Hochgeladenes Bild', use_container_width=True)
    
    # Text extrahieren
    reader = easyocr.Reader(['de', 'en'])
    result = reader.readtext(image, detail=0)
    
    # Daten in einer Tabelle anzeigen
    df = pd.DataFrame({"Extrahierter Text": result})
    st.write(df)

    # Download-Button für Excel
    st.download_button(
        label="Als Excel herunterladen",
        data=df.to_csv().encode('utf-8'), # Einfachheitshalber hier CSV
        file_name='kontakte.csv'
    )
