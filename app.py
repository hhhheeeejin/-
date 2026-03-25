import streamlit as st
import google.generativeai as genai
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. AI 설정
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel("models/gemini-1.5-flash")

# 2. 구글 시트 주소
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1_ko0JRJ6en5UKWZyCSKJZ3dxmfuLesV16YYu7PCCAGo/edit#gid=0"

# --- 화면 구성 ---
st.set_page_config(page_title="아시아나 채용 센터", page_icon="✈️")
st.title("✈️ 아시아나 에어포트 채용")

tab1, tab2 = st.tabs(["💬 채용 상담", "📝 1분 간편지원"])

# --- 탭 1: 상담 기능 ---
with tab1:
    st.info("안녕하세요! 아시아나 에어포트 채용에 대해 무엇이든 물어보세요. 😊")
    if "messages" not in st.session_state: st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    
    if prompt := st.chat_input("질문을 입력하세요!"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            response = model.generate_content(f"아시아나 에어포트 채용 담당자로서 친절히 답해줘: {prompt}")
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})

# --- 탭 2: 간편 지원 (에러 해결 버전) ---
with tab2:
    st.success("양식을 작성하고 아래 버튼을 누르면 담당자에게 즉시 전달됩니다!")
    
    # 폼 시작
    with st.form("apply_form", clear_on_submit=True):
        name = st.text_input("이름")
        gender = st.selectbox("성별", ["남성", "여성"])
        age = st.number_input("나이", min_value=19, max_value=70, value=25)
        phone = st.text_input("연락처 (예: 010-1234-5678)")
        address = st.text_input("주소 (OO동까지)")
        q1 = st.selectbox("교통방법", ["자차", "대중교통", "셔틀버스"])
        q2 = st.text_input("출퇴근 소요시간 (예: 40분)")
        q3 = st.radio("오전 05:20까지 공항 도착 가능여부", ["가능", "불가능"])
        
        # ⭐ 버튼을 폼 안으로 확실히 넣었습니다!
        submitted = st.form_submit_button("🚀 지금 지원하기")
        
        if submitted:
            if name and phone and address:
                try:
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    df = conn.read(spreadsheet=SPREADSHEET_URL, ttl=0)
                    
                    new_data = pd.DataFrame([{
                        "신청시간": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "이름": str(name), "성별": str(gender), "나이": int(age), "연락처": str(phone),
                        "주소": str(address), "교통방법": str(q1), "소요시간": str(q2), "새벽도착가능": str(q3)
                    }])
                    
                    updated_df = pd.concat([df, new_data], ignore_index=True)
                    conn.update(spreadsheet=SPREADSHEET_URL, data=updated_df)
                    
                    st.balloons()
                    st.success(f"🎊 {name}님, 지원서가 성공적으로 접수되었습니다!")
                except Exception as e:
                    st.error(f"⚠️ 시스템 연결 오류: {e}")
            else:
                st.error("모든 필수 항목(이름, 연락처, 주소)을 입력해주세요!")
