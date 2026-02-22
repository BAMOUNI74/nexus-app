import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime
import io

# Configuration de la page
st.set_page_config(page_title="Nexus Manager Ultime", layout="wide")

# --- INITIALISATION DES DONNÉES ET PARAMÈTRES ---
if 'cabinet' not in st.session_state:
    st.session_state['cabinet'] = {
        'nom': "Formation Nexus Compétences-BF",
        'pdg': "BAMOUNI Joseph Koaladuy",
        'titre': "Consultant - PDG du Cabinet",
        'contact': "22674042686",
        'email': "nexuscompetencesbf@gmail.com",
        'legal': "RCCM: BF-OUA-01-XXXX-B13 / IFU: 00XXXXXX"
    }

# Données issues de votre planification budgétaire
TARIFS = {
    "Partenariat Collectivités": 300000,
    "Partenariat Écoles": 200000,
    "Formations Écoles (Élèves/Profs)": 75000,
    "Renforcement de capacités": 100000,
    "Accompagnement Particulier": 100000,
    "Études de projets": 1000000
}
BUDGET_PREVU_GLOBAL = 2139500
OBJECTIF_ANNUEL = 15125000

# --- FONCTIONS TECHNIQUES ---
def charger_data(fichier, colonnes):
    if os.path.exists(fichier):
        return pd.read_csv(fichier)
    return pd.DataFrame(columns=colonnes)

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Nexus_Data')
    return output.getvalue()

class NexusPDF(FPDF):
    def header(self):
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 30)
        self.set_font("Arial", "B", 12)
        self.cell(0, 5, st.session_state['cabinet']['nom'], 0, 1, "R")
        self.set_font("Arial", "", 8)
        self.cell(0, 5, f"Contact: {st.session_state['cabinet']['contact']} | {st.session_state['cabinet']['email']}", 0, 1, "R")
        self.ln(20)

# --- BARRE LATÉRALE ---
st.sidebar.title(f"💎 {st.session_state['cabinet']['pdg']}")
menu = st.sidebar.radio("Navigation", [
    "📈 Tableau de Bord & Rapports", 
    "📑 Inscriptions & Reçus", 
    "💸 Suivi des Dépenses",
    "📚 Catalogue Scolaire & Relances",
    "⚙️ Paramètres du Cabinet"
])

# --- 1. TABLEAU DE BORD & RAPPORTS ---
if menu == "📈 Tableau de Bord & Rapports":
    st.title("📊 Rapport Financier Global")
    df_r = charger_data("recettes.csv", ["Date", "Nom", "Prestation", "Total", "Verse", "Mode"])
    df_d = charger_data("depenses.csv", ["Date", "Poste", "Libellé", "Montant"])
    
    encaisse = df_r['Verse'].sum() if not df_r.empty else 0
    depense = df_d['Montant'].sum() if not df_d.empty else 0
    solde = encaisse - depense
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Encaissé", f"{encaisse:,} CFA")
    col2.metric("Dépensé", f"{depense:,} CFA")
    col3.metric("Solde Net", f"{solde:,} CFA")
    col4.metric("Objectif", f"{(encaisse/OBJECTIF_ANNUEL)*100:.1f}%")

    st.write("---")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📈 Revenus par Type")
        if not df_r.empty: st.bar_chart(df_r.groupby('Prestation')['Verse'].sum())
    with c2:
        st.subheader("📉 Dépenses par Poste")
        if not df_d.empty: st.bar_chart(df_d.groupby('Poste')['Montant'].sum())

    st.write("---")
    st.subheader("📥 Exportation Professionnelle")
    ex_c1, ex_c2 = st.columns(2)
    if not df_r.empty:
        ex_c1.download_button("📂 Exporter Recettes (Excel)", to_excel(df_r), "Recettes_Nexus.xlsx")
    if not df_d.empty:
        ex_c2.download_button("📂 Exporter Dépenses (Excel)", to_excel(df_d), "Depenses_Nexus.xlsx")

