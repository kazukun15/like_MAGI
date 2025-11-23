import os
import io
import re
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
    page_title="MAGI風マルチAI分析システム（テキスト簡易版）",
    page_icon="🧬",
    layout="wide",
)

# ------------------------------------------------------
# MAGI風 カスタムCSS（スマホ対応）
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
        margin-top: 4px;
        font-size: 13px;
        line-height: 1.6;
        color: #e3e7ff;
    }

    .magi-vote {
        display: inline-flex;
        flex-direction: column;
        align-items: flex-start;
        justify-content: center;
        padding: 4px 8px;
        border-radius: 6px;
        margin-bottom: 4px;
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
            fontサイズ: 16px;
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
                GEMINI 2.5 FLASH · TEXT-ONLY LIGHTWEIGHT ANALYSIS
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
    <b>概要：</b> テキスト・画像・音声などを入力すると、<b>Magi-Logic / Magi-Human / Magi-Reality / Magi-Media</b> が
    それぞれ短いコメントと判定を出し、最後に統合MAGIが結論をまとめます。<br>
    出力はプレーンテキスト形式のみとし、JSON解析を行わないことで安定性を優先した簡易版です。
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
    # レスポンス形式は各呼び出し側で処理
    return genai.GenerativeModel("gemini-2.5-flash")


# ======================================================
# ユーティリティ
# ======================================================
def clean_text_for_display(text: str) -> str:
    if not text:
        return ""
    return text.replace("*", "・")


def trim_text(s: str, max_chars: int = 600) -> str:
    if not s:
        return ""
    if len(s) <= max_chars:
        return s
    return s[:max_chars] + "\n…（長文のためここで省略）"


def extract_text_from_response(resp) -> Optional[str]:
    """
    google.generativeai のレスポンスから、できるだけ安全にテキストを取り出す。
    - resp.text が使えればそれを使う（ValueError は握りつぶす）
    - ダメなら candidates → content.parts から text を集める
    - MAX_TOKENS や SAFETY の終了理由があれば、それに応じたエラーメッセージを返す
    """
    try:
        t = (getattr(resp, "text", "") or "").strip()
        if t:
            return t
    except ValueError:
        pass

    texts: list[str] = []
    max_tokens_hit = False
    safety_block = False

    for cand in getattr(resp, "candidates", []) or []:
        finish_reason = getattr(cand, "finish_reason", None)
        if finish_reason == "MAX_TOKENS":
            max_tokens_hit = True
        if finish_reason == "SAFETY":
            safety_block = True

        content = getattr(cand, "content", None)
        if not content:
            continue

        for part in getattr(content, "parts", []) or []:
            part_text = getattr(part, "text", None)
            if part_text:
                texts.append(part_text)

    if texts:
        return "\n".join(texts).strip()

    if max_tokens_hit:
        return (
            "【エラー】Gemini の出力トークン上限(MAX_TOKENS)に達したため、"
            "テキストを最後まで生成できませんでした。質問や補足テキストを短くして再実行してください。"
        )
    if safety_block:
        return (
            "【エラー】Gemini の安全フィルタにより出力がブロックされました。\n"
            "表現を少し穏やかにする・個人情報や過激な表現を避けるなどして再実行してください。"
        )

    pf = getattr(resp, "prompt_feedback", None)
    block_reason = getattr(pf, "block_reason", None) if pf else None
    if block_reason:
        return f"【エラー】Gemini がテキストを返しませんでした（block_reason: {block_reason}）。"

    return None


# ======================================================
# 媒体のテキスト化（画像・音声）
# ======================================================
def describe_image_with_gemini(img: Image.Image) -> str:
    model = get_gemini_model()
    prompt = (
        "この画像に何が写っているか、日本語で簡潔に2〜3文で説明してください。\n"
        "心理的な印象も1文で添えてください。"
    )
    try:
        resp = model.generate_content(
            [prompt, img],
            generation_config={
                "max_output_tokens": 256,
            },
        )
        text = extract_text_from_response(resp)
        if not text:
            return "【エラー】Gemini が画像の説明テキストを返しませんでした。"
        return clean_text_for_display(text)
    except Exception as e:
        return f"【エラー】画像解析に失敗しました: {str(e)}"


def transcribe_audio_with_gemini(uploaded_file) -> str:
    model = get_gemini_model()
    audio_bytes = uploaded_file.getvalue()
    mime_type = uploaded_file.type or "audio/wav"

    prompt = (
        "この音声の内容を日本語でできるだけ正確に文字起こししてください。\n"
        "出力は通常の日本語文のみで書いてください。"
    )
    try:
        resp = model.generate_content(
            [prompt, {"mime_type": mime_type, "data": audio_bytes}],
            generation_config={
                "max_output_tokens": 2048,
            },
        )
        text = extract_text_from_response(resp)
        if not text:
            return "【エラー】Gemini が音声の文字起こしテキストを返しませんでした。"
        return clean_text_for_display(text)
    except Exception as e:
        return f"【エラー】音声解析に失敗しました: {str(e)}"


# ======================================================
# MAGI テキスト生成（プレーンテキスト）
# ======================================================
def build_sys_prompt(mode_label: str) -> str:
    """
    ラジオボタンで選択されたモードに応じて、
    どのエージェントブロックを出力させるかを制御する。
    """
    full = mode_label.startswith("フル")
    use_logic = full or ("Logic" in mode_label)
    use_human = full or ("Human" in mode_label)
    use_reality = full or ("Reality" in mode_label)
    use_media = full or ("Media" in mode_label)

    header = f"""
あなたは NERV の MAGI システム全体を模した統合AIです。
現在のモード: {mode_label}
ユーザーから与えられた情報をもとに、指定されたエージェント視点でコメントと判定を出し、
最後に統合MAGIとしての結論を書いてください。
出力は、以下のフォーマットだけを使って日本語で行います。
"""

    blocks = []

    if use_logic:
        blocks.append(
            """【Magi-Logic】
判定: 可決 または 保留 または 否決 のいずれか
要約: 2〜3文、合計120文字以内"""
        )

    if use_human:
        blocks.append(
            """【Magi-Human】
判定: 可決 または 保留 または 否決 のいずれか
要約: 2〜3文、合計120文字以内"""
        )

    if use_reality:
        blocks.append(
            """【Magi-Reality】
判定: 可決 または 保留 または 否決 のいずれか
要約: 2〜3文、合計120文字以内"""
        )

    if use_media:
        blocks.append(
            """【Magi-Media】
判定: 可決 または 保留 または 否決 のいずれか
要約: 2〜3文、合計120文字以内"""
        )

    # 統合サマリー・詳細は常に出力
    blocks.append(
        """【MAGI-統合サマリー】
全体としての結論を150文字以内でまとめる"""
    )
    blocks.append(
        """【MAGI-統合詳細】
統合的な視点から、2〜4段落・合計500文字以内で詳細なコメントと推奨アクションを書く"""
    )

    constraints = """
[制約]
- 箇条書き（・や番号付きリスト）は使わない。
- 上記の見出し・ラベル以外の文言や飾りは追加しない。
- 出力は必ずこのフォーマットに沿ったプレーンテキストのみとする。
"""

    return header + "\n\n" + "\n\n".join(blocks) + "\n\n" + constraints


def call_magi_plain(context: Dict[str, Any], mode_label: str) -> Optional[str]:
    """
    MAGI 4視点＋統合、もしくは選択された単独エージェント＋統合を
    決め打ちフォーマットのテキストとして返す。
    """
    model = get_gemini_model()

    trimmed_context = {
        "user_question": trim_text(context.get("user_question", "")),
        "text_input": trim_text(context.get("text_input", "")),
        "audio_transcript": trim_text(context.get("audio_transcript", "")),
        "image_description": trim_text(context.get("image_description", "")),
    }

    sys_prompt = build_sys_prompt(mode_label)

    ctx_text = (
        "【ユーザーからの情報】\n"
        + f"質問: {trimmed_context['user_question']}\n"
        + (
            f"テキスト入力: {trimmed_context['text_input']}\n"
            if trimmed_context["text_input"]
            else ""
        )
        + (
            f"音声文字起こし: {trimmed_context['audio_transcript']}\n"
            if trimmed_context["audio_transcript"]
            else ""
        )
        + (
            f"画像説明: {trimmed_context['image_description']}\n"
            if trimmed_context["image_description"]
            else ""
        )
    )

    try:
        resp = model.generate_content(
            [sys_prompt, ctx_text],
            generation_config={
                "max_output_tokens": 512,
                "temperature": 0.6,
            },
        )
    except ResourceExhausted:
        return "【エラー】Gemini のリソース上限に達しました。時間をおいてから再度お試しください。"
    except GoogleAPIError as e:
        return f"【エラー】Gemini API で問題が発生しました: {str(e)}"
    except Exception as e:
        return f"【エラー】MAGI分析中に想定外のエラーが発生しました: {str(e)}"

    text = extract_text_from_response(resp)
    return text


# ======================================================
# テキスト → 擬似エージェント構造へのパース
# ======================================================
def parse_magi_text(text: str) -> tuple[Dict[str, Any], Dict[str, str]]:
    agents: Dict[str, Any] = {}
    aggregated: Dict[str, str] = {"summary": "", "details": ""}

    pattern = r"^【(Magi-Logic|Magi-Human|Magi-Reality|Magi-Media|MAGI-統合サマリー|MAGI-統合詳細)】"
    parts = re.split(pattern, text, flags=re.MULTILINE)

    it = iter(parts[1:])

    for name, body in zip(it, it):
        body = body.strip()
        if name == "Magi-Logic":
            agents["logic"] = parse_agent_block("Magi-Logic（論理・構造担当）", body)
        elif name == "Magi-Human":
            agents["human"] = parse_agent_block("Magi-Human（感情・人間面担当）", body)
        elif name == "Magi-Reality":
            agents["reality"] = parse_agent_block("Magi-Reality（現実運用・リスク担当）", body)
        elif name == "Magi-Media":
            agents["media"] = parse_agent_block("Magi-Media（表現・印象担当）", body)
        elif name == "MAGI-統合サマリー":
            aggregated["summary"] = body.replace("\n", " ").strip()
        elif name == "MAGI-統合詳細":
            aggregated["details"] = body.strip()

    if not agents and not (aggregated["summary"] or aggregated["details"]):
        aggregated["details"] = text.strip()

    return agents, aggregated


def parse_agent_block(name_jp: str, body: str) -> Dict[str, Any]:
    lines = [l.strip() for l in body.splitlines() if l.strip()]
    decision_jp = "保留"
    summary = ""

    for line in lines:
        if line.startswith("判定"):
            if "可決" in line:
                decision_jp = "可決"
            elif "否決" in line:
                decision_jp = "否決"
            elif "保留" in line:
                decision_jp = "保留"
        elif line.startswith("要約"):
            summary = line.replace("要約", "").replace(":", "").replace("：", "").strip()
        else:
            if summary:
                summary += " " + line

    decision_code = {
        "可決": "Go",
        "否決": "No-Go",
        "保留": "Hold",
    }.get(decision_jp, "Hold")

    return {
        "name_jp": name_jp,
        "summary": summary,
        "decision_jp": decision_jp,
        "decision_code": decision_code,
    }


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
    magi_raw_text: str,
    image: Optional[Image.Image] = None,
) -> bytes:
    doc = docx.Document()
    doc.add_heading("MAGI風マルチAI分析レポート（テキスト簡易版）", level=1)

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

    # 第2章 各MAGIエージェントの要約
    doc.add_heading("第2章 各MAGIエージェントの要約と判定", level=2)
    if agents:
        for key in ["logic", "human", "reality", "media"]:
            if key not in agents:
                continue
            a = agents[key]
            name = a.get("name_jp", key)
            doc.add_heading(name, level=3)
            doc.add_paragraph(f"判定：{a.get('decision_jp', '')}")
            doc.add_paragraph(f"要約：{clean_text_for_display(a.get('summary', ''))}")
    else:
        doc.add_paragraph("今回の実行では、MAGIエージェントの詳細出力は取得できませんでした。")

    # 第3章 MAGI統合AIの結論
    doc.add_heading("第3章 MAGI統合AIの結論・アクションプラン", level=2)
    agg_summary = clean_text_for_display(aggregated.get("summary", ""))
    agg_details = clean_text_for_display(aggregated.get("details", ""))
    if agg_summary:
        doc.add_paragraph("【サマリー】")
        doc.add_paragraph(agg_summary)
    if agg_details:
        doc.add_paragraph("【詳細】")
        for line in agg_details.splitlines():
            doc.add_paragraph(line)

    # 付録：生テキスト
    doc.add_heading("付録：MAGI生テキスト", level=2)
    for line in magi_raw_text.splitlines():
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

