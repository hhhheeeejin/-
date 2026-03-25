import streamlit as st
import google.generativeai as genai
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. 설정
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1oMWwVXy9R-YbI-xkpQZVuwmYHZhHbph6AalWE42nxfs/edit?usp=sharing"

# 2. 모델 설정
@st.cache_resource
def get_model():
    model = genai.GenerativeModel("models/gemini-1.5-flash")
    return model

model = get_model()
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 화면 구성 ---
st.set_page_config(page_title="아시아나 에어포트 채용", page_icon="✈️")
st.markdown("### ✈️ 아시아나 에어포트 채용 센터")

tab1, tab2 = st.tabs(["💬 실시간 상담", "📝 1분 간편지원"])

with tab1:
    st.info("안녕하세요! 궁금한 점을 질문해 주세요. 😊")
    # (챗봇 로직은 동일하므로 생략 가능하나 전체 코드를 위해 유지)
    if "messages" not in st.session_state: st.session_state.messages = []
    user_input = st.chat_input("공고에 대해 궁금한 점을 물어보세요!")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("assistant"):
            response = model.generate_content(f"아시아나 에어포트 채용 담당자로서 친절히 답해줘: {user_input}")
            st.markdown(response.text)

with tab2:
    st.info("양식을 작성하면 구글 시트로 즉시 접수됩니다.")
    with st.form("application_form", clear_on_submit=True):
        name = st.text_input("이름")
        gender = st.selectbox("성별", ["남성", "여성"])
        age = st.number_input("나이", min_value=19, max_value=70, value=25)
        phone = st.text_input("연락처 (예: 010-1234-5678)")
        address = st.text_input("주소 (OO동까지)")
        q1 = st.selectbox("교통방법", ["자차", "대중교통", "셔틀버스"])
        q2 = st.text_input("출퇴근 소요시간")
        q3 = st.radio("오전 05:20까지 도착 가능여부", ["가능", "불가능"])
        
        submitted = st.form_submit_button("🚀 지금 지원하기")
        
        if submitted:
            if name and phone and address:
                try:
                    # ⭐ 핵심: 시트의 첫 줄을 무조건 읽어오도록 강제 설정
                    df = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="시트1", ttl=0)
                    
                    new_entry = pd.DataFrame([{
                        "신청시간": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "이름": name, "성별": gender, "나이": age, "연락처": phone,
                        "주소": address, "교통방법": q1, "소요시간": q2, "새벽도착가능": q3
                    }])
                    
                    updated_df = pd.concat([df, new_entry], ignore_index=True)
                    conn.update(spreadsheet=SPREADSHEET_URL, data=updated_df)
                    
                    st.balloons()
                    st.success(f"{name}님, 접수 완료! ✈️")
                except Exception as e:
                    # 🔍 에러가 나면 구체적인 이유를 화면에 띄웁니다.
                    st.error(f"⚠️ 연결 오류 발생: {str(e)}")
            else:
                st.error("필수 항목을 모두 입력해 주세요!")
