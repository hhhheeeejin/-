import streamlit as st
import google.generativeai as genai
import pandas as pd
import os

# 1. 설정 (보안을 위해 st.secrets 사용)
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
APPLICANT_FILE = "applicants.xlsx"
QUESTION_LOG_FILE = "questions_log.xlsx"

# 2. 공고 내용
job_info = """
[채용 공고 내용]
- 회사명: 아시아나 에어포트(인천공항)
- 업무: 항공기 기내청소, 정리정돈, 시트/벽면/주방 청소 및 정비
- 근무시간: 오전(05:45~14:45), 오후(14:00~23:00) 스케줄 근무 (3일 근무 1일 휴무)
- 급여: 기본급+식대+교통비+기타수당 포함 월 평균 289만원 이상
- 복리후생: 교통비 일 1.2만원 지원(새벽근무 시 1만원 추가지급), 유니폼 지급, 셔틀버스 지원
- 셔틀시간: 발산 및 김포공항 04:30, 부천 원종사거리 04:30
- 특징: 신입 교육 제공, 팀 단위 업무, 소형기 기준 청소 30분 소요
"""

# 3. 모델 설정
@st.cache_resource
def get_model():
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    for name in ["models/gemini-1.5-flash", "models/gemini-pro"]:
        if name in available_models: return genai.GenerativeModel(name)
    return genai.GenerativeModel(available_models[0])

model = get_model()

# --- 화면 구성 (모바일 최적화 레이아웃) ---
st.set_page_config(page_title="아시아나 에어포트 채용", page_icon="✈️")
st.markdown("### ✈️ 아시아나 에어포트 채용 센터")

# 상단 탭 생성 (모바일에서 가장 잘 보임)
tab1, tab2 = st.tabs(["💬 실시간 상담", "📝 1분 간편지원"])

# --- 탭 1: 채용 상담 챗봇 ---
with tab1:
    st.success("안녕하세요! 궁금한 점을 버튼으로 누르거나 질문해 주세요. 😊")
    
    # FAQ 버튼
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💰 급여"): st.session_state.faq_input = "급여 조건 알려줘"
    with col2:
        if st.button("🚌 셔틀"): st.session_state.faq_input = "셔틀 노선 알려줘"
    with col3:
        if st.button("⏰ 시간"): st.session_state.faq_input = "근무 시간 알려줘"

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 질문 처리 로직
    if "faq_input" in st.session_state:
        user_input = st.session_state.faq_input
        del st.session_state.faq_input
    else:
        user_input = st.chat_input("공고에 대해 궁금한 점을 물어보세요!")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        # 질문 로그 저장
        new_q = {"시간": [pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")], "질문내용": [user_input]}
        df_q = pd.DataFrame(new_q)
        if not os.path.exists(QUESTION_LOG_FILE):
            df_q.to_excel(QUESTION_LOG_FILE, index=False)
        else:
            pd.concat([pd.read_excel(QUESTION_LOG_FILE), df_q], ignore_index=True).to_excel(QUESTION_LOG_FILE, index=False)

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        with st.chat_message("assistant"):
            full_prompt = f"너는 아시아나 에어포트의 다정한 채용 담당자야. 다음 정보를 바탕으로 존댓말로 답해줘.\n{job_info}\n질문: {st.session_state.messages[-1]['content']}"
            response = model.generate_content(full_prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})

# --- 탭 2: 간편 지원서 ---
with tab2:
    st.info("양식을 작성하고 '지원하기' 버튼을 누르면 접수가 완료됩니다.")
    with st.form("application_form", clear_on_submit=True):
        st.subheader("1. 기본 정보")
        name = st.text_input("이름")
        gender = st.selectbox("성별", ["남성", "여성"])
        age = st.number_input("나이", min_value=19, max_value=70, value=25)
        phone = st.text_input("연락처 (예: 010-1234-5678)")
        address = st.text_input("주소 (OO동까지)")
        
        st.divider()
        st.subheader("2. 추가 질문")
        q1 = st.selectbox("교통방법", ["자차", "대중교통", "셔틀버스"])
        q2 = st.text_input("출퇴근 소요시간")
        q3 = st.radio("오전 05:20까지 도착 가능여부", ["가능", "불가능"])
        
        submitted = st.form_submit_button("🚀 지금 지원하기")
        
        if submitted:
            if name and phone and address:
                # 중복 체크 및 저장 로직
                is_duplicate = False
                if os.path.exists(APPLICANT_FILE):
                    df_temp = pd.read_excel(APPLICANT_FILE)
                    if phone in df_temp['연락처'].astype(str).values:
                        is_duplicate = True
                
                if is_duplicate:
                    st.warning("이미 지원하신 연락처입니다! 확인 후 연락드릴게요.")
                else:
                    new_app = {
                        "신청시간": [pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")],
                        "이름": [name], "성별": [gender], "나이": [age],
                        "연락처": [phone], "주소": [address],
                        "교통방법": [q1], "소요시간": [q2], "새벽도착가능": [q3]
                    }
                    df_app = pd.DataFrame(new_app)
                    if not os.path.exists(APPLICANT_FILE):
                        df_app.to_excel(APPLICANT_FILE, index=False)
                    else:
                        pd.concat([pd.read_excel(APPLICANT_FILE), df_app], ignore_index=True).to_excel(APPLICANT_FILE, index=False)
                    st.balloons()
                    st.success(f"{name}님, 지원이 완료되었습니다! 담당자가 곧 연락드릴게요. ✈️")
            else:
                st.error("필수 항목(이름, 연락처, 주소)을 모두 입력해 주세요!")
