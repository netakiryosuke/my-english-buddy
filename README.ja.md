# My English Buddy

My English Buddy は、OpenAI API を利用した英会話練習用のデスクトップアプリケーションです。

マイクから音声を継続的に聞き取り、OpenAI Speech-to-Text で文字起こしし、OpenAI Chat Completions で会話応答を生成し、OpenAI Text-to-Speech で音声化して話しかけます。シンプルな GUI ウィンドウで会話ログを表示します。

## クイックスタート

### Windows（PowerShell）

```powershell
Copy-Item .env.example .env
# .env を編集して OPENAI_API_KEY と OPENAI_MODEL を設定

uv sync
Copy-Item prompt.txt.example prompt.txt  # 任意（システムプロンプトをカスタマイズする場合）

uv run python -m app.main
```

### macOS/Linux/WSL

```bash
cp .env.example .env
# .env を編集して OPENAI_API_KEY と OPENAI_MODEL を設定

uv sync
cp prompt.txt.example prompt.txt  # 任意（システムプロンプトをカスタマイズする場合）

uv run python -m app.main
```

起動後に "buddy" と言って開始し、その後は英語で話しかけてください。

任意:
- 別の dotenv を読む: `uv run python -m app.main --env-file path/to/.env`
- dotenv 読み込みを無効化: `uv run python -m app.main --env-file ""`

## 挙動

- **ウェイクワード**: "buddy" と言って開始します。約 3 分間の無操作でスリープし、再度 "buddy" が必要になります。
- **割り込み**: アシスタントが話している間に話しかけると再生を停止します。
- **メモリ**: セッション中のみ（最大 50 メッセージ、コンテキストには最新 20 を使用）。再起動でクリアされます。
- **ログ**: 終了時に `logs/YYYY-MM-DD_HH-MM-SS.txt` に保存されます。

## 環境変数

環境変数でアプリを設定できます（通常は `.env` に記述）。

| 名前 | 必須 | デフォルト | 説明 |
| --- | --- | --- | --- |
| `OPENAI_API_KEY` | Yes | - | OpenAI SDK で使用される API キー |
| `OPENAI_MODEL` | Yes | - | 応答に使用するチャットモデル（例: `gpt-4o-mini`） |
| `OPENAI_BASE_URL` | No | - | API ベース URL を上書き（プロキシ/互換エンドポイント用） |
| `MY_ENGLISH_BUDDY_SYSTEM_PROMPT` | No | - | インラインのシステムプロンプトテキスト。設定されている場合、プロンプトファイルより優先されます |
| `MY_ENGLISH_BUDDY_SYSTEM_PROMPT_FILE` | No | `prompt.txt` | システムプロンプトを含むテキストファイルのパス。ファイルが存在し、空でない場合のみ使用されます |
| `MY_ENGLISH_BUDDY_STT_PROVIDER` | No | `openai` | Speech-to-Text プロバイダー: `openai`（デフォルト）または `local`（faster-whisper） |
| `MY_ENGLISH_BUDDY_LOCAL_STT_MODEL` | No | `distil-large-v3` | ローカル STT のモデル名（例: `distil-large-v3`, `large-v3`, `medium`）。`MY_ENGLISH_BUDDY_STT_PROVIDER=local` の場合のみ使用 |
| `MY_ENGLISH_BUDDY_TTS_PROVIDER` | No | `openai` | Text-to-Speech プロバイダー: `openai`（デフォルト）または `local`（Kokoro） |
| `MY_ENGLISH_BUDDY_TTS_VOICE` | No | *(プロバイダーのデフォルト)* | ボイス名。OpenAI デフォルト: `alloy`。Kokoro デフォルト: `af_heart` |
| `MY_ENGLISH_BUDDY_TTS_LANG_CODE` | No | `a` | Kokoro 言語コード。`a`=American English、`j`=日本語、`b`=British English。`MY_ENGLISH_BUDDY_TTS_PROVIDER=local` の場合のみ使用 |

システムプロンプトの解決順序:

1) `MY_ENGLISH_BUDDY_SYSTEM_PROMPT`（環境変数）
2) `MY_ENGLISH_BUDDY_SYSTEM_PROMPT_FILE`（デフォルト: `prompt.txt`）ファイルが存在し、空でない場合
3) アプリケーションに組み込まれたデフォルトプロンプト

## オプション: ローカル Speech-to-Text

OpenAI STT の代わりに、ローカル（faster-whisper）で文字起こしできます:

例:

```bash
uv sync --extra local-stt

# ローカル STT を有効化（.env に追記）
MY_ENGLISH_BUDDY_STT_PROVIDER=local
# 任意
MY_ENGLISH_BUDDY_LOCAL_STT_MODEL=distil-large-v3
```

補足:
- CUDA が見つからない場合は CPU にフォールバックします。
- チャットのために `OPENAI_API_KEY` は必要です。

## オプション: ローカル Text-to-Speech

OpenAI TTS の代わりに、Kokoro（高品質なローカル TTS エンジン）を使用できます（API 呼び出しなし、ランニングコスト 0）:

```bash
uv sync --extra local-tts

# ローカル TTS を有効化（.env に追記）
MY_ENGLISH_BUDDY_TTS_PROVIDER=local
# 任意: ボイスと言語コード
MY_ENGLISH_BUDDY_TTS_VOICE=af_heart
MY_ENGLISH_BUDDY_TTS_LANG_CODE=a
```

補足:
- GPU（CUDA）推奨（低遅延）。CPU のみでも動作しますが遅くなります。
- 初回起動時に Kokoro モデル（約 300 MB）が Hugging Face から自動ダウンロードされます。
- Linux では CUDA 12.4 対応 PyTorch wheel が自動的に使われます。macOS や CPU のみの環境では PyPI の CPU wheel が使われます。
- チャットのために `OPENAI_API_KEY` は必要です。
- **日本語 TTS**: `uv sync --extra local-tts` は英語サポートのみです。日本語 (`MY_ENGLISH_BUDDY_TTS_LANG_CODE=j`) を使う場合は追加で `uv sync --extra local-tts-ja` を実行してください。`local-tts-ja` には C/C++ ビルドツール（Linux/macOS）または Visual Studio Build Tools（Windows）が必要です。

## 開発

### テストの実行

プロジェクトにはユニットテストが含まれています。テストを実行するには:

```bash
# テスト依存関係をインストール
uv sync --extra test

# テストを実行
uv run pytest
```

## トラブルシューティング

- **ウェイクワードが動かない**: "buddy" をはっきり言ってください。無操作でスリープした場合も、再度 "buddy" が必要です。
- **反応が鈍い/過敏**: メニューの `Tools` → `ノイズキャリブレーション` を試してください。
- **音声が途中で止まる**: アシスタント発話中に話しかけると再生が停止します。
- **ローカル STT**: `uv sync --extra local-stt` で導入します。
- **ローカル TTS**: `uv sync --extra local-tts` で導入します。
- **ログ**: 終了時に `logs/` 配下へ保存されます（不具合報告に添付してください）。
