# RoutineFit Android APK build package

This directory is meant to be copied into the root of https://github.com/nanami128-sketch/routinefit together with `.github/workflows/android-build.yml`.

- The existing web app is automatically copied into Android assets for each build. This does not edit the web app source or its storage key.
- App ID: `com.nanami128sketch.routinefit`, matching the Android Developer Console registration.
- The app WebView uses `https://appassets.androidplatform.net/assets/` (a device-local HTTPS origin) and has localStorage and IndexedDB support.
- Chrome/PWA and Android WebView have **different storage origins**. To move existing records, export a JSON backup in the PWA, then import it inside the APK. Always test the restored records before uninstalling the old PWA.
- JSON backup in Android uses the system's Save Document picker, never silent public filesystem access. JSON import uses the system's file picker.
- App store approval is not implied by a successful APK build or Android Developer Console package verification.

## Debug build (no secrets needed)

After committing these files to `main`, open GitHub -> Actions -> "RoutineFit Android APK". A push runs the debug job automatically, or click Run workflow. Open the successful job's Artifacts and download `routinefit-debug-apk`. The zip contains `app-debug.apk`. **Debug APK is for testing only and cannot serve as an app-store release.**

## Signed release (never upload your JKS to the repository)

1. On your own phone (Termux) convert your release keystore to base64 **without printing it in a public log**. For example:
   `base64 -w 0 ~/storage/shared/Documents/routinefit-release.jks | termux-clipboard-set`
   This requires the `termux-api` package and Termux:API app; alternatively save base64 locally then copy it privately. Delete temporary base64 copies afterwards.
2. In GitHub repository Settings -> Secrets and variables -> Actions -> New repository secret, create the following **private** secrets:
   - `ROUTINEFIT_KEYSTORE_BASE64`: full one-line base64 text of your JKS bytes
   - `ROUTINEFIT_KEYSTORE_PASSWORD`: the private JKS password
   - `ROUTINEFIT_KEY_ALIAS`: `routinefit`
   - `ROUTINEFIT_KEY_PASSWORD`: your key password (same as JKS password if you pressed Enter at that prompt)
3. On `main`, GitHub Actions -> RoutineFit Android APK -> Run workflow. `signed-release` runs only for manual `workflow_dispatch` builds on `main`, using the stored encrypted secrets. Download `routinefit-release-signed-apk` artifact.
4. Use `apksigner verify --print-certs app-release.apk` on the release APK to confirm the SHA-256 signing certificate matches the one registered in Android Developer Console.

**Important:** The keystore file and both passwords must be backed up securely outside GitHub. Losing them can block future app updates. Never paste keys or passwords into ChatGPT or GitHub source files. If you already exposed keystore bytes publicly, rotate the key before release.

Android Gradle Plugin 8.9.2 / Gradle 8.11.1 / Android SDK 35 / Java 17 / AndroidX WebKit 1.14.0. `JsAlertResult` is not imported; the native entry point is self-contained.
