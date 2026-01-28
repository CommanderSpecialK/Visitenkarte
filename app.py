import streamlit as st
import easyocr
import pandas as pd
from PIL import Image
import numpy as np


# 1. Diese Funktion muss ganz links am Rand stehen
@st.cache_resource
def load_reader():
    # Diese Zeile MUSS 4 Leerzeichen eingerückt sein
    return easyocr.Reader(['de', 'en'], gpu=False)

# 2. Den Reader aufrufen (auch ganz links)
reader = load_reader()

st.title("Visitenkarten Scanner")

# Datei-Upload im Webinterface
uploaded_file = st.file_uploader("Bild hochladen", type=['jpg', 'png', 'jpeg'])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption='Vorschau', use_container_width=True)
    
    # Bild für EasyOCR vorbereiten
    img_array = np.array(image)
    
    # Text extrahieren
    with st.spinner('Extrahiere Text...'):
        result = reader.readtext(img_array, detail=0)
    # Daten in einer Tabelle anzeigen
    df = pd.DataFrame({"Extrahierter Text": result})
    st.write(df)

    # Download-Button für Excel
    st.download_button(
        label="Als Excel herunterladen",
        data=df.to_csv().encode('utf-8'), # Einfachheitshalber hier CSV
        file_name='kontakte.csv'
    )
