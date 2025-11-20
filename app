import io
import json
import tempfile
from typing import Dict, Any, Optional

import streamlit as st
from PIL import Image

import google.generativeai as genai
import docx
import whisper

from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline


# ==============================
# ページ設定
# ==============================
st.set_page_config(
    page_title="MAGI風マルチAI分析システム（精度重視版）",
    page_icon="🧬",
    layout="wide",
)

st.title("🧬 MAGI風 マルチAI分析システム（精度重視版）")
st.caption("Gemini 2.5 Flash + HuggingFace LLM + Whisper による多視点・高精度分析")


# ==============================
# 外部サービス設定
# ==============================
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])


@st.cache_resource(show_spinner=False)
def get_gemini_model():
    return genai.GenerativeModel("gemini-2.5-flash")


@st.cache_resource(show_spinner=True)
def load_whisper_model():
    # 日本語も比較的安定している base モデル
    return whisper.load_model("base")


@st.cache_resource(show_spinner=True)
def load_hf_pipeline(model_name: str):
    """
    Hugging Face LLM を読み込んで text-generation パイプラインを返す。
    精度重視のため、温度は低め・長めの出力を許容。
    """
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map="auto",
        torch_dtype="auto",
    )
    gen = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=800,
        do_sample=True,
        temperature=0.3,  # 精度重視で低め
        top_p=0.9,
    )
    return gen


# ==============================
# ユーティリティ：媒体テキスト化など
# ==============================
def transcribe_audio(uploaded_file) -> str:
    """音声ファイルを Whisper で文字起こし"""
    model = load_whisper_model()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name
    result = model.transcribe(tmp_path, language="ja")
    return result.get("text", "")


def describe_image_with_gemini(img: Image.Image) -> str:
    """画像の内容を Gemini に要約させる（テキスト化＋印象）"""
    model = get_gemini_model()
    prompt = """
この画像に何が写っているか、日本語で簡潔に説明してください。
続けて、その画像が与える心理的な印象を一行で述べてください。
"""
    resp = model.generate_content([prompt, img])
    return resp.text.strip()


def call_gemini_structured(role_prompt: str, context: Dict[str, Any]) -> str:
    """
    各エージェント用 Gemini 呼び出し（構造化出力）。
    """
    model = get_gemini_model()

    sys_prompt = f"""
あなたは以下の役割を持つ MAGI システムの一員です。

[あなたの役割]
{role_prompt}

[出力フォーマット（必ずこの順番・見出しで出力すること）]
### 【前提認識】
- （状況や前提を箇条書きで整理）

### 【分析】
- （あなたの観点からの詳細な分析）

### 【リスク・懸念】
- （想定されるリスクや不確実性）

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


def call_hf_llm_structured(model_name: str, role_prompt: str, context: Dict[str, Any]) -> str:
    """
    Hugging Face LLM を使った構造化出力。
    """
    gen = load_hf_pipeline(model_name)
    user_context = json.dumps(context, ensure_ascii=False, indent=2)

    sys_and_format = f"""
あなたは以下の役割を持つ MAGI システムの一員です。

[あなたの役割]
{role_prompt}

[出力フォーマット（必ずこの見出し・順番・構造を守ること）]
### 【前提認識】
- 箇条書きで

### 【分析】
- 箇条書きや短い段落で詳しく

### 【リスク・懸念】
- 箇条書きで

### 【このエージェントの結論と提案】
- 結論：
- 提案：
"""

    prompt = (
        sys_and_format
        + "\n\n以下がユーザーからの情報です。これに基づいて日本語で慎重に分析してください。\n"
        + user_context
        + "\n\n上記のフォーマットに従って出力してください。"
    )

    out = gen(prompt)[0]["generated_text"]
    # ざっくりプロンプト部分を削除
    trimmed = out[len(prompt):].strip()
    return trimmed if trimmed else out.strip()


def call_gemini_aggregator(agent_outputs: Dict[str, str], context: Dict[str, Any]) -> str:
    """
    各エージェントの出力を統合する最終 MAGI。
    """
    model = get_gemini_model()

    sys_prompt = """
