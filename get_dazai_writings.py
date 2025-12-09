import re
import requests
import zipfile
import io


def clean_aozora_text(text: str) -> str:
    """
    青空文庫のテキストからルビ、注記、ヘッダー、フッターを削除する。

    Args:
        text (str): 青空文庫の生テキストデータ

    Returns:
        str: クリーニング済みのテキスト
    """
    # 1. ルビ、注記、入力者情報などを削除
    # ルビの削除: 《...》
    text = re.sub(r"《[^》]+》", "", text)
    # 注記の削除: ［＃...］
    text = re.sub(r"［＃[^］]+］", "", text)
    # ルビ付与のための区切り文字「｜」の削除
    text = re.sub(r"｜", "", text)

    # 2. ヘッダーとフッターの削除
    lines: list[str] = text.split("\n")
    start_idx: int = 0
    end_idx: int = len(lines)

    # ヘッダー（-------で区切られた最初のブロック）をスキップ
    separator_count: int = 0
    for i, line in enumerate(lines):
        if "-------------------------------------------------------" in line:
            separator_count += 1
            if separator_count == 2:  # 2回目の区切り線の後から本文が始まることが多い
                start_idx = i + 1
                break

    # フッター（底本情報など）を削除
    for i in range(start_idx, len(lines)):
        # 「底本：」や「底本の親本：」などのメタデータセクションの開始を検知
        if line.startswith("底本：") or line.startswith("底本の親本："):
            end_idx = i
            break

    if separator_count < 2:
        start_idx = 0

    cleaned_lines: list[str] = lines[start_idx:end_idx]

    # 空行を除去しつつ結合
    cleaned_text: str = "\n".join(
        [line.rstrip() for line in cleaned_lines if line.strip()]
    )

    return cleaned_text


def download_and_process_aozora(url: str) -> str:
    """
    URLからZIPをダウンロードし、テキストをクリーニングして返す。

    Args:
        url (str): 青空文庫のZIPファイルURL

    Returns:
        str: 処理済みのテキスト（失敗時は空文字）
    """
    try:
        response: requests.Response = requests.get(url)
        response.raise_for_status()

        # ZIPファイルをメモリ上で開く
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            # ZIP内のテキストファイル名を取得（通常は1つだけ）
            text_files: list[str] = [
                name for name in z.namelist() if name.endswith(".txt")
            ]
            if not text_files:
                return ""

            text_filename: str = text_files[0]

            # テキストを読み込む（青空文庫はShift_JISが多い）
            with z.open(text_filename) as f:
                raw_text: str = f.read().decode("shift_jis", errors="ignore")

        return clean_aozora_text(raw_text)

    except Exception as e:
        print(f"Error processing {url}: {e}")
        return ""


# 太宰治の代表的な作品のZIPファイルURLリスト
dazai_urls: list[str] = [
    "https://www.aozora.gr.jp/cards/000035/files/301_ruby_5915.zip",  # 人間失格
    "https://www.aozora.gr.jp/cards/000035/files/1567_ruby_4948.zip",  # 走れメロス
    "https://www.aozora.gr.jp/cards/000035/files/1565_ruby_8220.zip",  # 斜陽
    "https://www.aozora.gr.jp/cards/000035/files/2253_ruby_1031.zip",  # ヴィヨンの妻
    "https://www.aozora.gr.jp/cards/000035/files/275_ruby_1532.zip",  # 女生徒
    "https://www.aozora.gr.jp/cards/000035/files/277_ruby_33097.zip",  # 駈込み訴え
    "https://www.aozora.gr.jp/cards/000035/files/270_ruby_1164.zip",  # 富嶽百景
    "https://www.aozora.gr.jp/cards/000035/files/246_ruby_1636.zip",  # 畜犬談
    "https://www.aozora.gr.jp/cards/000035/files/2282_ruby_1996.zip",  # 津軽
]

OUTPUT_FILE: str = "dazai_corpus.txt"


def main() -> None:
    print(f"Starting download and processing of {len(dazai_urls)} works...")

    full_corpus: list[str] = []

    for url in dazai_urls:
        filename: str = url.split("/")[-1]
        print(f"Processing: {filename} ...", end="")

        text: str = download_and_process_aozora(url)

        if text:
            full_corpus.append(text)
            print(" Done.")
            # 学習データのサンプルとして冒頭を表示 (改行をスペースに置換して表示)
            sample_text: str = text[:50].replace("\n", " ")
            print(f"--- Sample: {sample_text}... ---")
        else:
            print(" Failed.")

    # ファイルに保存
    if full_corpus:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n\n".join(full_corpus))

        total_chars: int = sum(len(t) for t in full_corpus)
        print(f"\nCompleted! Saved to {OUTPUT_FILE}")
        print(f"Total characters: {total_chars}")
    else:
        print("\nNo text data extracted.")


if __name__ == "__main__":
    main()
