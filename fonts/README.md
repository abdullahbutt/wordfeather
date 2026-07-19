# Fonts Folder

## ⚠️ IMPORTANT: This folder must contain your font file

**Filename required:** `Indopak-nastaleeq-hanafi-normal-v4.2.2-with-waqf-lazmi.woff2`

If your font file goes missing:

1. Download from: https://qul.tarteel.ai/resources/font
2. Get the "Indo-Pak Hanafi" `.woff2` file (v4.2.2 or newer)
3. Place it here as `Indopak-nastaleeq-hanafi-normal-v4.2.2-with-waqf-lazmi.woff2`

## Why this exists

The path is referenced in `docs/index.html` as:

```css
@font-face {
  font-family: 'IndoPak';
  src: url('./fonts/Indopak-nastaleeq-hanafi-normal-v4.2.2-with-waqf-lazmi.woff2') format('woff2');
  ...
}
```

If the file is missing, Quranic text falls back to Google's "Amiri Quran" font — readable, but not faithful to Pakistani mushaf style.
