import json
import os
import random
from datetime import datetime, timedelta
from PIL import Image
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# ==========================================
# 1. CONFIGURATION & RAFRAÎCHISSEMENT AUTO
# ==========================================
st.set_page_config(
    page_title="Mon Cochon d'Inde",
    page_icon="🐹",
    layout="wide",
)

st_autorefresh(interval=10000, key="datarefresh")

SAVE_FILE = "save_cavy.json"
IMAGE_FILE = "watermarked_img_2562265923558829485.jpg"
MAX_ACTIONS_PAR_HEURE = 10  # 10 actions max sur une fenêtre de 60 minutes


# ==========================================
# 2. LOGIQUE DE SAUVEGARDE & ÉTAT
# ==========================================
def charger_sauvegarde():
  defauts = {
      "faim": 80,
      "hygiene": 80,
      "bonheur": 80,
      "energie": 80,
      "malade": False,
      "mort": False,
      "zero_since": None,
      "animation": "sain",
      "anim_time": datetime.now().isoformat(),
      "last_update": datetime.now().isoformat(),
      "action_timestamps": [],  # Liste des horodatages des actions reçues
      "message": "Couik couik ! Bienvenue !",
  }

  if os.path.exists(SAVE_FILE):
    try:
      with open(SAVE_FILE, "r") as f:
        donnees = json.load(f)
        for cle, valeur in defauts.items():
          if cle not in donnees:
            donnees[cle] = valeur
        return donnees
    except:
      return defauts
  else:
    return defauts


def sauvegarder(etat):
  with open(SAVE_FILE, "w") as f:
    json.dump(etat, f)


def clamp(val):
  return max(0, min(100, val))


etat = charger_sauvegarde()
maintenant = datetime.now()
une_heure_de_la = maintenant - timedelta(hours=1)

# Nettoyage des horodatages de plus de 60 minutes
timestamps_valides = []
for ts_str in etat.get("action_timestamps", []):
  try:
    ts = datetime.fromisoformat(ts_str)
    if ts > une_heure_de_la:
      timestamps_valides.append(ts_str)
  except:
    pass

etat["action_timestamps"] = timestamps_valides
sauvegarder(etat)

# ==========================================
# 3. DÉCOUPAGE DE L'IMAGE
# ==========================================
@st.cache_data
def load_images():
  try:
    img = Image.open(IMAGE_FILE)
    w, h = img.size
    return {
        "sain": img.crop((0, 0, w / 2, h / 2)),
        "malade": img.crop((w / 2, 0, w, h / 2)),
        "mange": img.crop((0, h / 2, w / 2, h)),
        "joue": img.crop((w / 2, h / 2, w, h)),
    }
  except Exception as e:
    st.error(
        f"Erreur d'image : Vérifie que '{IMAGE_FILE}' est bien sur GitHub."
        f" ({e})"
    )
    return None


images = load_images()

# ==========================================
# 4. GESTION DE LA MORT ET DU DÉLAI DE GRÂCE
# ==========================================
if etat.get("mort", False):
  st.markdown(
      "<h1 style='text-align: center; color: #7f8c8d;'>🌈 Un bel"
      " hommage...</h1>",
      unsafe_allow_html=True,
  )
  if images:
    col_img1, col_img2, col_img3 = st.columns([1, 2, 1])
    with col_img2:
      st.image(images["malade"], use_container_width=True)
  st.error("💀 Ton cochon d'inde s'est éteint faute de soins...")
  if st.button("🌻 Adopter un nouveau cochon d'inde", use_container_width=True):
    if os.path.exists(SAVE_FILE):
      os.remove(SAVE_FILE)
    st.rerun()
  st.stop()

# Écoulement du temps
derniere_maj = datetime.fromisoformat(etat["last_update"])
minutes_ecoulees = (maintenant - derniere_maj).total_seconds() / 60.0