st.markdown("#### 分析するMAGIエージェント")
analysis_mode = st.radio(
    "どのエージェントにコメントさせるか選択してください。",
    [
        "フル（4エージェント＋統合）",
        "Magi-Logicのみ",
        "Magi-Humanのみ",
        "Magi-Realityのみ",
        "Magi-Mediaのみ",
    ],
    index=0,
)

st.markdown("#### 媒体入力モード（任意）")
input_mode = st.radio(
    "画像・音声の入力方法を選択してください。",
    ["ファイル／写真ライブラリから選択", "カメラで撮影", "使用しない"],
    index=0,
)

col1, col2 = st.columns(2)
uploaded_file: Optional[Any] = None
image_for_report: Optional[Image.Image] = None

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
        st.audio(uploaded_file)
        with st.spinner("音声を文字起こし中（Gemini）..."):
            transcript = transcribe_audio_with_gemini(uploaded_file)
        context["audio_transcript"] = transcript

    else:
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
# MAGI 分析実行
# ======================================================
st.markdown(
    '<div class="magi-section-title">PROCESS · MAGI ANALYSIS</div><hr class="magi-divider">',
    unsafe_allow_html=True,
)

if st.button("🔎 MAGI による分析を実行", type="primary"):
    if not user_question and not text_input and not any(
        [context["audio_transcript"], context["image_description"]]
    ):
        st.warning("最低でも質問・テキスト・媒体のいずれかが必要です。")
        st.stop()

    with st.spinner("MAGI 分析を実行中..."):
        magi_text = call_magi_plain(context, analysis_mode)

    if magi_text is None:
        st.error(
            "【エラー】Gemini が有効なテキストを返しませんでした。\n"
            "・内容が極端に長い\n・安全フィルタにかかる表現が含まれている\nなどの可能性があります。\n\n"
            "一度、質問やテキストを短く・穏やかな表現にして再実行してみてください。"
        )
        st.stop()

    if isinstance(magi_text, str) and magi_text.startswith("【エラー】"):
        st.error(magi_text)
        st.stop()

    agents, aggregated = parse_magi_text(magi_text)

    st.success("MAGI の分析が完了しました。")

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
                    {clean_text_for_display(a.get("summary", "")).replace("\\n", "<br>")}
                  </div>
                </div>
                ''',
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
                    {clean_text_for_display(a.get("summary", "")).replace("\\n", "<br>")}
                  </div>
                </div>
                ''',
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
                    {clean_text_for_display(a.get("summary", "")).replace("\\n", "<br>")}
                  </div>
                </div>
                ''',
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
                    {clean_text_for_display(a.get("summary", "")).replace("\\n", "<br>")}
                  </div>
                </div>
                ''',
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
        f'<div class="magi-aggregator">{agg_html.replace("\\n", "<br>")}</div>',
        unsafe_allow_html=True,
    )

    # ==================================================
    # レポート出力
    # ==================================================
    report_bytes = build_word_report(
        context=context,
        agents=agents,
        aggregated=aggregated,
        magi_raw_text=magi_text,
        image=image_for_report,
    )

    st.markdown(
        '<div class="magi-section-title">REPORT · EXPORT</div><hr class="magi-divider">',
        unsafe_allow_html=True,
    )

    st.download_button(
        "MAGIレポート（Word）をダウンロード",
        data=report_bytes,
        file_name="MAGI分析レポート_テキスト簡易版.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

else:
    st.info(
        "下のボタンを押すと、選択したMAGIエージェントがコメントと判定を出し、統合MAGIが結論をまとめます。\n"
        "まずは「Magi-Logicのみ」など単独エージェントで試すと動作確認しやすいです。"
    )
