import streamlit as st
import base64
import io
from openai import OpenAI
from PIL import Image

# ==========================================
# 🔴 ใส่ API Key ของ OpenAI ตรงนี้ (แบบตรงๆ)
import streamlit as st
# ... (import อื่นๆ เหมือนเดิม)

# โค้ดส่วนดึง API Key จากตู้เซฟ (Secrets)
try:
    if "OPENAI_API_KEY" in st.secrets:
        OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    else:
        st.error("ไม่พบ API Key กรุณาตั้งค่าใน Secrets")
        st.stop()
except FileNotFoundError:
    st.error("ไม่พบไฟล์ Secrets กรุณาตั้งค่าบน Streamlit Cloud")
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)
# ==========================================

client = OpenAI(api_key=OPENAI_API_KEY)

def encode_image(image):
    buffered = io.BytesIO()
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    image.save(buffered, format="JPEG", quality=95)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def generate_stock_prompt(image_input):
    base64_image = encode_image(image_input)
    
    # --- UPGRADED BRAIN V3: เพิ่มหมวด Travel, Food, Spa, Lifestyle ---
    system_instruction = """
    You are an elite "Stock Photography Art Director". 
    Your task is to analyze the image and write a premium generative AI prompt.
    
    --- 1. CATEGORY DETECTION ---
    Identify the primary niche of the image from these categories:
    - [FINANCE/BUSINESS]: Stocks, Office, Meeting, Growth, Economy.
    - [COMMODITIES/ENERGY]: Gold, Oil, Solar, Industry.
    - [BEAUTY/SPA/WELLNESS]: Skincare, Massage, Zen, Cosmetics, Relaxation.
    - [TRAVEL/HOTEL]: Resorts, Lobby, Luggage, Tourism, Infinity Pool, Room Service.
    - [FOOD/RESTAURANT]: Fine Dining, Plating, Chef, Ingredients, Cafe atmosphere.
    - [LIFESTYLE]: Candid moments, Hobbies, Friends, Daily life, Authentic.
    - [HEALTH/FITNESS]: Gym, Yoga, Medical, Hospital.
    - [3D/ABSTRACT]: Podiums, Minimalist backgrounds.
    
    --- 2. KEYWORD INJECTION PROTOCOL ---
    Based on the detected category, YOU MUST weave these specific keywords into the prompt:
    
    * IF BEAUTY/SPA: "Glowing skin, skincare routine, rejuvenation, luxury spa, aromatherapy, herbal ingredients, zen atmosphere, soft towels, flawless complexion, natural beauty, serenity, pampering."
    * IF TRAVEL/HOTEL: "Luxury resort, wanderlust, boutique hotel, hospitality, check-in, vacation mode, tourism, infinity pool, scenic view, hotel lobby, suitcase, getaway, concierge service."
    * IF FOOD/RESTAURANT: "Culinary arts, fine dining, gourmet plating, mouth-watering, fresh ingredients, chef at work, restaurant ambiance, savory, food photography, delicious, menu, wine pairing."
    * IF LIFESTYLE: "Authentic moment, candid shot, enjoying life, social gathering, leisure time, modern lifestyle, happiness, genuine emotion, diversity, real people."
    * IF FINANCE/BUSINESS: "Financial growth, investment portfolio, corporate success, modern office, leadership, teamwork, economic analysis, fintech."
    * IF COMMODITIES/ENERGY: "Gold bullion, wealth, oil rig, renewable energy, sustainability, industrial power, precious metals."
    * IF HEALTH/FITNESS: "Active lifestyle, wellness, yoga pose, medical care, healthy living, determination, gym workout."
    * IF 3D/ABSTRACT: "Octane render, minimalism, pastel colors, podium, product display, soft studio lighting, clean composition."
    
    --- 3. VISUAL STYLE (ALWAYS INCLUDE) ---
    "Hyper-realistic, 8k resolution, cinematic lighting, photorealistic, highly detailed, depth of field, sharp focus, commercial stock photography, shot on 35mm lens."

    --- OUTPUT FORMAT ---
    - Write ONE cohesive, detailed paragraph.
    - Start with the Subject.
    - Describe Action/Context -> Environment -> Lighting/Mood -> Specific Keywords -> Technical Style.
    - NO intro/outro text. Just the prompt.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": [
                    {"type": "text", "text": "Generate a detailed stock photo prompt for this image."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}
            ],
            max_tokens=500, # เพิ่มความยาวอีกนิดสำหรับบรรยายอาหาร/สถานที่
            temperature=0.6
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

# --- UI ส่วนหน้าจอ ---
st.set_page_config(layout="wide", page_title="Universal Stock AI V3")
st.markdown("""
<style>
    .stTextArea textarea { font-size: 16px !important; color: #222; background-color: #f8f9fa; }
    h1 { color: #2E86C1; }
</style>
""", unsafe_allow_html=True)

st.title("💎 Premium Stock Prompt AI (Full Categories)")
st.caption("รองรับ: Beauty, Spa, Hotel, Travel, Food, Lifestyle, Business, Gold, Oil, 3D")

col_left, col_right = st.columns([1, 2])

with col_left:
    st.success("📂 **Upload Zone**")
    uploaded_files = st.file_uploader(
        "อัพโหลดภาพ Ref (คละหมวดหมู่ได้เลย)", 
        type=['png', 'jpg', 'jpeg', 'webp'], 
        accept_multiple_files=True
    )
    
    st.divider()
    start_btn = st.button("⚡ Generate Prompts", type="primary", use_container_width=True)

with col_right:
    st.header("📝 Generated Prompts")
    
    if start_btn and uploaded_files:
        progress_bar = st.progress(0)
        
        for i, uploaded_file in enumerate(uploaded_files):
            image = Image.open(uploaded_file)
            
            with st.container(border=True):
                c1, c2 = st.columns([1, 4])
                with c1:
                    st.image(image, use_column_width=True)
                with c2:
                    with st.spinner('AI กำลังวิเคราะห์สไตล์ภาพและเลือกคีย์เวิร์ด...'):
                        prompt_text = generate_stock_prompt(image)
                        st.text_area(
                            f"Prompt #{i+1}",
                            value=prompt_text,
                            height=200, # ขยายกล่องข้อความให้ใหญ่ขึ้น
                            key=f"p_{i}"
                        )
            
            progress_bar.progress((i + 1) / len(uploaded_files))
        
        st.success("✅ เสร็จสิ้นทุกรูปครับ")
