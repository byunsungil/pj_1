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
import pymysql
import plotly.graph_objects as go


# 한글 폰트 설정
matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# 페이지 기본 설정
st.set_page_config(page_title="법인차량 대시보드", layout="wide")

# 사이드바 메뉴 구성
menu = st.sidebar.radio("📋 메뉴 선택", ["수입 법인차량 등록","차량 등록 현황","차량 정보 필터", "데이터 시각화", "뉴스 정보" ,"FAQ"])

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

@st.cache_data
def load_data_car_reg():
    return pd.read_csv("car_reg.csv")
#==========================================================================================================#

if menu == "차량 등록 현황":
    st.title("🚗 법인 차량 등록 통계")

    df = load_data_car_reg()
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
if menu == "수입 법인차량 등록":
    st.title("🚘 등록현황")
    
    # CSV 파일 읽기
    car_reg = load_data_car_reg()
    
    # 2023년과 2024년 컬럼 선택
    # (첫번째 열 '차종별' 제외하고, '23'로 시작하는 컬럼들은 2023년, '24'로 시작하는 컬럼들은 2024년 데이터로 가정)
    # 2023년 데이터 평균 계산
    columns_2023 = [col for col in car_reg.columns if col.startswith("23")]
    car_reg['2023_avg'] = car_reg[columns_2023].mean(axis=1)
    
    # 만약 2024년 평균이나 증감 컬럼도 필요한 경우에는 먼저 계산 후
    columns_2024 = [col for col in car_reg.columns if col.startswith("24")]
    car_reg['2024_avg'] = car_reg[columns_2024].mean(axis=1)
    car_reg['증감'] = car_reg['2024_avg'] - car_reg['2023_avg']
    
    # 이후 정수형으로 변환
    car_reg['2023_avg'] = car_reg['2023_avg'].round().astype(int)
    car_reg['2024_avg'] = car_reg['2024_avg'].round().astype(int)
    car_reg['증감'] = car_reg['증감'].round().astype(int)


    
    # 계산된 결과 미리보기 (원하는 경우)
    st.dataframe(car_reg[['차종별', '2023_avg', '2024_avg', '증감']])
    
    # Plotly를 사용하여 그룹형 바 차트 생성
    fig = go.Figure(data=[
        go.Bar(name="2023년 평균 등록수", x=car_reg['차종별'], y=car_reg['2023_avg']),
        go.Bar(name="2024년 평균 등록수", x=car_reg['차종별'], y=car_reg['2024_avg']),
        go.Bar(name="전년 대비 증감", x=car_reg['차종별'], y=car_reg['증감'])
    ])
    
    fig.update_layout(
        barmode='group',
        title="차종별 등록수 평균 및 전년 대비 증감",
        xaxis_title="차종별",
        yaxis_title="등록수"
    )
    
    # Streamlit에서 그래프 출력
    st.plotly_chart(fig)


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
        }).reset_index()

        # Plotly 구현
        fig = px.bar(
            group_df,
            x='제조사',
            y=['2024년_판매량', '2025년_판매량'],
            barmode='group',
            title='제조사별 판매량 비교',
            labels={
                'value': '판매량',
                'variable': '년도',
                '제조사': '제조사'
            }
        )

        # 가격 선그래프 추가
        fig2 = px.line(
            group_df,
            x='제조사',
            y=['2024년_가격', '2025년_가격'],
            markers=True,
            title='제조사별 평균 가격 비교',
            labels={
                'value': '가격(만원)',
                'variable': '년도',
                '제조사': '제조사'
            }
        )

        fig.update_layout(
            yaxis_title='판\n매\n량',
            xaxis_title='제조사'
        )
        st.plotly_chart(fig, use_container_width=True)

        fig2.update_layout(
            yaxis_title='가\n격',
            xaxis_title='제조사'
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("비교할 제조사를 선택해주세요.")    

#===========================================================================================================#

# 뉴스 정보, 검색어 입력, 요약, 링크
# 페이지 선택부분 수정 필요

elif menu == "뉴스 정보":
    st.title("📰 법인 관련 뉴스")

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

    def show_news_paginated(df):
        st.subheader("📰 뉴스 제목 및 요약 보기 (페이지별)")
        def truncate(text, limit=100):
            return text if len(text) <= limit else text[:limit] + "..."

        page_size = 10
        total_pages = (len(df) - 1) // page_size + 1
        page = st.number_input("페이지 선택", min_value=1, max_value=total_pages, step=1)
        start = (page - 1) * page_size
        end = start + page_size

        for i, row in df.iloc[start:end].iterrows():
            st.markdown(f"### 🔗 [{row['title']}]({row['url']})")
            st.write(f"📝 요약: {truncate(row['summary'], 100)}")
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

        show_news_paginated(df_all)
    else:
        st.warning("뉴스 데이터가 존재하지 않습니다.")



#===========================================================================================================#
elif menu == "FAQ":
    st.title("❓ 자주 묻는 질문 (FAQ)")

    # MySQL에서 FAQ 데이터 불러오기
    def load_data_from_mysql(host, user, password, database, table_name="faq"):
        conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            db=database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT question, answer FROM {table_name}")
            result = cursor.fetchall()
        conn.close()
        return pd.DataFrame(result)

    # Streamlit FAQ 페이지 실행 함수
    def render_faq():
        st.write("아래 질문을 클릭하면 답변을 확인할 수 있어요.")

        host = "127.0.0.1"
        user = "runnnn"
        password = "1111"
        database = "FAQ"
        table_name = "faq"

        try:
            df = load_data_from_mysql(host, user, password, database, table_name)
        except Exception as e:
            st.error(f"데이터를 불러오는 중 오류 발생: {e}")
            return

        query = st.text_input("🔍 질문 검색", "")
        if query:
            df = df[df["question"].str.contains(query, case=False, na=False)]

        for _, row in df.iterrows():
            with st.expander(f"❓ {row['question']}"):
                st.write(row['answer'])

    # ✅ 여기가 핵심! 메뉴에 진입했을 때 바로 실행
    render_faq()





#============================================================================================================#

