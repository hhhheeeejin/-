import streamlit as st
import google.generativeai as genai
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. AI 설정
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel("models/gemini-1.5-flash")

# 2. 구글 시트 주소 (새로 만든 시트 주소를 여기에 넣으세요!)
# 주소 끝에 /edit... 부분을 지우고 넣어도 되지만 그대로 넣으셔도 됩니다.
SPREADSHEET_URL = "여기에_새로_만든_시트_주소를_넣으세요"

# --- 화면 구성 ---
st.set_page_config(page_title="아시아나 채용 센터", page_icon="✈️")
st.title("✈️ 아시아나 에어포트 채용")

tab1, tab2 = st.tabs(["💬 채용 상담", "📝 1분 간편지원"])

# --- 탭 1: 상담 기능 ---
with tab1:
    st.info("안녕하세요! 궁금한 점을 물어보세요. 😊")
    if "messages" not in st.session_state: st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    
    if prompt := st.chat_input("질문을 입력하세요!"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            response = model.generate_content(f"아시아나 에어포트 채용 담당자로서 답해줘: {prompt}")
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})

# --- 탭 2: 간편 지원 (인증 없이 연결 시도) ---
with tab2:
    st.success("양식을 작성하고 '지원하기'를 누르면 시트에 바로 저장됩니다!")
    with st.form("apply_form", clear_on_submit=True):
        name = st.text_input("이름")
        gender = st.selectbox("성별", ["남성", "여성"])
        age = st.number_input("나이", min_value=19, max_value=70, value=25)
        phone = st.text_input("연락처")
        address = st.text_input("주소 (OO동)")
        q1 = st.selectbox("교통방법", ["자차", "대중교통", "셔틀버스"])
        q2 = st.text_input("소요시간")
        q3 = st.radio("새벽 05:20 도착 가능?", ["가능", "불가능"])
        
        submitted = st.form_submit_button("🚀 지금 지원하기")
        
        if submitted:
            if name and phone:
                try:
                    # 💡 인증 파일 없이 연결하는 핵심 로직
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    # 현재 시트 데이터 읽기
                    df = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="시트1")
                    
                    # 새 데이터 추가
                    new_data = pd.DataFrame([{
                        "신청시간": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "이름": name, "성별": gender, "나이": age, "연락처": phone,
                        "주소": address, "교통방법": q1, "소요시간": q2, "새벽도착가능": q3
                    }])
                    
                    updated_df = pd.concat([df, new_data], ignore_index=True)
                    # 시트 업데이트
                    conn.update(spreadsheet=SPREADSHEET_URL, data=updated_df)
                    
                    st.balloons()
                    st.success(f"{name}님, 접수가 완료되었습니다! ✈️")
                except Exception as e:
                    st.error(f"⚠️ 오류가 발생했어요. 시트 '공유' 설정이 '편집자'인지 확인해주세요!\n내용: {e}")
            else:
                st.error("이름과 연락처는 필수입니다!")
