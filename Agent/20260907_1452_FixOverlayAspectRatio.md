# 作業記録: 画像オーバーレイ表示のアスペクト比保持修正

## 1. 目的
- 画像オーバーレイ表示時に、元イラストの縦横比（アスペクト比）が崩れてペチャンコ（縦潰れ）になってしまう不具合を解消し、元画像の比率を100%維持して配置・表示すること。

## 2. 根本原因の特定
- `app.py`（プレビュー描画処理）において、以下の計算が行われていた：
  ```python
  scale_ratio_x = nw / 1080.0
  scale_ratio_y = nh / 1920.0
  pw_img = max(1, int(processed.width * scale_ratio_x))
  ph_img = max(1, int(processed.height * scale_ratio_y))
  ```
- 16:9横長動画の場合、プレビューキャンバス内で元動画が収まるよう `nw`（幅）と `nh`（高さ=幅の9/16）が計算されるため、`nh / 1920.0` は `nw / 1080.0` の約1/3以下となる。
- この異なる比率を画像の `width` と `height` それぞれに掛け合わせてリサイズしていたため、横幅に対して縦が3分の1以下に潰れ、極端に細長いペチャンコ画像になっていた。

## 3. 実施した修正
- `app.py` のプレビュー描画において、キャンバス（1080x1920）の基準スケーリング比率 `scale_ratio = self.current_preview_w / 1080.0` に統一。
- プレビュー画像の縮小計算：
  ```python
  scale_ratio = self.current_preview_w / 1080.0
  pw_img = max(1, int(processed.width * scale_ratio))
  ph_img = max(1, int(processed.height * scale_ratio))
  preview_overlay = processed.resize((pw_img, ph_img), PIL.Image.Resampling.LANCZOS)
  ```
- 配置座標計算：
  ```python
  px_base = int(job.get("overlay_x", 100) * scale_ratio)
  py_base = int(job.get("overlay_y", 100) * scale_ratio)
  ```
- これにより、完成動画レンダリング時（`video.py`）と同様に元イラストのアスペクト比が完全に保持され、プレビュー表示と完成動画での比率・位置・サイズが完全に一致するようになった。

## 4. 検証結果
- 指定画像（`名称未設定 1.png`、315x236、アスペクト比 1.3347）で検証：
  - 修正前: 105x24（比率 4.3750、縦が約3.3倍潰れる）
  - 修正後: 105x78（比率 1.3462、元画像比率を100%維持）
- PyInstaller によるEXE再ビルドおよび配備完了。
