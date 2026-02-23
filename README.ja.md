# My English Buddy

My English Buddy は、OpenAI API を利用した英会話練習用のデスクトップアプリケーションです。

マイクから音声を継続的に聞き取り、OpenAI Speech-to-Text で文字起こしし、OpenAI Chat Completions で会話応答を生成し、OpenAI Text-to-Speech で音声化して話しかけます。シンプルな GUI ウィンドウで会話ログを表示します。

このプロジェクトは現在も **開発中** です。README は網羅的ではなく、実用的な内容を優先しています。

## 概要

- **インターフェース**: GUI アプリケーション（PySide6）、会話ログを表示
- **入力**: 継続的なマイク聞き取り、音声自動検出
- **ウェイクワード**: "buddy" と言って会話を開始（初回のみ必要）
- **文字起こし**: 選択可能な Speech-to-Text プロバイダー
  - **OpenAI**（デフォルト）: OpenAI 音声認識 API を使用（`gpt-4o-mini-transcribe`）
  - **Local**: faster-whisper を使用したオフライン文字起こし（追加セットアップが必要）
- **応答**: OpenAI Chat Completions API（`OPENAI_MODEL` を使用）
- **音声出力**: OpenAI Text-to-Speech API（`gpt-4o-mini-tts`、`alloy` ボイスにハードコード）
- **メモリ**: セッション中、最大 50 メッセージの会話履歴をメモリ内に保持
- **割り込み**: アシスタントの発話中に話しかけると、即座に停止します

現在の制限事項（この段階では想定内）:

- メモリはセッション間で保存されません（再起動時にクリア）
- 会話履歴は `logs/` ディレクトリにテキストファイルとして出力されますが、再インポートはできません
- TTS モデルとボイスは環境変数で設定できません
- ローカル STT は GPU アクセラレーションに CUDA 12 + cuDNN が必要です（CPU のみモードも利用可能ですが遅くなります）

## 必要要件

- **Python**: 3.12（`.python-version` 参照）
- **OpenAI API キー**: 使用するモデル（文字起こし、チャット、TTS）へのアクセス権が必要
  - ローカル STT プロバイダーを使用する場合は不要（チャットと TTS のみ OpenAI が必要）
- **マイクアクセス** と動作するオーディオスタック
- **音声出力**（スピーカーまたはヘッドフォン）
- **uv**（推奨）: リポジトリには `uv.lock` が含まれています

オプション（ローカル STT 用）:
- **CUDA 12 + cuDNN**: GPU アクセラレーション対応のローカル文字起こし用（推奨）
- **faster-whisper**: `uv sync --extra local-stt` でインストール

## セットアップ

1) 環境ファイルを作成します:

```bash
cp .env.example .env
```

2) `.env` を編集し、少なくとも `OPENAI_API_KEY` と `OPENAI_MODEL` を設定します。

3) 依存関係をインストールします:

```bash
# 基本インストール（OpenAI STT）
uv sync

# または: ローカル STT サポート付きでインストール（オプション）
uv sync --extra local-stt
```

4) アプリケーションを実行します:

```bash
uv run python -m app.main
```

GUI ウィンドウが開き、聞き取りを開始します。"buddy" と言って起動し、その後は自然に英語で話してください。アシスタントが音声で返答します。

オプション: システムプロンプトのカスタマイズ（推奨）:

```bash
cp prompt.txt.example prompt.txt
# prompt.txt を編集してアシスタントの動作をカスタマイズ
```

別の dotenv ファイルを読み込む場合:

```bash
uv run python -m app.main --env-file path/to/.env
```

dotenv の読み込みを完全に無効にする場合は、空の値を渡します:

```bash
uv run python -m app.main --env-file ""
```

## 動作の仕組み