# --- 2. INSCRIPTIONS & REÇUS ---
elif menu == "📑 Inscriptions & Reçus":
    st.header("✍️ Gestion des Encaissements")
    df = charger_data("recettes.csv", ["Date", "Nom", "Prestation", "Total", "Verse", "Mode"])
    
    with st.form("new_reg"):
        c1, c2 = st.columns(2)
        nom = c1.text_input("Nom du Client")
        presta = c1.selectbox("Prestation", list(TARIFS.keys()))
        montant_v = c2.number_input("Montant Versé (CFA)", min_value=0)
        mode = c2.selectbox("Mode de Paiement", ["Espèces", "Virement", "Orange Money", "Moov Money"])
        if st.form_submit_button("Enregistrer & Calculer %"):
            total_d = TARIFS[presta]
            nouvel = pd.DataFrame([[datetime.now().strftime("%d/%m/%Y"), nom, presta, total_d, montant_v, mode]], columns=df.columns)
            pd.concat([df, nouvel]).to_csv("recettes.csv", index=False)
            st.rerun()

    st.write("### 🧾 Générer un Reçu de Paiement")
    if not df.empty:
        sel = st.selectbox("Choisir le client", df['Nom'].unique())
        if st.button("📄 Créer le Reçu PDF"):
            row = df[df['Nom'] == sel].iloc[-1]
            pourcent = (row['Verse'] / row['Total']) * 100
            pdf = NexusPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "REÇU DE PAIEMENT", 0, 1, "C")
            pdf.ln(10)
            pdf.set_font("Arial", "", 12)
            pdf.cell(0, 8, f"Client : {row['Nom']}", 0, 1)
            pdf.cell(0, 8, f"Prestation : {row['Prestation']}", 0, 1)
            pdf.cell(0, 8, f"Mode : {row['Mode']}", 0, 1)
            pdf.ln(5)
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 12, f"Montant Versé : {row['Verse']:,} CFA ({pourcent:.1f}%)", 1, 1, "C")
            pdf.set_font("Arial", "I", 10)
            pdf.cell(0, 8, f"Reste à payer : {row['Total'] - row['Verse']:,} CFA", 0, 1)
            pdf.ln(20)
            pdf.set_font("Arial", "B", 11)
            pdf.cell(0, 6, f"Le PDG,", 0, 1, "R")
            pdf.cell(0, 6, st.session_state['cabinet']['pdg'], 0, 1, "R")
            pdf.output(f"Recu_{sel}.pdf")
            st.success(f"Reçu généré : Recu_{sel}.pdf")

# --- 3. SUIVI DES DÉPENSES ---
elif menu == "💸 Suivi des Dépenses":
    st.header("💸 Contrôle des Sorties d'Argent")
    df = charger_data("depenses.csv", ["Date", "Poste", "Libellé", "Montant"])
    with st.form("dep"):
        poste = st.selectbox("Catégorie", ["Formalisation", "Matériel", "Fonctionnement", "Marketing", "Frais Études", "Autre"])
        lib = st.text_input("Libellé précis")
        mont = st.number_input("Montant (CFA)", min_value=0)
        if st.form_submit_button("Enregistrer la dépense"):
            n = pd.DataFrame([[datetime.now().strftime("%d/%m/%Y"), poste, lib, mont]], columns=df.columns)
            pd.concat([df, n]).to_csv("depenses.csv", index=False)
            st.rerun()
    st.dataframe(df)

# --- 4. CATALOGUE & RELANCES ---
elif menu == "📚 Catalogue Scolaire & Relances":
    st.header("🏫 Volet Scolaire & Suivi WhatsApp")
    t1, t2 = st.tabs(["Catalogue", "Relances Impayés"])
    with t1:
        st.subheader("Thématiques Élèves & Enseignants")
        st.write("**Élèves :** Confiance, Éloquence, Méthodes d'étude.\n\n**Profs :** Gestion de classe, Pédagogie active.")
    with t2:
        df_r = charger_data("recettes.csv", ["Date", "Nom", "Prestation", "Total", "Verse", "Mode"])
        impayes = df_r[df_r['Verse'] < df_r['Total']]
        for i, r in impayes.iterrows():
            st.warning(f"{r['Nom']} : Reste {r['Total']-r['Verse']:,} CFA")
            link = f"https://wa.me/{st.session_state['cabinet']['contact']}?text=Bonjour, Nexus vous relance pour..."
            st.markdown(f"[📲 Relancer sur WhatsApp]({link})")

# --- 5. PARAMÈTRES ---
elif menu == "⚙️ Paramètres du Cabinet":
    st.header("⚙️ Configuration")
    st.session_state['cabinet']['pdg'] = st.text_input("Nom du PDG", st.session_state['cabinet']['pdg'])
    st.session_state['cabinet']['email'] = st.text_input("Email", st.session_state['cabinet']['email'])
    st.session_state['cabinet']['legal'] = st.text_area("Références Légales", st.session_state['cabinet']['legal'])