あなたは NERV の MAGI システムにおける統合 AI です。

[役割]
- 各エージェントの分析結果を読み取り、矛盾点・共通点・補完関係を整理する
- ユーザーにとって実行可能で現実的な「結論」と「具体的なアクションプラン」を提示する
- 必要に応じて、Go（実行すべき） / Hold（条件付きで検討） / No-Go（見送るべき）の判断も行う

[出力フォーマット]
### 【全体サマリー】
- 3〜7行程度で要約

### 【合議結果の要点】
- Magi-Logic：
- Magi-Human：
- Magi-Reality：
- Magi-Media：

### 【推奨アクションプラン】
- （ステップ形式で列挙）

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


def build_word_report(
    context: Dict[str, Any],
    agent_outputs: Dict[str, str],
    aggregated: str,
    image: Optional[Image.Image] = None,
) -> bytes:
    """MAGI風章立ての Word レポート作成"""
    doc = docx.Document()
    doc.add_heading("MAGI風マルチAI分析レポート（精度重視）", level=1)

    # 1. 入力情報
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

    # 2. 各MAGIエージェントの分析
    doc.add_heading("第2章 各MAGIエージェントの分析", level=2)
    for name, text in agent_outputs.items():
        doc.add_heading(name, level=3)
        for line in text.splitlines():
            doc.add_paragraph(line)

    # 3. MAGI統合AIの結論
    doc.add_heading("第3章 MAGI統合AIの結論・アクションプラン", level=2)
    for line in aggregated.splitlines():
        doc.add_paragraph(line)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.getvalue()


# ==============================
# UI：入力エリア
# ==============================
st.markdown("### 1. 質問・テーマの入力")

user_question = st.text_area(
    "あなたが相談したい内容・聞きたいこと（必須）",
    placeholder="例：この企画書の方向性と改善点を多角的に教えてほしい\n例：この仕事の進め方とリスクをMAGIに評価してほしい など",
    height=120,
)

st.markdown("### 2. 分析したい媒体（任意）")
col1, col2 = st.columns(2)

uploaded_file = None
uploaded_image = None
media_type = None

with col1:
    file = st.file_uploader(
        "画像 / 音声 / テキストファイル など",
        type=["jpg", "jpeg", "png", "wav", "mp3", "m4a", "txt"],
    )
    if file:
        uploaded_file = file

with col2:
    cam = st.camera_input("カメラで撮影（任意）")
    if cam:
        uploaded_file = cam

text_input = st.text_area(
    "補足テキスト（任意）",
    height=100,
    placeholder="追記したい説明やメモなどがあれば入力してください。",
)

if not user_question and not uploaded_file and not text_input:
    st.info("質問か、媒体（画像・音声など）、または補足テキストのいずれかを入力してください。")
    st.stop()

# ==============================
# 媒体のテキスト化
# ==============================
context: Dict[str, Any] = {
    "user_question": user_question,
    "text_input": text_input,
    "audio_transcript": "",
    "image_description": "",
}

image_for_report: Optional[Image.Image] = None

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
        with st.spinner("音声を文字起こし中（Whisper）..."):
            transcript = transcribe_audio(uploaded_file)
        context["audio_transcript"] = transcript

    else:
        media_type = "other"
        if uploaded_file.type == "text/plain":
            text_bytes = uploaded_file.read()
            context["text_input"] += "\n\n[ファイル内容]\n" + text_bytes.decode(
                "utf-8", errors="ignore"
            )

# ==============================
# MAGI エージェント呼び出し
# ==============================
st.markdown("### 3. MAGI エージェントによる分析")

