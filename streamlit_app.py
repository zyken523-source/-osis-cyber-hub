
import os
from openai import OpenAI
import streamlit as st

st.set_page_config(
    page_title="MURDANY // AI INTELLIGENCE",
    page_icon="🛰️",
    layout="wide"
)

st.title("MURDANY // AI INTELLIGENCE")
st.caption("AI-powered data analysis")

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("OPENAI_API_KEY belum dipasang.")
    st.stop()

client = OpenAI(api_key=api_key)

uploaded = st.file_uploader(
    "Upload data untuk dianalisis",
    type=["txt", "csv", "json", "md"]
)

question = st.text_area(
    "Instruksi analisis",
    placeholder="Analisis data ini, temukan pola, hubungan, dan kesimpulannya..."
)

if st.button("MULAI ANALISIS", type="primary"):
    if not uploaded and not question.strip():
        st.warning("Masukkan pertanyaan atau upload data.")
        st.stop()

    data = ""
    if uploaded:
        data = uploaded.getvalue().decode("utf-8", errors="replace")

    prompt = f"""
    Kamu adalah MURDANY AI Intelligence Analyst.
    Analisis hanya berdasarkan data yang diberikan.
    Jangan mengarang fakta.
    Pisahkan fakta, dugaan, dan hal yang belum diketahui.

    DATA:
    {data[:50000]}

    PERMINTAAN:
    {question}
    """

    with st.spinner("AI sedang menganalisis..."):
        try:
            response = client.responses.create(
                model="gpt-6",
                input=prompt
            )
            st.subheader("HASIL ANALISIS")
            st.markdown(response.output_text)
        except Exception as e:
            st.error(f"API Error: {e}")
