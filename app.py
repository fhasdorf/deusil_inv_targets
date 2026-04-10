# -*- coding: utf-8 -*-
# @Author: Frank Hasdorf
# @Date:   10-04-2026
# Combined: Investor Discovery + Market Signals Dashboard

import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ─────────────────────────────────────────────
# 1. KONFIGURATION
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Deutsche Silber SE | Intelligence Hub",
    page_icon="🥈",
    layout="wide",
)

# ─────────────────────────────────────────────
# 2. CUSTOM STYLING
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Hintergrund & Primärfarben */
    [data-testid="stAppViewContainer"] {
        background-color: #0d1117;
    }
    [data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    /* Navigations-Buttons */
    .nav-container {
        display: flex;
        gap: 12px;
        margin-bottom: 24px;
    }
    /* Metriken */
    [data-testid="metric-container"] {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 16px;
    }
    /* Header */
    h1, h2, h3 {
        color: #e6edf3 !important;
    }
    /* Silber-Akzent */
    .silver-badge {
        display: inline-block;
        background: linear-gradient(135deg, #8b9bb4, #c8d6e5, #8b9bb4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 1.1rem;
    }
    .module-header {
        border-left: 3px solid #8b9bb4;
        padding-left: 12px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 3. DATEN LADEN
# ─────────────────────────────────────────────
@st.cache_data
def load_investor_data(path: str):
    """Lädt die Investor-Leads aus der HR-Abfrage."""
    try:
        df = pd.read_csv(path)
        if 'relevanz_score' in df.columns:
            df['relevanz_score'] = pd.to_numeric(df['relevanz_score'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"Fehler beim Laden der Investor-Leads: {e}")
        return None


def load_news_data():
    """Lädt die aktuellste News-CSV-Datei."""
    file_path = "data/news_export_20260409_1825.csv"
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    return None


# ─────────────────────────────────────────────
# 4. MODUL: INVESTOR DISCOVERY
# ─────────────────────────────────────────────
def render_investor_module():
    st.markdown('<div class="module-header"><h2>🏢 Investor Discovery</h2></div>', unsafe_allow_html=True)
    st.caption("Analyse der Companies House Leads für die Deutsche Silber SE")

    # Sidebar-Filter für dieses Modul
    st.sidebar.header("⚙️ Filter – Investoren")
    investor_path = st.sidebar.text_input(
        "Pfad zur Leads-CSV",
        value=r"data\leads.csv"
    )
    min_score = st.sidebar.slider("Minimaler Relevanz-Score", 0, 100, 50)

    df = load_investor_data(investor_path)

    if df is not None:
        filtered_df = df[df['relevanz_score'] >= min_score].sort_values(
            by='relevanz_score', ascending=False
        )

        # Metriken
        m1, m2, m3 = st.columns(3)
        m1.metric("Leads gesamt", len(df))
        m2.metric("Qualifizierte Leads", len(filtered_df))
        avg_score = int(filtered_df['relevanz_score'].mean()) if not filtered_df.empty else 0
        m3.metric("Ø Relevanz", f"{avg_score}%")

        st.write("### Top-Investmentgesellschaften")

        display_cols = ["name", "relevanz_score", "sic_codes", "sic_beschreibungen"]
        if "zweck_preview" in filtered_df.columns:
            display_cols.append("zweck_preview")

        # Nur Spalten anzeigen, die wirklich vorhanden sind
        display_cols = [c for c in display_cols if c in filtered_df.columns]

        st.dataframe(
            filtered_df[display_cols],
            column_config={
                "relevanz_score": st.column_config.ProgressColumn(
                    "Score", min_value=0, max_value=100, format="%d%%"
                ),
                "name": "Unternehmen",
                "sic_beschreibungen": "Branchen-Fokus",
                "zweck_preview": "Gesellschaftszweck (Vorschau)",
            },
            use_container_width=True,
            hide_index=True,
        )

        # ── Aktuelle Marktsignale als Ergänzung zum Investor-Tab ──
        st.divider()
        st.write("### 📰 Aktuelle Marktsignale (Top-News)")
        st.caption("Die neuesten Schlagzeilen aus dem News-Monitor – passend zu deinen Investoren-Leads.")

        news_df = load_news_data()
        if news_df is not None:
            cols = news_df.columns.tolist()
            title_col  = next((c for c in cols if 'title'   in c.lower()), None)
            source_col = next((c for c in cols if 'source'  in c.lower() or 'domain' in c.lower()), None)
            url_col    = next((c for c in cols if 'url'     in c.lower()), None)
            kw_col     = next((c for c in cols if 'keyword' in c.lower() or 'search' in c.lower()), None)

            if title_col and url_col:
                top_news = news_df.head(6)  # Die 6 aktuellsten Einträge

                # 3-spaltige Kacheln
                card_cols = st.columns(3)
                for i, (_, row) in enumerate(top_news.iterrows()):
                    title   = row.get(title_col,  "Kein Titel")
                    source  = row.get(source_col, "–") if source_col else "–"
                    url     = row.get(url_col,    "#") if url_col    else "#"
                    keyword = row.get(kw_col,     "")  if kw_col     else ""

                    with card_cols[i % 3]:
                        st.markdown(f"""
<div style="
    background:#161b22;
    border:1px solid #30363d;
    border-left: 3px solid #8b9bb4;
    border-radius:8px;
    padding:14px 16px;
    margin-bottom:12px;
    min-height:130px;
">
    <div style="font-size:0.72rem;color:#8b9bb4;margin-bottom:6px;text-transform:uppercase;letter-spacing:.05em;">
        {keyword} · {source}
    </div>
    <div style="font-size:0.9rem;color:#e6edf3;font-weight:600;line-height:1.4;margin-bottom:10px;">
        {title}
    </div>
    <a href="{url}" target="_blank" style="font-size:0.78rem;color:#8b9bb4;text-decoration:none;">
        → Artikel lesen
    </a>
</div>
""", unsafe_allow_html=True)
            else:
                st.info("News-Spalten konnten nicht zugeordnet werden.")
        else:
            st.info("Noch keine News-Daten vorhanden. Starte das API-Skript für Marktsignale.")
    else:
        st.warning(
            "Keine Leads gefunden. Bitte starte zuerst das Skript `investor_discovery.py` "
            "und prüfe den Dateipfad in der Sidebar."
        )


# ─────────────────────────────────────────────
# 5. MODUL: MARKET SIGNALS (NEWS)
# ─────────────────────────────────────────────
def render_news_module():
    st.markdown('<div class="module-header"><h2>📰 Marktsignale aus News</h2></div>', unsafe_allow_html=True)
    st.caption("Aktuelle Marktsignale aus News-Quellen")

    df = load_news_data()

    if df is not None:
        cols = df.columns.tolist()

        title_col  = next((c for c in cols if 'title'   in c.lower()), None)
        source_col = next((c for c in cols if 'source'  in c.lower() or 'domain' in c.lower()), None)
        url_col    = next((c for c in cols if 'url'     in c.lower()), None)
        kw_col     = next((c for c in cols if 'keyword' in c.lower() or 'search' in c.lower()), None)

        if title_col and url_col:
            display_df = df[[c for c in [title_col, source_col, url_col, kw_col] if c]].copy()
            display_df.columns = ["Titel", "Quelle", "Link", "Keywords"][:len(display_df.columns)]

            # Suchfeld
            search = st.text_input("🔍 Tabelle filtern (z. B. Spanien, Investment):")
            if search:
                mask = display_df.apply(
                    lambda r: r.astype(str).str.contains(search, case=False, na=False).any(), axis=1
                )
                display_df = display_df[mask]

            # Metriken
            total = len(pd.read_csv("data/news_export_20260409_1825.csv")) if os.path.exists("data/news_export_20260409_1825.csv") else 0
            n1, n2 = st.columns(2)
            n1.metric("Signale gesamt", total)
            n2.metric("Angezeigte Signale", len(display_df))

            # Tabelle
            col_config = {"Link": st.column_config.LinkColumn("Artikel öffnen")}
            if "Keywords" in display_df.columns:
                col_config["Keywords"] = st.column_config.TextColumn("Gefundene Signale")

            st.dataframe(
                display_df,
                column_config=col_config,
                use_container_width=True,
                hide_index=True,
            )

            # Keyword-Verteilung (falls vorhanden)
            if "Keywords" in display_df.columns and not display_df.empty:
                st.divider()
                st.write("### 📊 Signal-Verteilung nach Keywords")
                kw_counts = display_df["Keywords"].value_counts().reset_index()
                kw_counts.columns = ["Keyword", "Anzahl"]
                fig = px.bar(
                    kw_counts,
                    x="Keyword",
                    y="Anzahl",
                    title="Häufigste Marktsignale",
                    color_discrete_sequence=["#8b9bb4"],
                )
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#e6edf3',
                    xaxis=dict(gridcolor='#30363d'),
                    yaxis=dict(gridcolor='#30363d'),
                )
                st.plotly_chart(fig, use_container_width=True)

        else:
            st.error("Spalten konnten nicht zugeordnet werden. Bitte prüfe die CSV-Header.")
    else:
        st.warning("Keine Daten gefunden. Bitte starte das API-Skript und prüfe den Dateipfad.")


# ─────────────────────────────────────────────
# 6. HAUPTNAVIGATION
# ─────────────────────────────────────────────
def main():
    # Header
    st.markdown(
        '<h1>🥈 Deutsche Silber SE <span class="silver-badge">Intelligence Hub</span></h1>',
        unsafe_allow_html=True
    )

    # Navigation via Tabs (oben, wie gewünscht)
    tab1, tab2 = st.tabs(["🏢  Potenzielle Investoren", "📰  Marktsignale aus News"])

    with tab1:
        render_investor_module()

    with tab2:
        render_news_module()


if __name__ == "__main__":
    main()
