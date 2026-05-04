SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ADB="$SCRIPT_DIR/.psproject/android-sdk/platform-tools/adb"

cd project_dist/gradle
./gradlew assembleDebug
$ADB install -r app/build/outputs/apk/debug/app-debug.apk