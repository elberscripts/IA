# Localiza o JDK e as ferramentas de build
export BUILD_TOOLS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/.build-tools"
if [ -z "${JAVA_HOME:-}" ] || [ ! -x "${JAVA_HOME:-}/bin/java" ]; then
  if command -v java >/dev/null 2>&1; then
    export JAVA_HOME="$(dirname "$(dirname "$(readlink -f "$(command -v java)")")")"
  else
    export JAVA_HOME="$(python3 -c 'import jdk4py;print(jdk4py.JAVA_HOME)' 2>/dev/null)"
  fi
fi
export JAVA="$JAVA_HOME/bin/java"
export AAPT2="$BUILD_TOOLS/bin/aapt2"
export ANDROID_JAR="$BUILD_TOOLS/android.jar"
export ECJ="$BUILD_TOOLS/ecj-3.45.0.jar"
export D8="$BUILD_TOOLS/d8.jar"
export APKSIGNER="$BUILD_TOOLS/apksigner.jar"
