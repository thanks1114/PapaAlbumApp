[app]

title = PapaAlbumApp
package.name = papaalbumapp
package.domain = org.yoyopc
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1

entrypoint = main.py

requirements = python3,kivy,pillow,piexif,androidstorage4kivy,ffmpeg-kit-python

android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,MANAGE_EXTERNAL_STORAGE

android.api = 33
android.minapi = 21

android.sdk = 33
android.ndk = 25b
android.build_tools = 33.0.2
android.gradle_dependencies = com.arthenica:ffmpeg-kit-full:5.1

# recipes を使わないので空にする
p4a.local_recipes =

icon.filename = icon.png
orientation = portrait

android.python_version = 3.10

android.allow_backup = True
android.enable_androidx = True

log_level = 2

android.release_keystore = release.keystore
android.release_keystore_pass = password
android.release_keyalias = key0
android.release_keyalias_pass = password
