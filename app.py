import os
import textwrap

import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError, ResourceExhausted


# ==============================
# 1. APIキーの設定
# ==============================
# どちらかでOK：
# - 環境変数 GEMINI_API_KEY にセットしておく
# - 下の api_key に直書きする

api_key = os.getenv("GEMINI_API_KEY")  # or "ここに直接キーを書いてテストしてもOK"

if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY が設定されていません。\n"
        "環境変数 GEMINI_API_KEY を設定するか、コード中の api_key に直接キーを書いてください。"
    )

genai.configure(api_key=api_key)


# ==============================
# 2. テスト用の関数
# ==============================
def print_header(title: str):
    print("=" * 80)
    print(title)
    print("=" * 80)


def test_gemini_simple():
    print_header("1) モデルの初期化")
    model_name = "gemini-2.5-flash"
    print(f"使用モデル: {model_name}")

    model = genai.GenerativeModel(model_name)

    # プロンプトはできるだけ短く・シンプルに
    prompt = "天気は？"

    print_header("2) 送信するプロンプト")
    print(prompt)
    print()

    try:
        print_header("3) generate_content 呼び出し中...")
        resp = model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": 128,  # 意図的にかなり少なめ
                "temperature": 0.6,
            },
        )
    except ResourceExhausted as e:
        print_header("!! ResourceExhausted 例外発生（アカウント or リソース上限の可能性）")
        print(repr(e))
        return
    except GoogleAPIError as e:
        print_header("!! GoogleAPIError 発生（API レベルのエラー）")
        print(repr(e))
        return
    except Exception as e:
        print_header("!! 想定外の例外発生")
        print(type(e), e)
        return

    # ==========================
    # 4. レスポンス全体の概要
    # ==========================
    print_header("4) resp の型と dir(resp)")
    print("type(resp):", type(resp))
    print("dir(resp)（一部）:", [a for a in dir(resp) if not a.startswith("_")][:40])

    # ==========================
    # 5. resp.text を直接見てみる
    # ==========================
    print_header("5) resp.text を直接取得してみる")
    try:
        t = (getattr(resp, "text", "") or "").strip()
        print("resp.text:", repr(t))
    except Exception as e:
        print("resp.text 取得時に例外:", type(e), e)

    # ==========================
    # 6. candidates / finish_reason / parts を詳細に
    # ==========================
    print_header("6) candidates / finish_reason / parts の詳細")

    candidates = getattr(resp, "candidates", None)
    print("candidates 存在有無:", candidates is not None)
    if not candidates:
        print("candidates が None または空です。")
    else:
        print(f"candidates の数: {len(candidates)}")
        for idx, cand in enumerate(candidates):
            print("-" * 60)
            print(f"[candidate {idx}] type:", type(cand))
            finish_reason = getattr(cand, "finish_reason", None)
            print("  finish_reason:", finish_reason)

            content = getattr(cand, "content", None)
            print("  content type:", type(content))
            print("  dir(content)（一部）:",
                  [a for a in dir(content) if not a.startswith("_")][:30])

            parts = getattr(content, "parts", None) if content is not None else None
            print("  parts 存在有無:", parts is not None)
            if not parts:
                print("  parts が None または空です。")
            else:
                print(f"  parts の数: {len(parts)}")
                for p_idx, part in enumerate(parts):
                    print(f"    [part {p_idx}] type:", type(part))
                    part_text = getattr(part, "text", None)
                    print("      part.text:", repr(part_text))

    # ==========================
    # 7. prompt_feedback / usage_metadata
    # ==========================
    print_header("7) prompt_feedback / usage_metadata")

    pf = getattr(resp, "prompt_feedback", None)
    print("prompt_feedback:", pf)

    usage = getattr(resp, "usage_metadata", None)
    print("usage_metadata:", usage)

    # ==========================
    # 8. resp 全体の repr
    # ==========================
    print_header("8) resp 全体の repr（2000文字まで）")
    try:
        s = repr(resp)
    except Exception as e:
        s = f"<repr(resp) で例外発生: {e}>"
    print(textwrap.shorten(s, width=2000, placeholder="..."))


if __name__ == "__main__":
    test_gemini_simple()
