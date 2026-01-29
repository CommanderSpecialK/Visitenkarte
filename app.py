import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import json
import io

def check_password():
    """Gibt True zurück, wenn der Benutzer das richtige Passwort eingegeben hat."""
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Bitte Passwort eingeben", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Bitte Passwort eingeben", type="password", on_change=password_entered, key="password")
        st.error("😕 Passwort falsch.")
        return False
    else:
        return True

def create_vcard(row):
    """Erstellt einen vCard-String im Format 2.1 für bessere Outlook-Kompatibilität."""
    vcf = [
        "BEGIN:VCARD",
        "VERSION:2.1",
        f"N;CHARSET=UTF-8:{row.get('Name', '')};{row.get('Vorname', '')}",
        f"FN;CHARSET=UTF-8:{row.get('Vorname', '')} {row.get('Name', '')}",
        f"ORG;CHARSET=UTF-8:{row.get('Firma', '')}",
        f"TITLE;CHARSET=UTF-8:{row.get('Abteilung', '')}",
        f"TEL;WORK;VOICE:{row.get('Telefon', '')}",
        f"TEL;CELL;VOICE:{row.get('Mobiltelefon', '')}",
        f"ADR;WORK;CHARSET=UTF-8:;;{row.get('Adresse', '')}",
        f"EMAIL;PREF;INTERNET:{row.get('Email', '')}",
        f"URL:{row.get('URL', '')}",
        "END:VCARD"
    ]
    return "\n".join(vcf)

# --- APP START ---
if check_password():
    # 1. Konfiguration
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    else:
        st.error("Bitte 'GEMINI_API_KEY' in den Secrets hinterlegen!")

    model = genai.GenerativeModel('gemini-2.5-flash')

    if 'alle_kontakte' not in st.session_state:
        st.session_state.alle_kontakte = []
    if 'total_tokens' not in st.session_state:
        st.session_state.total_tokens = 0

    col1, col2, col3 = st.columns([2, 1, 2])  
    with col2:
        try: st.image("WFL_OS.JPG", use_container_width=True)
        except: pass

    st.title("Pro Visitenkarten-Scanner")

    # 2. Dateiupload
    uploaded_file = st.file_uploader("Bild hochladen", type=['jpg', 'png', 'jpeg'])

    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption='Vorschau', use_container_width=True)
        
        if st.button("🚀 Analyse starten"):
            with st.status("Verarbeite Visitenkarte...", expanded=True) as status:
                prompt = """
                Analysiere dieses Bild. Extrahiere alle Visitenkartendaten.
                Gib NUR eine Liste von JSON-Objekten zurück mit:
                Firma, Name, Vorname, Abteilung, Adresse, Telefon, Mobiltelefon, Email, URL.
                """
                try:
                    response = model.generate_content([prompt, image])
                    st.session_state.total_tokens += response.usage_metadata.total_token_count
                    clean_json = response.text.replace('```json', '').replace('```', '').strip()
                    extrakt = json.loads(clean_json)
                    if isinstance(extrakt, dict): extrakt = [extrakt]
                    
                    spalten = ["Firma", "Name", "Vorname", "Abteilung", "Adresse", "Telefon", "Mobiltelefon", "Email", "URL"]
                    for eintrag in extrakt:
                        # Wir speichern es als Dictionary für den vCard-Generator
                        st.session_state.alle_kontakte.append(eintrag)
                    status.update(label="✅ Analyse erfolgreich!", state="complete", expanded=False)
                except Exception as e:
                    st.error(f"Fehler: {e}")

    # 3. Editor & Export
    if st.session_state.alle_kontakte:
        st.divider()
        st.subheader("Gescannte Kontakte")
        
        df_editor = pd.DataFrame(st.session_state.alle_kontakte)
        editiertes_df = st.data_editor(df_editor, num_rows="dynamic", use_container_width=True)
        st.session_state.alle_kontakte = editiertes_df.to_dict('records')

        # Export-Optionen
        col_vcf, col_csv, col_del = st.columns(3)
        
        with col_vcf:
            if not editiertes_df.empty:
                # Wir bauen die Datei zusammen
                vcard_collection = ""
                for _, row in editiertes_df.iterrows():
                    # Nur exportieren, wenn zumindest ein Name oder eine Firma da ist
                    if row.get('Name') or row.get('Firma'):
                        vcard_collection += create_vcard(row) + "\n\n"
                
                if vcard_collection:
                    st.download_button(
                        label="📇 Outlook Kontakte (.vcf)",
                        data=vcard_collection.encode('utf-8'), # UTF-8 Kodierung für Umlaute
                        file_name="outlook_kontakte.vcf",
                        mime="text/vcard",
                        use_container_width=True
                    )
            else:
                st.info("Keine Daten zum Exportieren.")
                
        with col_csv:
            # Falls du trotzdem noch Excel brauchst
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                editiertes_df.to_excel(writer, index=False)
            st.download_button("📥 Excel Download", buffer.getvalue(), "kontakte.xlsx")

        with col_del:
            if st.button("🗑️ Liste leeren"):
                st.session_state.alle_kontakte = []
                st.rerun()

    with st.sidebar:
        st.header("📊 Statistik")
        st.metric("Verbrauchte Tokens", f"{st.session_state.total_tokens:,}")
