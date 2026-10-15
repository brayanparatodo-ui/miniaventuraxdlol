[app]
title = Miniaventura
package.name = miniaventura
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,wav,mp3
version = 1.0

requirements = python3,kivy

orientation = landscape
fullscreen = 1

android.permissions =
android.api = 33
android.minapi = 21
android.archs = arm64-v8a, armeabi-v7a
android.build_tools_version = 33.0.2

p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1
