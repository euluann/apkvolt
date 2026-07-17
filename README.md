# APKVolt

APKVolt is a Python-based build system for packaging Python (Kivy) applications into Android APK files using precompiled runtime templates.

It is designed as a build toolchain that injects application code and assets into a structured APK template, then reconstructs and aligns the final package into a valid installable Android APK.

---

## Overview

APKVolt works by:

- Using a precompiled Android runtime template
- Injecting Python application code and assets into the APK structure
- Updating APK metadata (manifest, resources, package info)
- Rebuilding ZIP/APK binary structure (Local Headers, Central Directory, EOCD)
- Applying Android-compatible alignment rules
- Optionally signing the final APK

---

## Features

- APK binary parsing and reconstruction
- Template-based APK generation system
- Python/Kivy application packaging
- Native library (`.so`) alignment support
- APK metadata editing (package name, version, SDK levels)
- Asset injection (icons, splash screens, etc.)
- Secure APK signing (keystore-based, no CLI password exposure)
- CLI and Python library interface
- ZIP alignment system (zipalign-compatible behavior)

---

## Installation

From pip:

```bash
pip install apkvolt
```

From source:

```bash
git clone https://github.com/euluann/apkvolt
cd apkvolt
pip install .
```

---

Requirements

Python 3.11+

Linux or Termux environment recommended

---

CLI Usage

Build APK

```bash
apkvolt build . \
  --sign \
  --ks mykeystore.keystore \
  --ks-alias alias \
  --app-name "My App" \
  --min-sdk-version 21 \
  --target-sdk-version 34 \
  --app-version-code 1 \
  --app-version-name 0.1 \
  --app-package mypack.package.package \
  --icon icon.png \
  --icon-bg icon-bg.png \
  --icon-fg icon-fg.png \
  --splash splash.jpg \
  --output myapp.apk \
  --log-level info
```

Align APK

```bash
apkvolt align \
  app.apk \
  aligned-app.apk \
  -a 4 \
  -s 4096
```

Show libraries included in APK

```bash
apkvolt libs
```

---

If credentials are not provided, APKVolt will securely prompt for them using interactive input.


---

Python Usage


```python
from apkvolt import build, apkforge, zipalign

build(
    "/path/myproject",
    keystore_path="mykeystore.keystore",
    key_alias="myalias",
    keystore_pass="mykeystore_pass",
    key_pass="mykey_pass",
    apk_sign=True,
    app_name="APKVolt App",
    package="mypack.package.app",
    version_name="0.1",
    version_code=1,
    min_sdk_version=21,
    target_sdk_version=34,
    icon="icon.png",
    icon_background="icon_bg.png",
    icon_foreground="icon_fg.png",
    presplash="splash.png",
    output="app.apk"
)

zipalign.align(
    "app.apk",
    "app_aligned.apk",
    alignment=4,
    so_alignment=4096
)

apkforge.APK.signer(
    apk_path,
    keystore_path,
    key_alias,
    keystore_pass="mypass",
    key_pass="mypass"
)
```


---

Architecture

APKVolt build pipeline:

1. Load precompiled APK runtime template


2. Inject Python application into APK structure


3. Apply application metadata (manifest, package info, SDK levels)


4. Insert assets (icons, splash screens, resources)


5. Rebuild APK binary structure


6. Apply alignment rules


7. Optionally sign APK




---

Limitations

Strong dependency on Python 3.11 runtime environment for compile

Not a full source-to-native compiler (template-based system)

Requires careful version management of runtime APK base



---

Security

No password exposure via CLI arguments

Uses secure prompt input when needed

Recommended use of environment variables in automated environments



---

Project Goal

APKVolt aims to simplify Android application packaging for Python developers by providing a template-based build system for generating installable APKs without requiring a full native Android build toolchain.


---

License

MIT License. See LICENSE file for details.


---

Credits

See CREDITS.md for third-party assets and contributions.

