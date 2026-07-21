[app]
title = PapaAlbumApp
package.name = papaalbumapp
package.domain = org.thanks1114

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttc,ttf

version = 0.1

# (list) 依存ライブラリの定義
requirements = python3,kivy,pillow,piexif

# (str) 必須パーミッション
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, READ_MEDIA_VIDEO

# (list) 対象アーキテクチャ (Pixel 7/8/9/10 等の64bit専用端末対応)
android.archs = arm64-v8a

# (int) Target Android API
android.api = 33
android.minapi = 24