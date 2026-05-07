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
    # Загружаем файл (убедитесь, что имя файла совпадает с вашим на GitHub)
    df = pd.read_excel('steel_production_data.xlsx')
    df = df.rename(columns=column_mapping)
    
    if 'Дата создания' in df.columns:
        df['Дата создания'] = pd.to_datetime(df['Дата создания'])
        # Создаем колонку для фильтра месяцев
        df['Месяц_Фильтр'] = df['Дата создания'].dt.strftime('%Y-%m')
    
    # 1) Приравниваем "Сляб" и "СЛЯБ" (Нормализация регистра)
    if 'Вид единицы учета' in df.columns:
        df['Вид единицы учета'] = df['Вид единицы учета'].astype(str).str.strip().str.capitalize()
    
    # Группировка для матрицы (округляем для формирования сетки)
    df['Ширина_Группа'] = (df['Ширина, мм'] // 50 * 50).astype(int)
    df['Толщина_Группа'] = df['Толщина, мм'].round(1)
    
    return df

try:
    df = load_data()

    # 2. ФИЛЬТРЫ
    st.sidebar.header("Фильтры")
    available_months = sorted(df['Месяц_Фильтр'].unique(), reverse=True)
    selected_months = st.sidebar.multiselect(
        "Выберите месяцы", 
        options=available_months, 
        default=[available_months[0]]
    )

    if not selected_months:
        st.warning("Пожалуйста, выберите хотя бы один месяц.")
        st.stop()

    # Фильтрация данных по выбранным месяцам
    filtered_df = df[df['Месяц_Фильтр'].isin(selected_months)]

    # 3. КЛЮЧЕВЫЕ ПОКАЗАТЕЛИ
    st.subheader("Ключевые показатели")
    k1, k2, k3 = st.columns(3)
    
    k1.metric("Общий выпуск, тн", f"{filtered_df['Масса, тн'].sum():,.1f}")
    k2.metric("Средний вес ед., тн", f"{filtered_df['Масса, тн'].mean():,.2f}")
    k3.metric("Средняя толщина, мм", f"{filtered_df['Толщина, мм'].mean():,.1f}")

    # 4. СТРУКТУРНЫЕ РАЗРЕЗЫ (Круг и Динамика)
    st.divider()
    col_pie, col_line = st.columns([1, 1])

    with col_pie:
        st.subheader("Структура по видам")
        pie_data = filtered_df.groupby('Вид единицы учета')['Масса, тн'].sum().reset_index()
        fig_pie = px.pie(pie_data, names='Вид единицы учета', values='Масса, тн', hole=0.4)
        fig_pie.update_traces(textinfo='percent+value', hovertemplate="%{label}<br>%{value:,.1f} тн")
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_line:
        st.subheader("Динамика производства")
        line_data = filtered_df.set_index('Дата создания').resample('5D')['Масса, тн'].sum().reset_index()
        fig_line = px.line(line_data, x='Дата создания', y='Масса, тн', markers=True)
        fig_line.update_layout(showlegend=False, xaxis_title=None, yaxis_title="Масса, тн")
        st.plotly_chart(fig_line, use_container_width=True)

    # 5. МАТРИЦА СОРТАМЕНТА (ТАБЛИЧНАЯ ФОРМА)
    st.divider()
    st.subheader("Распределение по сортаментам (Масса, тн)")
    
    # Создаем сводную таблицу: Ширина в строках, Толщина в столбцах
    matrix_table = filtered_df.pivot_table(
        index='Ширина_Группа', 
        columns='Толщина_Группа', 
        values='Масса, тн', 
        aggfunc='sum'
    ).fillna(0)

    # Сортируем индексы и колонки по возрастанию
    matrix_table = matrix_table.sort_index(axis=0).sort_index(axis=1)

    # Применяем визуальное форматирование (цветовой градиент)
    styled_matrix = matrix_table.style.background_gradient(cmap='Greens', axis=None) \
                                      .format("{:.1f}")

    # Вывод таблицы
    st.dataframe(styled_matrix, use_container_width=True)

    # 6. ДЕТАЛИ
    with st.expander("Посмотреть исходные данные"):
        display_cols = [v for k, v in column_mapping.items() if v in filtered_df.columns]
        st.dataframe(filtered_df[display_cols], use_container_width=True)

except Exception as e:
    st.error(f"Произошла ошибка: {e}")
