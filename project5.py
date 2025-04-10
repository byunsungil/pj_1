
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import os
import plotly.express as px
import numpy as np
import seaborn as sns
import requests
from bs4 import BeautifulSoup
from collections import Counter
import re
from datetime import datetime, timedelta
import matplotlib.font_manager as fm


# 한글 폰트 설정
matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# 페이지 기본 설정
st.set_page_config(page_title="법인차량 대시보드", layout="wide")

# 사이드바 메뉴 구성
menu = st.sidebar.radio("📋 메뉴 선택", ["차량 등록 현황","차량 정보 필터", "데이터 시각화", "뉴스 정보" ,"자주 묻는 질문"])

# 데이터 불러오기
@st.cache_data
def load_data():
    return pd.read_csv("corporate_cars.csv")


# 가격을 '1억 5431만원' 형태로 포맷하는 함수
def format_price(value):
    value = int(value)
    if value >= 10000:
        return f"{value // 10000}억 {value % 10000}만원"
    else:
        return f"{value}만원"

df = load_data()

# 단위 조정
df['배기량'] = df['배기량'].str.replace("L", "").str.replace("이하", "000cc 이하").str.replace("이상", "000cc 이상").str.replace("~", "000cc~").str.replace(" ", "")
df['배기량'] = df['배기량'].str.replace("1.6", "1600").str.replace("2.0", "2000").str.replace("1.6", "1600").str.replace("2.0", "2000")
df['배기량'] = df['배기량'].str.replace("000cc", "cc")

# (임시) 차량 등록 데이터
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

#==========================================================================================================#

if menu == "차량 등록 현황":
    st.title("🚗 법인 차량 등록 통계")

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



#==========================================================================================================#

if menu == "차량 정보 필터":
    st.title("🚘 법인차량 조건별 정보 확인")

    col1, col2, col3 = st.columns(3)

    with col1:
        selected_prices = st.multiselect("💰 가격대", df['가격대'].unique())

    with col2:
        selected_engines = st.multiselect("🔧 배기량", df['배기량'].unique())

    with col3:
        selected_brands = st.multiselect("🏢 제조사", df['제조사'].unique())

    col4, col5 = st.columns(2)

    with col4:
        selected_fuels = st.multiselect("⛽ 연료", df['연료'].unique())

    with col5:
        selected_types = st.multiselect("🚗 차량 유형", df['유형'].unique())

    filtered_df = df.copy()
    if selected_prices:
        filtered_df = filtered_df[filtered_df['가격대'].isin(selected_prices)]
    if selected_engines:
        filtered_df = filtered_df[filtered_df['배기량'].isin(selected_engines)]
    if selected_brands:
        filtered_df = filtered_df[filtered_df['제조사'].isin(selected_brands)]
    if selected_fuels:
        filtered_df = filtered_df[filtered_df['연료'].isin(selected_fuels)]
    if selected_types:
        filtered_df = filtered_df[filtered_df['유형'].isin(selected_types)]

    # 가격 단위 붙이기
    df_display = filtered_df.copy()
    df_display['2024년_가격'] = df_display['2024년_가격'].apply(format_price)
    df_display['2025년_가격'] = df_display['2025년_가격'].apply(format_price)

    st.subheader("🔍 필터링된 차량 목록")
    st.dataframe(df_display)

#===========================================================================================================#