if st.button("🔎 MAGI による分析を実行", type="primary"):
    if not user_question and not text_input and not any(
        [context["audio_transcript"], context["image_description"]]
    ):
        st.warning("最低でも質問・テキスト・媒体のいずれかが必要です。")
        st.stop()

    agent_outputs: Dict[str, str] = {}

    # --- Magi-Logic（Gemini） ---
    with st.spinner("Magi-Logic（論理・構造担当 / Gemini）が分析中..."):
        out_logic = call_gemini_structured(
            role_prompt="""
論理・構造・因果関係の分析に特化した AI。
- 問題の構造化
- 論理的な矛盾の指摘
- 実現までのステップ設計
に重点を置いて、高精度に分析してください。
""",
            context=context,
        )
    agent_outputs["Magi-Logic（論理・構造担当 / Gemini）"] = out_logic

    # --- Magi-Human（HF 精度重視 LLM） ---
    with st.spinner("Magi-Human（感情・心理担当 / HF LLM）が分析中..."):
        hf_model_human = st.secrets.get(
            "HF_MODEL_HUMAN",
            "Qwen/Qwen2.5-7B-Instruct",
        )
        out_human = call_hf_llm_structured(
            model_name=hf_model_human,
            role_prompt="""
人間の感情・心理・コミュニケーションに特化した AI。
- 関係者がどんな気持ちになるか
- 伝え方・言葉選びの配慮
- メンタル面のリスク・ケア
に重点を置いて、高精度に分析してください。
""",
            context=context,
        )
    agent_outputs["Magi-Human（感情・心理担当 / HF LLM）"] = out_human

    # --- Magi-Reality（別HF LLM） ---
    with st.spinner("Magi-Reality（現実・運用担当 / HF LLM）が分析中..."):
        hf_model_reality = st.secrets.get(
            "HF_MODEL_REALITY",
            "google/gemma-2-9b-it",
        )
        out_reality = call_hf_llm_structured(
            model_name=hf_model_reality,
            role_prompt="""
現実的な運用・コスト・リスク管理に特化した AI。
- 実現可能性
- 必要なリソースと制約
- 現場で起こりそうな問題
に重点を置いて、高精度に分析してください。
""",
            context=context,
        )
    agent_outputs["Magi-Reality（現実・運用担当 / HF LLM）"] = out_reality

    # --- Magi-Media（Gemini Vision/通常） ---
    with st.spinner("Magi-Media（媒体解釈担当 / Gemini）が分析中..."):
        out_media = call_gemini_structured(
            role_prompt="""
画像・音声・テキストなど媒体の特徴を踏まえた解釈に特化した AI。
- 入力された媒体が与える印象
- その媒体をどう活かすべきか
- 改善案（構図・表現・長さなど）
に重点を置いて分析してください。
画像や音声が無い場合は、文章表現の観点から分析してください。
""",
            context=context,
        )
    agent_outputs["Magi-Media（媒体解釈担当 / Gemini）"] = out_media

    st.success("各エージェントの分析が完了しました。")

    # 各エージェントの結果表示
    for name, text in agent_outputs.items():
        with st.expander(f"🧬 {name}", expanded=False):
            st.markdown(text)

    # 統合フェーズ
    st.markdown("### 4. MAGI統合AIの結論（合議結果レポート）")
    with st.spinner("MAGI統合AIが結論をまとめています..."):
        aggregated = call_gemini_aggregator(agent_outputs, context)
    st.markdown(aggregated)

    # レポート出力
    report_bytes = build_word_report(
        context=context,
        agent_outputs=agent_outputs,
        aggregated=aggregated,
        image=image_for_report,
    )

    st.markdown("### 5. レポート出力")
    st.download_button(
        "📝 MAGIレポート（Word）をダウンロード",
        data=report_bytes,
        file_name="MAGI分析レポート_精度重視版.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

else:
    st.info("「🔎 MAGI による分析を実行」を押すと、各AIが順番に分析を開始します。")
