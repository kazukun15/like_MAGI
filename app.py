import os
import io
import json
from typing import Dict, Any, Optional

import streamlit as st
from PIL import Image

import google.generativeai as genai
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
# MAGI風 カスタムCSS
# ------------------------------------------------------
st.markdown(
    """
    <style>
    /* 全体の背景とフォント */
    .stApp {
        background: radial-gradient(circle at top, #222b40 0, #050710 45%, #02030a 100%);
        color: #e0e4ff;
        font-family: "Roboto Mono", "SF Mono", "Consolas", "Noto Sans JP", monospace;
    }

    /* スクロールバー細め */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-thumb {
        background: #3e4a6e;
        border-radius: 3px;
    }

    /* MAGIヘッダー */
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
    .magi-header-left {
        display: flex;
        flex-direction: column;
    }
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

    /* インフォカード（上部説明など） */
    .magi-info-card {
        border-radius: 10px;
        border: 1px solid rgba(130,140,200,0.6);
        background: linear-gradient(135deg, rgba(16,22,48,0.95), rgba(6,10,26,0.95));
        padding: 10px 14px;
        font-size: 13px;
        color: #cfd6ff;
        margin-bottom: 8px;
    }
    .magi-info-card b {
        color: #ffffff;
    }

    /* MAGI エージェントパネル共通 */
    .magi-panel {
        border-radius: 10px;
        padding: 10px 14px;
        margin-top: 6px;
        margin-bottom: 6px;
        font-size: 13px;
        line-height: 1.5;
        border: 1px solid rgba(140,160,255,0.4);
        background: radial-gradient(circle at top, rgba(18,26,60,0.98), rgba(5,8,22,0.98));
        box-shadow: 0 0 15px rgba(90,110,200,0.35);
    }
    .magi-panel h3, .magi-panel h4 {
        margin-top: 8px;
        margin-bottom: 4px;
        font-size: 14px;
        color: #ffffff;
    }

    /* 各エージェント色分け */
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

    /* 統合コンソール */
    .magi-aggregator {
        border-radius: 12px;
        padding: 16px 18px;
        margin-top: 10px;
        border: 1px solid #6f8dff;
        background: radial-gradient(circle at top, rgba(31,42,90,0.98), rgba(6,8,20,0.98));
        box-shadow: 0 0 22px rgba(110,140,255,0.5);
        font-size: 14px;
        color: #ecf0ff;
    }
    .magi-aggregator h3, .magi-aggregator h4 {
        margin-top: 10px;
        margin-bottom: 6px;
        color: #ffffff;
    }

    /* セクションタイトルの装飾 */
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

# 1行目は説明カード
st.markdown(
    """
    <div class="magi-info-card">
    <b>概要：</b> テキスト・画像・音声など、媒体を問わず入力された情報を、
    <b>Magi-Logic / Magi-Human / Magi-Reality / Magi-Media</b> の 4つのエージェントがそれぞれの視点から分析し、<br>
    最後に統合 AI が <b>MAGI システム風レポート</b> として結論・アクションプランを提示します。
    </div>
    """,
    unsafe_allow_html=True,
)


# ======================================================
# Gemini API 初期化（安全版）
# ======================================================
api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY"))

if not api_key:
    st.error(
        "❌ Gemini の API キーが設定されていません。\n\n"
        "【Streamlit Cloud の場合】\n"
        "  Settings → Secrets で以下のように設定してください：\n"
        '  GEMINI_API_KEY = "あなたのGemini APIキー"\n\n'
        "【ローカル実行の場合】\n"
        "  プロジェクト直下に .streamlit/secrets.toml を作り、同様に設定するか、\n"
        "  環境変数 GEMINI_API_KEY を設定してください。"
    )
    st.stop()

genai.configure(api_key=api_key)


@st.cache_resource(show_spinner=False)
def get_gemini_model():
    return genai.GenerativeModel("gemini-2.5-flash")


# ======================================================
# 媒体のテキスト化（画像・音声）
# ======================================================
def describe_image_with_gemini(img: Image.Image) -> str:
    """画像の内容を Gemini に説明させる"""
    model = get_gemini_model()
    prompt = (
        "この画像に何が写っているか、日本語で簡潔に説明してください。\n"
        "続けて、その画像が与える心理的な印象を一行で述べてください。"
    )
    resp = model.generate_content([prompt, img])
    return resp.text.strip()


def transcribe_audio_with_gemini(uploaded_file) -> str:
    """音声ファイルを Gemini に渡して文字起こし"""
    model = get_gemini_model()
    audio_bytes = uploaded_file.getvalue()
    mime_type = uploaded_file.type or "audio/wav"

    prompt = "この音声の内容を日本語でできるだけ正確に文字起こししてください。"

    resp = model.generate_content(
        [
            prompt,
            {"mime_type": mime_type, "data": audio_bytes},
        ]
    )
    return resp.text.strip()


# ======================================================
# MAGI エージェント呼び出し
# ======================================================
def call_gemini_agent_structured(role_prompt: str, context: Dict[str, Any]) -> str:
    """
    各 MAGI エージェントの役割を与え、構造化されたレポートを生成させる。
    """
    model = get_gemini_model()

    sys_prompt = f"""
あなたは MAGI システムの一員です。

[あなたの役割]
{role_prompt}

[出力フォーマット（必ずこの見出しと順番を守ること）]
### 【前提認識】
- 箇条書きで状況や前提を整理してください。

### 【分析】
- あなたの視点から詳しく分析してください（箇条書き＋短い段落）。

### 【リスク・懸念】
- 想定されるリスクや不確実性を列挙してください。

### 【このエージェントの結論と提案】
- 結論：
- 提案：
"""

    user_context = json.dumps(context, ensure_ascii=False, indent=2)

    resp = model.generate_content(
        [
            sys_prompt,
            f"以下がユーザーからの情報です。これに基づいて高精度に分析してください。\n\n{user_context}",
        ]
    )
    return resp.text.strip()


def call_magi_aggregator(agent_outputs: Dict[str, str], context: Dict[str, Any]) -> str:
    """
    各エージェントの出力を読み取り、MAGIシステムとしての結論をまとめる。
    """
    model = get_gemini_model()

    sys_prompt = """
あなたは NERV の MAGI システムにおける統合 AI です。

[役割]
- 各エージェントの分析結果を読み取り、矛盾点・共通点・補完関係を整理する
- ユーザーにとって実行可能で現実的な「結論」と「アクションプラン」を提示する
- Go（実行）/ Hold（条件付き検討）/ No-Go（見送り）の判断を行う

[出力フォーマット]
### 【全体サマリー】
- 3〜7行程度で、今回の状況と結論を要約してください。

### 【合議結果の要点】
- Magi-Logic：
- Magi-Human：
- Magi-Reality：
- Magi-Media：

### 【推奨アクションプラン】
- ステップ形式で 3〜7項目程度に整理してください。

### 【MAGIとしての最終判断】
- 判断：Go / Hold / No-Go のいずれか
- 理由：
"""

    context_text = json.dumps(context, ensure_ascii=False, indent=2)
    agents_text = json.dumps(agent_outputs, ensure_ascii=False, indent=2)

    resp = model.generate_content(
        [
            sys_prompt,
            f"[ユーザーの元情報]\n{context_text}\n\n[各エージェントの結果]\n{agents_text}",
        ]
    )
    return resp.text.strip()


# ======================================================
# Word レポート生成
# ======================================================
def build_word_report(
    context: Dict[str, Any],
    agent_outputs: Dict[str, str],
    aggregated: str,
    image: Optional[Image.Image] = None,
) -> bytes:
    """
    MAGI風の章立てで Word レポートを作成する。
    """
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
    for name, text in agent_outputs.items():
        doc.add_heading(name, level=3)
        for line in text.splitlines():
            doc.add_paragraph(line)

    # 第3章 MAGI統合AIの結論
    doc.add_heading("第3章 MAGI統合AIの結論・アクションプラン", level=2)
    for line in aggregated.splitlines():
        doc.add_paragraph(line)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.getvalue()


# ======================================================
# UI：入力エリア
# ======================================================
st.markdown('<div class="magi-section-title">INPUT · QUERY & MEDIA</div><hr class="magi-divider">', unsafe_allow_html=True)

user_question = st.text_area(
    "MAGI に投げたい「問い」",
    placeholder="例：この企画の方向性と改善点をMAGIに評価してほしい。\n例：この写真や音声から受ける印象と、次に取るべき行動を知りたい、など。",
    height=120,
)

st.markdown("#### 媒体アップロード（任意）")
col1, col2 = st.columns(2)

uploaded_file = None
image_for_report: Optional[Image.Image] = None
media_type: Optional[str] = None

with col1:
    file = st.file_uploader(
        "画像 / 音声 / テキストファイル",
        type=["jpg", "jpeg", "png", "wav", "mp3", "m4a", "txt"],
    )
    if file:
        uploaded_file = file

with col2:
    cam = st.camera_input("カメラで撮影")
    if cam:
        uploaded_file = cam

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
    if uploaded_file.type.startswith("image/"):
        media_type = "image"
        image = Image.open(uploaded_file).convert("RGB")
        image_for_report = image
        st.image(image, caption="入力画像", use_column_width=True)

        with st.spinner("画像内容を解析中（Gemini）..."):
            img_desc = describe_image_with_gemini(image)
        context["image_description"] = img_desc

    elif uploaded_file.type.startswith("audio/"):
        media_type = "audio"
        st.audio(uploaded_file)

        with st.spinner("音声を文字起こし中（Gemini）..."):
            transcript = transcribe_audio_with_gemini(uploaded_file)
        context["audio_transcript"] = transcript

    else:
        media_type = "other"
        if uploaded_file.type == "text/plain":
            text_bytes = uploaded_file.read()
            context["text_input"] += "\n\n[ファイル内容]\n" + text_bytes.decode(
                "utf-8", errors="ignore"
            )

# ======================================================
# MAGI エージェントによる分析
# ======================================================
st.markdown('<div class="magi-section-title">PROCESS · MAGI AGENT ANALYSIS</div><hr class="magi-divider">', unsafe_allow_html=True)

if st.button("🔎 MAGI による分析を実行", type="primary"):
    if not user_question and not text_input and not any(
        [context["audio_transcript"], context["image_description"]]
    ):
        st.warning("最低でも質問・テキスト・媒体のいずれかが必要です。")
        st.stop()

    agent_outputs: Dict[str, str] = {}

    # --- Magi-Logic ---
    with st.spinner("Magi-Logic（論理・構造担当）が分析中..."):
        out_logic = call_gemini_agent_structured(
            role_prompt="""
論理・構造・因果関係の分析に特化した AI。
- 問題の構造化
- 論理的な矛盾の指摘
- 実現までのステップ設計
に重点を置いて、高精度に分析してください。
""",
            context=context,
        )
    agent_outputs["Magi-Logic（論理・構造担当）"] = out_logic

    # --- Magi-Human ---
    with st.spinner("Magi-Human（感情・心理担当）が分析中..."):
        out_human = call_gemini_agent_structured(
            role_prompt="""
人間の感情・心理・コミュニケーションに特化した AI。
- 関係者がどんな気持ちになるか
- 伝え方・言葉選びの配慮
- メンタル面のリスク・ケア
に重点を置いて分析してください。
""",
            context=context,
        )
    agent_outputs["Magi-Human（感情・心理担当）"] = out_human

    # --- Magi-Reality ---
    with st.spinner("Magi-Reality（現実・運用担当）が分析中..."):
        out_reality = call_gemini_agent_structured(
            role_prompt="""
現実的な運用・コスト・リスク管理に特化した AI。
- 実現可能性
- 必要なリソースと制約
- 現場で起こりそうな問題
に重点を置いて分析してください。
""",
            context=context,
        )
    agent_outputs["Magi-Reality（現実・運用担当）"] = out_reality

    # --- Magi-Media ---
    with st.spinner("Magi-Media（媒体解釈担当）が分析中..."):
        out_media = call_gemini_agent_structured(
            role_prompt="""
画像・音声・テキストなど媒体の特徴を踏まえた解釈に特化した AI。
- 入力された媒体が与える印象
- その媒体をどう活かすべきか
- 改善案（構図・表現・長さなど）
に重点を置いて分析してください。
媒体が無い場合は、文章表現の観点から分析してください。
""",
            context=context,
        )
    agent_outputs["Magi-Media（媒体解釈担当）"] = out_media

    st.success("各エージェントの分析が完了しました。")

    # --- 各エージェントの結果を MAGIパネル風に表示 ---
    colL, colR = st.columns(2)

    with colL:
        st.markdown("##### Magi-Logic")
        st.markdown(
            f'<div class="magi-panel magi-panel-logic">{agent_outputs["Magi-Logic（論理・構造担当）"].replace("\n", "<br>")}</div>',
            unsafe_allow_html=True,
        )

        st.markdown("##### Magi-Reality")
        st.markdown(
            f'<div class="magi-panel magi-panel-reality">{agent_outputs["Magi-Reality（現実・運用担当）"].replace("\n", "<br>")}</div>',
            unsafe_allow_html=True,
        )

    with colR:
        st.markdown("##### Magi-Human")
        st.markdown(
            f'<div class="magi-panel magi-panel-human">{agent_outputs["Magi-Human（感情・心理担当）"].replace("\n", "<br>")}</div>',
            unsafe_allow_html=True,
        )

        st.markdown("##### Magi-Media")
        st.markdown(
            f'<div class="magi-panel magi-panel-media">{agent_outputs["Magi-Media（媒体解釈担当）"].replace("\n", "<br>")}</div>',
            unsafe_allow_html=True,
        )

    # ==================================================
    # MAGI 統合AI
    # ==================================================
    st.markdown('<div class="magi-section-title">OUTPUT · MAGI AGGREGATED DECISION</div><hr class="magi-divider">', unsafe_allow_html=True)

    with st.spinner("MAGI統合AIが結論をまとめています..."):
        aggregated = call_magi_aggregator(agent_outputs, context)

    st.markdown(
        f'<div class="magi-aggregator">{aggregated.replace("\n", "<br>")}</div>',
        unsafe_allow_html=True,
    )

    # ==================================================
    # レポート出力
    # ==================================================
    report_bytes = build_word_report(
        context=context,
        agent_outputs=agent_outputs,
        aggregated=aggregated,
        image=image_for_report,
    )

    st.markdown('<div class="magi-section-title">REPORT · EXPORT</div><hr class="magi-divider">', unsafe_allow_html=True)

    st.download_button(
        "📝 MAGIレポート（Word）をダウンロード",
        data=report_bytes,
        file_name="MAGI分析レポート_Gemini版.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

else:
    st.info("下のボタンを押すと、MAGI の各エージェントが順次分析を開始します。")
