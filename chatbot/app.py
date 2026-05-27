import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="Brickstore AI 상담사", page_icon="🧱", layout="centered")
st.title("🧱 Brickstore AI 상담사")
st.caption("Powered by Databricks")

with st.sidebar:
    st.header("⚙️ 설정")
    databricks_token = st.text_input("Databricks Token", type="password")
    base_url = st.text_input(
        "Databricks Endpoint URL",
        placeholder="https://<workspace>.cloud.databricks.com/serving-endpoints",
    )
    model_name = st.text_input("Model Name", placeholder="예: my-model-endpoint")
    st.divider()
    if st.button("🗑️ 대화 초기화"):
        st.session_state.messages = []
        st.rerun()

missing = [
    name
    for name, val in [
        ("Databricks Token", databricks_token),
        ("Endpoint URL", base_url),
        ("Model Name", model_name),
    ]
    if not val
]
if missing:
    st.info(f"👈 사이드바에서 {', '.join(missing)}을(를) 입력하세요.")
    st.stop()

client = OpenAI(api_key=databricks_token, base_url=base_url)

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("메시지를 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        current_item_id = None
        current_text = ""

        try:
            stream = client.responses.create(
                model=model_name,
                input=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True,
            )
            for event in stream:
                if getattr(event, "type", "") != "response.output_text.delta":
                    continue

                item_id = getattr(event, "item_id", "") or ""
                if not item_id.startswith("msg_bdrk_"):
                    continue

                # 새 메시지(step)가 시작되면 이전 텍스트(중간 사고 과정)는 버리고 리셋
                if item_id != current_item_id:
                    current_item_id = item_id
                    current_text = ""

                current_text += getattr(event, "delta", "") or ""
                placeholder.markdown(current_text + "▌")

            placeholder.markdown(current_text)
            st.session_state.messages.append(
                {"role": "assistant", "content": current_text}
            )

        except Exception as e:
            placeholder.error(f"오류 발생: {type(e).__name__}: {e}")
