import subprocess
import sys
import os
import math
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from datetime import datetime
import urllib.request
import json
import ssl

try:
    from fpdf import FPDF
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fpdf2"])
    from fpdf import FPDF

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

donnees_devis = {}
FICHIER_CONFIG = "config_sap_villes.json"

# --- DÉFINITION DÉTAILLÉE DES 21 ACTIVITÉS & LEURS MODULES DE TÂCHES ---
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
        "description": "Courses d'appoint, épluchage, cuisson de plats frais et équilibrés."
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
        "description": "Acheminement des provisions depuis le magasin jusqu'aux placards."
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

TEMPS_PAR_M2 = 1.5 / 60
MAJORATION_PIECE_EAU = 0.15
VITESSE_MOYENNE_TRAJET = 30.0

EXPLICATIONS_SIG = {
    "Valeur Ajoutée (VA)": "CA HT - achats externes (fournitures, matériel, carburant, IK). Cible : ≥ 75 %.",
    "Charges de Personnel": "Masse salariale totale (directe terrain + indirecte encadrement). Cible : ≤ 75 %.",
    "Excédent Brut d'Exploitation (EBE)": "Richesse brute restante après masse salariale complète. Cible : ≥ 5 %.",
    "Résultat d'Exploitation (REX)": "Résultat net après frais fixes de siège, loyer et abonnements pro. Cible : ≥ 4 %.",
    "Résultat Net": "Bénéfice final de l'entreprise après déduction de l'IS. Cible plancher : ≥ 4 %."
}

def clean_float(val, default=0.0):
    if not val:
        return default
    return float(str(val).strip().replace(',', '.'))

def actualiser_reste_a_charge_live(*args):
    val = var_taux_force.get().strip().replace(',', '.')
    if val:
        try:
            t = float(val)
            label_live_rac.config(text=f"👉 Reste à charge client (Avance immédiate Urssaf) : {t/2:.2f} € TTC/h")
        except ValueError:
            label_live_rac.config(text="👉 Reste à charge client : saisie en cours...")
    else:
        label_live_rac.config(text="👉 Reste à charge client : calculé automatiquement si non forcé")

def chercher_villes(event=None):
    cp = var_cp.get().strip()
    if len(cp) == 5 and cp.isdigit():
        try:
            url = f"https://geo.api.gouv.fr/communes?codePostal={cp}&fields=nom&format=json"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, context=ctx, timeout=3) as response:
                data = json.loads(response.read().decode('utf-8'))
                villes = [item['nom'] for item in data]
                combo_ville['values'] = villes
                if villes:
                    combo_ville.set(villes[0])
                else:
                    combo_ville.set("Aucune ville trouvée")
        except Exception:
            combo_ville['values'] = ["Erreur connexion"]
            combo_ville.set("Saisie manuelle")
    else:
        combo_ville['values'] = []
        combo_ville.set('')

def afficher_details_sig(event=None):
    selection = tree_sig.selection()
    if selection:
        nom_sig = tree_sig.item(selection[0])['values'][0]
        label_explication_sig.config(text=f"📌 {nom_sig} :\n{EXPLICATIONS_SIG.get(nom_sig, '')}")

