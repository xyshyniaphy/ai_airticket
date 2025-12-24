Now let me create the updated README with all your requirements:

# AI Air Ticket Search Agent (航空券検索AI)

中国語での航空券検索と価格履歴追跡を行う自律型AIエージェント。`tour.ne.jp`から航空券データを検索し、美しいレポートをTelegram経由で配信します。

## 主な機能

- **自動検索**: 複数の目的地と日付で`tour.ne.jp`から航空券データを取得
- **AI分析**: Google Geminiを使用して航空券オプションを分析し、包括的な中国語レポートを生成
- **価格履歴追跡**: SQLiteデータベースで価格履歴を保存し、同一フライトの価格推移をグラフ化
- **ビジュアルレポート**: モバイル表示に最適化された美しいHTMLレポートをPNG画像として生成
- **Telegram通知**: 画像レポートをTelegramボットで直接配信
- **モバイル最適化**: スマートフォンの縦向き表示に最適化されたレポートデザイン
- **設定可能**: `.env`ファイルで検索パラメータ(出発地、目的地、日付)を簡単に設定
- **コンテナ化**: ヘッドレスChromeを含むDockerコンテナで一貫した実行環境を提供

## 技術スタック

- **言語**: Python 3.12
- **パッケージマネージャー**: uv (高速Pythonパッケージマネージャー)
- **AIフレームワーク**: LangGraph, LangChain
- **AIモデル**: Google Gemini
- **Webスクレイピング**: Selenium (ヘッドレスChrome)
- **画像レンダリング**: Chrome headless スクリーンショット
- **データベース**: SQLite (価格履歴保存)
- **メッセージング**: Telegram Bot API
- **コンテナ化**: Docker + Docker Compose

## アーキテクチャ

エージェントはLangGraphによって調整された洗練されたパイプラインアーキテクチャを使用:

1. **Config Loader**: `.env`ファイルから検索パラメータを読み込み
2. **Scraper**: ヘッドレスChromeで航空券データをスクレイピング
3. **HTML Parser**: 生HTMLを構造化JSONに変換
4. **Report Generator**: AI分析を使用して美しい中国語HTMLレポートを作成
5. **Price History Tracker**: SQLiteに価格データを保存し、履歴グラフを生成
6. **Image Renderer**: HTMLレポートをヘッドレスChromeでPNG画像に変換
7. **Telegram Sender**: PNG画像をTelegramボット経由で送信

## ビジュアルレポート機能

- **モダンデザイン**: 美しいグラデーション背景とカードベースレイアウト
- **モバイルファースト**: スマートフォン縦向き表示に最適化(390x844px)
- **レスポンシブレイアウト**: タッチフレンドリーなインターフェース
- **プロフェッショナルスタイリング**: モダンなタイポグラフィとカラースキーム
- **フライトカード**: 各フライトを魅力的なカード形式で表示
- **価格履歴グラフ**: 同一フライトの過去の価格推移を視覚化
- **完全な情報**: 価格、航空会社、便名、所要時間、乗り継ぎ、手荷物情報
- **空港詳細**: IATAコード付きの完全な空港名(中国語)

## はじめに

### 前提条件

- [Git](https://git-scm.com/)
- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/)

### インストール

1. **リポジトリをクローン:**
   ```sh
   git clone <repository-url>
   cd ai_airticket
   ```

2. **エージェントを設定:**
   サンプルファイルから`.env`ファイルを作成:
   ```sh
   cp .env.sample .env
   ```
   `.env`ファイルを編集し、必要な値を入力してください。**Telegram Bot TokenとGemini API Keyは必須です。**

   ```dotenv
   # 必須シークレット - 必ず入力してください
   TELEGRAM_BOT_TOKEN="your_telegram_bot_token_here"
   GEMINI_API_KEY="your_gemini_api_key_here"

   # --- 検索パラメータ ---

   # 出発空港コード(IATA形式)
   ORIGIN="TYO"

   # 目的地空港コードのカンマ区切りリスト
   DESTINATIONS="CMB,BKK"

   # 出発日のカンマ区切りリスト(YYYYMMDD形式)
   DEPARTURE_DATES="20251227,20251228"

   # フライトタイプ: 0 = 片道, 1 = 往復
   AIR_TYPE="0"

   # 帰国日(YYYYMMDD形式) - air_typeが1の場合のみ使用
   RETURN_DATE=""

   # 乗客数
   PASSENGERS="1"

   # データベースとグラフ保存先(Dockerボリュームマウント)
   DATA_FOLDER="/app/data"
   ```

3. **Docker Composeでビルドと実行:**
   ```sh
   docker compose up --build
   ```
   
   バックグラウンドで実行する場合:
   ```sh
   docker compose up -d --build
   ```

## Docker Compose設定

`docker-compose.yml`の例:

```yaml
version: '3.8'

services:
  ai-air-ticket:
    build:
      context: .
      dockerfile: Dockerfile
    env_file:
      - .env
    volumes:
      - ./data:/app/data  # 価格履歴DBとグラフを永続化
    restart: unless-stopped
```

## Dockerfile構成

プロジェクトはPython 3.12とuvパッケージマネージャーを使用したマルチステージビルドを採用:

```dockerfile
# ビルドステージ
FROM python:3.12-slim AS builder

# ランタイムステージ
FROM python:3.12-slim AS runtime

# 仮想環境の使用
RUN python -m venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# uvを使用したパッケージインストール
RUN source .venv/bin/activate && \
    uv pip install -r requirements.txt
```

## 使用方法

Telegramボットを通じて以下のコマンドでエージェントと対話:

- `/start`: ウェルカムメッセージと使用方法を表示
- `/run`: 新しい航空券検索を開始し、ビジュアルレポートを画像として送信
- `/help`: 使用例を表示

エージェントは以下を実行します:
1. 設定に基づいて航空券を検索
2. AIを使用して結果を分析
3. 美しい中国語HTMLレポートを生成
4. SQLiteに価格データを保存
5. 同一フライトの価格履歴グラフを生成
6. モバイル最適化されたPNG画像にレンダリング
7. Telegramチャンネルに画像を送信

## 価格履歴機能

- **SQLiteデータベース**: 全ての検索結果と価格を`data/price_history.db`に保存
- **詳細追跡**: フライト番号、出発地、目的地、日付、価格、検索日時を記録
- **価格推移グラフ**: 同一フライトの過去の価格変動を視覚化
- **永続化**: Dockerボリュームマウントでデータを永続保存
- **データ分析**: 価格トレンドの分析とベストプライス検出

### データベーススキーマ

```sql
CREATE TABLE flight_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flight_number TEXT NOT NULL,
    airline TEXT NOT NULL,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    departure_date TEXT NOT NULL,
    price REAL NOT NULL,
    currency TEXT DEFAULT 'JPY',
    search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(flight_number, departure_date, search_date)
);
```

## テスト

Chromeレンダリング機能のテスト:
```bash
source .venv/bin/activate
python test_chrome_rendering.py
```

HTMLレポート生成のテスト:
```bash
source .venv/bin/activate
python test_html_report.py
```

価格履歴機能のテスト:
```bash
source .venv/bin/activate
python test_price_history.py
```

## 最近の更新

- **Python 3.12**: 最新のPython 3.12を使用
- **uvパッケージマネージャー**: 高速なパッケージインストール
- **仮想環境の厳密な使用**: `.venv`を必ず有効化
- **環境変数の厳密な管理**: `.env`ファイルからのみ値を読み込み、`os.getenv`は使用不可
- **価格履歴追跡**: SQLiteで詳細な価格履歴を保存
- **価格推移グラフ**: 同一フライトの価格変動を視覚化
- **Docker Compose対応**: データフォルダをボリュームマウントで設定
- **中国語レポート**: 全てのレポートは中国語で生成
- **ビジュアルレポート**: HTMLレポートをモバイル向けPNG画像に変換
- **画像配信**: テキストではなく画像としてTelegramに送信

## プロジェクト構成

```
ai_airticket/
├── .env                      # 環境変数設定(必須)
├── .env.sample              # 環境変数サンプル
├── docker-compose.yml       # Docker Compose設定
├── Dockerfile               # マルチステージDockerfile
├── requirements.txt         # Python依存関係
├── data/                    # 永続データ(Dockerボリューム)
│   ├── price_history.db    # SQLite価格履歴DB
│   └── graphs/             # 価格推移グラフ
├── src/
│   ├── config_loader.py    # .env設定読み込み
│   ├── scraper.py          # Webスクレイピング
│   ├── parser.py           # HTMLパーサー
│   ├── report_generator.py # 中国語レポート生成
│   ├── price_history.py    # 価格履歴管理
│   ├── graph_generator.py  # グラフ生成
│   ├── renderer.py         # HTML→PNG変換
│   └── telegram_bot.py     # Telegramボット
└── tests/
    ├── test_chrome_rendering.py
    ├── test_html_report.py
    └── test_price_history.py
```

## 重要な注意事項

1. **仮想環境の使用**: 全てのPythonコマンド実行前に`source .venv/bin/activate`を実行
2. **uvの使用**: パッケージインストールには`uv pip`を使用
3. **環境変数**: `.env`ファイルからのみ設定を読み込み、`os.getenv`は絶対に使用しない
4. **データ永続化**: `data/`フォルダはDocker Composeでボリュームマウント
5. **中国語出力**: レポートは中国語で生成される

## ライセンス

このプロジェクトはLICENSEファイルの条項に基づいてライセンスされています。

