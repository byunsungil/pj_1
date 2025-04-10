import seaborn as sns
import requests
from bs4 import BeautifulSoup
from collections import Counter
import re
from datetime import datetime, timedelta
import matplotlib.font_manager as fm


# 뉴스 정보 메뉴
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