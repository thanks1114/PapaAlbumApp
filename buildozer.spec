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

# (str) Application versioning (method 1)
version = 1.1.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy,pillow,piexif,pyjnius

# (list) Permissions
android.permissions = READ_MEDIA_IMAGES, READ_MEDIA_VIDEO, ACCESS_MEDIA_LOCATION, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# (int) Target Android API, should be as high as possible.
android.api = 34

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (list) Native libraries to include (.so)
android.add_libs_arm64_v8a = libs/arm64-v8a/libSvtAv1Enc.so, libs/arm64-v8a/libavutil.so, libs/arm64-v8a/libswresample.so, libs/arm64-v8a/libavcodec.so, libs/arm64-v8a/libswscale.so, libs/arm64-v8a/libavformat.so, libs/arm64-v8a/libavfilter.so, libs/arm64-v8a/libffmpeg.so

# (list) Pattern to match files that should be excluded from the built package
source.exclude_patterns = license,images/*/*.jpg

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Architecture to build for
android.archs = arm64-v8a

# (bool) Enable Android AutoBackup feature (API >= 23)
android.allow_backup = True

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = disable, 1 = enable)
warn_on_root = 1