import requests
import streamlit as st


API_BASE_URL = "http://127.0.0.1:8000"


st.set_page_config(
    page_title="Job Application Assistant",
    page_icon="💼",
    layout="wide"
)


st.title("💼 Job Application Assistant")
st.write(
    "CV dosyanı ve iş ilanını yükleyerek yapay zeka destekli analiz, kapak yazısı ve mülakat hazırlığı oluşturabilirsin."
)


tab_analyze, tab_cover_letter, tab_interview, tab_history = st.tabs(
    [
        "CV Analizi",
        "Kapak Yazısı",
        "Mülakat Hazırlığı",
        "Geçmiş"
    ]
)


with tab_analyze:
    st.header("CV ve İş İlanı Analizi")

    analyze_cv_file = st.file_uploader(
        "CV dosyanı yükle",
        type=["pdf", "docx"],
        key="analyze_cv_file"
    )

    analyze_job_text = st.text_area(
        "İş ilanı metnini yapıştır",
        height=200,
        key="analyze_job_text"
    )

    if st.button("Analiz Et"):
        if analyze_cv_file is None:
            st.warning("Lütfen bir CV dosyası yükle.")
        elif not analyze_job_text.strip():
            st.warning("Lütfen iş ilanı metnini gir.")
        else:
            with st.spinner("CV analiz ediliyor..."):
                files = {
                    "cv_file": (
                        analyze_cv_file.name,
                        analyze_cv_file.getvalue(),
                        analyze_cv_file.type
                    )
                }

                data = {
                    "job_text": analyze_job_text
                }

                response = requests.post(
                    f"{API_BASE_URL}/analyze",
                    files=files,
                    data=data
                )

                if response.status_code == 200:
                    result = response.json()["result"]

                    st.success("Analiz tamamlandı.")

                    st.metric(
                        label="Uyum Skoru",
                        value=result.get("match_score", "N/A")
                    )

                    st.subheader("Genel Değerlendirme")
                    st.write(result.get("summary", ""))

                    st.subheader("Güçlü Yönler")
                    for item in result.get("strengths", []):
                        st.write(f"- {item}")

                    st.subheader("Eksik / Zayıf Yönler")
                    for item in result.get("weaknesses", []):
                        st.write(f"- {item}")

                    st.subheader("CV İyileştirme Önerileri")
                    for item in result.get("cv_improvements", []):
                        st.write(f"- {item}")

                    st.subheader("Başvuru Stratejisi")
                    st.write(result.get("application_strategy", ""))

                    st.subheader("Genel Sonuç")
                    st.write(result.get("final_recommendation", ""))

                else:
                    st.error(response.text)


with tab_cover_letter:
    st.header("Kapak Yazısı Oluştur")

    cover_cv_file = st.file_uploader(
        "CV dosyanı yükle",
        type=["pdf", "docx"],
        key="cover_cv_file"
    )

    cover_job_text = st.text_area(
        "İş ilanı metnini yapıştır",
        height=200,
        key="cover_job_text"
    )

    tone = st.selectbox(
        "Yazı tonu",
        ["professional", "friendly", "confident", "formal", "short"]
    )

    language = st.selectbox(
        "Kapak yazısı dili",
        ["Turkish", "English"]
    )

    if st.button("Kapak Yazısı Oluştur"):
        if cover_cv_file is None:
            st.warning("Lütfen bir CV dosyası yükle.")
        elif not cover_job_text.strip():
            st.warning("Lütfen iş ilanı metnini gir.")
        else:
            with st.spinner("Kapak yazısı oluşturuluyor..."):
                files = {
                    "cv_file": (
                        cover_cv_file.name,
                        cover_cv_file.getvalue(),
                        cover_cv_file.type
                    )
                }

                data = {
                    "job_text": cover_job_text,
                    "tone": tone,
                    "language": language
                }

                response = requests.post(
                    f"{API_BASE_URL}/cover-letter",
                    files=files,
                    data=data
                )

                if response.status_code == 200:
                    result = response.json()["result"]

                    st.success("Kapak yazısı oluşturuldu.")
                    st.text_area(
                        "Oluşturulan Kapak Yazısı",
                        value=result,
                        height=350
                    )

                else:
                    st.error(response.text)


with tab_interview:
    st.header("Mülakat Hazırlığı")

    interview_job_text = st.text_area(
        "İş ilanı metnini yapıştır",
        height=250,
        key="interview_job_text"
    )

    interview_language = st.selectbox(
        "Mülakat hazırlığı dili",
        ["Turkish", "English"],
        key="interview_language"
    )

    if st.button("Mülakat Soruları Oluştur"):
        if not interview_job_text.strip():
            st.warning("Lütfen iş ilanı metnini gir.")
        else:
            with st.spinner("Mülakat soruları oluşturuluyor..."):
                data = {
                    "job_text": interview_job_text,
                    "language": interview_language
                }

                response = requests.post(
                    f"{API_BASE_URL}/interview-prep",
                    data=data
                )

                if response.status_code == 200:
                    result = response.json()["result"]

                    st.success("Mülakat hazırlığı oluşturuldu.")

                    st.subheader("Teknik Sorular")
                    for item in result.get("technical_questions", []):
                        st.markdown(f"**Soru:** {item.get('question')}")
                        st.write(f"İpucu: {item.get('answer_hint')}")
                        st.divider()

                    st.subheader("HR Soruları")
                    for item in result.get("hr_questions", []):
                        st.markdown(f"**Soru:** {item.get('question')}")
                        st.write(f"İpucu: {item.get('answer_hint')}")
                        st.divider()

                    st.subheader("Zorlayıcı Sorular")
                    for item in result.get("challenging_questions", []):
                        st.markdown(f"**Soru:** {item.get('question')}")
                        st.write(f"İpucu: {item.get('answer_hint')}")
                        st.divider()

                    st.subheader("Hazırlık Önerileri")
                    for tip in result.get("preparation_tips", []):
                        st.write(f"- {tip}")

                else:
                    st.error(response.text)


with tab_history:
    st.header("Geçmiş Kayıtlar")

    if st.button("Geçmişi Yenile"):
        response = requests.get(f"{API_BASE_URL}/history")

        if response.status_code == 200:
            history_items = response.json()

            if not history_items:
                st.info("Henüz geçmiş kayıt yok.")
            else:
                for item in history_items:
                    with st.expander(
                        f"{item['id']} - {item['request_type']} - {item['created_at']}"
                    ):
                        st.write("Dosya:", item.get("cv_filename"))
                        st.write("Sonuç:")
                        st.json(item.get("result")) if isinstance(item.get("result"), dict) else st.write(item.get("result"))

        else:
            st.error(response.text)