[app]

title = PapaAlbumApp
package.name = papaalbumapp
package.domain = org.yoyopc
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1

# main.py を起動
entrypoint = main.py

# Kivy 必須
requirements = python3,kivy,pillow,piexif,androidstorage4kivy,ffmpeg-kit-python

# Android 権限（ファイル選択・保存に必須）
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE

# Android 13 以降のストレージ制限を回避
android.api = 33
android.minapi = 21

# Java
android.sdk = 28
android.ndk = 25b
android.build_tools = 33.0.2
android.gradle_dependencies = com.arthenica:ffmpeg-kit-full:5.1

# アプリのアイコン（任意）
icon.filename = icon.png

# 画面の向き
orientation = portrait

# Python 実行環境
android.python_version = 3.10

# ffmpeg-kit のための設定
android.allow_backup = True
android.enable_androidx = True

# ビルド高速化
p4a.local_recipes = ./recipes

# デバッグビルド
log_level = 2

# 署名（debug の場合は自動）
android.release_keystore = release.keystore
android.release_keystore_pass = password
android.release_keyalias = key0
android.release_keyalias_pass = password
