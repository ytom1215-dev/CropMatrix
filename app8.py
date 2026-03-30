import streamlit as st
import pandas as pd
import itertools

# ページ設定（ブラウザのタブに表示される名前とアイコン）
st.set_page_config(page_title="PlotBuilder", page_icon="🌱", layout="centered")

st.title("🌱 PlotBuilder - 調査データ様式ジェネレーター")
st.markdown("試験の要因数と水準を設定すると、統計解析にそのまま使える「整然データ（Tidy Data）」形式の入力様式を自動生成します。")

# --- データ入力の4つの鉄則（目立つようにアコーディオン形式で表示） ---
with st.expander("💡 新人さんへ：データ入力 4つの鉄則（必ず読んでね！）", expanded=True):
    st.markdown("""
    統計解析（RやPython）をスムーズに行うため、以下のルールを守って入力してください。
    
    1. **1行1データの原則**: 「横」にデータを伸ばさず「縦」に追加する。
    2. **セル結合は絶対禁止**: 結合するとプログラムで読み込めなくなります。
    3. **「数値」と「文字」を混ぜない**: 例）「45(病害)」はNG。特記事項は必ず「備考」列へ。
    4. **欠損値の扱いを統一**: 枯死などでデータが取れなかった場合は「空欄」にする（「-」や「欠」は入力しない）。
    """)

st.divider()

# --- 1. 試験設計の基本設定 ---
st.subheader("1. 試験区の設計")

# 要因の数をユーザーに決めさせる
num_factors = st.number_input("設定する要因の数", min_value=1, max_value=5, value=2, step=1)

factor_names = []
factor_levels_list = []

st.markdown("#### 要因と水準の入力")
# 設定した要因の数だけ、入力欄を動的にループで生成
for i in range(num_factors):
    col1, col2 = st.columns([1, 2])
    with col1:
        # デフォルト名を少し工夫（1つ目は品種、2つ目は施肥量、3つ目以降は要因3...）
        default_name = ["品種", "施肥量", "栽植密度"][i] if i < 3 else f"要因{i+1}"
        f_name = st.text_input(f"要因 {i+1} の名前", value=default_name, key=f"name_{i}")
        factor_names.append(f_name)
    with col2:
        default_levels = ["ニシユタカ, とうや, ホッカイコガネ", "多, 中, 少", "疎, 密"][i] if i < 3 else "水準A, 水準B"
        f_levels = st.text_input(f"要因 {i+1} の水準（カンマ区切り）", value=default_levels, key=f"levels_{i}")
        # カンマで分割して前後の空白を削除し、リスト化
        cleaned_levels = [x.strip() for x in f_levels.split(",") if x.strip() != ""]
        factor_levels_list.append(cleaned_levels)

st.markdown("#### 反復と調査項目の設定")
col3, col4 = st.columns(2)
with col3:
    reps = st.number_input("反復（ブロック）数", min_value=1, max_value=20, value=3)
with col4:
    target_var = st.text_input("目的変数（調査項目）", "収量_kg/a")

st.divider()

# --- 2. テンプレート生成処理 ---
if st.button("📝 この設計で入力様式を作成する", type="primary"):
    
    # 反復のリストを作成
    rep_list = list(range(1, reps + 1))
    
    # 全組み合わせの生成 (* を使って可変長のリストを展開)
    combinations = list(itertools.product(rep_list, *factor_levels_list))
    
    # データフレーム化（列名：反復 + 各要因名）
    columns = ["反復"] + factor_names
    df_template = pd.DataFrame(combinations, columns=columns)
    
    # 圃場での調査を想定し、反復 > 要因1 > 要因2... の順でソート
    df_template = df_template.sort_values(by=["反復"] + factor_names).reset_index(drop=True)
    
    # 目的変数と備考列を追加
    df_template[target_var] = None
    df_template["備考"] = None
    
    # --- 3. 結果の表示とダウンロード ---
    st.subheader("2. 生成された入力様式")
    
    # 区画数の計算
    total_plots = reps
    for levels in factor_levels_list:
        total_plots *= len(levels)
        
    st.success(f"全 {total_plots} 区画の入力様式が作成されました！")
    
    # --- Rでそのまま解析できることのアピールとコード例 ---
    st.info("💡 **ここがポイント！**\n\nダウンロードしたCSVに調査データを入力すれば、面倒なデータ整形（前処理）は一切不要です。そのままRに読み込ませて、すぐに分散分析などの統計解析が実行できます。")
    
    # 設定した要因名を使って、Rの数式（フォーミュラ）を自動生成
    if num_factors >= 2:
        # 要因が2つ以上の場合はメインの2つで交互作用（*）を含める例
        r_formula = f"{target_var} ~ {factor_names[0]} * {factor_names[1]} + Error(反復)"
    else:
        # 要因が1つの場合
        r_formula = f"{target_var} ~ {factor_names[0]} + Error(反復)"
        
    st.markdown("**▼ Rでの分散分析（乱塊法）の実行イメージ**")
    st.code(f"""
# 1. データを読み込む
df <- read.csv("field_survey_template.csv")

# 2. そのまま分散分析を実行！
result <- aov({r_formula}, data = df)
summary(result)
    """, language="r")
    
    # 画面上でプレビュー
    st.dataframe(df_template, use_container_width=True)
    
    # CSVダウンロードボタン
    csv = df_template.to_csv(index=False).encode('utf-8-sig') # utf-8-sigでExcel文字化け防止
    st.download_button(
        label="📥 この様式をダウンロード (CSV)",
        data=csv,
        file_name="field_survey_template.csv",
        mime="text/csv",
    )
