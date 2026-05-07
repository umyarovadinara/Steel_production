import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Дашборд производства стали", layout="wide")

st.title("📊 Аналитика производства стали")

# 1. СЛОВАРЬ ПЕРЕИМЕНОВАНИЯ (Маппинг)
# Слева — как в файле, Справа — как будет на дашборде
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
    # Загружаем твой реальный файл
    df = pd.read_excel('steel_production_data.xlsx')
    
    # ПЕРЕИМЕНОВАНИЕ: меняем заголовки на красивые
    df = df.rename(columns=column_mapping)
    
    # Преобразование даты (используем уже новое название)
    if 'Дата создания' in df.columns:
        df['Дата создания'] = pd.to_datetime(df['Дата создания'])
    
    return df

try:
    df = load_data()
    
    # Список новых названий для отображения на главной (только те, что мы переименовали)
    main_display_columns = list(column_mapping.values())

    # 2. БОКОВАЯ ПАНЕЛЬ (ФИЛЬТРЫ)
    st.sidebar.header("Настройки фильтров")
    
    # Фильтр по дате (используем новое название)
    if 'Дата создания' in df.columns:
        min_date = df['Дата создания'].min().date()
        max_date = df['Дата создания'].max().date()
        date_range = st.sidebar.date_input("Выберите период", [min_date, max_date])
    else:
        st.error("Колонка 'Дата создания' не найдена в файле!")
        st.stop()

    # Фильтр по марке
    all_marks = df['Марка'].unique()
    selected_marks = st.sidebar.multiselect("Фильтр по маркам стали", all_marks, default=all_marks)

    # Применяем фильтры
    mask = (df['Дата создания'].dt.date >= date_range[0]) & \
           (df['Дата создания'].dt.date <= date_range[1]) & \
           (df['Марка'].isin(selected_marks))
    
    filtered_df = df.loc[mask]

    # 3. ГЛАВНЫЕ ПОКАЗАТЕЛИ (ВИЗУАЛ)
    col1, col2 = st.columns(2)
    with col1:
        # Используем новое название 'Масса, тн'
        total_mass = filtered_df['Масса, тн'].sum()
        st.metric("Итого произведено (тн)", f"{total_mass:,.2f}")
    with col2:
        st.metric("Всего записей в выборке", len(filtered_df))

    # График динамики
    st.subheader("Динамика выпуска продукции")
    line_data = filtered_df.groupby('Дата создания')['Масса, тн'].sum().reset_index()
    fig = px.line(line_data, x='Дата создания', y='Масса, тн', markers=True, 
                 labels={'Масса, тн': 'Вес (тонны)', 'Дата создания': 'День'})
    st.plotly_chart(fig, use_container_width=True)

    # 4. РАБОТА С ТАБЛИЦАМИ
    st.divider()
    tab1, tab2 = st.tabs(["📋 Основные показатели", "🔍 Все данные (включая второстепенные)"])

    with tab1:
        st.write("Только важные поля с новыми названиями:")
        # Показываем только колонки из нашего списка переименования
        st.dataframe(filtered_df[main_display_columns], use_container_width=True)

    with tab2:
        st.write("Полная таблица (здесь все поля, включая те, что не вошли в список важных):")
        st.dataframe(filtered_df, use_container_width=True)

except Exception as e:
    st.error(f"Ошибка: {e}")
    st.info("Убедитесь, что названия колонок в Excel точно такие: Масса (учет.), Дата создания, Марка, Вид ЕМ, Длина, Ширина, Толщ.")
