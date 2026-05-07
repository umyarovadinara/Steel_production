import streamlit as st
import pandas as pd
import plotly.express as px

# Настройка страницы
st.set_page_config(page_title="Дашборд производства стали", layout="wide")

st.title("📊 Аналитика производства стали")

# 1. СЛОВАРЬ ПЕРЕИМЕНОВАНИЯ (Маппинг)
# ВАЖНО: Слева пишем точь-в-точь как в Excel, справа — как хотим видеть на экране
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
    # Замени 'steel_production_data.xlsx' на имя твоего файла, если оно другое
    df = pd.read_excel('steel_production_data.xlsx')
    
    # Сохраняем копию оригинальных названий для диагностики
    original_cols = df.columns.tolist()
    
    # Переименовываем колонки
    df = df.rename(columns=column_mapping)
    
    # Превращаем дату в нужный формат (используем уже новое название)
    if 'Дата создания' in df.columns:
        df['Дата создания'] = pd.to_datetime(df['Дата создания'])
        
    return df, original_cols

try:
    df, raw_column_names = load_data()
    
    # Проверка на наличие ключевой колонки "Дата создания"
    if 'Дата создания' not in df.columns:
        st.error("❌ Ошибка: Колонка 'Дата создания' не найдена!")
        st.write("### Что видит компьютер в вашем Excel:")
        st.write(raw_column_names) # Выводим список всех колонок из файла
        st.info("""
        **Как исправить:** Сравните список выше с тем, что написано в коде в блоке `column_mapping`. 
        Возможно, в Excel есть лишний пробел, например `'Дата создания '` вместо `'Дата создания'`.
        """)
        st.stop() # Останавливаем выполнение, чтобы не плодить ошибки дальше

    # Список названий для отображения на главной вкладке
    main_display_columns = [v for k, v in column_mapping.items() if v in df.columns]

    # 2. БОКОВАЯ ПАНЕЛЬ (ФИЛЬТРЫ)
    st.sidebar.header("Настройки фильтров")
    
    # Фильтр по дате
    min_date = df['Дата создания'].min().date()
    max_date = df['Дата создания'].max().date()
    date_range = st.sidebar.date_input("Выберите период", [min_date, max_date])

    # Фильтр по марке
    all_marks = df['Марка'].unique()
    selected_marks = st.sidebar.multiselect("Фильтр по маркам стали", all_marks, default=all_marks)

    # Применяем фильтры
    if len(date_range) == 2:
        mask = (df['Дата создания'].dt.date >= date_range[0]) & \
               (df['Дата создания'].dt.date <= date_range[1]) & \
               (df['Марка'].isin(selected_marks))
        filtered_df = df.loc[mask]
    else:
        filtered_df = df # Если дата еще не выбрана полностью

    # 3. ГЛАВНЫЕ ПОКАЗАТЕЛИ
    col1, col2 = st.columns(2)
    with col1:
        total_mass = filtered_df['Масса, тн'].sum()
        st.metric("Итого произведено (тн)", f"{total_mass:,.2f}")
    with col2:
        st.metric("Всего записей", len(filtered_df))

    # График
    st.subheader("Динамика выпуска продукции")
    line_data = filtered_df.groupby('Дата создания')['Масса, тн'].sum().reset_index()
    fig = px.line(line_data, x='Дата создания', y='Масса, тн', markers=True)
    st.plotly_chart(fig, use_container_width=True)

    # 4. ТАБЛИЦЫ
    st.divider()
    tab1, tab2 = st.tabs(["📋 Основные показатели", "🔍 Все данные (скрытые поля)"])

    with tab1:
        st.dataframe(filtered_df[main_display_columns], use_container_width=True)

    with tab2:
        st.dataframe(filtered_df, use_container_width=True)

except Exception as e:
    st.error(f"Произошла критическая ошибка: {e}")
