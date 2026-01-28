import streamlit as st
import easyocr
import pandas as pd
from PIL import Image
import numpy as np


st.title("Visitenkarten Scanner")

# Datei-Upload im Webinterface
uploaded_file = st.file_uploader("Bild hochladen", type=['jpg', 'png', 'jpeg'])

if uploaded_file:
    image = Image.open(uploaded_file)
    img_array = np.array(image) # Bild umwandeln
    result = reader.readtext(img_array, detail=0)
    
    # Text extrahieren
    @st.cache_resource
def load_reader():
    # Lädt das Modell nur einmal und speichert es im Zwischenspeicher
    return easyocr.Reader(['de', 'en'], gpu=False)

    reader = load_reader()
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
