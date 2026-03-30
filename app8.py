import streamlit as st
import pandas as pd
import itertools

st.title("🌱 調査データ様式ジェネレーター（多要因対応版）")
st.markdown("試験の要因数と水準を設定すると、解析にそのまま使える整然データ（Tidy Data）の様式を自動生成します。")

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
        # カンマで分割してリスト化
        cleaned_levels = [x.strip() for x in f_levels.split(",")]
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
    
    # 全組み合わせの生成
    # itertools.productに *（アスタリスク）をつけてリストを展開して渡すのがポイント
    combinations = list(itertools.product(rep_list, *factor_levels_list))
    
    # データフレーム化（列名：反復 + 各要因名）
    columns = ["反復"] + factor_names
    df_template = pd.DataFrame(combinations, columns=columns)
    
    # 圃場での調査を想定し、反復 > 要因1 > 要因2... の順でソート
    df_template = df_template.sort_values(by=["反復"] + factor_names).reset_index(drop=True)
    
    # 目的変数と備考列を追加
    df_template[target_var] = None
    df_template["備考"] = None
    
    # --- 結果の表示とダウンロード ---
    st.subheader("2. 生成された入力様式")
    
    # 区画数の計算（反復数 × 各要因の水準数）
    total_plots = reps
    for levels in factor_levels_list:
        total_plots *= len(levels)
        
    st.success(f"全 {total_plots} 区画の入力様式が作成されました！")
    
    # 画面上でプレビュー
    st.dataframe(df_template, use_container_width=True)
    
    # CSVダウンロードボタン
    csv = df_template.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 この様式をダウンロード (CSV)",
        data=csv,
        file_name="field_survey_template.csv",
        mime="text/csv",
    )