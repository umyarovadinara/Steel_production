import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Steel Production Analytics", layout="wide")

st.title("📊 Аналитика производства стали")

# 1. МАППИНГ И ЗАГРУЗКА
column_mapping = {
    'Масса (учет.)': 'Масса, тн',
    'Дата создания': 'Дата создания',
    'Марка': 'Марка',
    'Вид ЕМ': 'Вид единицы учета',
    'Длина': 'Длина, мм',
    'Ширина': 'Ширина, мм',
    'Толщ.': 'Толщина, мм'
}

@st.cache_data
def load_data():
    df = pd.read_excel('steel_production_data.xlsx')
    df = df.rename(columns=column_mapping)
    if 'Дата создания' in df.columns:
        df['Дата создания'] = pd.to_datetime(df['Дата создания'])
    return df

try:
    df = load_data()
    main_display_columns = [v for k, v in column_mapping.items() if v in df.columns]

    # 2. ФИЛЬТРЫ
    st.sidebar.header("🎛 Настройки анализа")
    
    date_range = st.sidebar.date_input("Период", [df['Дата создания'].min(), df['Дата создания'].max()])
    
    all_marks = sorted(df['Марка'].unique())
    selected_marks = st.sidebar.multiselect("Марки стали", all_marks, default=all_marks[:3])

    # Фильтрация
    mask = (df['Дата создания'].dt.date >= date_range[0]) & (df['Дата создания'].dt.date <= date_range[1]) & (df['Марка'].isin(selected_marks))
    filtered_df = df.loc[mask]

    # 3. ВЕРХНИЙ УРОВЕНЬ (KPI)
    st.subheader("📈 Ключевые показатели")
    kpi1, kpi2, kpi3 = st.columns(3)
    
    total_mass = filtered_df['Масса, тн'].sum()
    avg_weight = filtered_df['Масса, тн'].mean()
    
    kpi1.metric("Общий выпуск, тн", f"{total_mass:,.1f}")
    kpi2.metric("Средний вес ед., тн", f"{avg_weight:,.2f}")
    kpi3.metric("Средняя толщина, мм", f"{filtered_df['Толщина, мм'].mean():,.1f}")

    # 4. ДИНАМИКА С ШАГОМ 5 ДНЕЙ (Разрез марок)
    st.divider()
    st.subheader("📅 Динамика производства (шаг 5 дней)")
    
    # Группировка по 5 дней для плавности
    resampled_df = filtered_df.set_index('Дата создания').groupby([pd.Grouper(freq='5D'), 'Марка'])['Масса, тн'].sum().reset_index()
    
    fig_line = px.line(resampled_df, x='Дата создания', y='Масса, тн', color='Марка', 
                       markers=True, line_shape="spline", title="Выпуск в разрезе марок")
    st.plotly_chart(fig_line, use_container_width=True)

    # 5. СТРУКТУРНЫЙ АНАЛИЗ (MECE)
    st.divider()
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📦 Структура по видам продукции")
        fig_pie = px.sunburst(filtered_df, path=['Вид единицы учета', 'Марка'], values='Масса, тн',
                              color='Масса, тн', color_continuous_scale='Blues')
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_right:
        st.subheader("📏 Распределение геометрии")
        # Гистограмма толщины для технолога
        fig_hist = px.histogram(filtered_df, x="Толщина, мм", y="Масса, тн", color="Вид единицы учета",
                               marginal="box", title="Масса продукции по толщине")
        st.plotly_chart(fig_hist, use_container_width=True)

    # 6. ДЕТАЛЬНЫЙ ПРОСМОТР
    st.divider()
    with st.expander("📄 Таблица данных (Детальный просмотр)"):
        st.dataframe(filtered_df[main_display_columns], use_container_width=True)

except Exception as e:
    st.error(f"Ошибка визуализации: {e}")
