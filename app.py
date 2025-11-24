import streamlit as st
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError, ResourceExhausted
import os
import json
import textwrap


# =============================================================================
# 初期設定
# =============================================================================

st.set_page_config(
    page_title="Gemini動作テスト（2.5 Flash）",
    layout="centered",
)

st.title("🔬 Gemini 2.5 Flash 動作テスト")
st.caption("※ このアプリは MAGI ではなく Gemini の挙動確認専用のテスターです")

api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))

if not api_key:
    st.error("❌ Gemini APIキーが設定されていません。\n\n環境変数 or Streamlit secrets に設定してください。")
    st.stop()

genai.configure(api_key=api_key)


# =============================================================================
# テスト用関数
# =============================================================================

def test_gemini(prompt: str):
    model_name = "gemini-2.5-flash"
    model = genai.GenerativeModel(model_name)

    try:
        resp = model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": 128,
                "temperature": 0.6,
            },
        )
        return resp

    except ResourceExhausted as e:
        return f"ResourceExhausted: {repr(e)}"

    except GoogleAPIError as e:
        return f"GoogleAPIError: {repr(e)}"

    except Exception as e:
        return f"Exception: {repr(e)}"


# =============================================================================
# UI
# =============================================================================

prompt = st.text_area(
    "送信するテキスト（短文推奨）",
    "天気は？",
    height=100,
)

if st.button("▶ テスト実行"):
    with st.spinner("Geminiへ問い合わせ中..."):
        resp = test_gemini(prompt)

    # -------------------------------------------------------------
    # 1) 例外で返ってきたケース（最上位が文字列）
    # -------------------------------------------------------------
    if isinstance(resp, str):
        st.error("❌ API or SDK レベルのエラー（例外）発生")
        st.code(resp)
        st.stop()

    # -------------------------------------------------------------
    # 2) resp 全体の repr
    # -------------------------------------------------------------
    st.subheader("🧪 resp（生データ repr）")
    try:
        full_repr = repr(resp)
    except Exception as e:
        full_repr = f"<repr(resp) failed: {e}>"

    st.code(textwrap.shorten(full_repr, width=2000, placeholder="..."), language="python")

    # -------------------------------------------------------------
    # 3) resp.text
    # -------------------------------------------------------------
    st.subheader("🧪 resp.text の中身")
    try:
        text_val = (getattr(resp, "text", "") or "").strip()
        st.code(text_val if text_val else "<空>", language="markdown")
    except Exception as e:
        st.code(f"resp.text 取得時例外: {repr(e)}")

    # -------------------------------------------------------------
    # 4) candidates
    # -------------------------------------------------------------
    st.subheader("🧪 candidates 詳細")

    candidates = getattr(resp, "candidates", None)

    if not candidates:
        st.warning("candidates が None または空です。")
    else:
        st.write(f"候補数: {len(candidates)}")

        for idx, cand in enumerate(candidates):
            st.write(f"### candidate[{idx}]")
            st.json({
                "finish_reason": getattr(cand, "finish_reason", None),
                "index": getattr(cand, "index", None),
            })

            # content
            content = getattr(cand, "content", None)
            st.write("content:", type(content).__name__)

            if content is not None:
                parts = getattr(content, "parts", None)
                if not parts:
                    st.warning("parts が None または空")
                else:
                    st.write(f"parts 数: {len(parts)}")
                    for p_idx, part in enumerate(parts):
                        st.write(f"#### parts[{p_idx}]")
                        st.json({
                            "type": type(part).__name__,
                            "text": getattr(part, "text", None),
                        })

    # -------------------------------------------------------------
    # 5) prompt_feedback と usage_metadata
    # -------------------------------------------------------------
    st.subheader("🧪 prompt_feedback")
    pf = getattr(resp, "prompt_feedback", None)
    st.json(pf if pf else "<なし>")

    st.subheader("🧪 usage_metadata")
    usage = getattr(resp, "usage_metadata", None)
    st.json(usage if usage else "<なし>")

