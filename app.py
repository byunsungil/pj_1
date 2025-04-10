# streamlit_car_news_app.py

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import requests
from bs4 import BeautifulSoup
from collections import Counter
from wordcloud import WordCloud
import re
from datetime import datetime, timedelta
import matplotlib.font_manager as fm
import plotly.express as px
import os

# ---------------------- 설정 ----------------------
st.set_page_config(page_title="법인차량 관련 FAQ 시스템", layout="wide")

# ---------------------- 데이터 로드 ----------------------
@st.cache_data
def load_car_data():
    cars = pd.read_csv("자동차등록현황보고_자동차등록대수현황 시도별 (201101 ~ 202502).csv", encoding="cp949", skiprows=5)
    cars.columns = ['일시', '시도명', '시군구', '승용_관용', '승용_자가용', '승용_영업용', '승용_계',
                    '승합_관용', '승합_자가용', '승합_영업용', '승합_계',
                    '화물_관용', '화물_자가용', '화물_영업용', '화물_계',
                    '특수_관용', '특수_자가용', '특수_영업용', '특수_계',
                    '총계_관용', '총계_자가용', '총계_영업용', '총계']
    cars = cars[(cars['시도명'] == '서울') & (cars['시군구'] == '강남구')]
    cars['일시'] = pd.to_datetime(cars['일시'])
    cars['승용_영업용'] = cars['승용_영업용'].str.replace(',', '').astype(int)
    return cars[['일시', '승용_영업용']]

# ---------------------- 차량 분석 ----------------------
def car_analysis():
    st.title("🚗 강남구 영업 차량 등록 통계")

    df = load_car_data()
    df_recent = df[-24:].reset_index(drop=True)

    avg_2023 = df_recent[:12]['승용_영업용'].mean()
    avg_2024 = df_recent[12:]['승용_영업용'].mean()

    st.write("2023-2024 영업용 승용차 변동 추이")
    fig = px.scatter(df_recent, x="일시", y="승용_영업용", title="월별 등록수 변화")
  

    st.plotly_chart(fig)

    col1, col2, col3 = st.columns(3)

    col1.metric("🚗 2023 평균 등록수", f"{avg_2023:.0f}대")
    col2.metric("🚗 2024 평균 등록수", f"{avg_2024:.0f}대")
    diff = avg_2024 - avg_2023
    rate = (diff / avg_2023) * 100
    col3.metric("📉 전년 대비 변화", f"{diff:+.0f}대", f"{rate:+.1f}%")


# ---------------------- 뉴스 워드클라우드 ----------------------
def news_wordcloud():
    st.title("📰 네이버 뉴스 워드클라우드")
    query = st.text_input("검색어를 입력하세요", value="법인자동차 제도")

    if st.button("분석 시작") and query:
        articles = []
        for page in range(1, 6):
            start = (page - 1) * 10 + 1
            url = f"https://search.naver.com/search.naver?where=news&query={query}&start={start}"
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(res.text, "html.parser")
            news_items = soup.select("ul.list_news li.bx")
            for item in news_items:
                title_tag = item.select_one("a.news_tit")
                if title_tag:
                    articles.append(title_tag["title"])

        if articles:
            text = " ".join(articles)
            text = re.sub("[^가-힣\s]", "", text)
            words = [w for w in text.split() if len(w) > 1]
            freq = Counter(words)

            wc = WordCloud(font_path="NanumGothicCoding.ttf", width=800, height=400, background_color="white")
            wc.generate_from_frequencies(freq)

            fig, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wc, interpolation="bilinear")
            ax.axis("off")
            st.pyplot(fig)
        else:
            st.warning("기사를 찾을 수 없습니다.")

