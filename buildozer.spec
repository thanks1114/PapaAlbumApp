[app]

# (string) アプリケーションのタイトル
title = PapaAlbumApp

# (string) パッケージ名（英小文字と数字のみ）
package.name = papaalbumapp

# (string) パッケージドメイン（Androidアプリの識別子用）
package.domain = org.thanks1114

# (string) main.py が配置されているソースコードのディレクトリ
source.dir = .

# (list) 含めるファイルの拡張子（空にするとすべてのファイルが含まれます）
source.include_exts = py,png,jpg,kv,atlas,ttf,ttc

# (list) パターンマッチングを使用した含めるファイルのリスト
#source.include_patterns = assets/*,images/*.png

# (list) 除外するファイルの拡張子
#source.exclude_exts = spec

# (list) 除外するディレクトリのリスト
#source.exclude_dirs = tests, bin, venv

# (list) パターンマッチングを使用した除外するファイルのリスト
#source.exclude_patterns = license,images/not_used/*

# (string) アプリケーションのバージョン決定方法 ('coefficient', 'field', 'regex' のいずれか)
version.method = semantic

# (string) アプリケーションのバージョン
version = 0.1

# (list) アプリケーションの依存要件（ライブラリ）
# 処理に必要な kivy, pillow, piexif を明記しています
requirements = python3,kivy,pillow,plyer,pyjnius,android

# (str) 要件（requirements）用のカスタムソースフォルダ
# p4a.local_recipes =

# (list) Garden（Kivyの拡張プラグイン）の要件
#garden_requirements =

# (list) アプリ起動時に表示されるプレスプラッシュ画像のファイル名
#presplash.filename = %(source.dir)s/data/presplash.png

# (list) アプリケーションのアイコンファイル名
#icon.filename = %(source.dir)s/data/icon.png
icon.filename = icon.png

# (str) サポートする画面の向き (landscape, sensorLandscape, portrait, all のいずれか)
orientation = portrait

# (list) 宣言するバックグラウンドサービスのリスト
#services = NAME:ENTRYPOINT_TO_PY,NAME2:ENTRYPOINT2_TO_PY


#
# Android 固有の設定
#

# (bool) アプリケーションをフルスクリーンにするかどうか (0 = False, 1 = True)
fullscreen = 1

# (list) パーミッション（権限）の設定
# Android 13以降の画像権限、および12以下のストレージ権限を網羅しています
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, ACCESS_MEDIA_LOCATION

# (list) アプリに必要なハードウェア機能
#android.features =

# (int) ターゲットとするAndroid APIレベル
# Google Playの要件およびp4aのデフォルト推奨値に適合させています
android.api = 34

# (int) サポートする最小のAndroid APIレベル
android.minapi = 21

# (int) 使用するAndroid SDKのバージョン
#android.sdk = 34

# (str) 使用するAndroid NDKのバージョン
#android.ndk = 25b

# (int) 使用するAndroid NDKのAPIレベル（通常は android.minapi と一致させます）
#android.ndk_api = 21

# (bool) プライベートデータストレージを使用するか (True)、公開ストレージを使用するか (False)
#android.private_storage = True

# (str) Android NDKのディレクトリ（空の場合は自動的にダウンロードされます）
#android.ndk_path =

# (str) Android SDKのディレクトリ（空の場合は自動的にダウンロードされます）
#android.sdk_path =

# (str) ANTのディレクトリ（空の場合は自動的にダウンロードされます）
#android.ant_path =

# (str) コンパイルに使用する python-for-android (p4a) のブランチ
#android.p4a_branch = master

# (list) python-for-android に渡す追加の引数
#android.p4a_extra_args =

# (list) Androidアプリケーションが依存するAARライブラリ
#android.add_aars =

# (list) Gradleの依存関係
#android.gradle_dependencies =

# (list) 追加するJavaファイル
#android.add_src =

# (list) Androidマニフェスト（AndroidManifest.xml）の属性
#android.manifest_attributes =

# (list) Androidマニフェストの xmlns 属性
#android.manifest_xmlns =

# (str) アプリケーション要素に適用するAndroid XML属性
#android.manifest_app_attributes =

# (list) ビルド対象のAndroidアーキテクチャ（armeabi-v7a, arm64-v8a, x86, x86_64）
# GitHub Actionsのビルド時間を抑えつつ、主要な実機に対応する構成です
android.archs = arm64-v8a, armeabi-v7a

# (bool) AndroidXのサポートを有効にするかどうか。最新のAPIレベルでは必須です
android.enable_androidx = True

# (bool) .py ファイルのバイトコンパイル（最適化）をスキップするかどうか
#android.skip_byte_compile = False

# (str) リリースモードでのパッケージ形式 (aab, apk, aar)
android.release_artifact = apk

# (str) デバッグモードでのパッケージ形式 (apk, aar)
android.debug_artifact = apk


#
# Python for android (p4a) 固有の設定
#

# (str) p4aのディレクトリ（指定するとバックグラウンドのリスト設定を上書きします）
#p4a.dir =


#
# ----------------------------------------
# 他のビルドターゲット（iOSやOSXなど）の設定は使用しないため省略しています。
# ----------------------------------------

[buildozer]

# (int) ログ出力レベル (0 = エラーのみ, 1 = 通常情報, 2 = デバッグ（コマンド実行結果も出力）)
log_level = 2

# (int) root権限でbuildozerが実行された場合に警告を表示するか (0 = False, 1 = True)
warn_on_root = 1
