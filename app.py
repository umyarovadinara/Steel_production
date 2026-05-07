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
    # Загружаем файл
    df = pd.read_excel('steel_production_data.xlsx')
    df = df.rename(columns=column_mapping)
    
    if 'Дата создания' in df.columns:
        df['Дата создания'] = pd.to_datetime(df['Дата создания'])
        df['Месяц_Фильтр'] = df['Дата создания'].dt.strftime('%Y-%m')
    
    if 'Вид единицы учета' in df.columns:
        df['Вид единицы учета'] = df['Вид единицы учета'].astype(str).str.strip().str.capitalize()
    
    # Группировка для матрицы
    df['Ширина_Группа'] = (df['Ширина, мм'] // 50 * 50).astype(int)
    df['Толщина_Группа'] = df['Толщина, мм'].round(1)
    
    return df

try:
    df = load_data()

    # 2. ФИЛЬТРЫ
    st.sidebar.header("Фильтры")
    available_months = sorted(df['Месяц_Фильтр'].unique(), reverse=True)
    selected_months = st.sidebar.multiselect("Выберите месяцы", options=available_months, default=[available_months[0]])

    if not selected_months:
        st.warning("Пожалуйста, выберите хотя бы один месяц.")
        st.stop()

    filtered_df = df[df['Месяц_Фильтр'].isin(selected_months)]

    # 3. КЛЮЧЕВЫЕ ПОКАЗАТЕЛИ (Оставили 2 показателя)
    st.subheader("Ключевые показатели")
    k1, k2 = st.columns(2)
    k1.metric("Общий выпуск, тн", f"{filtered_df['Масса, тн'].sum():,.1f}")
    k2.metric("Средняя толщина, мм", f"{filtered_df['Толщина, мм'].mean():,.1f}")

    # 4. СТРУКТУРНЫЕ РАЗРЕЗЫ
    st.divider()
    c_pie, c_line = st.columns(2)

    with c_pie:
        st.subheader("Структура по видам")
        pie_data = filtered_df.groupby('Вид единицы учета')['Масса, тн'].sum().reset_index()
        fig_pie = px.pie(pie_data, names='Вид единицы учета', values='Масса, тн', hole=0.4)
        fig_pie.update_traces(textinfo='percent+value')
        st.plotly_chart(fig_pie, use_container_width=True)

    with c_line:
        st.subheader("Динамика производства")
        line_data = filtered_df.set_index('Дата создания').resample('5D')['Масса, тн'].sum().reset_index()
        fig_line = px.line(line_data, x='Дата создания', y='Масса, тн', markers=True)
        
        # Единое форматирование дат на оси X
        fig_line.update_xaxes(
            dtick="D5", 
            tickformat="%d.%m.%Y",
            tickangle=-45
        )
        fig_line.update_layout(showlegend=False, yaxis_title="Масса, тн", xaxis_title=None)
        st.plotly_chart(fig_line, use_container_width=True)

    # 5. МАТРИЦА СОРТАМЕНТА
    st.divider()
    st.subheader("Распределение по сортаментам (Масса, тн)")
    
    # Визуальный указатель для толщины
    st.write("← Ширина, мм / **Толщина, мм** →")
    
    matrix = filtered_df.pivot_table(
        index='Ширина_Группа', 
        columns='Толщина_Группа', 
        values='Масса, тн', 
        aggfunc='sum'
    ).fillna(0).sort_index(axis=0).sort_index(axis=1)

    # Применяем форматирование
    styled_matrix = matrix.style.background_gradient(cmap='Greens', axis=None).format("{:.1f}")
    
    st.write(styled_matrix)

except Exception as e:
    st.error(f"Произошла ошибка: {e}")
