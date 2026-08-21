import streamlit as st
import json
import os
import random
from PIL import Image

# ==========================================
# 1. CONFIGURATION & CONSTANTES
# ==========================================
st.set_page_config(page_title="Mon Cochon d'Inde Virtuel", page_icon="🐹", layout="centered")

SAVE_FILE = "save_cavy.json"
# Nom exact de l'image générée contenant les 4 expressions
IMAGE_FILE = "watermarked_img_2562265923558829485.jpg" 

# ==========================================
# 2. FONCTIONS DE SAUVEGARDE ET GESTION D'ÉTAT
# ==========================================
def load_state():
    """Charge la sauvegarde si elle existe, sinon initialise les valeurs par défaut."""
    if 'faim' not in st.session_state:
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, 'r') as f:
                data = json.load(f)
                for key, value in data.items():
                    st.session_state[key] = value
        else:
            reset_game()

def save_game():
    """Sauvegarde l'état actuel dans un fichier JSON."""
    data = {
        'faim': st.session_state.faim,
        'hygiene': st.session_state.hygiene,
        'bonheur': st.session_state.bonheur,
        'energie': st.session_state.energie,
        'etat': st.session_state.etat,
        'message': st.session_state.message
    }
    with open(SAVE_FILE, 'w') as f:
        json.dump(data, f)

def reset_game():
    """Réinitialise le cochon d'inde."""
    st.session_state.faim = 80
    st.session_state.hygiene = 80
    st.session_state.bonheur = 80
    st.session_state.energie = 80
    st.session_state.etat = "normal"
    st.session_state.message = "Couik couik ! Bienvenue !"
    save_game()

