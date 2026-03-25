import streamlit as st
import google.generativeai as genai
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. AI 설정 (Streamlit Secrets의 GOOGLE_API_KEY를 사용합니다)
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel("models/gemini-1.5-flash")

# 2. 구글 시트 주소 (희희진님의 시트 주소입니다)
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1_ko0JRJ6en5UKWZyCSKJZ3dxmfuLesV16YYu7PCCAGo/edit#gid=0"

# --- 화면 구성 ---
st.set_page_config(page_title="아시아나 채용 센터", page_icon="✈️")
st.title("✈️ 아시아나 에어포트 채용")

tab1, tab2 = st.tabs(["💬 채용 상담", "📝 1분 간편지원"])

# --- 탭 1: 상담 기능 (채용 담당자 AI) ---
with tab1:
    st.info("안녕하세요! 아시아나 에어포트 채용에 대해 무엇이든 물어보세요. 😊")
    if "messages" not in st.session_state: st.session_state.messages = []
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    
    if prompt := st.chat_input("예: 급여 조건이 어떻게 되나요?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            # 채용 공고 기반 답변 유도
            context = "너는 아시아나 에어포트 채용 담당자야. 친절하고 자세하게 설명해줘."
            response = model.generate_content(f"{context}\n질문: {prompt}")
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})

# --- 탭 2: 간편 지원 (구글 시트 연동) ---
with tab2:
    st.success("양식을 작성하고 아래 버튼을 누르면 담당자에게 즉시 전달됩니다!")
    with st.form("apply_form", clear_on_submit=True):
        name = st.text_input("이름")
        gender = st.selectbox("성별", ["남성", "여성"])
        age = st
