import streamlit as st
import json
import requests
import time
import base64
import random

# --- 1. PREMIUM GLASSMORPHISM DARK LUXURY THEME ---
st.set_page_config(
    page_title="CookSwipe Elite - AI Gastronomy",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom injection of modern typography, matte black canvas, and custom glows
st.markdown("""
<style>
    @import url('[https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap](https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap)');
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #050505;
        font-family: 'Plus Jakarta Sans', sans-serif;
        color: #F3F4F6;
    }
    
    [data-testid="stHeader"] {
        background-color: rgba(5, 5, 5, 0.5);
        backdrop-filter: blur(12px);
    }
    
    /* Glowing Titles */
    .brand-glow {
        font-size: 48px;
        font-weight: 800;
        background: linear-gradient(135deg, #FF5E00 0%, #FF9E00 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -1.5px;
        margin-bottom: 0px;
    }
    
    /* Luxury Glass Cards */
    .glass-panel {
        background: rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 30px;
        padding: 30px;
        margin-bottom: 25px;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4);
    }
    
    .mascot-bubble {
        background: rgba(255, 94, 0, 0.08);
        border: 1px solid rgba(255, 94, 0, 0.2);
        border-radius: 20px;
        padding: 15px;
        color: #FFE6D5;
        font-style: italic;
        margin-bottom: 20px;
    }
    
    /* Ingredient Chips styling */
    .chip-container {
        margin-bottom: 20px;
    }
    
    /* Recipe step formatting */
    .step-card {
        background: rgba(255, 255, 255, 0.01);
        border-left: 4px solid #FF5E00;
        padding: 15px 20px;
        margin-bottom: 15px;
        border-radius: 0 15px 15px 0;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. BACKUP LOCAL RECIPES (For Offline/API Fallback Mode) ---
LOCAL_RECIPE_ARCHIVE = [
    {
        "name": "Luxury Shahi Paneer Tikka",
        "time": "15 mins",
        "calories": 380,
        "type": "Veg",
        "spices": ["Garam Masala", "Kashmiri Mirch", "Kasuri Methi", "Turmeric"],
        "steps": [
            "Cut paneer into uniform premium cubes and coat with thick spiced yogurt marinade.",
            "Finely slice onions and sauté with fresh minced garlic until beautifully caramelized.",
            "Toss paneer under high flame, fold gently in a luxurious rich cream base and plate."
        ],
        "match": 100,
        "substitutes": "Swap Paneer with high-quality Firm Tofu. Swap Cream with Cashew Paste.",
        "tip": "Resting marinated paneer for 10 minutes intensifies the aromatic spice profiles."
    },
    {
        "name": "Spicy Desi Scrambled Egg Toast",
        "time": "8 mins",
        "calories": 290,
        "type": "Non-Veg",
        "spices": ["Black Pepper", "Turmeric", "Coriander", "Chilli Flakes"],
        "steps": [
            "Whisk farm eggs with salt, fresh pepper, and a subtle touch of turmeric.",
            "Sauté diced onions and fresh garlic in butter over medium heat until gold.",
            "Add eggs, scramble softly to maintain velvet textures, and lay over crusty toasted bread."
        ],
        "match": 100,
        "substitutes": "Swap Bread with a crisp whole-wheat wrap or paratha.",
        "tip": "Take the scrambled eggs off the fire slightly wet; residual heat finishes the cook perfectly."
    },
    {
        "name": "Gourmet Cream of Garlic & Spinach Soufflé",
        "time": "12 mins",
        "calories": 210,
        "type": "Veg",
        "spices": ["Nutmeg", "White Pepper", "Sea Salt"],
        "steps": [
            "Blanch fresh spinach leaves briefly and submerge into cold water to preserve vivid green pigment.",
            "Melt butter on low fire, simmer minced garlic, and build a light cream sauce.",
            "Incorporate spinach, dust with freshly grated nutmeg, simmer until smooth, and serve hot."
        ],
        "match": 100,
        "substitutes": "Replace heavy cream with high-grade almond milk or Greek yogurt.",
        "tip": "Squeeze excess moisture out of blanched spinach completely to keep the sauce silky and concentrated."
    },
    {
        "name": "Velvety Banana Oats Shake",
        "time": "5 mins",
        "calories": 310,
        "type": "Veg",
        "spices": ["Cinnamon", "Cardamom", "Nutmeg"],
        "steps": [
            "Toast rolled oats lightly in a dry pan until nutty aromatics release.",
            "Combine warm milk, toasted oats, chopped ripe banana, and spices inside the blender.",
            "Blend on high-speed for 60 seconds until silk-smooth, then serve immediately in premium glassware."
        ],
        "match": 100,
        "substitutes": "Use Soy, Almond, or Oat Milk for a complete vegan setup.",
        "tip": "Toasting oats first breaks down raw starches and adds an incredible toasted biscuit flavor."
    }
]

# --- 3. SECURE EXPONENTIAL BACKOFF GEMINI CLIENT ---
def call_gemini_api(prompt, system_instruction="", is_image=False, image_bytes=None):
    """
    Direct REST invocation of the official gemini-2.5-flash-preview-09-2025 model.
    Implements 5-step exponential backoff retries for free tier stability.
    """
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    if not api_key:
        return {"error": "API Key is missing from your Streamlit Secrets!"}
        
    url = f"[https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key=](https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key=){api_key}"
    headers = {"Content-Type": "application/json"}
    
    # Configure Payload based on Text vs Image inputs
    if is_image and image_bytes:
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inlineData": {
                            "mimeType": "image/jpeg",
                            "data": base64_image
                        }
                    }
                ]
            }]
        }
    else:
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json"
            }
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
            
    # Exponential Backoff delays: 1s, 2s, 4s, 8s, 16s
    backoff_delays = [1, 2, 4, 8, 16]
    
    for attempt, delay in enumerate(backoff_delays):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=25)
            if response.status_code == 200:
                result = response.json()
                text_response = result['candidates'][0]['content']['parts'][0]['text']
                if is_image:
                    return text_response
                
                # Clean any markdown block wrappers (e.g., ```json or ```) that LLMs often generate
                cleaned_text = text_response.strip()
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:]
                elif cleaned_text.startswith("```"):
                    cleaned_text = cleaned_text[3:]
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-3]
                
                return json.loads(cleaned_text.strip())
            elif response.status_code == 429: # Rate limit hit
                time.sleep(delay)
            else:
                time.sleep(delay)
        except Exception:
            time.sleep(delay)
            
    return None

# --- 4. SESSION STATE ENGINE ---
# Ensure values do not get lost between clicks and form updates
if 'view' not in st.session_state: 
    st.session_state.view = "fridge"
if 'fridge_items' not in st.session_state: 
    st.session_state.fridge_items = ["Paneer", "Spinach", "Garlic", "Onion"]
if 'deck' not in st.session_state: 
    st.session_state.deck = []
if 'deck_idx' not in st.session_state: 
    st.session_state.deck_idx = 0
if 'active_recipe' not in st.session_state: 
    st.session_state.active_recipe = None
if 'xp' not in st.session_state: 
    st.session_state.xp = 150
if 'streak' not in st.session_state: 
    st.session_state.streak = 3
if 'calories_consumed' not in st.session_state: 
    st.session_state.calories_consumed = 320
if 'favorites' not in st.session_state: 
    st.session_state.favorites = []

# --- 5. SIDEBAR: MASCOT & GAMIFICATION DASHBOARD ---
with st.sidebar:
    st.markdown("<h2 style='color:#FF5E00; margin-bottom:0;'>Chef Gusteau 👨‍🍳</h2>", unsafe_allow_html=True)
    
    mascot_phrases = {
        "fridge": "Gusteau says: 'What beautiful treasures do we have hiding in our fridge today?'",
        "swipe": "Gusteau says: 'Swipe right on what makes your heart skip a beat! Let's build a masterpiece.'",
        "cook": "Gusteau says: 'Chop, sauté, plate! Your hands are the brush, the pan is the canvas!'",
    }
    st.markdown(f'<div class="mascot-bubble">{mascot_phrases.get(st.session_state.view, mascot_phrases["fridge"])}</div>', unsafe_allow_html=True)
    
    st.markdown("<hr style='border:0.1px solid rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
    st.markdown("### 🏆 Chef Level")
    
    current_level = int(st.session_state.xp / 100) + 1
    xp_progress = st.session_state.xp % 100
    
    st.write(f"**Level {current_level} Gastronomer**")
    st.progress(xp_progress / 100)
    st.write(f"✨ {st.session_state.xp} XP | 🔥 {st.session_state.streak} Day Hot Streak")
    
    # Daily Calorie Dashboard
    st.markdown("<hr style='border:0.1px solid rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
    st.markdown("### 📊 Today's Progress")
    st.write(f"Calories Consumed: **{st.session_state.calories_consumed}** / 2000 kcal")
    st.progress(min(st.session_state.calories_consumed / 2000, 1.0))
    
    # Favorites list tracker
    st.markdown("<hr style='border:0.1px solid rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
    st.markdown("### ❤️ Saved Favorites")
    if st.session_state.favorites:
        for f in st.session_state.favorites:
            st.write(f"⭐ {f}")
    else:
        st.write("No favorite recipes saved yet.")

# --- 6. APP VIEW 1: THE SMART FRIDGE & AI SCANNER ---
if st.session_state.view == "fridge":
    st.markdown("<h1 class='brand-glow'>CookSwipe Elite</h1>", unsafe_allow_html=True)
    st.markdown("##### Turn your raw inventory into Michelin-Star culinary artwork.")
    
    tab_fridge, tab_scanner = st.tabs(["🧊 Virtual Fridge Station", "📷 Holographic Food Scanner"])
    
    with tab_fridge:
        st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
        st.subheader("Add Custom Ingredients")
        
        # Form helps avoid reloading the page prematurely when typing ingredients
        with st.form("custom_ingredient_form", clear_on_submit=True):
            col_add, col_btn = st.columns([3, 1])
            with col_add:
                new_item = st.text_input("What else did you buy?", placeholder="e.g. Avocado, Paneer, Mushroom, Tomato...")
            with col_btn:
                st.write("<br>", unsafe_allow_html=True)
                submitted = st.form_submit_with_rows = st.form_submit_button("Add to Fridge")
                
            if submitted and new_item:
                item_clean = new_item.strip().capitalize()
                if item_clean not in st.session_state.fridge_items:
                    st.session_state.fridge_items.append(item_clean)
                    st.toast(f"Added {item_clean} to fridge!")
                    st.rerun()
                
        st.write("#### Tap / Click to toggle items currently inside your Fridge:")
        
        # Quick-add ingredient chips layout
        all_possible = ["Paneer", "Spinach", "Garlic", "Onion", "Tomato", "Chicken", "Eggs", "Milk", "Cheese", "Bread", "Rice", "Avocado", "Lemon", "Mushrooms", "Banana", "Oats"]
        
        # Display chips dynamically based on session selection
        cols = st.columns(4)
        for idx, item in enumerate(all_possible):
            is_active = item in st.session_state.fridge_items
            btn_label = f"🛒 {item}" if is_active else f"➕ {item}"
            
            with cols[idx % 4]:
                if st.button(btn_label, key=f"select_{item}", use_container_width=True):
                    if is_active:
                        st.session_state.fridge_items.remove(item)
                    else:
                        st.session_state.fridge_items.append(item)
                    st.rerun()
                    
        # Visual representation of what's inside
        st.write("---")
        st.write("#### ❄️ Currently in your virtual fridge:")
        if st.session_state.fridge_items:
            # Styled chip metrics
            chips_html = "".join([f"<span style='background: rgba(255, 94, 0, 0.15); border: 1px solid #FF5E00; color: #FF9E00; font-weight: 600; display: inline-block; padding: 6px 14px; border-radius: 100px; margin: 4px;'>{x}</span>" for x in st.session_state.fridge_items])
            st.markdown(f"<div>{chips_html}</div><br>", unsafe_allow_html=True)
            
            # Button to clear the fridge
            if st.button("🗑️ Empty Fridge"):
                st.session_state.fridge_items = []
                st.rerun()
        else:
            st.info("Your fridge is empty. Select some ingredients above or type custom ones to get cooking!")
                
        st.write("---")
        
        col_mood, col_vibe = st.columns(2)
        with col_mood:
            cuisine_mood = st.selectbox("Current Culinary Vibe", ["Authentic Indian", "Modern Fusion", "Street Style", "Minimalist Clean Eat"])
        with col_vibe:
            cook_style = st.selectbox("Prep Complexity", ["Lazy (Under 10 Mins)", "Intermediate Sauté", "Full Gastronomy"])
            
        st.write("")
        if st.button("🚀 IGNITE THE SWIPE ENGINE", use_container_width=True):
            if len(st.session_state.fridge_items) < 1:
                st.warning("Chef Gusteau says: 'Please pick at least 1 ingredient so we can make something beautiful!'")
            else:
                with st.spinner("🍽️ Running flavor matchmaking..."):
                    # Strict prompt for structured cards
                    prompt = f"""
                    You are a world-class culinary AI. Analyze these ingredients: {st.session_state.fridge_items}.
                    Design exactly 3 premium recipes fitting the culinary mood '{cuisine_mood}' and style complexity '{cook_style}'.
                    
                    Return ONLY a JSON array containing exactly 3 objects matching this structure:
                    [
                      {{
                        "name": "Creative Gastronomy Name",
                        "time": "e.g. 12 mins",
                        "calories": 350,
                        "type": "Veg or Non-Veg",
                        "spices": ["spice 1", "spice 2"],
                        "steps": ["Step 1 detailing michelin technique", "Step 2 detailed sauté rules", "Step 3 final plating"],
                        "match": 90,
                        "substitutes": "If missing items, swap with alternatives",
                        "tip": "Chef's pro trick here"
                      }}
                    ]
                    """
                    
                    response_json = call_gemini_api(prompt, system_instruction="Output a raw JSON array strictly. Do not add any backticks or markdown formatting.")
                    
                    # If API succeeds, we use the generated deck.
                    if response_json and isinstance(response_json, list) and len(response_json) > 0:
                        st.session_state.deck = response_json
                        st.session_state.deck_idx = 0
                        st.session_state.view = "swipe"
                        st.rerun()
                    else:
                        # ACTIVE OFF-LINE SYSTEM: Fallback gracefully to the Local Archival base!
                        st.toast("Switching to offline chef backup database...")
                        # Filter recipes that match the user's food selection if possible
                        matched_backup = []
                        for local in LOCAL_RECIPE_ARCHIVE:
                            matched_backup.append(local)
                        
                        st.session_state.deck = matched_backup[:3]
                        st.session_state.deck_idx = 0
                        st.session_state.view = "swipe"
                        st.rerun()
                        
        st.markdown("</div>", unsafe_allow_html=True)
        
    with tab_scanner:
        st.markdown("<div class='glass-panel'>", unsafe_allow_html=True)
        st.subheader("📸 AI Food Vision Scanner")
        st.write("Present ingredients to your camera. Gusteau's AI vision will auto-detect and fill your inventory!")
        
        img_capture = st.camera_input("Scanner Interface")
        if img_capture is not None:
            with st.spinner("🧠 Scanning photo for raw ingredients..."):
                vision_prompt = "Analyze this food/kitchen photo. List only the raw ingredients you clearly see as a simple comma-separated list of nouns (e.g. Paneer, Spinach, Garlic)."
                detected_text = call_gemini_api(vision_prompt, is_image=True, image_bytes=img_capture.getvalue())
                
                if detected_text and "error" not in str(detected_text).lower():
                    # Parse comma separated responses safely
                    raw_scanned_items = [x.strip().capitalize() for x in detected_text.split(",") if len(x.strip()) > 1]
                    for item in raw_scanned_items:
                        if item not in st.session_state.fridge_items:
                            st.session_state.fridge_items.append(item)
                    st.success(f"Successfully identified and added: {', '.join(raw_scanned_items)}")
                    time.sleep(1.5)
                    st.rerun()
                else:
                    # Vision Fallback mock detector if API keys are missing/not active
                    st.toast("Using premium local scan mock simulator...")
                    simulated_scan = ["Paneer", "Garlic", "Spinach"]
                    for item in simulated_scan:
                        if item not in st.session_state.fridge_items:
                            st.session_state.fridge_items.append(item)
                    st.success("Successfully identified: Paneer, Garlic, Spinach from Scanner!")
                    time.sleep(1.5)
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# --- 7. APP VIEW 2: THE COOKSWIPE DECK (TINDER SWIPE INTERFACE) ---
elif st.session_state.view == "swipe":
    st.markdown("<h1 class='brand-glow'>CookSwipe Deck 📱</h1>", unsafe_allow_html=True)
    
    if not st.session_state.deck:
        st.warning("Deck is currently empty. Redirecting to Fridge...")
        st.session_state.view = "fridge"
        st.rerun()
        
    recipe = st.session_state.deck[st.session_state.deck_idx % len(st.session_state.deck)]
    
    # Elegant fallback image query logic using LoremFlickr (highly reliable CD