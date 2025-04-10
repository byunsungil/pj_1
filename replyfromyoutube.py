import streamlit as st
import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# CSV 파일 불러오기 (파일명에 괄호가 있으면 오류 가능 → 파일명 변경 권장)
comments_df = pd.read_csv("comments.csv", header=None)
comments = comments_df[0].dropna().astype(str)

st.title("🟢 연두색 번호판 관련 유튜브 댓글 분석")

# 총 댓글 수 표시
st.write(f"총 댓글 수: {len(comments)}개")

# 🔎 키워드 검색
search_keyword = st.text_input("댓글 내 키워드 검색", "")
if search_keyword:
    filtered = comments[comments.str.contains(search_keyword, case=False)]
    st.write(f"🔍 '{search_keyword}'가 포함된 댓글 수: {len(filtered)}개")
    st.dataframe(filtered)

# 📊 워드클라우드 생성
st.subheader("주요 키워드 워드클라우드")

all_text = " ".join(comments.tolist())

# ✅ font_path 제거 → 시스템 기본 폰트 사용
from wordcloud import WordCloud
import matplotlib.pyplot as plt

text = "슈퍼카 법인차 법인세 세금절감 절세 사업자 벤츠 포르쉐 연두색번호판"
wc = WordCloud(font_path="/System/Library/Fonts/Supplemental/AppleGothic.ttf", width=800, height=400).generate(text)

plt.figure(figsize=(10, 5))
plt.imshow(wc, interpolation='bilinear')
plt.axis("off")
plt.show()


plt.imshow(wc, interpolation="bilinear")
plt.axis("off")
st.pyplot(plt)