# ==========================================
# 3. GESTION DES IMAGES DYNAMIQUES
# ==========================================
def get_cropped_image(etat):
    """Découpe l'image 2x2 selon l'état actuel du cochon d'inde."""
    if not os.path.exists(IMAGE_FILE):
        return None
    
    try:
        img = Image.open(IMAGE_FILE)
        w, h = img.size
        # Coordonnées de découpe (gauche, haut, droite, bas)
        crops = {
            "normal": (0, 0, w//2, h//2),
            "malade": (w//2, 0, w, h//2),
            "mange":  (0, h//2, w//2, h),
            "joue":   (w//2, h//2, w, h)
        }
        # Si l'état n'est pas reconnu, on affiche 'normal'
        box = crops.get(etat, crops["normal"])
        return img.crop(box)
    except Exception as e:
        return None

# ==========================================
# 4. LOGIQUE DU JEU
# ==========================================
def clamp(value):
    """Maintient une jauge entre 0 et 100."""
    return max(0, min(100, int(value)))

def check_random_events():
    """Génère un événement aléatoire avec 15% de chance à chaque action."""
    if random.random() < 0.15 and st.session_state.etat != "malade":
        events = [
            {
                "msg": "Oh non... Ton cochon d'inde a attrapé un coup de froid ! 🤧",
                "faim": 0, "hygiene": -10, "bonheur": -20, "energie": -30, "etat": "malade"
            },
            {
                "msg": "Miracle ! Il a trouvé un bout de carotte caché sous la litière ! 🥕",
                "faim": +20, "hygiene": 0, "bonheur": +15, "energie": +5, "etat": "mange"
            },
            {
                "msg": "Popcorning surprise ! Il saute de joie sans raison ! ✨",
                "faim": -5, "hygiene": 0, "bonheur": +25, "energie": -10, "etat": "joue"
            }
        ]
        return random.choice(events)
    return None

def perform_action(faim=0, hygiene=0, bonheur=0, energie=0, new_etat="normal", message=""):
    """Applique une action, modifie les stats, gère le temps et les événements."""
    
    # S'il est malade, on bloque certaines actions (sauf soins et repos)
    if st.session_state.etat == "malade" and new_etat not in ["normal", "dort"]:
        st.session_state.message = "Il est trop malade et faible pour ça... Donne-lui un médicament ! 💊"
        save_game()
        return

    # Application de l'action principale
    st.session_state.faim = clamp(st.session_state.faim + faim)
    st.session_state.hygiene = clamp(st.session_state.hygiene + hygiene)
    st.session_state.bonheur = clamp(st.session_state.bonheur + bonheur)
    st.session_state.energie = clamp(st.session_state.energie + energie)
    
    st.session_state.etat = new_etat
    st.session_state.message = message

    # Dégradation due au temps qui passe (à chaque clic)
    st.session_state.faim = clamp(st.session_state.faim - 2)
    st.session_state.hygiene = clamp(st.session_state.hygiene - 1)
    st.session_state.energie = clamp(st.session_state.energie - 2)
    if st.session_state.etat == "malade":
        st.session_state.bonheur = clamp(st.session_state.bonheur - 5) # Perd du bonheur s'il reste malade

    # Vérification des événements aléatoires
    event = check_random_events()
    if event:
        st.session_state.faim = clamp(st.session_state.faim + event["faim"])
        st.session_state.hygiene = clamp(st.session_state.hygiene + event["hygiene"])
        st.session_state.bonheur = clamp(st.session_state.bonheur + event["bonheur"])
        st.session_state.energie = clamp(st.session_state.energie + event["energie"])
        st.session_state.etat = event["etat"]
        st.session_state.message = event["msg"]

    save_game()

# ==========================================
# 5. INTERFACE UTILISATEUR (UI)
# ==========================================
load_state()

# CSS personnalisé pour embellir
st.markdown("""
<style>
    .titre { text-align: center; color: #E67E22; font-family: 'Comic Sans MS', cursive, sans-serif; }
    .message-box { 
        background-color: #FFF3E0; padding: 15px; border-radius: 10px; 
        text-align: center; font-size: 18px; font-style: italic; 
        color: #D35400; border: 2px dashed #E67E22; margin-bottom: 20px;
    }
    .stProgress > div > div > div > div { background-color: #E67E22; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='titre'>🐹 Mon Tamagotchi Cochon d'Inde</h1>", unsafe_allow_html=True)

# Affichage de l'image découpée selon l'état
col_img1, col_img2, col_img3 = st.columns([1, 2, 1])
with col_img2:
    img = get_cropped_image(st.session_state.etat)
    if img:
        st.image(img, use_container_width=True, caption=f"État : {st.session_state.etat.capitalize()}")
    else:
        st.error(f"Image '{IMAGE_FILE}' introuvable ! Place-la dans le même dossier que app.py sur GitHub.")
        st.markdown("<div style='text-align:center; font-size:100px;'>🐹</div>", unsafe_allow_html=True)

# Boîte de dialogue
st.markdown(f"<div class='message-box'>« {st.session_state.message} »</div>", unsafe_allow_html=True)

# Jauges de statistiques avec couleurs d'alerte
c1, c2, c3, c4 = st.columns(4)
c1.metric("🍎 Faim", f"{st.session_state.faim}%")
c1.progress(st.session_state.faim / 100)

c2.metric("✨ Hygiène", f"{st.session_state.hygiene}%")
c2.progress(st.session_state.hygiene / 100)

c3.metric("❤️ Bonheur", f"{st.session_state.bonheur}%")
c3.progress(st.session_state.bonheur / 100)

c4.metric("⚡ Énergie", f"{st.session_state.energie}%")
c4.progress(st.session_state.energie / 100)

st.divider()

# ==========================================
# 6. ONGLETS D'INTERACTIONS
# ==========================================
tab_nourrir, tab_soins, tab_jouer, tab_repos = st.tabs(["🍎 Nourrir", "🛁 Soins", "🎾 Jouer", "💤 Repos"])

with tab_nourrir:
    col1, col2, col3 = st.columns(3)
    if col1.button("Donner du Foin 🌾", use_container_width=True):
        perform_action(faim=25, bonheur=5, new_etat="mange", message="Crounch ! Le foin, c'est indispensable pour mes dents.")
    if col2.button("Légumes frais 🥒", use_container_width=True):
        perform_action(faim=40, bonheur=15, hygiene=-5, new_etat="mange", message="Miam ! Un délicieux poivron !")
    if col3.button("Friandise 🍓", use_container_width=True):
        perform_action(faim=10, bonheur=30, energie=-5, new_etat="mange", message="Couik couik ! J'adore le sucré !")

with tab_soins:
    col1, col2, col3 = st.columns(3)
    if col1.button("Brosser les poils 🖌️", use_container_width=True):
        perform_action(hygiene=30, bonheur=15, new_etat="normal", message="Ronron... C'est très agréable.")
    if col2.button("Nettoyer la cage ✨", use_container_width=True):
        perform_action(hygiene=60, bonheur=10, energie=-10, new_etat="normal", message="Génial ! Tout est propre pour courir.")
    if col3.button("Donner Médicament 💊", use_container_width=True):
        if st.session_state.etat == "malade":
            perform_action(hygiene=10, bonheur=20, energie=10, new_etat="normal", message="Pouah, c'est pas bon, mais je me sens beaucoup mieux !")
        else:
            perform_action(bonheur=-10, new_etat="normal", message="Mais je ne suis pas malade ! Laisse-moi tranquille !")

with tab_jouer:
    col1, col2, col3 = st.columns(3)
    if col1.button("Sortie dans le parc 🏃‍♂️", use_container_width=True):
        perform_action(bonheur=40, energie=-30, faim=-15, hygiene=-10, new_etat="joue", message="Popcorn !! 🍿 Je saute partout !")
    if col2.button("Jouet à ronger 🪵", use_container_width=True):
        perform_action(bonheur=20, energie=-10, faim=-5, new_etat="joue", message="Je me fais les dents, c'est rigolo.")
    if col3.button("Câlins sur les genoux ❤️", use_container_width=True):
        perform_action(bonheur=35, energie=-5, new_etat="normal", message="Je m'aplatis comme une crêpe et je ronronne...")

with tab_repos:
    col1, col2 = st.columns(2)
    if col1.button("Faire une sieste 💤", use_container_width=True):
        perform_action(energie=40, faim=-10, new_etat="normal", message="Zzz... Une petite pause bien méritée.")
    if col2.button("Nuit complète 🌙", use_container_width=True):
        perform_action(energie=80, faim=-30, hygiene=-10, new_etat="normal", message="Zzz... Bonne nuit ! Demain on joue ?")

st.divider()

# Bouton de secours si on veut recommencer
if st.button("🔄 Recommencer à zéro (Reset)"):
    reset_game()
    st.rerun()
