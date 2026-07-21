[app]

# (string) アプリケーションのタイトル
title = PapaAlbumApp

# (string) パッケージ名（英小文字と数字のみ）
package.name = papaalbumapp

# (string) パッケージドメイン（Androidアプリの識別子用）
package.domain = org.thanks1114

# (string) main.py が配置されているソースコードのディレクトリ
source.dir = .

# (list) 含めるファイルの拡張子
source.include_exts = py,png,jpg,kv,atlas,ttf,ttc

# (string) アプリケーションのバージョン決定方法
version.method = semantic

# (string) アプリケーションのバージョン
version = 0.1

# (list) アプリケーションの依存要件（ライブラリ）
requirements = python3,kivy,pillow,piexif,plyer,pyjnius,android,pillow-heif

# (list) アプリケーションのアイコンファイル名
icon.filename = icon.png

# (str) サポートする画面の向き
orientation = portrait

# (bool) アプリケーションをフルスクリーンにするかどうか
fullscreen = 1

# (list) パーミッション（権限）の設定
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES

# (int) ターゲットとするAndroid APIレベル
android.api = 34

# (int) サポートする最小のAndroid APIレベル
android.minapi = 21

# (list) ビルド対象のAndroidアーキテクチャ
android.archs = arm64-v8a, armeabi-v7a

# (bool) AndroidXのサポートを有効にするかどうか
android.enable_androidx = True

# (str) リリースモードでのパッケージ形式
android.release_artifact = apk

# (str) デバッグモードでのパッケージ形式
android.debug_artifact = apk


[buildozer]

# (int) ログ出力レベル
log_level = 2

# (int) root権限でbuildozerが実行された場合に警告を表示するか
warn_on_root = 1