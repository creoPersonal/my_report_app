# Pythonの公式イメージをベースとして使用
FROM python:3.9-slim

# 作業ディレクトリを設定
WORKDIR /app

# requirements.txtをコピーし、依存関係をインストール
COPY requirements.txt .
RUN pip install -r requirements.txt

# その他のアプリケーションコードをコピー
COPY . .

# Flaskの環境変数を設定
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# アプリケーションを実行するポートを開放
EXPOSE 5000

# アプリケーションの起動コマンド
CMD ["flask", "run"]