# 뉴스 정보, 검색어 입력, 요약, 링크
# 페이지 선택부분 수정 필요요

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

    # 뉴스 출력 및 페이지 선택 함수
    def show_news(df):
        st.subheader("📰 뉴스 제목 및 요약 보기")
        num_per_page = 10
        total_items = len(df)
        total_pages = (total_items - 1) // num_per_page + 1

        # 세션 상태에 현재 페이지 번호 저장 (초기값 1)
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 1

        # 표시할 뉴스 데이터 슬라이싱
        start_idx = (st.session_state.current_page - 1) * num_per_page
        end_idx = start_idx + num_per_page
        df_page = df.iloc[start_idx:end_idx]

        def truncate(text, limit=100):
            return text if len(text) <= limit else text[:limit] + "..."
        
        # 뉴스 항목 출력
        for i, row in df_page.iterrows():
            st.markdown(f"### 🔗 [{row['title']}]({row['url']})")
            st.write(f"📝 요약: {truncate(row['summary'], 100)}")
            st.markdown("---")
        
        # 하단에 깔끔한 라디오 버튼으로 페이지 번호 선택 (가로 정렬)
        selected_page = st.radio("페이지 선택", list(range(1, total_pages + 1)),
                                 index=st.session_state.current_page - 1,
                                 horizontal=True)
        st.session_state.current_page = selected_page

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
        show_news(df_all)
    else:
        st.warning("뉴스 데이터가 존재하지 않습니다.")