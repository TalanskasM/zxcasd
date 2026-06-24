[app]
title = Game Overlay Assistant
package.name = gameassistant
package.domain = org.overlay
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,kivy,plyer
orientation = landscape
fullscreen = 1

# Android dependencies handled internally by GitHub
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 0
