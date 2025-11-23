import os
import io
import json
from typing import Dict, Any, Optional

import streamlit as st
from PIL import Image

import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, GoogleAPIError
import docx


# ======================================================
# ページ設定
# ======================================================
st.set_page_config(
    page_title="MAGI風マルチAI分析システム（Gemini版）",
    page_icon="🧬",
    layout="wide",
)

# ------------------------------------------------------
# MAGI風 カスタムCSS（スマホ対応・投票表示つき）
# ------------------------------------------------------
st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at top, #222b40 0, #050710 45%, #02030a 100%);
        color: #e0e4ff;
        font-family: "Roboto Mono", "SF Mono", "Consolas", "Noto Sans JP", monospace;
    }
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-thumb {
        background: #3e4a6e;
        border-radius: 3px;
    }
    .magi-header {
        border: 1px solid #4d5cff;
        border-radius: 10px;
        padding: 12px 18px;
        margin-bottom: 16px;
        background: linear-gradient(135deg, rgba(35,50,95,0.95), rgba(10,15,35,0.95));
        box-shadow: 0 0 20px rgba(80,120,255,0.35);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .magi-header-left { display: flex; flex-direction: column; }
    .magi-header-title {
        font-size: 20px;
        letter-spacing: 0.18em;
        color: #e8ecff;
        text-transform: uppercase;
    }
    .magi-header-sub {
        font-size: 11px;
        color: #9fa8ff;
        margin-top: 4px;
    }
    .magi-status {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 11px;
        color: #b6ffcc;
    }
    .magi-status-light {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: radial-gradient(circle, #9fffcb 0, #00ff66 40%, #008833 100%);
        box-shadow: 0 0 8px #00ff99;
        animation: magi-pulse 1.5s infinite ease-in-out;
    }
    @keyframes magi-pulse {
        0% { transform: scale(1); opacity: 0.8; }
        50% { transform: scale(1.3); opacity: 1; }
        100% { transform: scale(1); opacity: 0.8; }
    }
    .magi-info-card {
        border-radius: 10px;
        border: 1px solid rgba(130,140,200,0.6);
        background: linear-gradient(135deg, rgba(16,22,48,0.95), rgba(6,10,26,0.95));
        padding: 10px 14px;
        font-size: 13px;
        color: #cfd6ff;
        margin-bottom: 8px;
    }
    .magi-info-card b { color: #ffffff; }

    .magi-panel {
        border-radius: 10px;
        padding: 10px 14px;
        margin-top: 6px;
        margin-bottom: 6px;
        font-size: 13px;
        line-height: 1.6;
        border: 1px solid rgba(140,160,255,0.4);
        background: radial-gradient(circle at top, rgba(18,26,60,0.98), rgba(5,8,22,0.98));
        box-shadow: 0 0 15px rgba(90,110,200,0.35);
        overflow-wrap: break-word;
    }
    .magi-panel-logic {
        border-color: #497bff;
        box-shadow: 0 0 16px rgba(74,123,255,0.4);
    }
    .magi-panel-human {
        border-color: #ffb349;
        box-shadow: 0 0 16px rgba(255,179,73,0.4);
    }
    .magi-panel-reality {
        border-color: #3fd684;
        box-shadow: 0 0 16px rgba(63,214,132,0.4);
    }
    .magi-panel-media {
        border-color: #c36bff;
        box-shadow: 0 0 16px rgba(195,107,255,0.4);
    }
    .magi-panel-summary {
        margin-top: 8px;
        font-size: 13px;
        line-height: 1.6;
        color: #e3e7ff;
    }

    .magi-vote {
        display: inline-flex;
        flex-direction: column;
        align-items: flex-start;
        justify-content: center;
        padding: 6px 10px;
        border-radius: 6px;
        margin-bottom: 6px;
        font-size: 11px;
    }
    .magi-vote-label-en {
        font-size: 10px;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        opacity: 0.9;
    }
    .magi-vote-label-jp {
        font-size: 12px;
        font-weight: 600;
        margin-top: 2px;
    }
    .magi-vote-approve {
        background: linear-gradient(135deg, #0b5428, #21b35a);
        border: 1px solid #39ff9c;
        box-shadow: 0 0 12px rgba(50,255,170,0.7);
        color: #e8fff4;
    }
    .magi-vote-reject {
        background: linear-gradient(135deg, #5b1111, #d63232);
        border: 1px solid #ff7b7b;
        box-shadow: 0 0 12px rgba(255,100,100,0.7);
        color: #ffecec;
    }
    .magi-vote-hold {
        background: linear-gradient(135deg, #6a5212, #d7a52b);
        border: 1px solid #ffd966;
        box-shadow: 0 0 12px rgba(255,220,120,0.7);
        color: #fff8e1;
    }

    .magi-aggregator {
        border-radius: 12px;
        padding: 16px 18px;
        margin-top: 10px;
        border: 1px solid #6f8dff;
        background: radial-gradient(circle at top, rgba(31,42,90,0.98), rgba(6,8,20,0.98));
        box-shadow: 0 0 22px rgba(110,140,255,0.5);
        font-size: 14px;
        color: #ecf0ff;
        line-height: 1.7;
        overflow-wrap: break-word;
    }

    .magi-section-title {
        font-size: 15px;
        font-weight: 600;
        color: #e3e7ff;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-top: 16px;
        margin-bottom: 6px;
    }
    .magi-divider {
        height: 1px;
        border: none;
        background: linear-gradient(to right, #4b5cff, transparent);
        margin-bottom: 10px;
    }

    @media (max-width: 768px) {
        .magi-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 8px;
        }
        .magi-header-title {
            font-size: 16px;
        }
        .magi-panel {
            font-size: 12px;
            padding: 8px 10px;
        }
        .magi-aggregator {
            font-size: 13px;
            padding: 12px 14px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# MAGI ヘッダー
st.markdown(
    """
    <div class="magi-header">
        <div class="magi-header-left">
            <div class="magi-header-title">MAGI MULTI-AGENT INTELLIGENCE</div>
            <div class="magi-header-sub">
                GEMINI 2.5 FLASH · MULTI-VIEW ANALYSIS · HUMAN / LOGIC / REALITY / MEDIA
            </div>
        </div>
        <div class="magi-status">
            <div class="magi-status-light"></div>
            <span>SYSTEM STATUS: ONLINE</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="magi-info-card">
    <b>概要：</b> テキスト・画像・音声など、媒体を問わず入力された情報を、
    <b>Magi-Logic / Magi-Human / Magi-Reality / Magi-Media</b> の4つのエージェントがそれぞれの視点から分析し、<br>
    最後に統合 AI が <b>MAGI システム風レポート</b> として結論・アクションプランを提示します。
    </div>
    """,
    unsafe_allow_html=True,
)

# ======================================================
# Gemini API 初期化
# ======================================================
api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))

if not api_key:
    st.error(
        "Gemini の API キーが設定されていません。\n\n"
        "【Streamlit Cloud】Settings → Secrets で：\n"
        'GEMINI_API_KEY = "あなたのGemini APIキー"\n\n'
        "【ローカル】.streamlit/secrets.toml または環境変数 GEMINI_API_KEY に設定してください。"
    )
    st.stop()

genai.configure(api_key=api_key)


@st.cache_resource(show_spinner=False)
def get_gemini_model():
    return genai.GenerativeModel(
        "gemini-2.5-flash",
        generation_config={"max_output_tokens": 1024},
    )


# ======================================================
# 共通ユーティリティ
# ======================================================
def clean_text_for_display(text: str) -> str:
    if not text:
        return ""
    return text.replace("*", "・")


def trim_text(s: str, max_chars: int = 4000) -> str:
    if not s:
        return ""
    if len(s) <= max_chars:
        return s
    return s[:max_chars] + "\n…（長文のためここで省略）"


# ======================================================
# 媒体のテキスト化（画像・音声）
# ======================================================
def describe_image_with_gemini(img: Image.Image) -> str:
    model = get_gemini_model()
    prompt = (
        "この画像に何が写っているか、日本語で簡潔に説明してください。\n"
        "続けて、その画像が与える心理的な印象を一行で述べてください。\n"
        "箇条書きは 1. 2. のような番号のみを使い、記号は極力使わないでください。"
    )
    try:
        resp = model.generate_content([prompt, img])
        return clean_text_for_display(resp.text.strip())
    except ResourceExhausted:
        return "【エラー】Gemini のリソース上限に達しました（画像解析）。時間をおいて再実行してください。"
    except GoogleAPIError as e:
        return f"【エラー】Gemini API画像解析で問題が発生しました: {str(e)}"
    except Exception as e:
        return f"【エラー】画像解析中に想定外のエラーが発生しました: {str(e)}"


def transcribe_audio_with_gemini(uploaded_file) -> str:
    model = get_gemini_model()
    audio_bytes = uploaded_file.getvalue()
    mime_type = uploaded_file.type or "audio/wav"

    prompt = (
        "この音声の内容を日本語でできるだけ正確に文字起こししてください。\n"
        "出力には特別な記号は使わず、通常の日本語文だけで書いてください。"
    )
    try:
        resp = model.generate_content(
            [prompt, {"mime_type": mime_type, "data": audio_bytes}]
        )
        return clean_text_for_display(resp.text.strip())
    except ResourceExhausted:
        return "【エラー】Gemini のリソース上限に達しました（音声文字起こし）。時間をおいて再実行してください。"
    except GoogleAPIError as e:
        return f"【エラー】Gemini API音声解析で問題が発生しました: {str(e)}"
    except Exception as e:
        return f"【エラー】音声解析中に想定外のエラーが発生しました: {str(e)}"


# ======================================================
# 単一APIで MAGI 全員＋統合をまとめて呼び出す（JSON強制）
# ======================================================
def call_magi_all(context: Dict[str, Any]) -> Dict[str, Any] | str:
    """
    1回の Gemini 呼び出しで、
    ・4エージェントの結果
    ・統合MAGIの結果
    を JSON 形式で返してもらう。
    失敗時はエラー文の文字列を返す。
    """
    model = get_gemini_model()

    trimmed_context = {
        "user_question": trim_text(context.get("user_question", "")),
        "text_input": trim_text(context.get("text_input", "")),
        "audio_transcript": trim_text(context.get("audio_transcript", "")),
        "image_description": trim_text(context.get("image_description", "")),
    }

    sys_prompt = """
あなたは NERV の MAGI システム全体を同時にシミュレートする統合 AI です。
Magi-Logic / Magi-Human / Magi-Reality / Magi-Media の4エージェントと、
それらを統合する MAGI 統合 AI の役割をすべて一度に出力してください。

[重要]
- 出力は必ず JSON 形式のみで返してください。
- JSON以外の文字（説明文など）は出力しないでください。
- キー名は以下の構造に厳密に従ってください。

[JSON構造]

{
  "agents": {
    "logic": {
      "name_jp": "Magi-Logic（論理・構造担当）",
      "summary": "このエージェント視点の要約（2〜6行程度、日本語）",
      "full_report": "詳細なレポート全文（見出し「【要約】」「【前提認識】」などを含む日本語テキスト）",
      "decision_code": "Go または Hold または No-Go",
      "decision_jp": "可決 または 保留 または 否決"
    },
    "human": { ... 同様 ... },
    "reality": { ... 同様 ... },
    "media": { ... 同様 ... }
  },
  "aggregated": {
    "summary": "MAGI統合としての全体サマリー（日本語）",
    "details": "MAGI統合の詳細レポート（日本語。見出しを含んでもよい）"
  }
}

[各エージェントの役割]

- logic: 論理・構造・因果関係に特化。問題の構造化、矛盾の指摘、実行ステップ整理。
- human: 感情・心理・コミュニケーションに特化。関係者の感情、伝え方、メンタル面のリスク。
- reality: 現実運用・コスト・リスク管理に特化。実現可能性、リソース、現場のボトルネック。
- media: 画像・音声・テキストなど媒体表現に特化。印象、構図、表現の良し悪しと改善案。

[判断]
- decision_code は必ず "Go" / "Hold" / "No-Go" のいずれか。
- decision_jp はそれぞれ "可決" / "保留" / "否決" に対応させてください。
"""

    ctx_text = json.dumps(trimmed_context, ensure_ascii=False, indent=2)

    try:
        # ★ここで JSON を強制するのが今回の修正ポイント
        resp = model.generate_content(
            [sys_prompt, f"【ユーザーからの情報】\n{ctx_text}"],
            generation_config={
                "max_output_tokens": 1024,
                "response_mime_type": "application/json",
            },
        )
        raw = resp.text.strip()

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            # 生の応答も返してデバッグしやすく
            snippet = raw[:500]
            return (
                "【エラー】MAGI結果のJSONを正しく受信できませんでした。\n"
                f"JSONDecodeError: {str(e)}\n"
                "先頭500文字の生レスポンス：\n"
                f"{snippet}"
            )

        return data

    except ResourceExhausted:
        return "【エラー】Gemini のリソース上限に達しました（MAGI複合分析）。時間をおいて再実行してください。"
    except GoogleAPIError as e:
        return f"【エラー】Gemini API複合分析で問題が発生しました: {str(e)}"
    except Exception as e:
        return f"【エラー】MAGI複合分析中に想定外のエラーが発生しました: {str(e)}"


def decision_to_css(decision_code: str) -> Dict[str, str]:
    code = (decision_code or "Hold").strip()
    if code == "Go":
        return {"css": "approve", "en": "APPROVE", "jp": "可決"}
    if code == "No-Go":
        return {"css": "reject", "en": "REJECT", "jp": "否決"}
    return {"css": "hold", "en": "HOLD", "jp": "保留"}


# ======================================================
# Word レポート生成
# ======================================================
def build_word_report(
    context: Dict[str, Any],
    agents: Dict[str, Any],
    aggregated: Dict[str, Any],
    image: Optional[Image.Image] = None,
) -> bytes:
    doc = docx.Document()
    doc.add_heading("MAGI風マルチAI分析レポート（Gemini版）", level=1)

    # 第1章 入力情報
    doc.add_heading("第1章 入力情報", level=2)
    doc.add_paragraph(f"■ ユーザー質問：{context.get('user_question', '')}")
    if context.get("text_input"):
        doc.add_paragraph("■ テキスト入力：")
        doc.add_paragraph(context["text_input"])
    if context.get("audio_transcript"):
        doc.add_paragraph("■ 音声文字起こし：")
        doc.add_paragraph(context["audio_transcript"])
    if context.get("image_description"):
        doc.add_paragraph("■ 画像の説明：")
        doc.add_paragraph(context["image_description"])

    if image is not None:
        img_stream = io.BytesIO()
        image.save(img_stream, format="PNG")
        img_stream.seek(0)
        doc.add_picture(img_stream, width=docx.shared.Inches(3))

    # 第2章 各MAGIエージェントの分析
    doc.add_heading("第2章 各MAGIエージェントの分析", level=2)
    for key in ["logic", "human", "reality", "media"]:
        if key not in agents:
            continue
        a = agents[key]
        name = a.get("name_jp", key)
        doc.add_heading(name, level=3)
        full_report = clean_text_for_display(a.get("full_report", ""))
        for line in full_report.splitlines():
            doc.add_paragraph(line)

    # 第3章 MAGI統合AIの結論
    doc.add_heading("第3章 MAGI統合AIの結論・アクションプラン", level=2)
    agg_text = clean_text_for_display(aggregated.get("details", ""))
    for line in agg_text.splitlines():
        doc.add_paragraph(line)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.getvalue()


# ======================================================
# UI：入力エリア
# ======================================================
st.markdown(
    '<div class="magi-section-title">INPUT · QUERY & MEDIA</div><hr class="magi-divider">',
    unsafe_allow_html=True,
)

user_question = st.text_area(
    "MAGI に投げたい「問い」",
    placeholder=(
        "例：この企画の方向性と改善点をMAGIに評価してほしい。\n"
        "例：この写真や音声から受ける印象と、次に取るべき行動を知りたい。"
    ),
    height=120,
)

st.markdown("#### 媒体入力モード（任意）")
input_mode = st.radio(
    "画像・音声の入力方法を選択してください。",
    ["ファイル／写真ライブラリから選択", "カメラで撮影", "使用しない"],
    index=0,
)

col1, col2 = st.columns(2)
uploaded_file: Optional[st.runtime.uploaded_file_manager.UploadedFile] = None
image_for_report: Optional[Image.Image] = None
media_type: Optional[str] = None

with col1:
    if input_mode == "ファイル／写真ライブラリから選択":
        file = st.file_uploader(
            "画像 / 音声 / テキストファイル\n（スマホではここからカメラ撮影や写真選択ができます）",
            accept_multiple_files=False,
        )
        if file:
            uploaded_file = file
    else:
        st.write("ファイル／写真ライブラリからの選択は無効です。")

with col2:
    if input_mode == "カメラで撮影":
        cam = st.camera_input("カメラで撮影（対応端末のみ）")
        if cam:
            uploaded_file = cam
    else:
        st.write("カメラは現在オフになっています。")

text_input = st.text_area(
    "補足テキスト（任意）",
    height=100,
    placeholder="貼り付けたいメモや補足情報があれば入力してください。",
)

if not user_question and not uploaded_file and not text_input:
    st.info("質問か、媒体（画像・音声など）、または補足テキストのいずれかを入力してください。")
    st.stop()

# ======================================================
# 媒体の前処理（テキスト化）
# ======================================================
context: Dict[str, Any] = {
    "user_question": user_question,
    "text_input": text_input,
    "audio_transcript": "",
    "image_description": "",
}

if uploaded_file is not None:
    if uploaded_file.type and uploaded_file.type.startswith("image/"):
        media_type = "image"
        try:
            image = Image.open(uploaded_file).convert("RGB")
        except Exception:
            st.error("この画像形式には対応していません。JPEG または PNG 形式の画像を使用してください。")
            image = None

        if image is not None:
            image_for_report = image
            st.image(image, caption="入力画像", use_column_width=True)

            with st.spinner("画像内容を解析中（Gemini）..."):
                img_desc = describe_image_with_gemini(image)
            context["image_description"] = img_desc

    elif uploaded_file.type and uploaded_file.type.startswith("audio/"):
        media_type = "audio"
        st.audio(uploaded_file)

        with st.spinner("音声を文字起こし中（Gemini）..."):
            transcript = transcribe_audio_with_gemini(uploaded_file)
        context["audio_transcript"] = transcript

    else:
        media_type = "other"
        if (uploaded_file.type == "text/plain") or (
            isinstance(uploaded_file.name, str) and uploaded_file.name.lower().endswith(".txt")
        ):
            text_bytes = uploaded_file.read()
            context["text_input"] += "\n\n[ファイル内容]\n" + text_bytes.decode(
                "utf-8", errors="ignore"
            )
        else:
            st.warning("対応していないファイル形式です。画像・音声・テキストファイルを使用してください。")

# ======================================================
# MAGI 複合分析
# ======================================================
st.markdown(
    '<div class="magi-section-title">PROCESS · MAGI AGENT ANALYSIS</div><hr class="magi-divider">',
    unsafe_allow_html=True,
)

if st.button("🔎 MAGI による分析を実行", type="primary"):
    if not user_question and not text_input and not any(
        [context["audio_transcript"], context["image_description"]]
    ):
        st.warning("最低でも質問・テキスト・媒体のいずれかが必要です。")
        st.stop()

    with st.spinner("MAGI 複合分析を実行中..."):
        result = call_magi_all(context)

    if isinstance(result, str):
        st.error(result)
        st.stop()

    agents = result.get("agents", {})
    aggregated = result.get("aggregated", {"summary": "", "details": ""})

    st.success("各エージェントとMAGI統合の分析が完了しました。")

    colL, colR = st.columns(2)

    # 左側：Logic / Reality
    with colL:
        if "logic" in agents:
            a = agents["logic"]
            dec = decision_to_css(a.get("decision_code", "Hold"))
            st.markdown("##### Magi-Logic")
            st.markdown(
                f'''
                <div class="magi-panel magi-panel-logic">
                  <div class="magi-vote magi-vote-{dec["css"]}">
                    <div class="magi-vote-label-en">{dec["en"]}</div>
                    <div class="magi-vote-label-jp">{dec["jp"]}</div>
                  </div>
                  <div class="magi-panel-summary">
                    {clean_text_for_display(a.get("summary", "")).replace("\n", "<br>")}
                  </div>
                </div>
                ''',
                unsafe_allow_html=True,
            )
            with st.expander("Logic の詳細を見る"):
                st.markdown(
                    clean_text_for_display(a.get("full_report", "")).replace("\n", "<br>"),
                    unsafe_allow_html=True,
                )

        if "reality" in agents:
            a = agents["reality"]
            dec = decision_to_css(a.get("decision_code", "Hold"))
            st.markdown("##### Magi-Reality")
            st.markdown(
                f'''
                <div class="magi-panel magi-panel-reality">
                  <div class="magi-vote magi-vote-{dec["css"]}">
                    <div class="magi-vote-label-en">{dec["en"]}</div>
                    <div class="magi-vote-label-jp">{dec["jp"]}</div>
                  </div>
                  <div class="magi-panel-summary">
                    {clean_text_for_display(a.get("summary", "")).replace("\n", "<br>")}
                  </div>
                </div>
                ''',
                unsafe_allow_html=True,
            )
            with st.expander("Reality の詳細を見る"):
                st.markdown(
                    clean_text_for_display(a.get("full_report", "")).replace("\n", "<br>"),
                    unsafe_allow_html=True,
                )

    # 右側：Human / Media
    with colR:
        if "human" in agents:
            a = agents["human"]
            dec = decision_to_css(a.get("decision_code", "Hold"))
            st.markdown("##### Magi-Human")
            st.markdown(
                f'''
                <div class="magi-panel magi-panel-human">
                  <div class="magi-vote magi-vote-{dec["css"]}">
                    <div class="magi-vote-label-en">{dec["en"]}</div>
                    <div class="magi-vote-label-jp">{dec["jp"]}</div>
                  </div>
                  <div class="magi-panel-summary">
                    {clean_text_for_display(a.get("summary", "")).replace("\n", "<br>")}
                  </div>
                </div>
                ''',
                unsafe_allow_html=True,
            )
            with st.expander("Human の詳細を見る"):
                st.markdown(
                    clean_text_for_display(a.get("full_report", "")).replace("\n", "<br>"),
                    unsafe_allow_html=True,
                )

        if "media" in agents:
            a = agents["media"]
            dec = decision_to_css(a.get("decision_code", "Hold"))
            st.markdown("##### Magi-Media")
            st.markdown(
                f'''
                <div class="magi-panel magi-panel-media">
                  <div class="magi-vote magi-vote-{dec["css"]}">
                    <div class="magi-vote-label-en">{dec["en"]}</div>
                    <div class="magi-vote-label-jp">{dec["jp"]}</div>
                  </div>
                  <div class="magi-panel-summary">
                    {clean_text_for_display(a.get("summary", "")).replace("\n", "<br>")}
                  </div>
                </div>
                ''',
                unsafe_allow_html=True,
            )
            with st.expander("Media の詳細を見る"):
                st.markdown(
                    clean_text_for_display(a.get("full_report", "")).replace("\n", "<br>"),
                    unsafe_allow_html=True,
                )

    # ==================================================
    # MAGI 統合AI
    # ==================================================
    st.markdown(
        '<div class="magi-section-title">OUTPUT · MAGI AGGREGATED DECISION</div><hr class="magi-divider">',
        unsafe_allow_html=True,
    )

    agg_html = clean_text_for_display(
        aggregated.get("details", "") or aggregated.get("summary", "")
    )
    st.markdown(
        f'<div class="magi-aggregator">{agg_html.replace("\n", "<br>")}</div>',
        unsafe_allow_html=True,
    )

    # ==================================================
    # レポート出力
    # ==================================================
    report_bytes = build_word_report(
        context=context,
        agents=agents,
        aggregated=aggregated,
        image=image_for_report,
    )

    st.markdown(
        '<div class="magi-section-title">REPORT · EXPORT</div><hr class="magi-divider">',
        unsafe_allow_html=True,
    )

    st.download_button(
        "MAGIレポート（Word）をダウンロード",
        data=report_bytes,
        file_name="MAGI分析レポート_Gemini版.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

else:
    st.info("下のボタンを押すと、MAGI の各エージェントと統合AIが一度に分析を開始します。")
