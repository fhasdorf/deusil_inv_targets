# -*- coding: utf-8 -*-
# @Author: Frank Hasdorf
import streamlit as st
import pandas as pd
import plotly.express as px

# Konfiguration
st.set_page_config(page_title="Silver Investment Radar", layout="wide", initial_sidebar_state="expanded")

# --- DATEN LADEN & VORBEREITEN ---
@st.cache_data
def load_data():
    # Hier laden wir deine 20 Treffer
    df = pd.read_csv('data/uk_investors_with_finance.csv')
    
    # Koordinaten-Mapping für Londoner Hotspots
    geo_map = {
        'W1': [51.514, -0.142], 'EC2': [51.517, -0.087], 
        'SW1': [51.499, -0.141], 'E1': [51.516, -0.071],
        'W14': [51.493, -0.210], 'WC2': [51.512, -0.120],
        'NW1': [51.536, -0.141], 'SE1': [51.503, -0.102]
    }
    
    def get_lat_lon(addr):
        addr = str(addr).upper()
        for pc, coords in geo_map.items():
            if pc in addr: return coords
        return [51.507, -0.127] # London Center Default

    df[['lat', 'lon']] = df['address'].apply(lambda x: pd.Series(get_lat_lon(x)))
    return df

df = load_data()

# --- SIDEBAR ---
st.sidebar.title("🛠️ Filter & Steuerung")
st.sidebar.info("Projekt: Deutsche Silber SE - Investor Targeting 2026")
min_score = st.sidebar.slider("Minimaler Priority Score", 60, 120, 80)
filtered_df = df[df['priority_score'] >= min_score]

# --- HAUPTBEREICH ---
st.title("🎯 Investor Pitch Dashboard")
st.markdown(f"Aktuell befinden sich **{len(filtered_df)} hochrelevante Leads** in der Auswahl.")

# 1. Die Karte (Wo sitzt das Geld?)
st.subheader("📍 Geografische Analyse: Londoner Investment-Cluster")

# Plotly Karte erstellen
fig = px.scatter_mapbox(
    filtered_df, 
    lat="lat", 
    lon="lon", 
    hover_name="name", 
    hover_data={
        "priority_score": True, 
        "search_keyword": True,
        "lat": False, 
        "lon": False
    },
    color="priority_score",
    size="priority_score",
    color_continuous_scale=px.colors.sequential.Aggrnyl,
    zoom=11, 
    height=500
)

fig.update_layout(mapbox_style="open-street-map")
fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

# Karte anzeigen
st.plotly_chart(fig, use_container_width=True)

# 2. Top-Leads Tabelle
st.subheader("📑 Priorisierte Lead-Liste")
st.dataframe(filtered_df[['name', 'priority_score', 'tags', 'search_keyword', 'address']], use_container_width=True)

# --- INVESTOR INTELLIGENCE MATRIX ---
st.divider()
st.subheader("🔍 Analyse der Investmentschwerpunkte")

selected_name = st.selectbox("Wähle ein Unternehmen zur Detailanalyse:", filtered_df['name'].tolist())

if selected_name:
    row = filtered_df[filtered_df['name'] == selected_name].iloc[0]
    
    col_1, col_2, col_3 = st.columns(3)
    
    with col_1:
        st.write("### 🏗️ Sektor-Fokus")
        primary_focus = row['search_keyword']
        st.info(f"**Primär:** {primary_focus}")
        if pd.notna(row['tags']) and row['tags'] != "":
            st.write(f"**Sub-Sektoren:** {row['tags']}")

    with col_2:
        st.write("### 📈 Ermittelter Intent")
        if row['priority_score'] >= 110:
            intent_type = "Strategisches Kern-Investment"
            desc = "Hohe Wahrscheinlichkeit für direkte Projektbeteiligung."
        elif "FAMILY OFFICE" in str(row['name']).upper():
            intent_type = "Vermögenssicherung / Erhalt"
            desc = "Interesse an physischen Sachwerten (Silber) zur Diversifikation."
        else:
            intent_type = "Wachstumskapital"
            desc = "Suche nach Rendite in operativen Rohstoffprojekten."
        
        st.warning(f"**Typ:** {intent_type}")
        st.caption(desc)

    with col_3:
        st.write("### 📍 Standort-Indikator")
        addr = str(row['address']).upper()
        if any(pc in addr for pc in ['W1', 'EC2', 'SW1']):
            st.success("**Tier 1 Finanzzentrum**")
            st.caption("Ansässig in einem der Kern-Finanzdistrikte Londons. Hohe Liquidität zu erwarten.")
        else:
            st.write("**Regionaler Hub**")
            st.caption("Spezialisierter Nischeninvestor oder administrativer Sitz.")

    st.markdown("---")
    st.write(f"**Zusammenfassung für die Geschäftsführung:**")
    tags_text = row['tags'] if (pd.notna(row['tags']) and row['tags'] != "") else 'Rohstoff-nahe Projekte'
    st.write(f"Das Unternehmen **{row['name']}** weist durch die Kombination aus dem Gründungsjahr ({row['founded_on']}) "
             f"und dem Branchenschwerpunkt ({row['search_keyword']}) ein passgenaues Profil für die **Deutsche Silber SE** auf. "
             f"Besonders die Verknüpfung mit den Themen *{tags_text}* macht diesen Lead hochgradig relevant.")