#!/bin/bash

# 0. Parse and validate arguments
if [[ $# -lt 3 ]]; then
    echo "Usage: ./run.sh <DomainName> <EnviromentDataFilePath> <TimeStepPresent:true|false>"
    exit 1
fi

DOMAIN_NAME="$1"
ENV_FILE="$2"
TIMESTEP_FLAG="$3"

# 1. Get path of current script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 2. Extract up to AIProbe root
AIPROBE_ROOT=$(echo "$SCRIPT_DIR" | sed -E 's|(.*AIProbe).*|\1|')

# 3. Construct result + logs directory
RESULT_DIR="${AIPROBE_ROOT}/Result/${DOMAIN_NAME}"
LOG_DIR="${RESULT_DIR}/Logs"
SCRIPT_PATH="${AIPROBE_ROOT}/script.py"

# 4. OS Detection
OS="$(uname -s)"
ARCH="$(uname -m)"
if [[ "$OS" == "Linux" ]]; then
    APP_DIR="linux-x64"
elif [[ "$OS" == "Darwin" ]]; then
    if [[ "$ARCH" == "arm64" ]]; then
        APP_DIR="osx-arm64"
    else
        APP_DIR="osx-x64"
    fi
elif [[ "$OS" =~ MINGW.* || "$OS" =~ CYGWIN.* || "$OS" =~ MSYS.* ]]; then
    APP_DIR="win-x64"
else
    echo "Unsupported OS: $OS"
    exit 1
fi

echo "Detected OS folder: $APP_DIR"
echo "AIprobe root: $AIPROBE_ROOT"
echo "Result path: $RESULT_DIR"
echo "Env file: $ENV_FILE"
echo "⏱ TimeStepPresent: $TIMESTEP_FLAG"

# 5. Create folders
mkdir -p "$LOG_DIR"

# 6. Path to config XML
CONFIG_FILE="${SCRIPT_DIR}/${APP_DIR}/AIprobeConfig.xml"

if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "Config file not found: $CONFIG_FILE"
    exit 1
fi

echo "Updating config..."

# 7. Patch config XML with all required paths and flags
sed -i.bak \
    -e "s|<LogFilePath>.*</LogFilePath>|<LogFilePath>${LOG_DIR}</LogFilePath>|" \
    -e "s|<ResultFolderPath>.*</ResultFolderPath>|<ResultFolderPath>${RESULT_DIR}</ResultFolderPath>|" \
    -e "s|<ScriptFilePath>.*</ScriptFilePath>|<ScriptFilePath>${SCRIPT_PATH}</ScriptFilePath>|" \
    -e "s|<EnviromentDataFilePath>.*</EnviromentDataFilePath>|<EnviromentDataFilePath>${ENV_FILE}</EnviromentDataFilePath>|" \
    -e "s|<TimeStepPresent>.*</TimeStepPresent>|<TimeStepPresent>${TIMESTEP_FLAG}</TimeStepPresent>|" \
    "$CONFIG_FILE"

echo "Config updated:"
echo "   - LogFilePath:          $LOG_DIR"
echo "   - ResultFolderPath:     $RESULT_DIR"
echo "   - EnviromentDataFile:   $ENV_FILE"
echo "   - TimeStepPresent:      $TIMESTEP_FLAG"
echo "   - ScriptFilePath:       $SCRIPT_PATH"

# 8. Run AIprobe binary
cd "${SCRIPT_DIR}/${APP_DIR}"
chmod +x AIprobe
./AIprobe