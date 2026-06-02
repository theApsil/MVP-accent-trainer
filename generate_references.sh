set -e

VOICE="${1:-Samantha}"
TARGET_DIR="static/reference_audio"

if ! command -v ffmpeg &> /dev/null; then
    echo "❌ ffmpeg не установлен. Поставь: brew install ffmpeg"
    exit 1
fi

mkdir -p "$TARGET_DIR"
cd "$TARGET_DIR"

WORDS=(
    thought think three through thank this that they them there then though
    really right read red rock rural library February world girl work word car far bird third
    happy apple cat bad man bed head said ship sheep live leave bit beat full fool book food
    time nice buy now how house go no boat day say make boy toy voice
    school street strong spring scream splash twelve twelfth asked texts
    she show wash measure pleasure vision chair church watch judge juice
    computer interesting comfortable vegetable temperature photography photograph development opportunity necessary
    hello water morning evening question answer language English knowledge tough
)

UNIQUE_WORDS=($(echo "${WORDS[@]}" | tr ' ' '\n' | sort -u))

echo "🎵 Генерируем ${#UNIQUE_WORDS[@]} эталонов голосом $VOICE..."
COUNTER=0
for w in "${UNIQUE_WORDS[@]}"; do
    COUNTER=$((COUNTER + 1))
    if [[ -f "$w.wav" ]]; then
        echo "  [$COUNTER/${#UNIQUE_WORDS[@]}] ⏭  $w.wav (уже есть)"
        continue
    fi
    printf "  [%d/%d] → %s.wav\n" "$COUNTER" "${#UNIQUE_WORDS[@]}" "$w"
    say -v "$VOICE" -o "$w.aiff" "$w"
    ffmpeg -i "$w.aiff" -ar 16000 -ac 1 "$w.wav" -y -loglevel error
    rm "$w.aiff"
done

echo ""
echo "✅ Готово! Файлов в папке:"
ls *.wav | wc -l