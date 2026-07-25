[app]

# (str) Title of your application
title = PapaAlbum

# (str) Package name
package.name = papaalbum

# (str) Package domain (needed for android/ios packaging)
package.domain = org.thanks1114

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,ttf,ttc,so

# (list) Source files to include
source.include_dirs = 

# (str) Application versioning (method 1)
version = 1.1.0

# (list) Application requirements
requirements = python3,kivy,pillow,piexif,pyjnius

# (list) Supported orientations
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, READ_MEDIA_VIDEO, ACCESS_MEDIA_LOCATION, INTERNET

# (int) Target Android API, should be as high as possible.
android.api = 34

# (int) Minimum API required
android.minapi = 21

# (int) Android SDK version to use
android.sdk = 34

# (str) Android NDK version to use
android.ndk = 25b

# (bool) If True, then automatically accept SDK license
android.accept_sdk_license = True

# (bool) Enable AndroidX support. Required for modern Android targets
android.enable_androidx = True

# (list) Android architectures to build for
android.archs = arm64-v8a

# (list) Native libraries to include (.so)
# 分割された7つの実体ライブラリをカンマ区切りで指定
android.add_libs_arm64_v8a = libs/arm64-v8a/libSvtAv1Enc.so, libs/arm64-v8a/libavutil.so, libs/arm64-v8a/libswresample.so, libs/arm64-v8a/libavcodec.so, libs/arm64-v8a/libswscale.so, libs/arm64-v8a/libavformat.so, libs/arm64-v8a/libavfilter.so

# (bool) Copy library instead of making a lib dir and symlinking on android
android.copy_libs = 1

android.manifest.application_arguments = android:requestLegacyExternalStorage="true"


[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = error, 1 = warning, 2 = ignore)
warn_on_root = 1