elif menu == "데이터 시각화":
    st.title("📊 법인차량 데이터 시각화")

    chart_brands = st.multiselect("📌 제조사 선택", df['제조사'].unique())

    if chart_brands:
        chart_df = df[df['제조사'].isin(chart_brands)]

        group_df = chart_df.groupby('제조사').agg({
            '2024년_판매량': 'sum',
            '2025년_판매량': 'sum',
            '2024년_가격': 'mean',
            '2025년_가격': 'mean'
        })

        fig, ax1 = plt.subplots(figsize=(10, 6))

        x = range(len(group_df.index))
        bar1 = ax1.bar(x, group_df['2024년_판매량'], width=0.35, label='2024년 판매량', color='#4e79a7aa', zorder=3)
        bar2 = ax1.bar([p + 0.35 for p in x], group_df['2025년_판매량'], width=0.35, label='2025년 판매량', color='#f28e2b88', zorder=3)
        ax1.set_ylabel("판\n매\n량", rotation=0, labelpad=30, fontsize=12)
        ax1.set_xlabel("제조사", fontsize=12)
        ax1.set_xticks([p + 0.175 for p in x])
        ax1.set_xticklabels(group_df.index)
        ax1.grid(False)
        ax1.set_axisbelow(True)

        ax2 = ax1.twinx()
        ax2.plot([p + 0.175 for p in x], group_df['2024년_가격'], marker='o', color='#59a14f', label='2024년 가격 (단위 : 만원)', zorder=4)
        ax2.plot([p + 0.175 for p in x], group_df['2025년_가격'], marker='o', color='#e15759', label='2025년 가격 (단위 : 만원)', zorder=4)
        ax2.set_ylabel("평\n균\n가\n격", rotation=0, labelpad=50, fontsize=12)
        ax2.grid(False)

        plt.title("제조사별 판매량 및 평균 가격 비교", fontsize=14)
        ax1.legend(loc='lower left', bbox_to_anchor=(-0.02, -0.25), fontsize=9, frameon=True)
        ax2.legend(loc='lower right', bbox_to_anchor=(1.02, -0.25), fontsize=9, frameon=True)

        st.pyplot(fig)
    else:
        st.info("비교할 제조사를 선택해주세요.")

#===========================================================================================================#

# 키워드 분석과 뉴스 요약 표시를 확실히 작동하게 수정한 뉴스 정보 섹션

elif menu == "뉴스 정보":
    st.title("📰 법인 관련 뉴스")
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

    def crawl_news(query, pages=1):
        data = []
        for page in range(1, pages + 1):
            start = (page - 1) * 10 + 1
            url = f'https://search.naver.com/search.naver?where=news&query={query}&start={start}'
            res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(res.text, 'html.parser')
            articles = soup.select('div.news_wrap.api_ani_send')

            for article in articles:
                title_tag = article.select_one('a.news_tit')
                if not title_tag:
                    continue
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
                data.append({'title': title, 'press': press, 'date': date, 'summary': summary, 'url': link})
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

    def show_news(df):
        st.subheader("📰 뉴스 제목 및 요약 보기")
        def truncate(text, limit=100):
            return text if len(text) <= limit else text[:limit] + "..."

        if st.checkbox("뉴스 제목 + 링크 + 요약 보기", value=True):
            for i, row in df.iterrows():
                title = row['title']
                link = row['url']
                summary = row['summary']
                st.markdown(f"### 🔗 [{title}]({link})")
                st.write(f"📝 요약: {truncate(summary, 100)}")
                st.markdown("---")

    pages = st.number_input("크롤링할 뉴스 페이지 수 입력 (10개 단위)", min_value=1, max_value=10, step=1)

    if st.button("최신 뉴스 크롤링하기"):
        df_today = crawl_news(QUERY, pages)
        df_all = save_news(df_today)
        st.success(f"{len(df_today)}건 수집 완료! 전체 {len(df_all)}건 저장됨.")
    elif os.path.exists(FILE_PATH):
        df_all = pd.read_csv(FILE_PATH)
    else:
        st.warning("저장된 뉴스 데이터가 없습니다. 먼저 크롤링을 실행하세요.")
        df_all = pd.DataFrame()

    if not df_all.empty:
        st.subheader("최근 수집된 뉴스 미리보기")
        st.dataframe(df_all[['date', 'title', 'press', 'summary']])

        st.subheader("키워드 분석 결과")
        keyword_visualization(df_all)

        show_news(df_all)
    else:
        st.warning("뉴스 데이터가 존재하지 않습니다.")


#============================================================================================================#
elif menu == "자주 묻는 질문":
    st.title("❓ 자주 묻는 질문 (FAQ)")
    with st.expander("Q1. 법인차량을 개인적으로 사용해도 되나요?"):
        st.write("A. 업무 외의 개인적 사용은 세무상 문제가 발생할 수 있습니다. 규정을 반드시 확인하세요.")
    with st.expander("Q2. 법인차량 구매 시 세금 혜택이 있나요?"):
        st.write("A. 네, 부가가치세 환급 등 다양한 혜택이 존재합니다.")
    with st.expander("Q3. 전기차도 법인차로 등록 가능한가요?"):
        st.write("A. 네, 오히려 친환경 혜택으로 인해 많이 권장되고 있습니다.")
