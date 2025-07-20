import base64
import streamlit as st
from utils.fusionbrain_api import FusionBrainAPI
import psycopg2

# Конфигурация страницы
st.set_page_config(
    page_title="Генератор изображений",
    page_icon="🎨",
    layout="wide"
)

# Функция для подключения к PostgreSQL
def get_db_connection():
    return psycopg2.connect(
        dbname=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
        host=st.secrets["DB_HOST"],
        port=st.secrets["DB_PORT"]
    )

# Функция для получения данных из базы данных
def get_data_from_db():
    data = {
        "styles": [],
        "genres": [],
        "lighting": [],
        "techniques": [],
        "colors": []
    }
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Запрос для стилей (с разными уровнями описания)
        cursor.execute("SELECT name, short_description, medium_description, long_description FROM styles")
        data["styles"] = cursor.fetchall()
        
        # Запрос для жанров
        cursor.execute("SELECT name, description FROM genres")
        data["genres"] = cursor.fetchall()
        
        # Запрос для освещения
        cursor.execute("SELECT name, description FROM lighting")
        data["lighting"] = cursor.fetchall()
        
        # Запрос для техник
        cursor.execute("SELECT name, description FROM techniques")
        data["techniques"] = cursor.fetchall()
        
        # Запрос для цветов
        cursor.execute("SELECT name, description FROM colors")
        data["colors"] = cursor.fetchall()
        
        cursor.close()
        conn.close()
    except Exception as e:
        st.error(f"Ошибка при загрузке данных: {str(e)}")
    
    return data

# Инициализация состояния
def init_session_state():
    if 'db_data' not in st.session_state:
        st.session_state.db_data = get_data_from_db()
    
    # Инициализация выбора параметров
    categories = ["style", "genre", "lighting", "technique", "color"]
    for category in categories:
        key = f"selected_{category}"
        if key not in st.session_state:
            st.session_state[key] = None
    
    # Инициализация уровня детализации (на русском)
    if 'detail_level' not in st.session_state:
        st.session_state.detail_level = "средний"  # По умолчанию средний
    
    # Инициализация промта
    if 'generated_prompt' not in st.session_state:
        st.session_state.generated_prompt = None
    
    # Инициализация изображения
    if 'image_data' not in st.session_state:
        st.session_state.image_data = None
    if 'generated_image' not in st.session_state:
        st.session_state.generated_image = False

# Категории интерфейса
categories = ["Направление", "Жанр", "Освещение", "Техника", "Цвета"]
category_keys = ["style", "genre", "lighting", "technique", "color"]
display_categories = ["Направление (стиль)", "Жанр", "Освещение", "Техника", "Цвета"]

# Заголовок приложения
st.title("🎨 Генератор изображений с помощью AI")
st.subheader("Создайте уникальное изображение по вашему описанию")

# Инициализация состояния
init_session_state()

# Основное поле для промта
main_prompt = st.text_area(
    "Опишите основную идею изображения:",
    placeholder="Например: Девушка в платье из цветов, ...",
    height=150,
    key="main_prompt"
)

# Секция выбора параметров
st.header("Настройка параметров изображения")

# Вкладки с параметрами
tabs = st.tabs(display_categories)

# Отображение параметров для каждой категории
for i, tab in enumerate(tabs):
    with tab:
        category_key = category_keys[i]
        # Сопоставление ключей категорий с ключами в данных
        data_key_map = {
            "style": "styles",
            "genre": "genres",
            "lighting": "lighting",
            "technique": "techniques",
            "color": "colors"
        }
        data_key = data_key_map[category_key]
        data = st.session_state.db_data[data_key]
        
        if data:
            # Создаем список названий для радиокнопок
            options = [item[0] for item in data]
            
            # Получаем текущее значение из session_state
            current_selection = st.session_state[f"selected_{category_key}"]
            
            # Определяем индекс для выбора в радио-кнопках
            index = None
            if current_selection and current_selection in options:
                index = options.index(current_selection)
            
            # Создаем радио-кнопки с опцией "Не выбрано"
            radio_options = ["Не выбрано"] + options
            selected_index = st.radio(
                f"Выберите {display_categories[i].lower()}:", 
                radio_options,
                index=0 if current_selection is None else index + 1,
                key=f"radio_{category_key}_{i}"
            )
            
            # Обновляем состояние выбора
            if selected_index == "Не выбрано":
                st.session_state[f"selected_{category_key}"] = None
            else:
                st.session_state[f"selected_{category_key}"] = selected_index
            
            # Для стиля добавляем выбор уровня детализации
            if category_key == "style" and st.session_state.selected_style:
                # Находим выбранный стиль в данных
                style_data = next(item for item in data if item[0] == st.session_state.selected_style)
                
                # Определяем индекс для уровня детализации
                detail_options = ["Низкий", "Средний", "Высокий"]
                
                # Получаем текущий уровень детализации на русском
                current_detail = st.session_state.detail_level.capitalize()
                
                # Проверяем наличие текущего значения в списке
                try:
                    detail_index = detail_options.index(current_detail)
                except ValueError:
                    # Если значение не найдено, используем средний по умолчанию
                    detail_index = 1
                    st.session_state.detail_level = "средний"
                
                # Выбор уровня детализации
                detail_level = st.radio(
                    "Уровень детализации стиля:",
                    detail_options,
                    index=detail_index,
                    key=f"detail_level_{i}"
                )
                st.session_state.detail_level = detail_level.lower()
                
                # Показать описание в зависимости от уровня детализации
                if detail_level == "Низкий":
                    description = style_data[1]  # short_description
                elif detail_level == "Средний":
                    description = style_data[2]  # medium_description
                else:
                    description = style_data[3]  # long_description
                
            
            # Для остальных категорий показываем обычное описание
            elif st.session_state[f"selected_{category_key}"]:
                # Находим описание для выбранного параметра
                description = next(item[1] for item in data if item[0] == st.session_state[f"selected_{category_key}"])
        else:
            st.warning(f"Для категории '{display_categories[i]}' не найдены данные")

