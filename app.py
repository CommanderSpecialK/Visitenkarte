import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import json
import io
import zipfile
import google.generativeai as genai


def check_password():
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

if check_password():
    st.success("Anmeldung erfolgreich!")

    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        
    else:
        st.error("Bitte 'GEMINI_API_KEY' in den Secrets hinterlegen!")

    model = genai.GenerativeModel('models/gemini-2.5-flash-lite')

    if 'alle_kontakte' not in st.session_state:
        st.session_state.alle_kontakte = []
    if 'total_tokens' not in st.session_state:
        st.session_state.total_tokens = 0

    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        try:
            st.image("WFL_OS.JPG", use_container_width=True)
        except:
            st.warning("Logo WFL_OS.JPG nicht gefunden.")

    st.title("Pro Visitenkarten-Scanner")

    with st.sidebar:
        try:
            st.image("WFL_OS.JPG", width=80)
        except:
            pass
        st.divider()

    uploaded_file = st.file_uploader("Bild hochladen", type=['jpg', 'png', 'jpeg'])

    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption='Vorschau', use_container_width=True)

        if st.button("🚀 Analyse starten"):
            with st.status("Verarbeite Visitenkarte...", expanded=True) as status:
                st.write("🔍 Bereite Bilddaten vor...")

                prompt = """
                Analysiere dieses Bild. Es enthält eine oder mehrere Visitenkarten.
                Extrahiere die Daten von JEDER einzelnen erkennbaren Karte.
                Gib mir NUR eine LISTE von JSON-Objekten zurück.
                Jedes Objekt muss exakt diese Schlüssel haben:
                Firma, Name, Vorname, Abteilung, Adresse, Telefon, Mobiltelefon, Email, URL.
                Falls ein Feld fehlt, setze es auf null.
                Beispiel-Format: [{"Firma": "A", "Name": "B", ...}]
                """

                try:
                    response = model.generate_content([prompt, image])
                    st.session_state.total_tokens += response.usage_metadata.total_token_count

                    clean_json = response.text.replace('```json', '').replace('```', '').strip()
                    extrakt = json.loads(clean_json)

                    if isinstance(extrakt, dict):
                        extrakt = [extrakt]

                    spalten = ["Firma", "Name", "Vorname", "Abteilung", "Adresse", "Telefon", "Mobiltelefon", "Email", "URL"]

                    for eintrag in extrakt:
                        sortierte_werte = [eintrag.get(col, "") or "" for col in spalten]
                        st.session_state.alle_kontakte.append(sortierte_werte)

                    status.update(label="✅ Analyse erfolgreich!", state="complete", expanded=False)

                except Exception as e:
                    status.update(label="❌ Fehler aufgetreten", state="error")
                    st.error(f"Details: {e}")

    if st.session_state.alle_kontakte:
        st.divider()
        st.subheader(f"Gesammelte Kontakte ({len(st.session_state.alle_kontakte)})")

        spalten_namen = ["Firma", "Name", "Vorname", "Abteilung", "Adresse", "Telefon", "Mobiltelefon", "Email", "URL"]
        df_editor = pd.DataFrame(st.session_state.alle_kontakte, columns=spalten_namen)

        st.markdown("""<style>div[data-testid="stDataEditor"] { background-color: #293133; padding: 10px; border-radius: 5px; }</style>""", unsafe_allow_html=True)

        editiertes_df = st.data_editor(df_editor, num_rows="dynamic", use_container_width=True)
        st.session_state.alle_kontakte = editiertes_df.values.tolist()

        col_l, col_r = st.columns(2)
        with col_l:
            if st.button("🗑️ Liste leeren"):
                st.session_state.alle_kontakte = []
                st.rerun()

        with col_r:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for index, row in editiertes_df.iterrows():
                    vcard = [
                        "BEGIN:VCARD",
                        "VERSION:3.0",
                        f"N:{row['Name']};{row['Vorname']};;;",
                        f"FN:{row['Vorname']} {row['Name']}".strip(),
                        f"ORG:{row['Firma']};{row['Abteilung']}",
                        f"TEL;TYPE=WORK,VOICE:{row['Telefon']}",
                        f"TEL;TYPE=CELL,VOICE:{row['Mobiltelefon']}",
                        f"ADR;TYPE=WORK:;;{row['Adresse']};;;",
                        f"EMAIL;TYPE=PREF,INTERNET:{row['Email']}",
                        f"URL:{row['URL']}",
                        "END:VCARD"
                    ]
                    vcard_content = "\n".join(vcard)
                    filename = f"Kontakt_{index+1}_{row['Vorname']}_{row['Name']}.vcf".replace(" ", "_")
                    zip_file.writestr(filename, vcard_content)

            st.download_button(
                label="📥 vCards als ZIP herunterladen",
                data=zip_buffer.getvalue(),
                file_name="visitenkarten_kontakte.zip",
                mime="application/zip"
            )

    with st.sidebar:
        st.header("📊 Statistik")
        st.metric("Verbrauchte Tokens", f"{st.session_state.total_tokens:,}")
        if st.button("Reset Stats"):
            st.session_state.total_tokens = 0
            st.rerun()