if minutes_ecoulees >= 1:
  perte = int(minutes_ecoulees * 1)
  etat["faim"] = clamp(etat["faim"] - perte)
  etat["hygiene"] = clamp(etat["hygiene"] - perte)
  etat["bonheur"] = clamp(etat["bonheur"] - perte)
  etat["energie"] = clamp(etat["energie"] - perte)
  etat["last_update"] = maintenant.isoformat()

  if not etat["malade"] and (etat["hygiene"] < 30 or etat["faim"] < 30):
    if random.random() < 0.10:
      etat["malade"] = True
      etat["message"] = "Atchoum... Je ne me sens pas très bien..."
      etat["animation"] = "malade"

  sauvegarder(etat)

# Délai de grâce (24h)
if etat["faim"] == 0 or etat["energie"] == 0:
  if etat.get("zero_since") is None:
    etat["zero_since"] = maintenant.isoformat()
    sauvegarder(etat)
  else:
    debut_zero = datetime.fromisoformat(etat["zero_since"])
    heures_a_zero = (maintenant - debut_zero).total_seconds() / 3600.0

    if heures_a_zero >= 24:
      etat["mort"] = True
      sauvegarder(etat)
      st.rerun()
    else:
      heures_restantes = max(1, int(24 - heures_a_zero))
      st.warning(
          "⚠️ **Urgence absolue !** Ton cochon d'inde est épuisé ou affamé. Il"
          f" lui reste environ **{heures_restantes}h** avant de s'éteindre !"
      )
else:
  if etat.get("zero_since") is not None:
    etat["zero_since"] = None
    sauvegarder(etat)

# Visuel normal après 10s
anim_time = datetime.fromisoformat(etat["anim_time"])
if (
    etat["animation"] in ["mange", "joue"]
    and (maintenant - anim_time).total_seconds() > 10
):
  etat["animation"] = "malade" if etat["malade"] else "sain"
  sauvegarder(etat)


# ==========================================
# 5. LOGIQUE DES ACTIONS AVEC HEURE GLISSANTE
# ==========================================
def faire_action(
    faim=0,
    hygiene=0,
    bonheur=0,
    energie=0,
    anim="sain",
    msg="",
    est_nourriture=False,
):
  now = datetime.now()
  limite_60_min = now - timedelta(hours=1)

  # Récupérer uniquement les actions faites lors des 60 dernières minutes
  actions_recents = [
      datetime.fromisoformat(ts)
      for ts in etat.get("action_timestamps", [])
      if datetime.fromisoformat(ts) > limite_60_min
  ]

  # Vérification du quota
  if len(actions_recents) >= MAX_ACTIONS_PAR_HEURE:
    plus_ancienne = min(actions_recents)
    temps_attente_min = int(
        (3600 - (now - plus_ancienne).total_seconds()) // 60 + 1
    )
    etat["message"] = (
        f"⏳ Oula ! Je suis fatigué... Reviens dans environ"
        f" {temps_attente_min} min pour la prochaine action !"
    )
    sauvegarder(etat)
    st.rerun()
    return

  if etat["malade"] and anim != "sain":
    etat["message"] = "Je suis trop malade pour ça... Soigne-moi d'abord !"
  else:
    # Ajouter la date/heure de l'action actuelle
    actions_recents.append(now)
    etat["action_timestamps"] = [ts.isoformat() for ts in actions_recents]

    if est_nourriture and etat["faim"] >= 90:
      etat["malade"] = True
      etat["animation"] = "malade"
      etat["hygiene"] = clamp(etat["hygiene"] - 15)
      etat["energie"] = clamp(etat["energie"] - 10)
      etat["message"] = "Ouch... J'ai trop mangé, j'ai super mal au ventre... 🤢"
      etat["anim_time"] = now.isoformat()
    else:
      etat["faim"] = clamp(etat["faim"] + faim)
      etat["hygiene"] = clamp(etat["hygiene"] + hygiene)
      etat["bonheur"] = clamp(etat["bonheur"] + bonheur)
      etat["energie"] = clamp(etat["energie"] + energie)
      etat["animation"] = anim
      etat["anim_time"] = now.isoformat()
      etat["message"] = msg

      if anim == "sain" and etat["malade"]:
        etat["malade"] = False

  sauvegarder(etat)
  st.rerun()


