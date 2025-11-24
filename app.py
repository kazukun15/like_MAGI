import os
import textwrap

import streamlit as st
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError, ResourceExhausted


# =============================================================================
# 初期設定
# =============================================================================

st.set_page_config(
    page_title="Gemini動作テスト（2.0 Flash Lite）",
    layout="centered",
)

st.title("🔬 Gemini 2.0 Flash Lite 動作テスト")
st.caption("※ このアプリは MAGI ではなく Gemini の挙動確認専用のテスターです")

# APIキー取得（secrets優先 → 環境変数）
api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))

if not api_key:
    st.error(
        "❌ Gemini APIキーが設定されていません。\n\n"
        "・Streamlit Cloud: Secrets に GEMINI_API_KEY を設定\n"
        "・ローカル: 環境変数 GEMINI_API_KEY を設定\n"
    )
    st.stop()

genai.configure(api_key=api_key)


# =============================================================================
# テスト用関数
# =============================================================================

def test_gemini(prompt: str):
    """
    gemini-2.0-flash-lite に対してシンプルな generate_content を行い、
    レスポンスオブジェクト or エラーメッセージ文字列を返す。
    """
    model_name = "gemini-2.0-flash-lite"
    model = genai.GenerativeModel(model_name)

    try:
        resp = model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": 256,  # 普通に1回答には十分な程度
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
    "送信するテキスト（短文でOK）",
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
        st.error("❌ API / SDK レベルで例外が発生しました")
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
    # 4) candidates / parts
    # -------------------------------------------------------------
    st.subheader("🧪 candidates の詳細")

    candidates = getattr(resp, "candidates", None)

    if not candidates:
        st.warning("candidates が None または空です。")
    else:
        st.write(f"候補数: {len(candidates)}")

        for idx, cand in enumerate(candidates):
            st.write(f"### candidate[{idx}]")

            finish_reason = getattr(cand, "finish_reason", None)
            index = getattr(cand, "index", None)
            st.json({
                "finish_reason": finish_reason,
                "index": index,
            })

            content = getattr(cand, "content", None)
            st.write("content の型:", type(content).__name__)

            if content is not None:
                parts = getattr(content, "parts", None)
                if not parts:
                    st.warning("parts が None または空です。")
                else:
                    st.write(f"parts 数: {len(parts)}")
                    for p_idx, part in enumerate(parts):
                        st.write(f"#### parts[{p_idx}]")
                        part_text = getattr(part, "text", None)
                        st.json({
                            "type": type(part).__name__,
                            "text": part_text,
                        })
            else:
                st.warning("content が None です。")

    # -------------------------------------------------------------
    # 5) prompt_feedback
    # -------------------------------------------------------------
    st.subheader("🧪 prompt_feedback")

    pf = getattr(resp, "prompt_feedback", None)
    if pf is None:
        st.json({"info": "なし"})
    else:
        # proto 系なら to_dict があることが多いのでそれを使う
        try:
            if hasattr(pf, "to_dict"):
                st.json(pf.to_dict())
            else:
                # そのまま渡すと JSON エラーになる可能性があるので repr で表示
                st.code(repr(pf))
        except Exception as e:
            st.code(f"prompt_feedback 表示時例外: {repr(e)}")

    # -------------------------------------------------------------
    # 6) usage_metadata
    # -------------------------------------------------------------
    st.subheader("🧪 usage_metadata")

    usage = getattr(resp, "usage_metadata", None)
    if usage is None:
        st.json({"info": "なし"})
    else:
        try:
            if hasattr(usage, "to_dict"):
                st.json(usage.to_dict())
            else:
                st.code(repr(usage))
        except Exception as e:
            st.code(f"usage_metadata 表示時例外: {repr(e)}")
