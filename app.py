import streamlit as st
import base64
import io
from openai import OpenAI
from PIL import Image

# ==========================================
# 🔴 ตั้งค่า API KEY
# เวลาขึ้นเว็บจริง เราจะไปใส่รหัสใน Secrets ของ Streamlit Cloud แทน
# ดังนั้นตรงนี้ปล่อยว่างไว้ หรือใส่โค้ดดักจับแบบนี้ครับ:

try:
    if "OPENAI_API_KEY" in st.secrets:
        OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    else:
        # กรณีรันในเครื่อง (และไม่ได้สร้างไฟล์ secrets.toml)
        # ให้ใส่รหัสตรงนี้เพื่อทดสอบ แล้วลบออกก่อนอัพขึ้น GitHub
        OPENAI_API_KEY = "" # <--- ลบรหัสตรงนี้ออกให้ว่างๆ แบบนี้ครับ!
        
        if not OPENAI_API_KEY:
            st.warning("⚠️ ไม่พบ API Key! กรุณาใส่ใน Streamlit Secrets หรือใส่ชั่วคราวในโค้ด")
            st.stop()
            
except FileNotFoundError:
    st.error("ไม่พบการตั้งค่า Secrets")
    st.stop()
# ==========================================

client = OpenAI(api_key=OPENAI_API_KEY)

# --- 1. ฟังก์ชั่นพื้นฐาน (แปลงภาพ) ---
def encode_image(image):
    buffered = io.BytesIO()
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    image.save(buffered, format="JPEG", quality=95)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# --- 2. ฟังก์ชั่นสร้าง Prompt ครั้งแรก (The Creator) ---
def generate_initial_prompt(image_input):
    base64_image = encode_image(image_input)
    
    system_instruction = """
    You are an elite "Stock Photography Art Director". 
    Analyze the image and write a premium generative AI prompt.
    
    1. CATEGORY DETECTION (Finance, Commodities, Beauty, Travel, Food, Lifestyle).
    2. KEYWORD INJECTION: Weave in specific technical keywords based on category.
    3. VISUAL STYLE: "Hyper-realistic, 8k resolution, cinematic lighting, photorealistic, highly detailed, depth of field, commercial stock photography, shot on 35mm lens."
    
    OUTPUT: A single detailed paragraph. Start with the Subject. No Intro/Outro.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": [
                    {"type": "text", "text": "Generate a detailed stock photo prompt."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]}
            ],
            max_tokens=500,
            temperature=0.6
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

# --- 3. ฟังก์ชั่นแก้งาน (The Editor) 🔴 เพิ่มใหม่ ---
def refine_prompt(original_prompt, user_instruction):
    system_instruction = """
    You are a professional Prompt Editor. 
    Your goal is to REWRITE the stock photography prompt based on the user's feedback.
    
    RULES:
    1. Keep the core subject and technical style (8k, hyper-realistic) of the original prompt.
    2. APPLY the user's specific instruction strictly (e.g., change lighting, add texture, change mood).
    3. Output the FULL corrected prompt (not just the changes).
    4. Do not talk to the user. Just output the prompt.
    """
    
    user_message = f"""
    ORIGINAL PROMPT: "{original_prompt}"
    
    USER INSTRUCTION: "{user_instruction}"
    
    Please rewrite the prompt to incorporate the instruction while maintaining high stock photo quality.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

# --- UI Application ---
st.set_page_config(layout="wide", page_title="AI Stock Prompt Pro (Editable)")
st.markdown("""<style>.stTextArea textarea { font-size: 16px !important; background-color: #f8f9fa; }</style>""", unsafe_allow_html=True)

st.title("🎨 AI Stock Prompt Pro (Editable)")
st.caption("Generate -> Review -> Refine (แก้ไขรายรูปได้ทันที)")

# --- Session State (ระบบความจำ) ---
# เราต้องสร้างตัวแปรเก็บ Prompt ไว้ ไม่ให้หายเวลากดปุ่ม
if 'prompts_data' not in st.session_state:
    st.session_state['prompts_data'] = {}

# --- Sidebar ---
with st.sidebar:
    st.header("1. Upload Zone")
    uploaded_files = st.file_uploader("เลือกรูปภาพ (Ref)", type=['jpg', 'png', 'jpeg'], accept_multiple_files=True)
    
    # ปุ่มเริ่ม Gen (กดเพื่อเริ่มสร้างครั้งแรก)
    if uploaded_files:
        if st.button("⚡ Generate All Prompts", type="primary", use_container_width=True):
            with st.spinner("กำลังสร้าง Prompt ชุดแรก..."):
                progress_bar = st.progress(0)
                for i, file in enumerate(uploaded_files):
                    # เช็คว่ารูปนี้เคยเจนรึยัง ถ้ายังค่อยเจน (ประหยัดเงิน)
                    if file.name not in st.session_state['prompts_data']:
                        img = Image.open(file)
                        prompt = generate_initial_prompt(img)
                        st.session_state['prompts_data'][file.name] = prompt
                    progress_bar.progress((i + 1) / len(uploaded_files))
                st.success("เสร็จสิ้น!")

# --- Main Area ---
st.header("2. Review & Refine")

if uploaded_files:
    # วนลูปแสดงผลทีละรูป
    for i, file in enumerate(uploaded_files):
        # ถ้ายังไม่มี Prompt (เพิ่งอัพโหลดแต่ยังไม่กด Gen) ให้ข้ามไปก่อน
        if file.name not in st.session_state['prompts_data']:
            continue
            
        current_prompt = st.session_state['prompts_data'][file.name]
        image = Image.open(file)
        
        # สร้างกรอบแสดงผล
        with st.container(border=True):
            c1, c2 = st.columns([1, 3])
            
            # คอลัมน์ซ้าย: รูปภาพ
            with c1:
                st.image(image, use_column_width=True)
                st.caption(f"File: {file.name}")
            
            # คอลัมน์ขวา: Prompt และเครื่องมือแก้ไข
            with c2:
                # 1. แสดง Prompt ปัจจุบัน
                st.subheader(f"Prompt #{i+1}")
                st.text_area("Result:", value=current_prompt, height=150, key=f"display_{file.name}")
                
                # 2. ส่วนแก้ไข (Expander)
                with st.expander(f"🛠️ ต้องการแก้ Prompt รูปนี้? ({file.name})"):
                    # ช่องกรอกคำสั่งแก้
                    user_instruction = st.text_input(
                        "พิมพ์คำสั่งแก้ที่นี่ (เช่น: ขอธนบัตรยับๆ, เปลี่ยนแสงเป็นตอนเย็น)", 
                        key=f"input_{file.name}"
                    )
                    
                    # ปุ่มกดอัพเดท
                    if st.button("Update Prompt 🔄", key=f"btn_{file.name}"):
                        if user_instruction:
                            with st.spinner("AI กำลังเรียบเรียง Prompt ใหม่..."):
                                # เรียกฟังก์ชั่น Editor
                                new_prompt = refine_prompt(current_prompt, user_instruction)
                                # บันทึกทับอันเดิมในความจำ
                                st.session_state['prompts_data'][file.name] = new_prompt
                                st.rerun() # รีเฟรชหน้าจอเพื่อแสดงผลใหม่ทันที
                        else:
                            st.warning("กรุณาพิมพ์คำสั่งก่อนกดปุ่มครับ")

else:
    st.info("👈 กรุณาอัพโหลดรูปภาพและกด Generate ทางซ้ายมือ")