def sauvegarder_configuration():
    config = {
        "entreprise_nom": entry_entreprise_nom.get(),
        "entreprise_adresse": entry_entreprise_adresse.get(),
        "entreprise_siret": entry_entreprise_siret.get(),
        "salaire_brut": entry_salaire.get(),
        "indemnite_km": entry_indemnite_km.get(),
        "charges_patronales": entry_charges.get(),
        "improductif": entry_improductif.get(),
        "pers_indirect": entry_pers_indirect.get(),
        "frais_siege": entry_frais_siege.get(),
        "cible_net": entry_cible_net.get(),
        "is": entry_is.get(),
        "intervacation": var_intervacation.get(),
        "arrondi_quart_heure": var_arrondi.get()
    }
    try:
        with open(FICHIER_CONFIG, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        messagebox.showinfo("Succès", "Configuration sauvegardée.")
    except Exception as e:
        messagebox.showerror("Erreur", f"Échec de l'enregistrement :\n{str(e)}")

def charger_configuration():
    if not os.path.exists(FICHIER_CONFIG):
        return
    try:
        with open(FICHIER_CONFIG, "r", encoding="utf-8") as f:
            config = json.load(f)
        entry_entreprise_nom.delete(0, tk.END)
        entry_entreprise_nom.insert(0, config.get("entreprise_nom", ""))
        entry_entreprise_adresse.delete(0, tk.END)
        entry_entreprise_adresse.insert(0, config.get("entreprise_adresse", ""))
        entry_entreprise_siret.delete(0, tk.END)
        entry_entreprise_siret.insert(0, config.get("entreprise_siret", ""))
        if "salaire_brut" in config:
            entry_salaire.delete(0, tk.END)
            entry_salaire.insert(0, config["salaire_brut"])
        if "indemnite_km" in config:
            entry_indemnite_km.delete(0, tk.END)
            entry_indemnite_km.insert(0, config["indemnite_km"])
        if "charges_patronales" in config:
            entry_charges.delete(0, tk.END)
            entry_charges.insert(0, config["charges_patronales"])
        if "improductif" in config:
            entry_improductif.delete(0, tk.END)
            entry_improductif.insert(0, config["improductif"])
        if "pers_indirect" in config:
            entry_pers_indirect.delete(0, tk.END)
            entry_pers_indirect.insert(0, config["pers_indirect"])
        if "frais_siege" in config:
            entry_frais_siege.delete(0, tk.END)
            entry_frais_siege.insert(0, config["frais_siege"])
        if "cible_net" in config:
            entry_cible_net.delete(0, tk.END)
            entry_cible_net.insert(0, config["cible_net"])
        if "is" in config:
            entry_is.delete(0, tk.END)
            entry_is.insert(0, config["is"])
        if "intervacation" in config:
            var_intervacation.set(config["intervacation"])
        if "arrondi_quart_heure" in config:
            var_arrondi.set(config["arrondi_quart_heure"])
    except Exception:
        pass

def on_select_activite(event=None):
    act = combo_activite.get()
    info = ACTIVITES_SAP.get(act, {})
    
    tva_val = info.get("tva", 10.0)
    combo_tva.set(f"{tva_val:.1f} %")
    lbl_desc_activite.config(text=f"ℹ️ {info.get('description', '')}\n🎯 Plafond fiscal client : {info.get('plafond_an', '')}")
    
    # Masquer tous les frames spécialisés
    for f in modules_specifiques.values():
        f.pack_forget()

    # Afficher le frame adéquat
    t_mod = info.get("type_module", "standard_heures")
    if t_mod in modules_specifiques:
        modules_specifiques[t_mod].pack(fill="x", pady=3)
    else:
        modules_specifiques["standard_heures"].pack(fill="x", pady=3)

    entry_conso_ext.delete(0, tk.END)
    entry_conso_ext.insert(0, str(info.get("conso_defaut", 4.0)))

def remise_a_zero():
    entry_nom.delete(0, tk.END)
    entry_prenom.delete(0, tk.END)
    entry_adresse.delete(0, tk.END)
    var_cp.set("")
    combo_ville.set("")
    combo_ville['values'] = []
    
    # Réinitialisation des modules
    entry_surface.delete(0, tk.END)
    entry_pieces.delete(0, tk.END)
    entry_jardin_pelouse.delete(0, tk.END)
    entry_jardin_haie.delete(0, tk.END)
    entry_jardin_massif.delete(0, tk.END)
    var_jardin_dechets.set(False)
    var_bricolage_tache.set("Montage meuble en kit standard (1h30)")
    var_enfants_nb.set("1 enfant")
    var_scolaire_niveau.set("Collège (1h30)")
    var_informatique_type.set("Mise en service & Box (1h00)")
    entry_repas_nb.delete(0, tk.END)
    entry_heures_directes.delete(0, tk.END)
    
    entry_distance.delete(0, tk.END)
    var_taux_force.set("")
    var_animaux.set(False)
    var_etage.set(False)
    combo_frequence.set("Hebdomadaire (1 fois/semaine)")
    var_intervacation.set(True)

    global donnees_devis
    donnees_devis = {}
    label_resultat.config(text="Lancez le calcul pour visualiser l'analyse des SIG.")
    for row in tree_sig.get_children():
        tree_sig.delete(row)
    btn_export.pack_forget()
    messagebox.showinfo("Remise à zéro", "Devis réinitialisé. Les informations de votre entreprise sont conservées.")

def calculer_devis():
    global donnees_devis
    try:
        act = combo_activite.get()
        info = ACTIVITES_SAP.get(act, {})
        t_mod = info.get("type_module", "standard_heures")

        distance = clean_float(entry_distance.get())
        salaire_brut = clean_float(entry_salaire.get())
        taux_tva = clean_float(combo_tva.get().split()[0]) / 100
        is_intervacation = var_intervacation.get()

        indemnite_km = clean_float(entry_indemnite_km.get())
        taux_charges = clean_float(entry_charges.get())
        taux_improductif = clean_float(entry_improductif.get()) / 100
        taux_pers_indirect = clean_float(entry_pers_indirect.get()) / 100
        taux_frais_siege_hors_salaires = clean_float(entry_frais_siege.get()) / 100
        taux_consommables = clean_float(entry_conso_ext.get()) / 100
        taux_cible_net = clean_float(entry_cible_net.get()) / 100
        taux_is = clean_float(entry_is.get()) / 100

        # --- CALCUL DU TEMPS SELON LES PARAMÈTRES VARIABLES DE L'ACTIVITÉ ---
        temps_brut = 0.0

        if t_mod == "menage":
            surface = clean_float(entry_surface.get(), 0.0)
            pieces_eau = int(clean_float(entry_pieces.get(), 0))
            temps_base = surface * TEMPS_PAR_M2
            majoration = 1.0 + (pieces_eau * MAJORATION_PIECE_EAU)
            if var_animaux.get():
                majoration += 0.10
            if var_etage.get():
                majoration += 0.10
            temps_brut = temps_base * majoration

        elif t_mod == "jardinage":
            # 500 m² pelouse = ~1h (0.002 h/m²)
            pelouse_m2 = clean_float(entry_jardin_pelouse.get(), 0.0)
            t_pelouse = pelouse_m2 * 0.002
            # 1 mètre linéaire haie = ~0.08 h (5 min par mètre linéaire taillé)
            haie_ml = clean_float(entry_jardin_haie.get(), 0.0)
            t_haie = haie_ml * 0.08
            # 1 m² désherbage = ~0.04 h (25 m²/h)
            massif_m2 = clean_float(entry_jardin_massif.get(), 0.0)
            t_massif = massif_m2 * 0.04
            # Évacuation déchetterie = +45 min (0.75h)
            t_evac = 0.75 if var_jardin_dechets.get() else 0.0
            temps_brut = t_pelouse + t_haie + t_massif + t_evac

        elif t_mod == "bricolage":
            tache = var_bricolage_tache.get()
            brico_durees = {
                "Montage meuble en kit standard (1h30)": 1.5,
                "Pose tringle à rideau / cadre / applique (0h45)": 0.75,
                "Remplacement joint / robinetterie (0h45)": 0.75,
                "Fixation d'étagères lourdes murales (1h00)": 1.0,
                "Petites réparations diverses (1h00)": 1.0,
                "Intervention bricolage maximale (2h00)": 2.0
            }
            temps_brut = brico_durees.get(tache, 1.0)

        elif t_mod == "enfants":
            nb_enf = var_enfants_nb.get()
            base_garde = clean_float(entry_enfants_heures.get(), 2.0)
            maj_enf = 1.15 if "2 enfants" in nb_enf else (1.25 if "3 enfants" in nb_enf else 1.0)
            temps_brut = base_garde * maj_enf

        elif t_mod == "scolaire":
            niv = var_scolaire_niveau.get()
            scolaire_durees = {
                "Primaire - Aide aux devoirs (1h00)": 1.0,
                "Collège (1h30)": 1.5,
                "Lycée (2h00)": 2.0,
                "Supérieur (2h00)": 2.0
            }
            temps_brut = scolaire_durees.get(niv, 1.5)

        elif t_mod == "informatique":
            t_info = var_informatique_type.get()
            info_durees = {
                "Mise en service & Box (1h00)": 1.0,
                "Nettoyage virus & lenteurs (1h30)": 1.5,
                "Sauvegarde & Réinstallation OS (2h00)": 2.0,
                "Formation & Initiation tablette/PC (1h00)": 1.0
            }
            temps_brut = info_durees.get(t_info, 1.0)

        elif t_mod == "admin":
            vol = var_admin_volume.get()
            admin_durees = {
                "Tri & classement courrier standard (1h00)": 1.0,
                "Démarches dématérialisées & dossiers (1h30)": 1.5,
                "Assistance administrative complète (2h00)": 2.0
            }
            temps_brut = admin_durees.get(vol, 1.5)

        elif t_mod == "repas":
            nb_repas = int(clean_float(entry_repas_nb.get(), 1))
            # 1 repas complet = ~1h15, +30 min par repas supplémentaire
            temps_brut = 1.25 + max(0, nb_repas - 1) * 0.5

        else:
            temps_brut = clean_float(entry_heures_directes.get(), 2.0)

        # Arrondi au quart d'heure supérieur si coché
        if var_arrondi.get():
            temps_estime = math.ceil(temps_brut * 4) / 4
        else:
            temps_estime = temps_brut

        if temps_estime <= 0:
            raise ValueError

        # Trajet & Intervacation
        if is_intervacation and distance > 0:
            frais_km_ht = distance * 2 * indemnite_km
            temps_trajet_heures = (distance * 2) / VITESSE_MOYENNE_TRAJET
        else:
            frais_km_ht = 0.0
            temps_trajet_heures = 0.0

        frais_km_ttc = frais_km_ht * (1 + taux_tva)

        coeff_charges = 1 + (taux_charges / 100)
        cout_horaire_charge = salaire_brut * coeff_charges * (1 + taux_improductif)
        cout_personnel_direct = (temps_estime + temps_trajet_heures) * cout_horaire_charge

        # Prix de vente
        taux_h_force_str = var_taux_force.get().strip().replace(',', '.')
        if taux_h_force_str:
            taux_horaire_client_ttc = float(taux_h_force_str)
            prestation_ttc = taux_horaire_client_ttc * temps_estime
            prix_vente_ttc = prestation_ttc + frais_km_ttc
            prix_vente_ht = prix_vente_ttc / (1 + taux_tva)
        else:
            cout_revient_ht = cout_personnel_direct + frais_km_ht
            prix_vente_ht = cout_revient_ht / (1 - 0.15)
            prix_vente_ttc = prix_vente_ht * (1 + taux_tva)
            taux_horaire_client_ttc = (prix_vente_ttc - frais_km_ttc) / temps_estime

        montant_tva = prix_vente_ttc - prix_vente_ht
        prix_prestation_ht = (prix_vente_ttc - frais_km_ttc) / (1 + taux_tva)
        taux_horaire_ht = prix_prestation_ht / temps_estime

        # SIG
        conso_externes = frais_km_ht + (prix_vente_ht * taux_consommables)
        valeur_ajoutee = prix_vente_ht - conso_externes
        cout_personnel_indirect = prix_vente_ht * taux_pers_indirect
        total_charges_personnel = cout_personnel_direct + cout_personnel_indirect

        ebe = valeur_ajoutee - total_charges_personnel
        frais_structure = prix_vente_ht * taux_frais_siege_hors_salaires
        rex = ebe - frais_structure
        impots = max(0.0, rex * taux_is)
        resultat_net = rex - impots

        ratio_va = (valeur_ajoutee / prix_vente_ht) * 100
        ratio_personnel = (total_charges_personnel / prix_vente_ht) * 100
        ratio_ebe = (ebe / prix_vente_ht) * 100
        ratio_rex = (rex / prix_vente_ht) * 100
        ratio_net = (resultat_net / prix_vente_ht) * 100

        prix_apres_credit = prix_vente_ttc / 2
        taux_h_apres_credit = taux_horaire_client_ttc / 2

        freq = combo_frequence.get()
        if "Hebdomadaire" in freq:
            nb_interventions = 52
            txt_mensu = f"Mensualisation (52 sem/an) : {(prix_vente_ttc * nb_interventions) / 12:.2f} € TTC/mois (soit {(prix_apres_credit * nb_interventions) / 12:.2f} € après crédit)"
        elif "15 jours" in freq:
            nb_interventions = 26
            txt_mensu = f"Mensualisation (26 sem/an) : {(prix_vente_ttc * nb_interventions) / 12:.2f} € TTC/mois (soit {(prix_apres_credit * nb_interventions) / 12:.2f} € après crédit)"
        else:
            txt_mensu = "Prestation ponctuelle"

        # Seuil de rentabilité
        taux_charges_structure = taux_consommables + taux_pers_indirect + taux_frais_siege_hors_salaires
        marge_nette_horaire = (taux_horaire_ht * (1 - taux_charges_structure)) - cout_horaire_charge
        cout_salaire_trajet = temps_trajet_heures * cout_horaire_charge

        if marge_nette_horaire > 0:
            temps_min_rentable = max(1.5, cout_salaire_trajet / marge_nette_horaire) if cout_salaire_trajet > 0 else 1.5
        else:
            temps_min_rentable = 3.0

        budget_disponible = (prix_vente_ht * (1 - taux_charges_structure)) - frais_km_ht - cout_salaire_trajet
        temps_max_rentable = max(temps_estime, budget_disponible / cout_horaire_charge)

        donnees_devis = {
            "activite": act,
            "entreprise_nom": entry_entreprise_nom.get(),
            "entreprise_adresse": entry_entreprise_adresse.get(),
            "entreprise_siret": entry_entreprise_siret.get(),
            "client_nom": entry_nom.get(),
            "client_prenom": entry_prenom.get(),
            "client_adresse": entry_adresse.get(),
            "client_cp": var_cp.get(),
            "client_ville": combo_ville.get(),
            "temps_estime": temps_estime,
            "taux_horaire_client_ttc": taux_horaire_client_ttc,
            "prix_prestation_ht": prix_prestation_ht,
            "prix_deplacement_ht": frais_km_ht,
            "prix_vente_ht": prix_vente_ht,
            "taux_tva_pct": taux_tva * 100,
            "montant_tva": montant_tva,
            "prix_vente_ttc": prix_vente_ttc,
            "prix_apres_credit": prix_apres_credit,
            "frequence": freq,
            "mensualisation": txt_mensu,
            "plafond_fiscal": info.get("plafond_an", "")
        }

        h_min = int(temps_min_rentable)
        m_min = int(round((temps_min_rentable - h_min) * 60))
        alerte_duree = "⚠️ ATTENTION : Durée < 2 h. Risque de sous-rentabilité logistique ou refus intervenant.\n" if temps_estime < 2.0 else ""
        txt_intervac = "≤ 30 min (Trajet indemnisé)" if is_intervacation else "> 30 min (Pas de trajet indemnisé)"

        synth = (
            f"ACTIVITÉ : {act.upper()}\n"
            f"{alerte_duree}"
            f"Temps calculé : {temps_estime:.2f} h  |  Taux : {taux_horaire_client_ttc:.2f} € TTC/h ({taux_h_apres_credit:.2f} € après crédit)\n"
            f"Facturé par intervention : {prix_vente_ttc:.2f} € TTC ({prix_vente_ht:.2f} € HT)  --->  RESTE À CHARGE : {prix_apres_credit:.2f} €\n"
            f"📅 {txt_mensu}  |  Déplacement : {txt_intervac}\n"
            f"----------------------------------------------------------------------------------------------------\n"
            f"PILOTAGE : Temps min d'amortissement = {temps_min_rentable:.2f} h ({h_min}h{m_min:02d}) | Temps max toléré = {temps_max_rentable:.2f} h"
        )
        label_resultat.config(text=synth)

        for row in tree_sig.get_children():
            tree_sig.delete(row)

        cibles = [
            ("Valeur Ajoutée (VA)", f"{valeur_ajoutee:.2f} €", f"{ratio_va:.1f} %", "≥ 75 %", ratio_va >= 75.0),
            ("Charges de Personnel", f"{total_charges_personnel:.2f} €", f"{ratio_personnel:.1f} %", "≤ 75 %", ratio_personnel <= 75.0),
            ("Excédent Brut d'Exploitation (EBE)", f"{ebe:.2f} €", f"{ratio_ebe:.1f} %", "≥ 5 %", ratio_ebe >= 5.0),
            ("Résultat d'Exploitation (REX)", f"{rex:.2f} €", f"{ratio_rex:.1f} %", "≥ 4 %", ratio_rex >= 4.0),
            ("Résultat Net", f"{resultat_net:.2f} €", f"{ratio_net:.1f} %", f"≥ {taux_cible_net*100:.1f} %", ratio_net >= (taux_cible_net * 100)),
        ]

        for item in cibles:
            tag = "ok" if item[4] else "alerte"
            tree_sig.insert("", "end", values=(item[0], item[1], item[2], item[3], "CONFORME" if item[4] else "ATTENTION"), tags=(tag,))

        btn_export.pack(pady=8)
        notebook.select(frame_tab_resultat)

    except ValueError:
        messagebox.showerror("Erreur de saisie", "Veuillez vérifier les champs numériques.")

def exporter_pdf():
    if not donnees_devis:
        return
    fichier = filedialog.asksaveasfilename(
        parent=root, defaultextension=".pdf", filetypes=[("Fichiers PDF", "*.pdf")],
        initialfile=f"Devis_{donnees_devis['client_nom']}.pdf", title="Sauvegarder le devis"
    )
    if not fichier:
        return
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", 'B', 14)
        pdf.cell(100, 8, donnees_devis['entreprise_nom'], border=0, align='L')
        pdf.set_font("Helvetica", 'B', 20)
        pdf.cell(90, 8, "DEVIS SAP", border=0, ln=1, align='R')
        pdf.set_font("Helvetica", '', 10)
        pdf.cell(100, 5, donnees_devis['entreprise_adresse'], border=0, ln=1, align='L')
        pdf.cell(100, 5, f"SIRET : {donnees_devis['entreprise_siret']}", border=0, ln=1, align='L')
        pdf.ln(10)

        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(100)
        pdf.cell(90, 6, f"Client : {donnees_devis['client_prenom']} {donnees_devis['client_nom']}", border=0, ln=1, align='L')
        pdf.set_font("Helvetica", '', 10)
        pdf.cell(100)
        pdf.cell(90, 5, donnees_devis['client_adresse'], border=0, ln=1, align='L')
        pdf.cell(100)
        pdf.cell(90, 5, f"{donnees_devis['client_cp']} {donnees_devis['client_ville']}", border=0, ln=1, align='L')
        pdf.ln(12)

        pdf.cell(100, 6, f"Date : {datetime.now().strftime('%d/%m/%Y')}", border=0, ln=1, align='L')
        pdf.cell(100, 6, f"Prestation : {donnees_devis['activite']}", border=0, ln=1, align='L')
        pdf.cell(100, 6, f"Frequence : {donnees_devis['frequence']}", border=0, ln=1, align='L')
        pdf.ln(8)

        pdf.set_font("Helvetica", 'B', 10)
        pdf.set_fill_color(220, 220, 220)
        pdf.cell(100, 8, " Description", border=1, align='L', fill=True)
        pdf.cell(30, 8, " Quantite", border=1, align='C', fill=True)
        pdf.cell(30, 8, " Prix Unit. HT", border=1, align='C', fill=True)
        pdf.cell(30, 8, " Total HT", border=1, ln=1, align='C', fill=True)

        pdf.set_font("Helvetica", '', 10)
        pdf.cell(100, 8, f" {donnees_devis['activite'][:45]}", border=1, align='L')
        pdf.cell(30, 8, f"{donnees_devis['temps_estime']:.2f} h", border=1, align='C')
        taux_ht = donnees_devis['prix_prestation_ht'] / donnees_devis['temps_estime']
        pdf.cell(30, 8, f"{taux_ht:.2f} EUR", border=1, align='C')
        pdf.cell(30, 8, f"{donnees_devis['prix_prestation_ht']:.2f} EUR", border=1, ln=1, align='C')

        if donnees_devis['prix_deplacement_ht'] > 0:
            pdf.cell(100, 8, " Deplacement / Logistique tournee", border=1, align='L')
            pdf.cell(30, 8, "1", border=1, align='C')
            pdf.cell(30, 8, f"{donnees_devis['prix_deplacement_ht']:.2f} EUR", border=1, align='C')
            pdf.cell(30, 8, f"{donnees_devis['prix_deplacement_ht']:.2f} EUR", border=1, ln=1, align='C')
        pdf.ln(6)

        pdf.cell(125)
        pdf.cell(35, 6, "Total HT :", border=0, align='R')
        pdf.cell(30, 6, f"{donnees_devis['prix_vente_ht']:.2f} EUR", border=0, ln=1, align='R')
        pdf.cell(125)
        pdf.cell(35, 6, f"TVA ({donnees_devis['taux_tva_pct']:.1f} %) :", border=0, align='R')
        pdf.cell(30, 6, f"{donnees_devis['montant_tva']:.2f} EUR", border=0, ln=1, align='R')
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(125)
        pdf.cell(35, 8, "TOTAL TTC :", border=0, align='R')
        pdf.cell(30, 8, f"{donnees_devis['prix_vente_ttc']:.2f} EUR", border=0, ln=1, align='R')
        pdf.ln(3)

        pdf.set_font("Helvetica", 'I', 11)
        pdf.set_text_color(0, 100, 0)
        pdf.cell(125)
        pdf.cell(35, 6, "Credit d'impot SAP (50%) :", border=0, align='R')
        pdf.cell(30, 6, f"- {donnees_devis['prix_apres_credit']:.2f} EUR", border=0, ln=1, align='R')
        pdf.set_font("Helvetica", 'B', 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(125)
        pdf.cell(35, 8, "RESTE A CHARGE :", border=0, align='R')
        pdf.cell(30, 8, f"{donnees_devis['prix_apres_credit']:.2f} EUR", border=0, ln=1, align='R')
        pdf.ln(6)

        pdf.set_font("Helvetica", 'I', 9)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 5, f"Dispositif Services a la Personne. Plafond fiscal applicable : {donnees_devis['plafond_fiscal']}", border=0, ln=1, align='L')
        pdf.output(fichier)
        messagebox.showinfo("Succès", f"Devis PDF généré avec succès :\n{fichier}")
    except Exception as e:
        messagebox.showerror("Erreur d'export", f"Une erreur est survenue :\n{str(e)}")

# --- INTERFACE TKINTER ---
root = tk.Tk()
root.title("Suite Métier Multi-Activités Services à la Personne (SAP)")
root.geometry("890x1050")
style = ttk.Style()
style.theme_use('clam')

notebook = ttk.Notebook(root)
notebook.pack(pady=8, expand=True, fill='both')

frame_tab_saisie = ttk.Frame(notebook)
frame_tab_params = ttk.Frame(notebook)
frame_tab_resultat = ttk.Frame(notebook)

notebook.add(frame_tab_saisie, text="Saisie Devis & Tâches Métier")
notebook.add(frame_tab_params, text="Paramètres Comptables & SIG")
notebook.add(frame_tab_resultat, text="Résultats & Analyse SIG")

# === ONGLET 1 : SAISIE DEVIS ===
frame_entreprise = tk.LabelFrame(frame_tab_saisie, text="Votre Entreprise (Conservé)", padx=10, pady=3)
frame_entreprise.pack(fill="x", padx=10, pady=2)
tk.Label(frame_entreprise, text="Nom :").grid(row=0, column=0, sticky="w")
entry_entreprise_nom = ttk.Entry(frame_entreprise, width=32)
entry_entreprise_nom.grid(row=0, column=1)
tk.Label(frame_entreprise, text="Adresse :").grid(row=1, column=0, sticky="w")
entry_entreprise_adresse = ttk.Entry(frame_entreprise, width=32)
entry_entreprise_adresse.grid(row=1, column=1)
tk.Label(frame_entreprise, text="SIRET :").grid(row=2, column=0, sticky="w")
entry_entreprise_siret = ttk.Entry(frame_entreprise, width=32)
entry_entreprise_siret.grid(row=2, column=1)

frame_client = tk.LabelFrame(frame_tab_saisie, text="Coordonnées Client", padx=10, pady=3)
frame_client.pack(fill="x", padx=10, pady=2)
tk.Label(frame_client, text="Nom :").grid(row=0, column=0, sticky="w")
entry_nom = ttk.Entry(frame_client, width=32)
entry_nom.grid(row=0, column=1, pady=1)
tk.Label(frame_client, text="Prénom :").grid(row=1, column=0, sticky="w")
entry_prenom = ttk.Entry(frame_client, width=32)
entry_prenom.grid(row=1, column=1, pady=1)
tk.Label(frame_client, text="Adresse :").grid(row=2, column=0, sticky="w")
entry_adresse = ttk.Entry(frame_client, width=32)
entry_adresse.grid(row=2, column=1, pady=1)
tk.Label(frame_client, text="Code Postal :").grid(row=3, column=0, sticky="w")
var_cp = tk.StringVar()
entry_cp = ttk.Entry(frame_client, width=32, textvariable=var_cp)
entry_cp.grid(row=3, column=1, pady=1)
entry_cp.bind("<KeyRelease>", chercher_villes)
tk.Label(frame_client, text="Ville :").grid(row=4, column=0, sticky="w")
combo_ville = ttk.Combobox(frame_client, width=29)
combo_ville.grid(row=4, column=1, pady=1)

frame_act = tk.LabelFrame(frame_tab_saisie, text="Sélection de l'Activité SAP Déclarative", padx=10, pady=4)
frame_act.pack(fill="x", padx=10, pady=3)
combo_activite = ttk.Combobox(frame_act, values=list(ACTIVITES_SAP.keys()), state="readonly", width=68)
combo_activite.set("Entretien de la maison et travaux ménagers")
combo_activite.pack(fill="x", pady=2)
combo_activite.bind("<<ComboboxSelected>>", on_select_activite)

lbl_desc_activite = tk.Label(frame_act, text="", font=("Arial", 8, "italic"), fg="#004085", justify="left")
lbl_desc_activite.pack(anchor="w", pady=2)

# Cadre des modules de tâches spécialisés
frame_modules_container = tk.LabelFrame(frame_tab_saisie, text="Paramètres & Tâches Techniques de l'Activité", padx=10, pady=4)
frame_modules_container.pack(fill="x", padx=10, pady=3)

modules_specifiques = {}

# 1. Ménage
f_menage = ttk.Frame(frame_modules_container)
tk.Label(f_menage, text="Surface du logement (m²) :").grid(row=0, column=0, sticky="w")
entry_surface = ttk.Entry(f_menage, width=10)
entry_surface.grid(row=0, column=1, sticky="w")
tk.Label(f_menage, text="Pièces d'eau (Cuisine, SDB, WC) :").grid(row=1, column=0, sticky="w")
entry_pieces = ttk.Entry(f_menage, width=10)
entry_pieces.grid(row=1, column=1, sticky="w")
var_animaux = tk.BooleanVar(value=False)
ttk.Checkbutton(f_menage, text="Animaux (+10%)", variable=var_animaux).grid(row=2, column=0, sticky="w")
var_etage = tk.BooleanVar(value=False)
ttk.Checkbutton(f_menage, text="Étage(s) (+10%)", variable=var_etage).grid(row=2, column=1, sticky="w")
modules_specifiques["menage"] = f_menage

# 2. Jardinage
f_jardin = ttk.Frame(frame_modules_container)
tk.Label(f_jardin, text="Superficie tonte pelouse (m²) :").grid(row=0, column=0, sticky="w")
entry_jardin_pelouse = ttk.Entry(f_jardin, width=10)
entry_jardin_pelouse.grid(row=0, column=1, sticky="w")
tk.Label(f_jardin, text="Taille de haie (mètres linéaires) :").grid(row=1, column=0, sticky="w")
entry_jardin_haie = ttk.Entry(f_jardin, width=10)
entry_jardin_haie.grid(row=1, column=1, sticky="w")
tk.Label(f_jardin, text="Désherbage massifs / bêchage (m²) :").grid(row=2, column=0, sticky="w")
entry_jardin_massif = ttk.Entry(f_jardin, width=10)
entry_jardin_massif.grid(row=2, column=1, sticky="w")
var_jardin_dechets = tk.BooleanVar(value=False)
ttk.Checkbutton(f_jardin, text="Évacuation en déchetterie (+45 min)", variable=var_jardin_dechets).grid(row=3, column=0, columnspan=2, sticky="w")
modules_specifiques["jardinage"] = f_jardin

# 3. Bricolage
f_brico = ttk.Frame(frame_modules_container)
tk.Label(f_brico, text="Type de tâche (Plafonné à 2h max par la loi) :").grid(row=0, column=0, sticky="w")
var_bricolage_tache = tk.StringVar(value="Montage meuble en kit standard (1h30)")
combo_brico_tache = ttk.Combobox(f_brico, textvariable=var_bricolage_tache, state="readonly", width=45, values=[
    "Montage meuble en kit standard (1h30)",
    "Pose tringle à rideau / cadre / applique (0h45)",
    "Remplacement joint / robinetterie (0h45)",
    "Fixation d'étagères lourdes murales (1h00)",
    "Petites réparations diverses (1h00)",
    "Intervention bricolage maximale (2h00)"
])
combo_brico_tache.grid(row=0, column=1, sticky="w")
modules_specifiques["bricolage"] = f_brico

# 4. Garde d'enfants
f_enfants = ttk.Frame(frame_modules_container)
tk.Label(f_enfants, text="Nombre d'enfants :").grid(row=0, column=0, sticky="w")
var_enfants_nb = tk.StringVar(value="1 enfant")
combo_enf_nb = ttk.Combobox(f_enfants, textvariable=var_enfants_nb, state="readonly", width=18, values=["1 enfant", "2 enfants (+15% temps)", "3 enfants et + (+25% temps)"])
combo_enf_nb.grid(row=0, column=1, sticky="w")
tk.Label(f_enfants, text="Durée de garde requise (h) :").grid(row=1, column=0, sticky="w")
entry_enfants_heures = ttk.Entry(f_enfants, width=10)
entry_enfants_heures.insert(0, "2.0")
entry_enfants_heures.grid(row=1, column=1, sticky="w")
modules_specifiques["enfants"] = f_enfants

# 5. Soutien scolaire
f_scolaire = ttk.Frame(frame_modules_container)
tk.Label(f_scolaire, text="Niveau de cours :").grid(row=0, column=0, sticky="w")
var_scolaire_niveau = tk.StringVar(value="Collège (1h30)")
combo_scolaire_niv = ttk.Combobox(f_scolaire, textvariable=var_scolaire_niveau, state="readonly", width=35, values=[
    "Primaire - Aide aux devoirs (1h00)",
    "Collège (1h30)",
    "Lycée (2h00)",
    "Supérieur (2h00)"
])
combo_scolaire_niv.grid(row=0, column=1, sticky="w")
modules_specifiques["scolaire"] = f_scolaire

# 6. Informatique
f_info = ttk.Frame(frame_modules_container)
tk.Label(f_info, text="Prestation informatique :").grid(row=0, column=0, sticky="w")
var_informatique_type = tk.StringVar(value="Mise en service & Box (1h00)")
combo_info_t = ttk.Combobox(f_info, textvariable=var_informatique_type, state="readonly", width=38, values=[
    "Mise en service & Box (1h00)",
    "Nettoyage virus & lenteurs (1h30)",
    "Sauvegarde & Réinstallation OS (2h00)",
    "Formation & Initiation tablette/PC (1h00)"
])
combo_info_t.grid(row=0, column=1, sticky="w")
modules_specifiques["informatique"] = f_info

# 7. Administration
f_admin = ttk.Frame(frame_modules_container)
tk.Label(f_admin, text="Volume d'assistance :").grid(row=0, column=0, sticky="w")
var_admin_volume = tk.StringVar(value="Démarches dématérialisées & dossiers (1h30)")
combo_admin_v = ttk.Combobox(f_admin, textvariable=var_admin_volume, state="readonly", width=42, values=[
    "Tri & classement courrier standard (1h00)",
    "Démarches dématérialisées & dossiers (1h30)",
    "Assistance administrative complète (2h00)"
])
combo_admin_v.grid(row=0, column=1, sticky="w")
modules_specifiques["admin"] = f_admin

# 8. Préparation de repas
f_repas = ttk.Frame(frame_modules_container)
tk.Label(f_repas, text="Nombre de repas à préparer :").grid(row=0, column=0, sticky="w")
entry_repas_nb = ttk.Entry(f_repas, width=8)
entry_repas_nb.insert(0, "1")
entry_repas_nb.grid(row=0, column=1, sticky="w")
modules_specifiques["repas"] = f_repas

# 9. Module Heures standard
f_heures_std = ttk.Frame(frame_modules_container)
tk.Label(f_heures_std, text="Durée d'intervention prévisionnelle (heures) :").grid(row=0, column=0, sticky="w")
entry_heures_directes = ttk.Entry(f_heures_std, width=10)
entry_heures_directes.insert(0, "2.0")
entry_heures_directes.grid(row=0, column=1, sticky="w")
modules_specifiques["standard_heures"] = f_heures_std

# Paramètres logistiques et financiers communs
frame_communs = tk.LabelFrame(frame_tab_saisie, text="Logistique, Trajet & Tarification", padx=10, pady=4)
frame_communs.pack(fill="x", padx=10, pady=2)

var_arrondi = tk.BooleanVar(value=True)
ttk.Checkbutton(frame_communs, text="Arrondir au 1/4 h supérieur", variable=var_arrondi).grid(row=0, column=0, sticky="w")

tk.Label(frame_communs, text="Fréquence :").grid(row=1, column=0, sticky="w")
combo_frequence = ttk.Combobox(frame_communs, width=28, values=["Hebdomadaire (1 fois/semaine)", "Tous les 15 jours (bimensuel)", "Ponctuel (unique)"], state="readonly")
combo_frequence.set("Hebdomadaire (1 fois/semaine)")
combo_frequence.grid(row=1, column=1, sticky="w")

tk.Label(frame_communs, text="Distance aller (km) [Zone idéale : ≤ 10 à 12 km] :").grid(row=2, column=0, sticky="w")
entry_distance = ttk.Entry(frame_communs, width=10)
entry_distance.grid(row=2, column=1, sticky="w")

var_intervacation = tk.BooleanVar(value=True)
ttk.Checkbutton(frame_communs, text="Intervacation ≤ 30 min (Mission chaînée : temps de route payé & IK versées)", variable=var_intervacation).grid(row=3, column=0, columnspan=2, sticky="w")

tk.Label(frame_communs, text="Salaire brut horaire intervenant (€) :").grid(row=4, column=0, sticky="w")
entry_salaire = ttk.Entry(frame_communs, width=10)
entry_salaire.insert(0, "12.31")
entry_salaire.grid(row=4, column=1, sticky="w")

tk.Label(frame_communs, text="Taux horaire TTC testé (€/h) [Optionnel] :", font=("Arial", 9, "italic"), fg="#004085").grid(row=5, column=0, sticky="w")
var_taux_force = tk.StringVar()
var_taux_force.trace_add("write", actualiser_reste_a_charge_live)
entry_taux_h_force = ttk.Entry(frame_communs, width=10, textvariable=var_taux_force)
entry_taux_h_force.grid(row=5, column=1, sticky="w")

label_live_rac = tk.Label(frame_communs, text="👉 Reste à charge client : calculé automatiquement si non forcé", font=("Arial", 9, "bold"), fg="#155724")
label_live_rac.grid(row=6, column=0, columnspan=2, sticky="w")

tk.Label(frame_communs, text="Taux de TVA :").grid(row=7, column=0, sticky="w")
combo_tva = ttk.Combobox(frame_communs, width=10, values=["10.0 %", "20.0 %", "0.0 %"], state="readonly")
combo_tva.set("10.0 %")
combo_tva.grid(row=7, column=1, sticky="w")

frame_boutons_actions = ttk.Frame(frame_tab_saisie)
frame_boutons_actions.pack(fill="x", padx=10, pady=6)
btn_calcul = tk.Button(frame_boutons_actions, text="Calculer et Analyser les SIG", font=("Arial", 11, "bold"), bg="#0052cc", fg="white", command=calculer_devis)
btn_calcul.pack(side="left", expand=True, fill="x", padx=2)
btn_reset = tk.Button(frame_boutons_actions, text="🔄 Remise à zéro devis", font=("Arial", 10, "bold"), bg="#6c757d", fg="white", command=remise_a_zero)
btn_reset.pack(side="right", padx=2)
btn_save_config = tk.Button(frame_boutons_actions, text="💾 Enregistrer configuration", font=("Arial", 10, "bold"), bg="#17a2b8", fg="white", command=sauvegarder_configuration)
btn_save_config.pack(side="right", padx=2)

# === ONGLET 2 : PARAMÈTRES COMPTABLES & SIG ===
frame_params_op = tk.LabelFrame(frame_tab_params, text="Charges Directes & Personnel de Terrain", padx=10, pady=5)
frame_params_op.pack(fill="x", padx=10, pady=5)
tk.Label(frame_params_op, text="Indemnité kilométrique intervenant (€/km) :").grid(row=0, column=0, sticky="w", pady=4)
entry_indemnite_km = ttk.Entry(frame_params_op, width=10)
entry_indemnite_km.insert(0, "0.50")
entry_indemnite_km.grid(row=0, column=1)

tk.Label(frame_params_op, text="Charges patronales intervenants direct [Moyen 30 à 35 %] :").grid(row=1, column=0, sticky="w", pady=4)
entry_charges = ttk.Entry(frame_params_op, width=10)
entry_charges.insert(0, "32")
entry_charges.grid(row=1, column=1)

tk.Label(frame_params_op, text="Congés payés (10%) & temps inter-missions payés non facturés (%) :").grid(row=2, column=0, sticky="w", pady=4)
entry_improductif = ttk.Entry(frame_params_op, width=10)
entry_improductif.insert(0, "12.0")
entry_improductif.grid(row=2, column=1)

frame_params_sig = tk.LabelFrame(frame_tab_params, text="Personnel Indirect, Frais de Siège & Objectifs (% CA HT)", padx=12, pady=8)
frame_params_sig.pack(fill="x", padx=10, pady=5)
tk.Label(frame_params_sig, text="Salaires personnel indirect / encadrement [Max 15 %] :").grid(row=0, column=0, sticky="w", pady=4)
entry_pers_indirect = ttk.Entry(frame_params_sig, width=8)
entry_pers_indirect.insert(0, "10.0")
entry_pers_indirect.grid(row=0, column=1, sticky="e")

tk.Label(frame_params_sig, text="Consommables, carburant & petit outillage [Conseillé 4 à 8 %] :").grid(row=1, column=0, sticky="w", pady=4)
entry_conso_ext = ttk.Entry(frame_params_sig, width=8)
entry_conso_ext.insert(0, "4.0")
entry_conso_ext.grid(row=1, column=1, sticky="e")

tk.Label(frame_params_sig, text="Frais de siège matériels & amortissements [Max 5 %] :").grid(row=2, column=0, sticky="w", pady=4)
entry_frais_siege = ttk.Entry(frame_params_sig, width=8)
entry_frais_siege.insert(0, "4.0")
entry_frais_siege.grid(row=2, column=1, sticky="e")

tk.Label(frame_params_sig, text="Résultat net visé [Cible plancher : min 4 %] :").grid(row=3, column=0, sticky="w", pady=4)
entry_cible_net = ttk.Entry(frame_params_sig, width=8)
entry_cible_net.insert(0, "4.0")
entry_cible_net.grid(row=3, column=1, sticky="e")

tk.Label(frame_params_sig, text="Taux IS [PME 15 % | Max 25 %] :").grid(row=4, column=0, sticky="w", pady=4)
entry_is = ttk.Entry(frame_params_sig, width=8)
entry_is.insert(0, "15.0")
entry_is.grid(row=4, column=1, sticky="e")

btn_save_config_tab2 = tk.Button(frame_tab_params, text="💾 Enregistrer la configuration par défaut", font=("Arial", 11, "bold"), bg="#17a2b8", fg="white", command=sauvegarder_configuration)
btn_save_config_tab2.pack(pady=10)

# === ONGLET 3 : RÉSULTATS & ANALYSE SIG ===
label_resultat = tk.Label(frame_tab_resultat, text="Lancez le calcul pour visualiser l'analyse des SIG.", font=("Arial", 10, "bold"), justify="center")
label_resultat.pack(pady=10)

frame_tableau = ttk.Frame(frame_tab_resultat)
frame_tableau.pack(fill="both", expand=True, padx=10, pady=5)

cols = ("sig", "montant", "ratio", "cible", "statut")
tree_sig = ttk.Treeview(frame_tableau, columns=cols, show="headings", height=5)
tree_sig.heading("sig", text="Solde de Gestion (SIG)")
tree_sig.heading("montant", text="Montant HT (€)")
tree_sig.heading("ratio", text="Ratio (% CA HT)")
tree_sig.heading("cible", text="Cible Métier")
tree_sig.heading("statut", text="Diagnostic")

tree_sig.column("sig", width=220, anchor="w")
tree_sig.column("montant", width=100, anchor="center")
tree_sig.column("ratio", width=110, anchor="center")
tree_sig.column("cible", width=100, anchor="center")
tree_sig.column("statut", width=110, anchor="center")
tree_sig.pack(fill="both", expand=True)

tree_sig.bind("<<TreeviewSelect>>", afficher_details_sig)
tree_sig.tag_configure("ok", foreground="#155724", background="#d4edda")
tree_sig.tag_configure("alerte", foreground="#721c24", background="#f8d7da")

frame_pedago = tk.LabelFrame(frame_tab_resultat, text="Comprendre le solde sélectionné", padx=10, pady=6)
frame_pedago.pack(fill="x", padx=10, pady=5)
label_explication_sig = tk.Label(frame_pedago, text="💡 Cliquez sur une ligne du tableau ci-dessus pour lire sa définition.", font=("Arial", 9), justify="left", wraplength=780, fg="#222222")
label_explication_sig.pack(fill="x", anchor="w")

btn_export = tk.Button(frame_tab_resultat, text="📥 Exporter le devis en PDF", font=("Arial", 11, "bold"), bg="#28a745", fg="white", command=exporter_pdf)

# Initialisation
charger_configuration()
on_select_activite()

root.mainloop()