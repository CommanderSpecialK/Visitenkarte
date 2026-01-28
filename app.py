import streamlit as st
import easyocr
import pandas as pd
from PIL import Image
import numpy as np


# 1. Diese Funktion muss ganz links am Rand stehen
@st.cache_resource
def load_reader():
    # 'gpu=False' spart Grafikspeicher, 'recog_network' auf Standard lassen
    return easyocr.Reader(['de', 'en'], gpu=False)

# 2. Den Reader aufrufen (auch ganz links)
reader = load_reader()

st.title("Visitenkarten Scanner")


# Datei-Upload im Webinterface
uploaded_file = st.file_uploader("Bild hochladen", type=['jpg', 'png', 'jpeg'])

if uploaded_file:
    image = Image.open(uploaded_file)
    
    # Bild verkleinern, um RAM zu sparen (max 1000 Pixel Breite)
    image.thumbnail((1000, 1000))
    
    st.image(image, caption='Vorschau (verkleinert)', use_container_width=True)
    
    img_array = np.array(image)
    
    # Text extrahieren mit Fehler-Abfang (Try/Except)
    try:
        with st.spinner('Extrahiere Text... Bitte warten...'):
            result = reader.readtext(img_array, detail=0)
        
        if result:
            df = pd.DataFrame({"Gefundener Text": result})
            st.success("Extraktion erfolgreich!")
            st.table(df)
        else:
            st.warning("Kein Text gefunden.")
    except Exception as e:
        st.error(f"Fehler bei der Extraktion: {e}")

    
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
