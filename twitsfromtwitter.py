import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="트위터 반응 보기", page_icon="🚗", layout="wide")
st.title("🚗 트위터 반응 수집 결과 보기")

csv_file = "tweet_contents.csv"

# CSV 로드
@st.cache_data
def load_data():
    if os.path.exists(csv_file):
        return pd.read_csv(csv_file)
    else:
        return pd.DataFrame(columns=["url", "text"])  # 빈 데이터프레임 반환

df = load_data()

if df.empty:
    st.error("❌ tweet_contents.csv 파일을 찾을 수 없습니다.")
else:
    st.success("✅ CSV 파일 로딩 완료!")

    search_keyword = st.text_input("🔍 키워드로 내용 검색 (예: 탈세, 포르쉐, 부자)")

    if search_keyword:
        filtered = df[df["text"].str.contains(search_keyword, case=False, na=False)]

        if not filtered.empty:
            for _, row in filtered.iterrows():
                st.markdown(f"**📝 트윗 내용**")
                st.write(row["text"])
                st.markdown("---")
        else:
            st.warning("❗ 검색 결과가 없습니다. 다른 키워드를 시도해보세요.")
