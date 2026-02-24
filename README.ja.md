# My English Buddy

My English Buddy は、OpenAI API を利用した英会話練習用のデスクトップアプリケーションです。

マイクから音声を継続的に聞き取り、OpenAI Speech-to-Text で文字起こしし、OpenAI Chat Completions で会話応答を生成し、OpenAI Text-to-Speech で音声化して話しかけます。シンプルな GUI ウィンドウで会話ログを表示します。

## クイックスタート

### Windows（PowerShell）

```powershell
Copy-Item .env.example .env
# .env を編集して OPENAI_API_KEY と OPENAI_MODEL を設定

uv sync
Copy-Item prompt.txt.example prompt.txt  # 任意（システムプロンプトをカスタマイズする場合。git管理されません）

uv run python -m app.main
```

### macOS/Linux/WSL

```bash
cp .env.example .env
# .env を編集して OPENAI_API_KEY と OPENAI_MODEL を設定

uv sync
cp prompt.txt.example prompt.txt  # 任意（システムプロンプトをカスタマイズする場合。git管理されません）

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
| `OPENAI_API_KEY` | Yes | - | OpenAI SDK で使用される API キー（現状、ローカル STT の場合でも必須です）|
| `OPENAI_MODEL` | Yes | - | 応答に使用するチャットモデル（例: `gpt-4o-mini`） |
| `OPENAI_BASE_URL` | No | - | API ベース URL を上書き（プロキシ/互換エンドポイント用） |
| `MY_ENGLISH_BUDDY_SYSTEM_PROMPT` | No | - | インラインのシステムプロンプトテキスト。設定されている場合、プロンプトファイルより優先されます |
| `MY_ENGLISH_BUDDY_SYSTEM_PROMPT_FILE` | No | `prompt.txt` | システムプロンプトを含むテキストファイルのパス。ファイルが存在し、空でない場合のみ使用されます |
| `MY_ENGLISH_BUDDY_STT_PROVIDER` | No | `openai` | Speech-to-Text プロバイダー: `openai`（デフォルト）または `local`（faster-whisper） |
| `MY_ENGLISH_BUDDY_LOCAL_STT_MODEL` | No | `distil-large-v3` | ローカル STT のモデル名（例: `distil-large-v3`, `large-v3`, `medium`）。`MY_ENGLISH_BUDDY_STT_PROVIDER=local` の場合のみ使用 |

システムプロンプトの解決順序:

1) `MY_ENGLISH_BUDDY_SYSTEM_PROMPT`（環境変数）
2) `MY_ENGLISH_BUDDY_SYSTEM_PROMPT_FILE`（デフォルト: `prompt.txt`）ファイルが存在し、空でない場合
3) アプリケーションに組み込まれたデフォルトプロンプト

## オプション: ローカル Speech-to-Text

OpenAI STT の代わりに、ローカル（faster-whisper）で文字起こしできます:

例:

```bash
uv sync --extra local-stt
```

補足:
- CUDA が見つからない場合は CPU にフォールバックします。
- チャット/TTS のために `OPENAI_API_KEY` は必要です。

## 開発

### テストの実行

プロジェクトには、コアアプリケーションロジック用のユニットテストが含まれています。テストを実行するには:

```bash
# テスト依存関係をインストール
uv sync --extra test

# テストを実行
uv run pytest
```

注意: テストカバレッジは現在、コアアプリケーションロジックに限定されています。インフラストラクチャと GUI レイヤーのテストは今後の開発で予定されています。

## トラブルシューティング

### マイクが動作しない

- **macOS/Linux**: ターミナルまたは Python にマイクの権限があることを、システム環境設定/設定で確認してください
- **すべてのプラットフォーム**: マイクが正しく接続され、デフォルトの入力デバイスとして設定されているか確認してください
- このアプリ以外で、簡単なオーディオテストを実行してマイクが動作するか確認してください

### 音声が出力されない

- スピーカー/ヘッドフォンが接続され、動作していることを確認してください
- システムの音量設定を確認してください
- OpenAI TTS API にアクセスできることを確認してください（API キーとネットワーク接続を確認）

### OpenAI API エラー

- `.env` で `OPENAI_API_KEY` が正しく設定されていることを確認してください
- API キーが必要なモデルへのアクセス権を持っていることを確認してください:
  - `gpt-4o-mini-transcribe`（Speech-to-Text、OpenAI STT を使用する場合のみ）
  - 選択した `OPENAI_MODEL`（Chat Completions）
  - `gpt-4o-mini-tts`（Text-to-Speech）
- OpenAI サービスへのネットワーク接続を確認してください
- ローカル STT を使用する場合、チャットと TTS モデルのみ OpenAI アクセスが必要です

### ローカル STT の問題

- **インストールエラー**: `uv sync --extra local-stt` を実行したことを確認してください
- **GPU が検出されない**: CUDA 12 + cuDNN をインストールするか、アプリは CPU にフォールバックします（遅くなります）
- **モデルのダウンロードに失敗**: インターネット接続を確認してください（初回使用時に Hugging Face からモデルがダウンロードされます）
- **文字起こしが遅い**: GPU アクセラレーションが推奨されます。CPU のみモードは大幅に遅くなります

### ウェイクワードが動作しない

- 最初に "buddy" をはっきりと言ってください
- GUI ログウィンドウで音声が文字起こしされているか確認してください
- 無操作でスリープした場合は、再度 "buddy" と言ってください
