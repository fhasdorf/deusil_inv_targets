# -*- coding: utf-8 -*-
# @Author: Frank Hasdorf
# @cd: c:\Projekte\deutschesilberse\App_Investor_Targets

import streamlit as st
import pandas as pd
import plotly.express as px

# Konfiguration der Seite (Muss als Erstes kommen)
st.set_page_config(page_title="Silver Investment Radar", layout="wide", initial_sidebar_state="expanded")

# ==============================================================================
# DATEN LADEN & VORBEREITEN
# ==============================================================================

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    # Koordinaten-Mapping für Londoner Postleitzahl-Präfixe
    geo_map = {
        'W1':  [51.514, -0.142], 'EC2': [51.517, -0.087],
        'SW1': [51.499, -0.141], 'E1':  [51.516, -0.071],
        'W14': [51.493, -0.210], 'WC2': [51.512, -0.120],
        'NW1': [51.536, -0.141], 'SE1': [51.503, -0.102],
        'EC1': [51.522, -0.099], 'EC3': [51.511, -0.082],
        'EC4': [51.513, -0.098], 'WC1': [51.521, -0.121],
    }

    def get_lat_lon(addr):
        addr = str(addr).upper()
        for pc, coords in geo_map.items():
            if pc in addr:
                return coords
        return [51.507, -0.127]  # London Center Default

    df[['lat', 'lon']] = df['address'].apply(lambda x: pd.Series(get_lat_lon(x)))

    # Spalten-Normalisierung
    if 'relevanz_score' not in df.columns:
        df['relevanz_score'] = 0
    if 'gesellschaftszweck' not in df.columns:
        df['gesellschaftszweck'] = ""
    if 'sic_beschreibungen' not in df.columns:
        df['sic_beschreibungen'] = ""
    if 'date_of_creation' not in df.columns:
        df['date_of_creation'] = ""

    df['gesellschaftszweck'] = df['gesellschaftszweck'].fillna("").astype(str)
    df['sic_beschreibungen'] = df['sic_beschreibungen'].fillna("").astype(str)

    return df


def render_news_section(csv_path: str):
    st.header("📊 Market Intelligence: Silber & Asset Allocation")
    st.subheader("Aktuelle Signale aus Top-Medienquellen")

    try:
        df = pd.read_csv(csv_path)
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%d.%m.%Y')

        for _, row in df.iterrows():
            with st.container():
                col1, col2 = st.columns([1, 4])
                with col1:
                    st.caption(f"📅 {row.get('date', 'N/A')}")
                    st.markdown(f"**{row.get('source.title', 'Quelle')}**")
                with col2:
                    if 'url' in row and pd.notna(row['url']):
                        st.markdown(f"#### [{row['title']}]({row['url']})")
                    else:
                        st.markdown(f"#### {row['title']}")
                    if 'body' in row and pd.notna(row['body']):
                        st.write(str(row['body'])[:200] + "...")
                st.divider()

    except Exception as e:
        st.error(f"Fehler beim Laden der News-Daten: {e}")


# ==============================================================================
# DATEN LADEN
# ==============================================================================

LEADS_FILE = "data/leads.csv"
NEWS_FILE  = "data/newsapi_silber_report_20260408_0912.csv"

try:
    df = load_data(LEADS_FILE)
except FileNotFoundError:
    st.error(f"Leads-Datei nicht gefunden: `{LEADS_FILE}`  \nBitte zuerst `investor_discovery.py --output {LEADS_FILE}` ausführen.")
    st.stop()

# ==============================================================================
# SIDEBAR
# ==============================================================================

st.sidebar.title("Filter & Steuerung")
st.sidebar.info("Deutsche Silber SE – Investor Screening 2026")

score_min = df['relevanz_score'].min()
score_max = df['relevanz_score'].max()

min_score = st.sidebar.slider(
    "Minimaler Relevanz-Score",
    int(score_min), int(score_max),
    int(score_min + (score_max - score_min) * 0.5)
)

# SIC-Filter
all_sics = sorted(set(
    sic for sics in df['sic_beschreibungen'].str.split("|") for sic in sics if sic
))
selected_sics = st.sidebar.multiselect(
    "SIC-Kategorie filtern (optional)", options=all_sics
)

# Gesellschaftszweck Freitext-Suche
zweck_filter = st.sidebar.text_input("Gesellschaftszweck enthält…", "")

# Filter anwenden
filtered_df = df[df['relevanz_score'] >= min_score].copy()

if selected_sics:
    filtered_df = filtered_df[
        filtered_df['sic_beschreibungen'].apply(
            lambda s: any(sic in s for sic in selected_sics)
        )
    ]

if zweck_filter.strip():
    filtered_df = filtered_df[
        filtered_df['gesellschaftszweck'].str.contains(zweck_filter.strip(), case=False, na=False)
    ]

# ==============================================================================
# HAUPTBEREICH
# ==============================================================================

