
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Дашборд производства стали", layout="wide")

st.title("📊 Аналитика производства стали")

# Загрузка данных
@st.cache_data
def load_data():
    df = pd.read_excel('steel_production_data.xlsx')
    df['Дата обработки'] = pd.to_datetime(df['Дата обработки'])
    return df

try:
    df = load_data()

    # БОКОВАЯ ПАНЕЛЬ (ФИЛЬТРЫ)
    st.sidebar.header("Фильтры")
    
    # Фильтр по дате
    min_date = df['Дата обработки'].min().date()
    max_date = df['Дата обработки'].max().date()
    date_range = st.sidebar.date_input("Период", [min_date, max_date])

    # Фильтр по марке
    selected_marks = st.sidebar.multiselect("Выберите марку", df['Марка'].unique(), default=df['Марка'].unique())

    # Фильтрация данных
    mask = (df['Дата обработки'].dt.date >= date_range[0]) & \
           (df['Дата обработки'].dt.date <= date_range[1]) & \
           (df['Марка'].isin(selected_marks))
    
    filtered_df = df.loc[mask]

    # ГЛАВНЫЕ ПОКАЗАТЕЛИ
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Общая масса (т)", f"{filtered_df['Масса (учет.)'].sum():,.2f}")
    with col2:
        st.metric("Кол-во записей", len(filtered_df))
    with col3:
        st.metric("Ср. толщина (мм)", round(filtered_df['Толщина'].mean(), 1))

    # ГРАФИКИ
    st.subheader("Динамика производства")
    line_chart = px.line(filtered_df.groupby('Дата обработки')['Масса (учет.)'].sum().reset_index(), 
                         x='Дата обработки', y='Масса (учет.)', 
                         title="Выпуск продукции по дням")
    st.plotly_chart(line_chart, use_container_width=True)

    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("Распределение по маркам")
        pie_chart = px.pie(filtered_df, values='Масса (учет.)', names='Марка')
        st.plotly_chart(pie_chart, use_container_width=True)

    with col_right:
        st.subheader("Виды ЕМ")
        bar_chart = px.bar(filtered_df.groupby('Вид ЕМ')['Масса (учет.)'].sum().reset_index(), 
                           x='Вид ЕМ', y='Масса (учет.)', color='Вид ЕМ')
        st.plotly_chart(bar_chart, use_container_width=True)

    # ТАБЛИЦА
    with st.expander("Посмотреть исходные данные"):
        st.write(filtered_df)

except Exception as e:
    st.error(f"Ошибка загрузки данных: {e}")
    st.info("Пожалуйста, убедитесь, что файл 'steel_production_data.xlsx' находится в той же папке.")
