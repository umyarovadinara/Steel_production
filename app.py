import streamlit as st
import pandas as pd
import plotly.express as px

# Настройка страницы
st.set_page_config(page_title="Производство S700MC", layout="wide")

st.title("Производство S700MC")

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
    # Убедись, что имя файла совпадает с твоим на GitHub
    df = pd.read_excel('steel_production_data.xlsx')
    df = df.rename(columns=column_mapping)
    
    if 'Дата создания' in df.columns:
        df['Дата создания'] = pd.to_datetime(df['Дата создания'])
        # Формат для фильтра: "2024-01 Январь"
        df['Месяц_Фильтр'] = df['Дата создания'].dt.strftime('%Y-%m')
    
    # Группировка для матрицы (округляем для читаемости)
    df['Ширина_Группа'] = (df['Ширина, мм'] // 50 * 50).astype(int)
    df['Толщина_Группа'] = df['Толщина, мм'].round(1)
    
    return df

try:
    df = load_data()

    # 2. БОКОВАЯ ПАНЕЛЬ (Множественный выбор)
    st.sidebar.header("Фильтры")
    
    available_months = sorted(df['Месяц_Фильтр'].unique(), reverse=True)
    selected_months = st.sidebar.multiselect(
        "Выберите месяцы (накопительно)", 
        options=available_months, 
        default=[available_months[0]]
    )

    if not selected_months:
        st.warning("Выберите хотя бы один месяц на боковой панели.")
        st.stop()

    # Фильтрация
    filtered_df = df[df['Месяц_Фильтр'].isin(selected_months)]

    # 3. КЛЮЧЕВЫЕ ПОКАЗАТЕЛИ
    st.subheader("Ключевые показатели")
    k1, k2, k3 = st.columns(3)
    
    with k1:
        st.metric("Общий выпуск, тн", f"{filtered_df['Масса, тн'].sum():,.1f}")
    with k2:
        st.metric("Средний вес ед., тн", f"{filtered_df['Масса, тн'].mean():,.2f}")
    with k3:
        st.metric("Средняя толщина, мм", f"{filtered_df['Толщина, мм'].mean():,.1f}")

    # 4. ДИНАМИКА ПРОИЗВОДСТВА
    st.divider()
    st.subheader("Динамика производства")
    # Группировка по 5 дням
    line_data = filtered_df.set_index('Дата создания').resample('5D')['Масса, тн'].sum().reset_index()
    fig_line = px.line(line_data, x='Дата создания', y='Масса, тн', markers=True)
    fig_line.update_layout(showlegend=False, xaxis_title=None, yaxis_title="Масса, тн")
    st.plotly_chart(fig_line, use_container_width=True)

    # 5. СТРУКТУРНЫЕ РАЗРЕЗЫ
    st.divider()
    c1, c2 = st.columns([1, 2]) # Матрице даем больше места

    with c1:
        st.subheader("Структура по видам")
        pie_data = filtered_df.groupby('Вид единицы учета')['Масса, тн'].sum().reset_index()
        fig_pie = px.pie(pie_data, names='Вид единицы учета', values='Масса, тн',
                         hole=0.4)
        fig_pie.update_traces(textinfo='percent+value', hovertemplate="%{label}<br>%{value:,.1f} тн")
        st.plotly_chart(fig_pie, use_container_width=True)

    with c2:
        st.subheader("Распределение по сортаментам")
        # Создаем матрицу Ширина x Толщина
        matrix = filtered_df.pivot_table(
            index='Ширина_Группа', 
            columns='Толщина_Группа', 
            values='Масса, тн', 
            aggfunc='sum'
        ).fillna(0)
        
        fig_matrix = px.imshow(
            matrix, 
            text_auto='.1f', 
            aspect="auto",
            color_continuous_scale='Greens',
            labels=dict(x="Толщина, мм", y="Ширина, мм", color="Масса, тн")
        )
        st.plotly_chart(fig_matrix, use_container_width=True)

    # 6. ДЕТАЛИ
    with st.expander("Посмотреть исходные данные"):
        st.dataframe(filtered_df.drop(columns=['Месяц_Фильтр', 'Ширина_Группа', 'Толщина_Группа']), use_container_width=True)

except Exception as e:
    st.error(f"Произошла ошибка при обработке данных: {e}")