st.title("🔭 Investor Pitch Dashboard")
st.markdown(
    f"Aktuell befinden sich **{len(filtered_df)} hochrelevante Leads** in der Auswahl "
    f"(von {len(df)} gesamt, Screening: {df['screening_datum'].iloc[0] if 'screening_datum' in df.columns else 'unbekannt'})."
)

# --- KARTE ---
st.subheader("📍 Geografische Analyse: Londoner Investment-Cluster")
fig = px.scatter_mapbox(
    filtered_df,
    lat="lat", lon="lon",
    hover_name="name",
    hover_data={
        "relevanz_score": True,
        "sic_beschreibungen": True,
        "lat": False, "lon": False
    },
    color="relevanz_score",
    size="relevanz_score",
    color_continuous_scale=px.colors.sequential.Aggrnyl,
    zoom=11,
    height=500
)
fig.update_layout(mapbox_style="open-street-map", margin={"r": 0, "t": 0, "l": 0, "b": 0})
st.plotly_chart(fig, use_container_width=True)

# --- LEAD-TABELLE ---
st.subheader("📑 Priorisierte Lead-Liste")

show_cols = ['name', 'relevanz_score', 'search_keyword', 'sic_beschreibungen', 'address', 'date_of_creation']
show_cols = [c for c in show_cols if c in filtered_df.columns]

st.dataframe(
    filtered_df[show_cols].reset_index(drop=True),
    use_container_width=True,
    column_config={
        "relevanz_score": st.column_config.ProgressColumn(
            "Score", min_value=0, max_value=100, format="%d"
        )
    }
)

# --- DETAILANALYSE ---
st.divider()
st.subheader("🔍 Detailanalyse eines Unternehmens")

selected_name = st.selectbox("Unternehmen auswählen:", filtered_df['name'].tolist())

if selected_name:
    row = filtered_df[filtered_df['name'] == selected_name].iloc[0]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("### 🏗️ Sektor-Fokus")
        st.info(f"**SIC-Suche:** {row['search_keyword']}")
        if row['sic_beschreibungen']:
            for sic in row['sic_beschreibungen'].split("|"):
                if sic:
                    st.write(f"• {sic}")

    with col2:
        st.write("### 📈 Ermittelter Intent")
        score = row['relevanz_score']
        sic_str = str(row.get('sic_beschreibungen', '')).upper()

        if score >= 80:
            intent_type = "Strategisches Kern-Investment"
            desc = "Hohe Wahrscheinlichkeit für direkte Projektbeteiligung."
            st.warning(f"**Typ:** {intent_type}")
        elif "FONDS" in sic_str or "INVESTMENTFONDS" in sic_str:
            intent_type = "Institutioneller Fondsinvestor"
            desc = "Strukturierte Beteiligung über Fondsvehikel zu erwarten."
            st.info(f"**Typ:** {intent_type}")
        else:
            intent_type = "Wachstumskapital / Beteiligung"
            desc = "Suche nach Rendite in operativen Rohstoffprojekten."
            st.write(f"**Typ:** {intent_type}")
        st.caption(desc)

    with col3:
        st.write("### 📍 Standort-Indikator")
        addr = str(row['address']).upper()
        if any(pc in addr for pc in ['W1', 'EC2', 'SW1', 'EC1', 'EC3', 'EC4']):
            st.success("**Tier 1 Finanzzentrum**")
            st.caption("Ansässig in einem der Kern-Finanzdistrikte Londons.")
        else:
            st.write("**Regionaler Hub**")
            st.caption("Spezialisierter Nischeninvestor oder administrativer Sitz.")

    # Gesellschaftszweck — eigener Block mit voller Breite
    st.markdown("---")
    st.write("### 📋 Gesellschaftszweck (eingetragen bei Companies House)")
    zweck = str(row.get('gesellschaftszweck', '')).strip()
    if zweck:
        st.info(zweck)
    else:
        st.caption("Kein Gesellschaftszweck im Handelsregister hinterlegt.")

    # GF-Zusammenfassung
    st.markdown("---")
    st.write("**Zusammenfassung für die Geschäftsführung:**")
    sic_text = row['sic_beschreibungen'] if row['sic_beschreibungen'] else "Rohstoff-nahe Projekte"
    gruendung = str(row.get('date_of_creation', 'unbekannt'))
    st.write(
        f"Das Unternehmen **{row['name']}** (gegr. {gruendung}) weist durch seinen Branchenschwerpunkt "
        f"(*{sic_text}*) ein passgenaues Profil für die **Deutsche Silber SE** auf. "
        f"Der Relevanz-Score beträgt **{int(row['relevanz_score'])}/100**."
    )
    if zweck:
        st.write(f"Der eingetragene Gesellschaftszweck lautet: *\"{zweck[:300]}{'…' if len(zweck) > 300 else ''}\"*")

# --- MARKET INTELLIGENCE ---
st.divider()
try:
    render_news_section(NEWS_FILE)
except Exception:
    st.info("News-Datei nicht vorhanden – Market Intelligence wird übersprungen.")

