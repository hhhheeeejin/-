import streamlit as st
import google.generativeai as genai
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. 설정 (보안 유지)
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
# 희흐히희진님이 주신 구글 시트 주소입니다.
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1oMWwVXy9R-YbI-xkpQZVuwmYHZhHbph6AalWE42nxfs/edit?usp=sharing"

# 2. 공고 내용
job_info = """
[채용 공고 내용]
- 회사명: 아시아나 에어포트(인천공항)
- 업무: 항공기 기내청소, 정리정돈, 시트/벽면/주방 청소 및 정비
- 근무시간: 오전(05:45~14:45), 오후(14:00~23:00) 스케줄 근무 (3일 근무 1일 휴무)
- 급여: 기본급+식대+교통비+기타수당 포함 월 평균 289만원 이상
- 특징: 신입 교육 제공, 팀 단위 업무, 소형기 기준 청소 30분 소요
"""

# 3. 모델 설정
@st.cache_resource
def get_model():
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model_name = "models/gemini-1.5-flash" if "models/gemini-1.5-flash" in available_models else available_models[0]
    return genai.GenerativeModel(model_name)

model = get_model()

# 4. 구글 시트 연결 설정
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 화면 구성 ---
st.set_page_config(page_title="아시아나 에어포트 채용", page_icon="✈️")
st.markdown("### ✈️ 아시아나 에어포트 채용 센터")

tab1, tab2 = st.tabs(["💬 실시간 상담", "📝 1분 간편지원"])

# --- 탭 1: 채용 상담 챗봇 ---
with tab1:
    st.success("안녕하세요! 궁금한 점을 질문해 주세요. 😊")
    if "messages" not in st.session_state: st.session_state.messages = []
    
    user_input = st.chat_input("공고에 대해 궁금한 점을 물어보세요!")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        for message in st.session_state.messages:
            with st.chat_message(message["role"]): st.markdown(message["content"])
        
        with st.chat_message("assistant"):
            full_prompt = f"너는 아시아나 에어포트 채용 담당자야. 다음 정보를 바탕으로 친절히 답해줘.\n{job_info}\n질문: {user_input}"
            response = model.generate_content(full_prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})

# --- 탭 2: 간편 지원서 (구글 시트 연동 버전) ---
with tab2:
    st.info("양식을 작성하면 실시간으로 접수됩니다.")
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
                    # 기존 데이터 가져오기
                    existing_data = conn.read(spreadsheet=SPREADSHEET_URL, usecols=list(range(9)))
                    # 새 데이터 생성
                    new_entry = pd.DataFrame([{
                        "신청시간": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "이름": name, "성별": gender, "나이": age, "연락처": phone,
                        "주소": address, "교통방법": q1, "소요시간": q2, "새벽도착가능": q3
                    }])
                    # 데이터 합치기 및 구글 시트 업데이트
                    updated_df = pd.concat([existing_data, new_entry], ignore_index=True)
                    conn.update(spreadsheet=SPREADSHEET_URL, data=updated_df)
                    
                    st.balloons()
                    st.success(f"{name}님, 지원이 완료되었습니다! 구글 시트에 기록되었습니다. ✈️")
                except Exception as e:
                    st.error(f"저장 중 오류가 발생했어요. 다시 시도해주세요! ({e})")
            else:
                st.error("필수 항목을 모두 입력해 주세요!")
