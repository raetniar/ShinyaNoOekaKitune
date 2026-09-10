# 作業記録: 字幕タイムライン見出しラベルのオミット

## 目的
ユーザーからの要望に基づき、字幕タイムライン上部の見出しラベル「字幕編集タイムライン (秒数・テキストは手動変更可能)」をオミットし、画面の縦領域を広く確保する。

## 変更内容
- **`system_files/src/app.py`**:
  - `self.sub_scroll = ctk.CTkScrollableFrame(rf, label_text="字幕編集タイムライン (秒数・テキストは手動変更可能)")`
  - 変更後: `self.sub_scroll = ctk.CTkScrollableFrame(rf)`
  - 見出しバーを削除し、字幕カードの表示スペースを縦方向に拡大。

## 検証結果
- `py_compile`: Exit code 0
- 自動UI検証スクリプト: `ALL TESTS PASSED SUCCESSFULLY!`
