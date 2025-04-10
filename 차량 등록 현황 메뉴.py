import plotly.express as px # 추가


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

# 차량 등록 현황 메뉴
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
