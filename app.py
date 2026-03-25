import streamlit as st
import google.generativeai as genai
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. AI 설정 (Secrets에 GOOGLE_API_KEY만 있으면 됩니다!)
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel("models/gemini-1.5-flash")

# 2. 구글 시트 주소 (오류 방지를 위해 지저분한 뒷부분을 잘라낸 깔끔한 주소입니다)
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1_ko0JRJ6en5UKWZyCSKJZ3dxmfuLesV16YYu7PCCAGo"

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
            # 채용 정보를 바탕으로 답변하도록 프롬프트 구성
            response = model.generate_content(f"너는 아시아나 에어포트 채용 담당자야. 친절하게 답해줘: {prompt}")
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})

# --- 탭 2: 간편 지원 ---
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
                    # 구글 시트 연결
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    
                    # 데이터 읽기 (워크시트 이름을 'Sheet1'으로 설정)
                    # 시트의 1행에는 반드시 제목들이 적혀 있어야 합니다!
                    df = conn.read(spreadsheet=SPREADSHEET_URL, worksheet="Sheet1", ttl=0)
                    
                    # 새 데이터 생성
                    new_data = pd.DataFrame([{
                        "신청시간": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "이름": name, "성별": gender, "나이": age, "연락처": phone,
                        "주소": address, "교통방법": q1, "소요시간": q2, "새벽도착가능": q3
                    }])
                    
                    # 기존 데이터에 새 데이터 합치기
                    updated_df = pd.concat([df, new_data], ignore_index=True)
                    
                    # 구글 시트에 다시 쓰기
                    conn.update(spreadsheet=SPREADSHEET_URL, data=updated_df)
                    
                    st.balloons()
                    st.success(f"{name}님, 접수가 완료되었습니다! 구글 시트를 확인해보세요. ✈️")
                except Exception as e:
                    st.error(f"⚠️ 연결 오류 발생! 주소 형식이 올바르지 않거나 공유 설정이 잘못되었습니다.\n오류내용: {e}")
            else:
                st.error("이름과 연락처는 필수입니다!")
