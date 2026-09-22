import streamlit as st
import math
import requests
from datetime import datetime
from fpdf import FPDF
import pandas as pd

# Configuration de la page Streamlit
st.set_page_config(
    page_title="Chiffrage & Rentabilité SAP Pro",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- BASE DE DONNÉES DES 21 ACTIVITÉS SAP DÉCLARATIVES (Art. D. 7231-1) ---
ACTIVITES_SAP = {
    "Entretien de la maison et travaux ménagers": {
        "tva": 10.0, "plafond_an": "12 000 € (+1 500 €/enfant ou ascendant)",
        "conso_defaut": 4.0, "type_module": "menage",
        "description": "Entretien courant des sols, sanitaires, vitres, repassage."
    },
    "Petits travaux de jardinage": {
        "tva": 20.0, "plafond_an": "5 000 € max / an / foyer",
        "conso_defaut": 8.0, "type_module": "jardinage",
        "description": "Tonte, taille de haies, désherbage, débroussaillage léger."
    },
    "Travaux de petit bricolage": {
        "tva": 20.0, "plafond_an": "500 € max / an / foyer (max 2h par intervention)",
        "conso_defaut": 7.0, "type_module": "bricolage",
        "description": "Montage de meubles, pose de tringles, fixations, joints."
    },
    "Garde d’enfants de plus de 3 ans à domicile": {
        "tva": 10.0, "plafond_an": "12 000 € (+1 500 €/enfant)",
        "conso_defaut": 2.0, "type_module": "enfants",
        "description": "Sortie d'école, garde périscolaire, repas, accompagnement devoirs."
    },
    "Soutien scolaire ou cours à domicile": {
        "tva": 20.0, "plafond_an": "12 000 € / an / foyer",
        "conso_defaut": 2.0, "type_module": "scolaire",
        "description": "Aide aux devoirs, cours particuliers, révisions ciblées."
    },
    "Assistance informatique à domicile": {
        "tva": 20.0, "plafond_an": "3 000 € max / an / foyer",
        "conso_defaut": 3.0, "type_module": "informatique",
        "description": "Installation box, périphériques, nettoyage virus, formation."
    },
    "Assistance administrative à domicile": {
        "tva": 20.0, "plafond_an": "12 000 € / an / foyer",
        "conso_defaut": 3.0, "type_module": "admin",
        "description": "Tri de documents, rédaction de courriers, démarches en ligne."
    },
    "Préparation de repas à domicile": {
        "tva": 10.0, "plafond_an": "12 000 € / an / foyer",
        "conso_defaut": 4.0, "type_module": "repas",
        "description": "Courses d'appoint, épluchage, cuisson de repas équilibrés."
    },
    "Soins d’esthétique à domicile pour personnes dépendantes": {
        "tva": 20.0, "plafond_an": "12 000 € / an / foyer",
        "conso_defaut": 6.0, "type_module": "standard_heures",
        "description": "Soins de beauté, manucure et coiffure pour personnes en perte d'autonomie."
    },
    "Livraison de repas à domicile": {
        "tva": 10.0, "plafond_an": "12 000 € (en offre couplée)",
        "conso_defaut": 8.0, "type_module": "standard_heures",
        "description": "Portage de barquettes ou plateaux-repas au domicile."
    },
    "Livraison de courses à domicile": {
        "tva": 10.0, "plafond_an": "12 000 € (en offre couplée)",
        "conso_defaut": 6.0, "type_module": "standard_heures",
        "description": "Acheminement des provisions depuis le magasin jusqu'au domicile."
    },
    "Collecte et livraison de linge repassé": {
        "tva": 10.0, "plafond_an": "12 000 € (en offre couplée)",
        "conso_defaut": 5.0, "type_module": "standard_heures",
        "description": "Enlèvement, repassage et restitution du linge propre."
    },
    "Soins et promenades d’animaux pour personnes dépendantes": {
        "tva": 20.0, "plafond_an": "12 000 € (hors soins vétérinaires)",
        "conso_defaut": 3.0, "type_module": "standard_heures",
        "description": "Sortie d'hygiène, nourriture, brossage d'animaux de compagnie."
    },
    "Maintenance, entretien et vigilance temporaires à domicile": {
        "tva": 20.0, "plafond_an": "12 000 € / an / foyer",
        "conso_defaut": 3.0, "type_module": "standard_heures",
        "description": "Rondes d'aération, arrosage, relève du courrier pendant les absences."
    },
    "Accompagnement des enfants de plus de 3 ans aux déplacements": {
        "tva": 10.0, "plafond_an": "12 000 € / an / foyer",
        "conso_defaut": 5.0, "type_module": "standard_heures",
        "description": "Trajets pédestres ou transports vers école et activités extra-scolaires."
    },
    "Télé-assistance et visio-assistance": {
        "tva": 20.0, "plafond_an": "12 000 € / an / foyer",
        "conso_defaut": 10.0, "type_module": "standard_heures",
        "description": "Écoute, vérification et mise en service de matériel d'assistance connecté."
    },
    "Interprète en langue des signes": {
        "tva": 20.0, "plafond_an": "12 000 € / an / foyer",
        "conso_defaut": 2.0, "type_module": "standard_heures",
        "description": "Assistance à la communication et traduction LSF au domicile."
    },
    "Assistance aux personnes ayant besoin d'une aide temporaire": {
        "tva": 10.0, "plafond_an": "12 000 € (hors actes médicaux)",
        "conso_defaut": 4.0, "type_module": "standard_heures",
        "description": "Aide quotidienne de soutien après sortie d'hôpital ou convalescence."
    },
    "Conduite du véhicule des personnes en invalidité temporaire": {
        "tva": 10.0, "plafond_an": "12 000 € / an / foyer",
        "conso_defaut": 5.0, "type_module": "standard_heures",
        "description": "Chauffeur au volant du véhicule personnel du particulier convalescent."
    },
    "Accompagnement des personnes en invalidité temporaire": {
        "tva": 10.0, "plafond_an": "12 000 € / an / foyer",
        "conso_defaut": 4.0, "type_module": "standard_heures",
        "description": "Aide à la marche, sorties et courses de proximité."
    },
    "Coordination et délivrance des services à la personne": {
        "tva": 10.0, "plafond_an": "12 000 € / an / foyer",
        "conso_defaut": 5.0, "type_module": "standard_heures",
        "description": "Montage des plannings, évaluations à domicile et suivi qualité des intervenants."
    }
}

EXPLICATIONS_SIG = {
    "Valeur Ajoutée (VA)": "CA HT diminué des consommations externes (fournitures, matériel, carburant, IK). Cible SAP : ≥ 75 %.",
    "Charges de Personnel": "Masse salariale totale (directe terrain + trajet payé + indirects de bureau). Cible : ≤ 75 %.",
    "Excédent Brut d'Exploitation (EBE)": "Richesse brute restante après la masse salariale complète. Cible : ≥ 5 %.",
    "Résultat d'Exploitation (REX)": "Résultat net après frais fixes de siège, loyer, logiciels pro et amortissements. Cible : ≥ 4 %.",
    "Résultat Net": "Bénéfice final restant dans l'entreprise après déduction de l'IS. Cible plancher : ≥ 4 %."
}

# --- FONCTION DE GÉNÉRATION DU PDF ---
def generer_pdf(d):
    pdf = FPDF()
    pdf.add_page()
    
    # En-tête entreprise
    pdf.set_font("Helvetica", 'B', 14)
    pdf.cell(100, 8, d['entreprise_nom'] or "AGENCE SAP", border=0, align='L')
    pdf.set_font("Helvetica", 'B', 18)
    pdf.cell(90, 8, "DEVIS SERVICES À LA PERSONNE", border=0, ln=1, align='R')
    
    pdf.set_font("Helvetica", '', 9)
    pdf.cell(100, 5, d['entreprise_adresse'] or "Adresse non renseignée", border=0, ln=1, align='L')
    pdf.cell(100, 5, f"SIRET : {d['entreprise_siret'] or 'Non renseigné'}", border=0, ln=1, align='L')
    pdf.ln(8)
    
    # Bloc Client
    pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(100)
    pdf.cell(90, 6, f"Client : {d['client_prenom']} {d['client_nom']}", border=0, ln=1, align='L')
    pdf.set_font("Helvetica", '', 9)
    pdf.cell(100)
    pdf.cell(90, 5, d['client_adresse'], border=0, ln=1, align='L')
    pdf.cell(100)
    pdf.cell(90, 5, f"{d['client_cp']} {d['client_ville']}", border=0, ln=1, align='L')
    pdf.ln(10)
    
    # Détails devis
    pdf.cell(100, 5, f"Date : {datetime.now().strftime('%d/%m/%Y')}", border=0, ln=1, align='L')
    pdf.cell(100, 5, f"Activité déclarative : {d['activite']}", border=0, ln=1, align='L')
    pdf.cell(100, 5, f"Périodicité : {d['frequence']}", border=0, ln=1, align='L')
    pdf.ln(6)
    
    # Tableau de facturation
    pdf.set_font("Helvetica", 'B', 9)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(100, 7, " Prestation", border=1, align='L', fill=True)
    pdf.cell(30, 7, " Quantité", border=1, align='C', fill=True)
    pdf.cell(30, 7, " Prix Unit. HT", border=1, align='C', fill=True)
    pdf.cell(30, 7, " Total HT", border=1, ln=1, align='C', fill=True)
    
    pdf.set_font("Helvetica", '', 9)
    pdf.cell(100, 7, f" {d['activite'][:45]}", border=1, align='L')
    pdf.cell(30, 7, f"{d['temps_estime']:.2f} h", border=1, align='C')
    taux_ht = d['prix_prestation_ht'] / d['temps_estime']
    pdf.cell(30, 7, f"{taux_ht:.2f} EUR", border=1, align='C')
    pdf.cell(30, 7, f"{d['prix_prestation_ht']:.2f} EUR", border=1, ln=1, align='C')
    
    if d['prix_deplacement_ht'] > 0:
        pdf.cell(100, 7, " Forfait déplacement / logistique", border=1, align='L')
        pdf.cell(30, 7, "1", border=1, align='C')
        pdf.cell(30, 7, f"{d['prix_deplacement_ht']:.2f} EUR", border=1, align='C')
        pdf.cell(30, 7, f"{d['prix_deplacement_ht']:.2f} EUR", border=1, ln=1, align='C')
    pdf.ln(5)
    
    # Totaux
    pdf.cell(125)
    pdf.cell(35, 5, "Total HT :", border=0, align='R')
    pdf.cell(30, 5, f"{d['prix_vente_ht']:.2f} EUR", border=0, ln=1, align='R')
    pdf.cell(125)
    pdf.cell(35, 5, f"TVA ({d['taux_tva_pct']:.1f} %) :", border=0, align='R')
    pdf.cell(30, 5, f"{d['montant_tva']:.2f} EUR", border=0, ln=1, align='R')
    
    pdf.set_font("Helvetica", 'B', 11)
    pdf.cell(125)
    pdf.cell(35, 7, "TOTAL TTC :", border=0, align='R')
    pdf.cell(30, 7, f"{d['prix_vente_ttc']:.2f} EUR", border=0, ln=1, align='R')
    
    pdf.set_font("Helvetica", 'I', 10)
    pdf.set_text_color(0, 120, 0)
    pdf.cell(125)
    pdf.cell(35, 6, "Avance immédiate (50%) :", border=0, align='R')
    pdf.cell(30, 6, f"- {d['prix_apres_credit']:.2f} EUR", border=0, ln=1, align='R')
    
    pdf.set_font("Helvetica", 'B', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(125)
    pdf.cell(35, 7, "RESTE À CHARGE :", border=0, align='R')
    pdf.cell(30, 7, f"{d['prix_apres_credit']:.2f} EUR", border=0, ln=1, align='R')
    pdf.ln(6)
    
    pdf.set_font("Helvetica", 'I', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 4, f"Organisme déclaré de Services à la Personne. Plafond fiscal applicable : {d['plafond_fiscal']}", border=0, ln=1, align='L')
    
    return bytes(pdf.output())

# --- BARRE LATÉRALE : COORDONNÉES DE VOTRE ENTREPRISE ---
with st.sidebar:
    st.header("🏢 Votre Entreprise")
    ent_nom = st.text_input("Nom commercial", value="Mon Agence SAP")
    ent_adresse = st.text_input("Adresse de l'agence", value="10 rue de la République, 75001 Paris")
    ent_siret = st.text_input("Numéro SIRET", value="123 456 789 00012")
    st.info("💡 Ces données sont réutilisées sur chaque devis et sur le PDF exporté.")

# --- NAVIGATION PAR ONGLETS PRINCIPAUX ---
tab_devis, tab_params, tab_resultat = st.tabs([
    "📝 Saisie Devis Multi-Activités", 
    "⚙️ Paramètres Comptables & SIG", 
    "📊 Résultats & Analyse SIG"
])

# ==============================================================================
# ONGLET 2 : PARAMÈTRES COMPTABLES & STRUCTURE (Géré en mémoire de session)
# ==============================================================================
with tab_params:
    st.subheader("Charges Directes & Personnel de Terrain")
    c_p1, c_p2, c_p3 = st.columns(3)
    with c_p1:
        indemnite_km = st.number_input("Indemnité kilométrique intervenant (€/km)", value=0.50, step=0.05, format="%.2f")
    with c_p2:
        charges_patronales = st.number_input("Charges patronales directes [Moyenne 30 à 35 % | Max 42 %]", value=32.0, step=1.0, format="%.1f")
    with c_p3:
        improductif = st.number_input("Congés payés (10%) & temps inter-missions payés non facturés (%)", value=12.0, step=1.0, format="%.1f")

    st.subheader("Personnel Indirect, Structure & Objectifs Financiers (% du CA HT)")
    c_s1, c_s2, c_s3, c_s4 = st.columns(4)
    with c_s1:
        pers_indirect = st.number_input("Salaires encadrement / planning / bureau [Plafond : max 15 %]", value=10.0, step=1.0, format="%.1f")
    with c_s2:
        frais_siege = st.number_input("Frais de siège matériels (loyer, logiciel pro, compta) [Max 5 %]", value=4.0, step=0.5, format="%.1f")
    with c_s3:
        cible_net = st.number_input("Résultat net visé [Cible plancher : min 4 %]", value=4.0, step=0.5, format="%.1f")
    with c_s4:
        taux_is = st.number_input("Taux d'Impôt sur les Sociétés [PME réduit 15 % | Normal 25 %]", value=15.0, step=1.0, format="%.1f")

# ==============================================================================
# ONGLET 1 : SAISIE DEVIS & MODULES TECHNIQUES
# ==============================================================================
with tab_devis:
    st.subheader("1. Coordonnées du Prospect / Client")
    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
    with col_c1:
        cli_nom = st.text_input("Nom", value="Dupont")
    with col_c2:
        cli_prenom = st.text_input("Prénom", value="Claire")
    with col_c3:
        cli_adresse = st.text_input("Adresse", value="14 allée des Cerisiers")
    with col_c4:
        cli_cp = st.text_input("Code Postal", value="49450")

    # Recherche automatique de la commune via l'API geo.gouv
    cli_ville = ""
    if len(cli_cp.strip()) == 5 and cli_cp.strip().isdigit():
        try:
            r = requests.get(f"https://geo.api.gouv.fr/communes?codePostal={cli_cp.strip()}&fields=nom&format=json", timeout=2)
            villes = [item['nom'] for item in r.json()] if r.status_code == 200 else []
            if villes:
                cli_ville = st.selectbox("Ville (détectée)", villes)
            else:
                cli_ville = st.text_input("Ville", value="")
        except Exception:
            cli_ville = st.text_input("Ville", value="")
    else:
        cli_ville = st.text_input("Ville", value="")

    st.markdown("---")
    st.subheader("2. Sélection de l'Activité Déclarative")
    activite_choisie = st.selectbox("Activité SAP :", list(ACTIVITES_SAP.keys()))
    info_act = ACTIVITES_SAP[activite_choisie]

    st.caption(f"ℹ️ **Description** : {info_act['description']} | 🎯 **Plafond fiscal annuel** : {info_act['plafond_an']}")

    # Formulaire technique dynamique
    st.markdown("##### Paramètres techniques & Tâches métier")
    t_mod = info_act["type_module"]
    temps_brut = 2.0

    if t_mod == "menage":
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            surface_m2 = st.number_input("Surface du logement (m²)", value=80, step=5)
        with col_m2:
            pieces_eau = st.number_input("Pièces d'eau (Cuisine, SDB, WC)", value=2, step=1)
        with col_m3:
            opt_animaux = st.checkbox("Animaux domestiques (+10% temps)", value=False)
        with col_m4:
            opt_etage = st.checkbox("Logement à étage(s) (+10% temps)", value=False)
            
        t_base = surface_m2 * (1.5 / 60)
        maj = 1.0 + (pieces_eau * 0.15)
        if opt_animaux: maj += 0.10
        if opt_etage: maj += 0.10
        temps_brut = t_base * maj

    elif t_mod == "jardinage":
        col_j1, col_j2, col_j3, col_j4 = st.columns(4)
        with col_j1:
            pelouse_m2 = st.number_input("Tonte de pelouse (m²)", value=400, step=50)
        with col_j2:
            haie_ml = st.number_input("Taille de haie (mètres linéaires)", value=15, step=5)
        with col_j3:
            massif_m2 = st.number_input("Désherbage massifs (m²)", value=10, step=5)
        with col_j4:
            opt_dechets = st.checkbox("Évacuation déchetterie (+45 min)", value=False)
        temps_brut = (pelouse_m2 * 0.002) + (haie_ml * 0.08) + (massif_m2 * 0.04) + (0.75 if opt_dechets else 0.0)

    elif t_mod == "bricolage":
        brico_tache = st.selectbox("Tâche de petit bricolage (loi : max 2h par intervention)", [
            "Montage meuble en kit standard (1h30)",
            "Pose tringle à rideau / cadre / applique (0h45)",
            "Remplacement joint / robinetterie (0h45)",
            "Fixation d'étagères murales lourdes (1h00)",
            "Petites réparations diverses (1h00)",
            "Intervention bricolage maximale (2h00)"
        ])
        brico_map = {
            "Montage meuble en kit standard (1h30)": 1.5,
            "Pose tringle à rideau / cadre / applique (0h45)": 0.75,
            "Remplacement joint / robinetterie (0h45)": 0.75,
            "Fixation d'étagères murales lourdes (1h00)": 1.0,
            "Petites réparations diverses (1h00)": 1.0,
            "Intervention bricolage maximale (2h00)": 2.0
        }
        temps_brut = brico_map.get(brico_tache, 1.0)

    elif t_mod == "enfants":
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            nb_enfants = st.selectbox("Nombre d'enfants", ["1 enfant", "2 enfants (+15% temps)", "3 enfants et + (+25% temps)"])
        with col_e2:
            base_garde = st.number_input("Volume horaire requis (h)", value=2.5, step=0.5)
        maj_enf = 1.15 if "2 enfants" in nb_enfants else (1.25 if "3 enfants" in nb_enfants else 1.0)
        temps_brut = base_garde * maj_enf

    elif t_mod == "scolaire":
        col_sc1 = st.selectbox("Niveau scolaire", [
            "Primaire - Aide aux devoirs (1h00)",
            "Collège (1h30)",
            "Lycée (2h00)",
            "Supérieur (2h00)"
        ])
        scol_map = {"Primaire - Aide aux devoirs (1h00)": 1.0, "Collège (1h30)": 1.5, "Lycée (2h00)": 2.0, "Supérieur (2h00)": 2.0}
        temps_brut = scol_map.get(col_sc1, 1.5)

    elif t_mod == "informatique":
        col_inf = st.selectbox("Intervention informatique", [
            "Mise en service & Box (1h00)",
            "Nettoyage virus & lenteurs (1h30)",
            "Sauvegarde & Réinstallation OS (2h00)",
            "Formation & Initiation tablette/PC (1h00)"
        ])
        inf_map = {"Mise en service & Box (1h00)": 1.0, "Nettoyage virus & lenteurs (1h30)": 1.5, "Sauvegarde & Réinstallation OS (2h00)": 2.0, "Formation & Initiation tablette/PC (1h00)": 1.0}
        temps_brut = inf_map.get(col_inf, 1.0)

    elif t_mod == "admin":
        col_adm = st.selectbox("Assistance administrative", [
            "Tri & classement courrier standard (1h00)",
            "Démarches dématérialisées & dossiers (1h30)",
            "Assistance administrative complète (2h00)"
        ])
        adm_map = {"Tri & classement courrier standard (1h00)": 1.0, "Démarches dématérialisées & dossiers (1h30)": 1.5, "Assistance administrative complète (2h00)": 2.0}
        temps_brut = adm_map.get(col_adm, 1.5)

    elif t_mod == "repas":
        nb_repas = st.number_input("Nombre de repas à préparer", value=1, min_value=1, step=1)
        temps_brut = 1.25 + max(0, nb_repas - 1) * 0.5

    else:
        temps_brut = st.number_input("Volume horaire prévisionnel (heures)", value=2.0, step=0.5)

    # Option d'arrondi
    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        arrondir_quart_heure = st.checkbox("Arrondir le temps facturé au quart d'heure supérieur (15 min)", value=True)
    with col_opt2:
        frequence_visite = st.selectbox("Fréquence d'intervention", [
            "Hebdomadaire (1 fois/semaine)", 
            "Tous les 15 jours (bimensuel)", 
            "Ponctuel (unique)"
        ])

    temps_facture = math.ceil(temps_brut * 4) / 4 if arrondir_quart_heure else temps_brut

    st.markdown("---")
    st.subheader("3. Logistique de Déplacement & Tarification")
    col_t1, col_t2, col_t3, col_t4 = st.columns(4)
    with col_t1:
        distance_aller = st.number_input("Distance aller (km) [Zone idéale : ≤ 10-12 km]", value=8.0, step=1.0)
    with col_t2:
        is_intervacation = st.checkbox("Intervacation ≤ 30 min\n(Route payée au salarié & IK versées)", value=True)
    with col_t3:
        salaire_brut_horaire = st.number_input("Salaire brut horaire intervenant direct (€)", value=12.31, step=0.10)
    with col_t4:
        conso_ext_pct = st.number_input("Fournitures & consommables de l'activité (%)", value=float(info_act["conso_defaut"]), step=0.5)

    col_tar1, col_tar2 = st.columns(2)
    with col_tar1:
        taux_horaire_force = st.number_input("Taux horaire client TTC testé (€/h) [Laisser à 0 pour marge auto 15 %]", value=29.00, step=1.0)
        if taux_horaire_force > 0:
            st.success(f"👉 **Reste à charge réel pour le client (Avance immédiate 50%) : {taux_horaire_force / 2:.2f} € TTC/h**")
    with col_tar2:
        tva_options = [10.0, 20.0, 0.0]
        def_tva_index = tva_options.index(info_act["tva"]) if info_act["tva"] in tva_options else 0
        taux_tva_choisi = st.selectbox("Taux de TVA applicable", tva_options, index=def_tva_index, format_func=lambda x: f"{x:.1f} %")

# ==============================================================================
# CALCUL FINANCIER & SOLDES INTERMÉDIAIRES DE GESTION (SIG)
# ==============================================================================
# 1. Trajet & logistique
if is_intervacation and distance_aller > 0:
    frais_km_ht = distance_aller * 2 * indemnite_km
    temps_trajet_heures = (distance_aller * 2) / 30.0  # Vitesse moyenne 30 km/h
else:
    frais_km_ht = 0.0
    temps_trajet_heures = 0.0

frais_km_ttc = frais_km_ht * (1 + (taux_tva_choisi / 100))

# 2. Coût horaire chargé du personnel direct
coeff_charges = 1 + (charges_patronales / 100)
cout_horaire_charge = salaire_brut_horaire * coeff_charges * (1 + (improductif / 100))
cout_personnel_direct = (temps_facture + temps_trajet_heures) * cout_horaire_charge

# 3. Chiffre d'affaires & Tarification
taux_tva_coef = taux_tva_choisi / 100
if taux_horaire_force > 0:
    taux_horaire_client_ttc = float(taux_horaire_force)
    prestation_ttc = taux_horaire_client_ttc * temps_facture
    prix_vente_ttc = prestation_ttc + frais_km_ttc
    prix_vente_ht = prix_vente_ttc / (1 + taux_tva_coef)
else:
    cout_revient_ht = cout_personnel_direct + frais_km_ht
    prix_vente_ht = cout_revient_ht / (1 - 0.15)
    prix_vente_ttc = prix_vente_ht * (1 + taux_tva_coef)
    taux_horaire_client_ttc = (prix_vente_ttc - frais_km_ttc) / temps_facture

montant_tva = prix_vente_ttc - prix_vente_ht
prix_prestation_ht = (prix_vente_ttc - frais_km_ttc) / (1 + taux_tva_coef)
taux_horaire_ht = prix_prestation_ht / temps_facture

# 4. Soldes Intermédiaires de Gestion
conso_externes = frais_km_ht + (prix_vente_ht * (conso_ext_pct / 100))
valeur_ajoutee = prix_vente_ht - conso_externes
cout_personnel_indirect = prix_vente_ht * (pers_indirect / 100)
total_charges_personnel = cout_personnel_direct + cout_personnel_indirect

ebe = valeur_ajoutee - total_charges_personnel
frais_structure = prix_vente_ht * (frais_siege / 100)
rex = ebe - frais_structure
impots = max(0.0, rex * (taux_is / 100))
resultat_net = rex - impots

# Ratios en % du CA HT
ratio_va = (valeur_ajoutee / prix_vente_ht) * 100
ratio_personnel = (total_charges_personnel / prix_vente_ht) * 100
ratio_ebe = (ebe / prix_vente_ht) * 100
ratio_rex = (rex / prix_vente_ht) * 100
ratio_net = (resultat_net / prix_vente_ht) * 100

prix_apres_credit = prix_vente_ttc / 2
taux_h_apres_credit = taux_horaire_client_ttc / 2

# 5. Seuils de rentabilité (sans double comptage des IK)
taux_charges_structure = (conso_ext_pct / 100) + (pers_indirect / 100) + (frais_siege / 100)
marge_nette_horaire = (taux_horaire_ht * (1 - taux_charges_structure)) - cout_horaire_charge
cout_salaire_trajet = temps_trajet_heures * cout_horaire_charge

if marge_nette_horaire > 0:
    temps_min_rentable = max(1.5, cout_salaire_trajet / marge_nette_horaire) if cout_salaire_trajet > 0 else 1.5
else:
    temps_min_rentable = 3.0

budget_salaires_dispo = (prix_vente_ht * (1 - taux_charges_structure)) - frais_km_ht - cout_salaire_trajet
temps_max_rentable = max(temps_facture, budget_salaires_dispo / cout_horaire_charge)

# Mensualisation
if "Hebdomadaire" in frequence_visite:
    nb_int = 52
    txt_mensu = f"{(prix_vente_ttc * nb_int)/12:.2f} € TTC/mois (soit {(prix_apres_credit * nb_int)/12:.2f} € après crédit)"
elif "15 jours" in frequence_visite:
    nb_int = 26
    txt_mensu = f"{(prix_vente_ttc * nb_int)/12:.2f} € TTC/mois (soit {(prix_apres_credit * nb_int)/12:.2f} € après crédit)"
else:
    txt_mensu = "Prestation ponctuelle"

# Dictionnaire pour le PDF
donnees_pdf = {
    "entreprise_nom": ent_nom,
    "entreprise_adresse": ent_adresse,
    "entreprise_siret": ent_siret,
    "client_nom": cli_nom,
    "client_prenom": cli_prenom,
    "client_adresse": cli_adresse,
    "client_cp": cli_cp,
    "client_ville": cli_ville,
    "activite": activite_choisie,
    "temps_estime": temps_facture,
    "taux_horaire_client_ttc": taux_horaire_client_ttc,
    "prix_prestation_ht": prix_prestation_ht,
    "prix_deplacement_ht": frais_km_ht,
    "prix_vente_ht": prix_vente_ht,
    "taux_tva_pct": taux_tva_choisi,
    "montant_tva": montant_tva,
    "prix_vente_ttc": prix_vente_ttc,
    "prix_apres_credit": prix_apres_credit,
    "frequence": frequence_visite,
    "plafond_fiscal": info_act["plafond_an"]
}

# ==============================================================================
# ONGLET 3 : RÉSULTATS & ANALYSE FINANCIÈRE
# ==============================================================================
with tab_resultat:
    st.subheader(f"📊 Synthèse Financière : {activite_choisie}")
    
    if temps_facture < 2.0:
        st.warning("⚠️ **Alerte durée d'intervention** : Mission < 2 h. Risque élevé de sous-rentabilité logistique ou de refus d'intervention.")

    # Cartes de synthèse clés
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Temps facturé", f"{temps_facture:.2f} h", help="Durée de travail retenue sur place")
    kpi2.metric("Total TTC intervention", f"{prix_vente_ttc:.2f} €", f"{prix_vente_ht:.2f} € HT")
    kpi3.metric("Reste à charge client (-50%)", f"{prix_apres_credit:.2f} €", f"{taux_h_apres_credit:.2f} €/h")
    kpi4.metric("Mensualisation lissée", txt_mensu)

    st.markdown("---")
    st.subheader("Pilotage de la Rentabilité & Point Mort")
    col_p1, col_p2 = st.columns(2)
    h_min = int(temps_min_rentable)
    m_min = int(round((temps_min_rentable - h_min) * 60))
    with col_p1:
        st.info(f"⏱️ **Temps minimum conseillé pour amortir le déplacement** : **{temps_min_rentable:.2f} h** ({h_min}h{m_min:02d})")
    with col_p2:
        st.info(f"⏳ **Temps maximum sur place toléré avant déficit** : **{temps_max_rentable:.2f} h**")

    # Tableau d'analyse des Soldes Intermédiaires de Gestion
    st.subheader("Analyse des Soldes Intermédiaires de Gestion (SIG)")
    
    # Conditions de conformité conformes à vos souhaits :
    # - Charges de personnel : conforme si <= 75%
    # - VA, EBE, REX, Net : conforme dès que le seuil plancher est atteint ou dépassé
    cibles_sig = [
        {"SIG": "Valeur Ajoutée (VA)", "Montant HT": f"{valeur_ajoutee:.2f} €", "Ratio (% CA HT)": f"{ratio_va:.1f} %", "Cible Métier": "≥ 75 %", "Diagnostic": "CONFORME" if ratio_va >= 75.0 else "ATTENTION"},
        {"SIG": "Charges de Personnel", "Montant HT": f"{total_charges_personnel:.2f} €", "Ratio (% CA HT)": f"{ratio_personnel:.1f} %", "Cible Métier": "≤ 75 %", "Diagnostic": "CONFORME" if ratio_personnel <= 75.0 else "ATTENTION"},
        {"SIG": "Excédent Brut d'Exploitation (EBE)", "Montant HT": f"{ebe:.2f} €", "Ratio (% CA HT)": f"{ratio_ebe:.1f} %", "Cible Métier": "≥ 5 %", "Diagnostic": "CONFORME" if ratio_ebe >= 5.0 else "ATTENTION"},
        {"SIG": "Résultat d'Exploitation (REX)", "Montant HT": f"{rex:.2f} €", "Ratio (% CA HT)": f"{ratio_rex:.1f} %", "Cible Métier": "≥ 4 %", "Diagnostic": "CONFORME" if ratio_rex >= 4.0 else "ATTENTION"},
        {"SIG": "Résultat Net", "Montant HT": f"{resultat_net:.2f} €", "Ratio (% CA HT)": f"{ratio_net:.1f} %", "Cible Métier": f"≥ {cible_net:.1f} %", "Diagnostic": "CONFORME" if ratio_net >= cible_net else "ATTENTION"},
    ]
    
    df_sig = pd.DataFrame(cibles_sig)
    
    # Mise en couleur automatique
    def color_statut(val):
        color = '#d4edda; color: #155724;' if val == 'CONFORME' else '#f8d7da; color: #721c24;'
        return f'background-color: {color}; font-weight: bold;'
    
    st.table(df_sig.style.map(color_statut, subset=['Diagnostic']))

    # Descriptif pédagogique
    with st.expander("📖 Comprendre les Soldes Intermédiaires de Gestion en agence SAP"):
        for nom, desc in EXPLICATIONS_SIG.items():
            st.markdown(f"**{nom}** : {desc}")

    # Export PDF via st.download_button
    st.markdown("---")
    st.subheader("📥 Exportation du Devis Client")
    pdf_bytes = generer_pdf(donnees_pdf)
    st.download_button(
        label="Télécharger le Devis en PDF",
        data=pdf_bytes,
        file_name=f"Devis_{cli_nom}_{activite_choisie[:15].replace(' ', '_')}.pdf",
        mime="application/pdf"
    )