# ---------------------- 뉴스 키워드 분석 ----------------------
def keyword_analysis():
    st.title("📊 뉴스 키워드 분석")
    QUERY = st.text_input("검색어를 입력하세요", value="법인차 제도")
    FILE_PATH = f"news_data/{QUERY}_news.csv"
    os.makedirs("news_data", exist_ok=True)

    def parse_date(text):
        if '일 전' in text:
            return datetime.now() - timedelta(days=int(text.replace('일 전', '').strip()))
        elif '시간 전' in text:
            return datetime.now()
        elif '.' in text:
            try:
                return datetime.strptime(text.strip(), "%Y.%m.%d.")
            except:
                return None
        return None

    def crawl_news(pages=10):
        data = []
        for page in range(1, pages + 1):
            start = (page - 1) * 10 + 1
            url = f'https://search.naver.com/search.naver?where=news&query={QUERY}&start={start}'
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(res.text, 'html.parser')
            articles = soup.select('div.news_wrap.api_ani_send')

            for article in articles:
                title_tag = article.select_one('a.news_tit')
                if not title_tag: continue
                title = title_tag['title']
                link = title_tag['href']
                press_tag = article.select_one('a.info.press')
                press = press_tag.text.strip() if press_tag else 'Unknown'
                date_tag = article.select('span.info')[-1]
                raw_date = date_tag.text.strip() if date_tag else ''
                parsed = parse_date(raw_date)
                date = parsed.strftime('%Y-%m-%d') if parsed else datetime.today().strftime('%Y-%m-%d')
                summary_tag = article.select_one('div.dsc_wrap')
                summary = summary_tag.text.strip() if summary_tag else ''
                data.append({ 'title': title, 'press': press, 'date': date, 'summary': summary, 'url': link })
        return pd.DataFrame(data)

    def save_news(df_new):
        if os.path.exists(FILE_PATH):
            df_old = pd.read_csv(FILE_PATH)
            df_all = pd.concat([df_old, df_new]).drop_duplicates(subset=['url'])
        else:
            df_all = df_new
        df_all.to_csv(FILE_PATH, index=False, encoding='utf-8-sig')
        return df_all

    def keyword_visualization(df):
        font_path = './fonts/NanumGothicCoding.ttf'
        font_name = fm.FontProperties(fname=font_path).get_name() if os.path.exists(font_path) else 'Malgun Gothic'
        plt.rcParams['font.family'] = font_name
        plt.rcParams['axes.unicode_minus'] = False

        all_words = []
        for summary in df['summary'].dropna():
            words = re.findall(r"[가-힣]{2,}", summary)
            all_words.extend(words)

        counter = Counter(all_words)
        common_keywords = counter.most_common(20)
        if not common_keywords:
            st.warning("키워드를 추출할 수 없습니다.")
            return

        words, counts = zip(*common_keywords)
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(x=list(counts), y=list(words), ax=ax)
        ax.set_title('뉴스 키워드 분석')
        st.pyplot(fig)

    pages = st.number_input("크롤링할 뉴스 페이지 수 입력 (10개 단위)", min_value=1, max_value=10, step=1)
    if st.button("최신 뉴스 크롤링하기"):
        df_today = crawl_news(pages)
        df_all = save_news(df_today)
        st.success(f"{len(df_today)}건 수집 완료! 전체 {len(df_all)}건 저장됨.")
    elif os.path.exists(FILE_PATH):
        df_all = pd.read_csv(FILE_PATH)
    else:
        st.warning("저장된 뉴스 데이터가 없습니다. 먼저 크롤링을 실행하세요.")
        return

    st.subheader("최근 수집된 뉴스 미리보기")
    st.dataframe(df_all[['date', 'title', 'press', 'summary']])

    st.subheader("키워드 분석 결과")
    keyword_visualization(df_all)

# ---------------------- 뉴스 요약 -------------------------
    def truncate(text, limit=100):
        return text if len(text) <= limit else text[:limit] + "..."

    if st.toggle("📰 뉴스 제목 + 링크 + 요약 보기"):
        st.subheader("📰 요약된 뉴스 리스트")
        for i, row in df_all.iterrows():
            title = row['title']
            link = row['url']
            summary = row['summary']
            st.markdown(f"### 🔗 [{title}]({link})")
            st.write(f"📝 요약: {truncate(summary, 100)}")
            st.markdown("---")

# ---------------------- FAQ -------------------------------
def FAQ():
    st.title("자주 묻는 질문")

# ---------------------- 페이지 라우팅 ----------------------
page = st.sidebar.selectbox("메뉴 선택", ["차량 분석", "뉴스 워드클라우드", "뉴스 키워드 분석","자주 묻는 질문"])

if page == "차량 분석":
    car_analysis()
elif page == "뉴스 워드클라우드":
    news_wordcloud()
elif page == "뉴스 키워드 분석":
    keyword_analysis()
elif page == "자주 묻는 질문":
    FAQ()

