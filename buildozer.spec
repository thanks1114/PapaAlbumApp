[app]

# (str) Title of your application
title = PapaAlbumApp

# (str) Package name
package.name = papaalbumapp

# (str) Package domain (needed for android/ios packaging)
package.domain = org.thanks1114

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,ttc,ttf

# (str) Application versioning
version = 0.1

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy,pillow,piexif

# (str) Supported orientations (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

#
# Android specific
#

# (list) Permissions
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, READ_MEDIA_VIDEO

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API required.
android.minapi = 24

# (list) List of architectures to build for
android.archs = arm64-v8a

# (bool) Automatically accept SDK licenses
android.accept_sdk_licenses = True

# (bool) Allow backup of application data
android.allow_backup = True

#
# Buildozer section
#

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 =  disable, 1 = enable)
warn_on_root = 1