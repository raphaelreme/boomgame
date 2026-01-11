for f in *.wav; do
  ffmpeg -i "$f" -c:a libvorbis -q:a 1 "${f%.wav}.ogg"
done