# ==========================================
# 6. INTERFACE UTILISATEUR
# ==========================================
st.markdown(
    "<h2 style='text-align: center; color: #D35400; margin-bottom:"
    " 15px;'>🐹 Mon Tamagotchi</h2>",
    unsafe_allow_html=True,
)

col_visuel, col_commandes = st.columns([1, 1], gap="medium")

with col_visuel:
  if images:
    st.image(images[etat["animation"]], use_container_width=True)

  st.markdown(
      f"<div style='text-align: center; font-size: 17px; font-style: italic;"
      " padding: 10px; background-color: #f0f2f6; border-radius: 10px;"
      f" margin-top: 10px;'>« {etat['message']} »</div>",
      unsafe_allow_html=True,
  )

with col_commandes:
  # Jauges
  g1, g2 = st.columns(2)
  g1.metric("🍎 Faim", f"{etat['faim']}%")
  g1.progress(etat["faim"] / 100)

  g2.metric("✨ Hygiène", f"{etat['hygiene']}%")
  g2.progress(etat["hygiene"] / 100)

  g3, g4 = st.columns(2)
  g3.metric("❤️ Bonheur", f"{etat['bonheur']}%")
  g3.progress(etat["bonheur"] / 100)

  g4.metric("⚡ Énergie", f"{etat['energie']}%")
  g4.progress(etat["energie"] / 100)

  # Affichage des actions restantes (heure glissante)
  nb_actions_60m = len(etat.get("action_timestamps", []))
  actions_restantes = max(0, MAX_ACTIONS_PAR_HEURE - nb_actions_60m)
  st.caption(
      f"🎯 **Actions disponibles (sur les 60 dernières minutes) :**"
      f" {actions_restantes} / {MAX_ACTIONS_PAR_HEURE}"
  )

  st.divider()

  # Actions
  t_nourrir, t_soins, t_jouer = st.tabs(["🍎 Nourrir", "🛁 Soins", "🎾 Jouer"])

  with t_nourrir:
    if st.button("Donner des Légumes 🥒", use_container_width=True):
      faire_action(
          faim=30,
          hygiene=-5,
          anim="mange",
          msg="Crounch crounch !",
          est_nourriture=True,
      )
    if st.button("Donner du Foin 🌾", use_container_width=True):
      faire_action(
          faim=15,
          bonheur=5,
          anim="mange",
          msg="Le foin, c'est bon !",
          est_nourriture=True,
      )
    if st.button("Donner une Friandise 🍓", use_container_width=True):
      faire_action(
          faim=10,
          bonheur=20,
          anim="mange",
          msg="Mmmh une fraise !",
          est_nourriture=True,
      )

  with t_soins:
    if etat["malade"]:
      if st.button("💊 Donner un Médicament", use_container_width=True):
        faire_action(
            bonheur=10,
            energie=20,
            anim="sain",
            msg="Ouf... Le médicament fait effet !",
        )
    if st.button("Changer la litière ✨", use_container_width=True):
      faire_action(
          hygiene=50,
          bonheur=10,
          energie=-10,
          anim="sain",
          msg="Une cage toute propre !",
      )
    if st.button("Faire une sieste 💤", use_container_width=True):
      faire_action(
          energie=50,
          faim=-10,
          anim="sain",
          msg="Zzz... Une bonne sieste...",
      )

  with t_jouer:
    if st.button("Popcorning dans le parc 🏃‍♂️", use_container_width=True):
      faire_action(
          bonheur=35,
          faim=-15,
          energie=-20,
          anim="joue",
          msg="Pop ! Pop ! Je saute !",
      )
    if st.button("Jouer avec la balle 🎾", use_container_width=True):
      faire_action(
          bonheur=20,
          energie=-10,
          anim="joue",
          msg="Je pousse la balle !",
      )
