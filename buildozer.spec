[app]

# (string) アプリのタイトル
title = PapaAlbumApp

# (string) パッケージ名 (小文字英数字、ドット区切り)
package.name = papaalbumapp

# (string) ドメイン名 (識別子用)
package.domain = org.thanks1114

# (string) ソースコードが含まれるディレクトリ (通常はメインスクリプトのある場所)
source.dir = .

# (list) 対象に含めるファイルの拡張子
source.include_exts = py,png,jpg,kv,atlas

# (string) アプリのバージョン
version = 1.0.0

# -----------------------------------------------------------------------------
# 【重要】依存ライブラリの指定
# -----------------------------------------------------------------------------
# Python標準、Kivy、Pillow (画像処理)、piexif (メタデータ保持) を指定
requirements = python3, kivy, pillow, piexif

# (list) サポートする画面の向き (縦固定にする場合は portrait)
orientation = portrait

# -----------------------------------------------------------------------------
# Android 特有の設定
# -----------------------------------------------------------------------------

# (bool) フルスクリーン表示にするかどうか
fullscreen = 1

# 【重要】Android 13 (API 33) 以上をターゲットにしつつ、権限を網羅
android.api = 33
android.minapi = 21

# 【重要】Androidのストレージ読み書き権限の要求
# 共有フォルダ(DCIMやDownload)へのアクセスに必要です
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, MANAGE_EXTERNAL_STORAGE

# (list) ビルド対象のアーキテクチャ (最近の端末は arm64-v8a が主流です)
android.archs = arm64-v8a, armeabi-v7a

# -----------------------------------------------------------------------------
# 【将来用】FFmpeg をバイナリとして同梱する場合の設定
# -----------------------------------------------------------------------------
# 将来的に Android 用の ffmpeg バイナリをプロジェクト配下の「binaries」フォルダ等に
# 配置する場合、以下のように拡張子なしファイルや特定フォルダを含める設定を追加します。
# source.include_patterns = binaries/*

[buildozer]
# (int) ログの出力レベル (2 にすると詳細なデバッグログが出ます)
log_level = 2

# (int) エラー時にビルドを即座に停止するかどうか
warn_on_root = 1
