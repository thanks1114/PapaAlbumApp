[app]

# (str) Title of your application
title = PapaAlbum

# (str) Package name
package.name = papaalbum

# (str) Package domain (needed for android/ios packaging)
package.domain = org.thanks1114

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the source project)
source.include_exts = py,png,jpg,kv,atlas,ttf,ttc,json

# (str) Application versioning
version = 1.1.3

# (list) Application requirements
requirements = python3, hostpython3, kivy, pillow, piexif, pyjnius

# (list) Permissions
android.permissions = READ_MEDIA_IMAGES, READ_MEDIA_VIDEO, ACCESS_MEDIA_LOCATION, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# (int) Target Android API
android.api = 34

# (int) Minimum API your APK will support
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (bool) C/C++ コンパイルキャッシュの有効化
android.ccache = 1

# (bool) Android SDK ライセンスの自動承諾
android.accept_sdk_license = True

# FFmpegKit Native Library を Gradle 経由で取得 (AV1を含むフルコーデック対応)
android.gradle_dependencies = com.arthenica:ffmpeg-kit-full:6.0-2

# (list) Pattern to match files that should be excluded from the built package
source.exclude_patterns = license,images/*/*.jpg

# (str) Supported orientation
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Architecture to build for
android.archs = arm64-v8a

# (bool) Enable Android AutoBackup feature
android.allow_backup = True

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug)
log_level = 2

# (int) Display warning if buildozer is run as root
warn_on_root = 1