1. **聞き取り**: アプリはバックグラウンドでマイクを継続的に聞き取ります
2. **ウェイクワード**: "buddy" と言って会話を開始します（セッション中に一度だけ必要）
3. **音声入力**: 起動後は自然に話してください。話し終わったことを自動検出します
4. **文字起こし**: 音声が OpenAI Speech-to-Text API を使ってテキストに変換されます
5. **チャット**: 文字起こしされたテキストが会話履歴とともに OpenAI Chat Completions API に送信されます
6. **音声出力**: アシスタントの応答が OpenAI Text-to-Speech API を使って音声化されます
7. **再生**: 音声がスピーカー/ヘッドフォンから再生されます
8. **割り込み**: アシスタントが話している間に話しかけると割り込むことができます

**メモリ管理:**

会話メモリは、セッション中に最大 50 メッセージを保存します。応答生成時には、会話の焦点を保つために最新の 20 メッセージをコンテキストとして使用します。メモリはアプリ再起動時にクリアされます。

## 環境変数

環境変数でアプリを設定できます（通常は `.env` に記述）。

| 名前 | 必須 | デフォルト | 説明 |
| --- | --- | --- | --- |
| `OPENAI_API_KEY` | Yes* | - | OpenAI SDK で使用される API キー。*ローカル STT のみを使用する場合は不要（チャットと TTS には必要）|
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

## 設定

### システムプロンプト

システムプロンプトは、アシスタントのパーソナリティと動作を定義します。3 つの方法でカスタマイズできます（優先順）:

1. **環境変数**: `MY_ENGLISH_BUDDY_SYSTEM_PROMPT` を直接設定
2. **プロンプトファイル**: `MY_ENGLISH_BUDDY_SYSTEM_PROMPT_FILE` で指定されたファイルを作成/編集（デフォルト: `prompt.txt`）
3. **組み込みデフォルト**: どちらも提供されていない場合、組み込みの英語チュータープロンプトを使用

例:

```bash
# カスタムプロンプトファイルを使用
cp prompt.txt.example prompt.txt
# prompt.txt を希望する指示内容で編集

# または環境変数を使用
export MY_ENGLISH_BUDDY_SYSTEM_PROMPT="You are a friendly English tutor. Keep replies short."
uv run python -m app.main
```

### Speech-to-Text プロバイダー

OpenAI のクラウドベース文字起こしまたはローカルオフライン文字起こしを選択できます:

**OpenAI STT（デフォルト）**:
- `gpt-4o-mini-transcribe` モデルを使用
- インターネット接続と OpenAI API キーが必要
- 高速で正確
- `MY_ENGLISH_BUDDY_STT_PROVIDER=openai` を設定（または未設定のまま）

**ローカル STT**:
- faster-whisper を使用したオフライン文字起こし
- 文字起こしにインターネット不要（チャットと TTS には OpenAI が必要）
- 依存関係のインストールに `uv sync --extra local-stt` が必要
- GPU アクセラレーション推奨（CUDA 12 + cuDNN）
- `MY_ENGLISH_BUDDY_STT_PROVIDER=local` を設定
- `MY_ENGLISH_BUDDY_LOCAL_STT_MODEL` でモデルを設定（デフォルト: `distil-large-v3`）

ローカル STT のセットアップ例:

```bash
# ローカル STT サポート付きで依存関係をインストール
uv sync --extra local-stt

# .env を設定
echo "MY_ENGLISH_BUDDY_STT_PROVIDER=local" >> .env
echo "MY_ENGLISH_BUDDY_LOCAL_STT_MODEL=distil-large-v3" >> .env

# アプリを実行
uv run python -m app.main
```

利用可能なローカルモデル（Hugging Face から、初回使用時に自動ダウンロード）:
- `distil-large-v3`（デフォルト、速度と精度のバランス）
- `large-v3`（最高精度、低速）
- `medium`（高速、低精度）
- その他のオプションは [faster-whisper ドキュメント](https://github.com/SYSTRAN/faster-whisper)を参照

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
- ウェイクワードはセッション中に一度だけ言う必要があります