# Инициализация API
@st.cache_resource
def init_fusionbrain_api():
    return FusionBrainAPI(
        url='https://api-key.fusionbrain.ai/',
        api_key=st.secrets["FUSIONBRAIN_API_KEY"],
        secret_key=st.secrets["FUSIONBRAIN_SECRET_KEY"]
    )

# Функция для создания промта
def create_prompt(base, db_data):
    base = base.strip().capitalize()
    fragments = []
    
    # Жанр (если выбран)
    if st.session_state.selected_genre:
        genre_desc = next(
            item[1] for item in db_data["genres"] 
            if item[0] == st.session_state.selected_genre
        )
        fragments.append(genre_desc)
    
    # Пользовательский ввод (основа)
    fragments.append(base)
    
    # Направление (стиль) с нужным уровнем детализации
    if st.session_state.selected_style:
        style_data = next(
            item for item in db_data["styles"] 
            if item[0] == st.session_state.selected_style
        )
        
        if st.session_state.detail_level == "низкий":
            fragments.append(style_data[1] + ".")  # short_description
        elif st.session_state.detail_level == "средний":
            fragments.append(style_data[2] + ".")  # medium_description
        else:  # высокий
            fragments.append(style_data[3] + ".")  # long_description
    
    # Техника (если выбрана)
    if st.session_state.selected_technique:
        technique_desc = next(
            item[1] for item in db_data["techniques"] 
            if item[0] == st.session_state.selected_technique
        )
        fragments.append(technique_desc + ".")
    
    # Освещение (если выбрано)
    if st.session_state.selected_lighting:
        lighting_desc = next(
            item[1] for item in db_data["lighting"] 
            if item[0] == st.session_state.selected_lighting
        )
        fragments.append(lighting_desc)
    
    # Цвета (если выбраны)
    if st.session_state.selected_color:
        color_desc = next(
            item[1] for item in db_data["colors"] 
            if item[0] == st.session_state.selected_color
        )
        fragments.append(color_desc + ".")
    
    return " ".join(fragments)

# Контейнер для отображения промта
prompt_container = st.empty()

# Кнопки генерации
col1, col2 = st.columns(2)

with col1:
    # Кнопка генерации промта
    if st.button("Сгенерировать промт", type="secondary", use_container_width=True):
        if not main_prompt.strip():
            st.warning("Пожалуйста, введите описание для генерации")
        else:
            full_prompt = create_prompt(
                base=main_prompt,
                db_data=st.session_state.db_data
            )
            st.session_state.generated_prompt = full_prompt

# Проверяем, есть ли сохраненный промт
if st.session_state.get("generated_prompt"):
    prompt_container.subheader("Финальное описание для генерации:")
    prompt_container.info(f'"{st.session_state.generated_prompt}"')

with col2:
    # Кнопка генерации изображения
    if st.button("Сгенерировать изображение", type="primary", use_container_width=True):
        if not st.session_state.get("generated_prompt"):
            st.warning("Сначала создайте промт с помощью кнопки 'Сгенерировать промт'")
        else:
            full_prompt = st.session_state.generated_prompt
            with st.spinner("Инициализация генерации..."):
                try:
                    api = init_fusionbrain_api()
                    pipeline_id = api.get_pipeline()
                    with st.spinner("Генерация изображения (это может занять 1-2 минуты)..."):
                        uuid = api.generate(
                            prompt=full_prompt,
                            pipeline=pipeline_id,
                            images=1,
                            width=1024,
                            height=1024
                        )
                        images_base64 = api.check_generation(
                            request_id=uuid,
                            attempts=30,
                            delay=3
                        )
                    if images_base64:
                        st.session_state.image_data = base64.b64decode(images_base64[0])
                        st.session_state.generated_image = True
                        st.success("Изображение успешно сгенерировано!")
                    else:
                        st.error("Не удалось сгенерировать изображение. Попробуйте снова.")
                except Exception as e:
                    st.error(f"Ошибка генерации: {str(e)}")

# Отображение результата генерации
if st.session_state.get("generated_image") and st.session_state.get("image_data"):
    st.subheader("Результат генерации:")
    st.image(
        st.session_state.image_data, 
        caption="Сгенерированное изображение", 
        use_container_width=True
    )
    st.download_button(
        label="Скачать изображение",
        data=st.session_state.image_data,
        file_name="generated_image.png",
        mime="image/png"
    )
    st.caption(f"Сгенерировано по описанию: '{st.session_state.generated_prompt}'")
