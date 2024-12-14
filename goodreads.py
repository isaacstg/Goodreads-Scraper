import streamlit as st
import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import os
import time
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


st.set_page_config(page_title='Estadísticas de Goodreads', layout='wide')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'}
base_url = 'https://www.goodreads.com'

countries = {
    'Todo el mundo': 'all',
    'Estados Unidos': 'US',
    'España': 'ES',
    'Alemania': 'DE',
    'Reino Unido': 'GB',
    'Italia': 'IT',
    'Canadá': 'CA',
    'México': 'MX',
    'Argentina': 'AR',
    'Australia':'AU'
}

def scrape_book_details(book_url):
    book_page_url = base_url + book_url
    response = requests.get(book_page_url, headers=headers)
    time.sleep(1)
    if response.status_code != 200:
        st.error(f"Error al obtener datos: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    genres = [genre.text.strip() for genre in soup.find_all('span', {'class': 'BookPageMetadataSection__genreButton'})]
    pages_info = soup.find('div', {'class': 'FeaturedDetails'})
    pages = None
    publication_date = None
    if pages_info:
        pages_text = pages_info.find('p', {'data-testid': 'pagesFormat'})
        if pages_text:
            pages = int(pages_text.text.strip().split()[0])
        pub_date_text = pages_info.find('p', {'data-testid': 'publicationInfo'})
        if pub_date_text:
            try:
                publication_date = datetime.strptime(pub_date_text.text.replace('First published', '').replace('Published', '').strip(), '%B %d, %Y').strftime('%d-%m-%Y')
            except ValueError:
                publication_date = None
    synopsis = soup.find('span', {'class': 'Formatted'})
    synopsis_text = synopsis.get_text(strip=True) if synopsis else ''
    reviews = []
    reviews_list = soup.find_all('article', {'class': 'ReviewCard'})
    for review in reviews_list:
        rating = review.find('span', {'class': 'RatingStars RatingStars__small'})
        review_rating = None
        if rating:
            review_rating = int(rating['aria-label'].split()[1])
        review_content = review.find('span', {'class': 'Formatted'})
        review_text = review_content.get_text(strip=True) if review_content else ''
        reviews.append({'rating': review_rating, 'content': review_text})
    return {
        'genres': genres,
        'pages': pages,
        'publication_date': publication_date,
        'synopsis': synopsis_text,
        'reviews': reviews
    }

def scrape_and_save(country='all', duration='y', filename=None):
    try:
        if filename is None:
            filename = f'{country}_most_read_books_{duration}.csv'
            
        url = f'https://www.goodreads.com/book/most_read?category=all&country={country}&duration={duration}'
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return
        soup = BeautifulSoup(response.text, 'html.parser')
        books_container = soup.find('table', {'class': 'tableList'})
        if not books_container:
            st.error('No se encontraron datos en Goodreads para los parámetros especificados.')
            return None
        
        data = []
        for book in books_container.find_all('tr', {'itemtype': 'http://schema.org/Book'}):
            try:
                ranking = int(book.find('td', {'class': 'number'}).text)
                title = book.find('a', {'class': 'bookTitle'}).get_text()
                author = book.find('a', {'class': 'authorName'}).get_text()
                avg_rating = float(book.find('span', {'class': 'minirating'}).get_text(strip=True).split(' ')[0])
                total_rating = int(book.find('span', {'class': 'minirating'}).get_text(strip=True).split(' ')[4].replace(',', ''))
                readers = int(book.find('span', {'class': 'greyText statistic'}).get_text(strip=True).split()[0].replace(',', ''))
                href = book.find('a', {'class': 'bookTitle'})['href']
                book_details = scrape_book_details(href)
                data.append({
                    'Ranking': ranking,
                    'Título': title,
                    'Autor': author,
                    'Calificación promedio': avg_rating,
                    'Total de calificaciones': total_rating,
                    'Número de lectores': readers,
                    'Genres': ', '.join(book_details.get('genres', [])),
                    'Páginas': book_details.get('pages', ''),
                    'Fecha de publicación': book_details.get('publication_date', ''),
                    'Synopsis': book_details.get('synopsis', ''),
                    'Reviews': book_details.get('reviews', [])
                })
                
            except AttributeError:
                continue
        if data:
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False)
            return filename
            
    except Exception as e:
        st.error(f"Error inesperado: {e}")
        

def load_data(filename):
    return pd.read_csv(filename)

def show_main_insights(df):
    st.header('Top 50 Libros Leídos')
    if df is not None:
        df_resumen = df.drop(columns=['Reviews','Synopsis','Genres'])
        st.dataframe(df_resumen, hide_index=True)
        # Subheader para géneros más populares
        st.subheader('Análisis de Libros')
        all_genres = ', '.join(df['Genres'].dropna()[df['Genres'].apply(lambda x: isinstance(x, str))])
        genre_counts = Counter(all_genres.split(', '))
        genres_df = pd.DataFrame(genre_counts.items(), columns=['Género', 'Popularidad']).sort_values(by='Popularidad', ascending=False)
        top_genres = genres_df.head(10)  # Seleccionar los 10 géneros más populares
       
       # Gráfico de barras con Plotly
        fig_genres = px.bar(top_genres, 
                            x='Género', 
                            y='Popularidad', 
                            text='Popularidad', 
                            title='Top 10 Géneros Más Populares',  
                            color='Popularidad', 
                            color_continuous_scale='Viridis')
        
        fig_genres.update_traces(textposition='outside')
        fig_genres.update_layout(xaxis_title='Género', yaxis_title='Popularidad', showlegend=False)
        st.plotly_chart(fig_genres)
        
        # Trace de la visualización
        trace = go.Scatterpolar(
            r=top_genres['Popularidad'],  # Popularidad como el valor radial
            theta=top_genres['Género'],   # Géneros como las categorías del eje angular
            fill='toself',  # Llenar el área del gráfico
            name='Top Géneros',  # Nombre para la leyenda
            marker=dict(color='cyan'),  # Color de los puntos
        )
        
        # Layout del gráfico
        layout = go.Layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,  # Hacer visible el eje radial
                    range=[0, top_genres['Popularidad'].max() * 1.1],  # Ajustar el rango radial
                ),
                angularaxis=dict(
                    tickmode='array',  # Asegurarse de que se muestren todos los géneros
                    tickvals=top_genres['Género'],  # Etiquetas de los géneros
                ),
            ),
            showlegend=False,  # Ocultar la leyenda si no es necesaria
            template='plotly_dark',  # Estilo oscuro
        )
        
        # Crear la figura y mostrar el gráfico
        fig = go.Figure(data=[trace], layout=layout)
        
        # Mostrar el gráfico en Streamlit
        st.plotly_chart(fig)
        
        if 'Fecha de publicación' in df.columns:
        # Asegurarse de que las fechas están en formato correcto y extraer el año
            df['Año de publicación'] = pd.to_datetime(df['Fecha de publicación'], errors='coerce').dt.year
            
            # Limpiar y separar géneros en listas
            df['Genres'] = df['Genres'].apply(lambda x: [genre.strip() for genre in str(x).split(',')])  # Separar géneros y quitar espacios extra
            
            # Tomar solo los tres Géneros de cada libro
            df['Género'] = df['Genres'].apply(lambda x: x[:2] if isinstance(x, list) else [])
            
            # Explode para separar los géneros en filas distintas
            df_exploded = df.explode('Género')
            
            # Preparar datos para el gráfico
            if 'Año de publicación' in df_exploded.columns and 'Género' in df_exploded.columns:
                # Contar la cantidad de libros por año y primer género
                genre_count_by_year = df_exploded.groupby(['Año de publicación', 'Género']).size().reset_index(name='Cantidad')
                
                # Crear el gráfico de barras apiladas
                fig_genre_count_by_year = px.bar(
                    genre_count_by_year,
                    x='Año de publicación',
                    y='Cantidad',
                    color='Género',
                    title='Por Año de Publicación',
                    labels={'Año de publicación': 'Año', 'Cantidad': 'Número de Libros'},
                    barmode='stack',
                    template='plotly_white'
                )
                
                all_years = sorted(df['Año de publicación'].dropna().unique())
                fig_genre_count_by_year.update_layout(
                    xaxis=dict(
                        tickmode='array',
                        tickvals=all_years,  # Asegura que se muestren todos los años
                        ticktext=[int(year) for year in all_years]  # Etiquetas de los años
                    )
            )
                # Mostrar el gráfico
                st.plotly_chart(fig_genre_count_by_year)


            if 'Fecha de publicación' in df.columns:
                # Asegurarse de que las fechas están en formato correcto y extraer el año
                df['Año de publicación'] = pd.to_datetime(df['Fecha de publicación'], errors='coerce').dt.year
                
                # Contar la cantidad de libros por año
                books_by_year = df['Año de publicación'].value_counts().reset_index()
                books_by_year.columns = ['Año de publicación', 'Cantidad de Libros']
                books_by_year = books_by_year.sort_values(by='Año de publicación', ascending=True)
                books_by_year = books_by_year[books_by_year['Cantidad de Libros'] > 0]

                # Crear el gráfico de barras para la cantidad de libros por año
                fig_books_by_year = px.bar(
                    books_by_year,
                    x='Año de publicación',
                    y='Cantidad de Libros',
                    title = 'Libros Publicados por Año',
                    labels={'Año de publicación': 'Año', 'Cantidad de Libros': 'Número de Libros'},
                    color='Cantidad de Libros',
                    color_continuous_scale='Viridis',
                    template='plotly_white'
                )
            
                # Mostrar el gráfico
                st.plotly_chart(fig_books_by_year)

            if 'Páginas' in df.columns and 'Genres' in df.columns:
               
                # Tomar solo el primer género de cada libro y asegurarse de que está limpio
                df['Primer Género'] = df['Genres'].apply(lambda x: x[0].replace("['", "").replace("'", "").strip() if isinstance(x, list) else None)
                
                # Filtrar para evitar nulos en 'Páginas' o 'Primer Género'
                df_filtered = df.dropna(subset=['Páginas', 'Primer Género'])
                
                # Crear el gráfico de dispersión
                fig_pages_genres = px.scatter(
                    df_filtered,
                    x='Páginas',
                    y='Primer Género',
                    color='Primer Género',
                    title='Relación entre Número de Páginas y Géneros',
                    labels={'Páginas': 'Páginas', 'Primer Género': 'Género'},
                    color_continuous_scale='Viridis',  # O cualquier otra escala de colores
                    template='plotly_white',
                    hover_data=['Título']  # Mostrar el título del libro al pasar el mouse
                )
                
                # Mostrar el gráfico
                st.plotly_chart(fig_pages_genres)
                
    else: 
        st.rerun()

   
    

def analyze_book_reviews(df):
    if df is not None:

        st.header('Análisis de Reseñas por Libro')
        book_title = st.selectbox('Selecciona un libro', df['Título'].unique())
        selected_book = df[df['Título'] == book_title].iloc[0]
        st.subheader('Detalles:')
        st.write(f"**Autor:** {selected_book['Autor']}")
        st.write(f"**Calificación promedio:** {selected_book['Calificación promedio']}")
        st.write(f"**Total de calificaciones:** {int(selected_book['Total de calificaciones'])}")
        st.write(f"**Géneros:** {', '.join(selected_book['Genres']).replace('[', '').replace(']', '')}")
        st.write(f"**Número de lectores:** {selected_book['Número de lectores']}")
        reviews = eval(selected_book['Reviews'])
        review_texts = [review['content'] for review in reviews if review['content']]
        sentiments = analyze_sentiment(reviews)
        all_words = ' '.join(review_texts).lower().split()
        
        # Remove stop words
        stop_words = {
        'and', 'if', 'the', 'i', 'to', 'of', 'a', 'in', 'for', 'on', 'is', 
        'it', 'that', 'this', 'with', 'as', 'are', 'was', 'at', 'by', 
        'an', 'be', 'not', 'or', 'but', 'from', 'my', 'you', 'your', 
        'he', 'she', 'they', 'we', 'all', 'so', 'what', 'there', 'when', 
        'where', 'who', 'which', 'how', 'just', 'like', 'about', 'more', 
        'than', 'up', 'out', 'some', 'other', 'no', 'yes', 'do', 'does', 
        'did', 'will', 'would', 'could', 'should', 'y', 'de', 'la', 
        'que', 'el', 'en', 'los', 'se', 'del', 'por', 'un', 'una', 
        'con', 'no', 'es', 'para', 'su', 'al', 'como', 'más', 'o', 
        'pero', 'fue', 'este', 'entre', 'también', 'hasta', 'hay', 
        'todo', 'esta', 'ser', 'son', 'me', 'si', 'sobre', 'mi', 
        'te', 'ya', 'muy', 'donde', 'quien', 'cuando', 'qué', 'cómo', 
        'así', 'solo', 'uno', 'dos', 'tres', 'cuatro', 'cinco', 
        'seis', 'siete', 'ocho', 'nueve', 'diez', 'otro', 'mismo', 
        'tanto', 'poco', 'mucho', 'cada', 'algunos', 'ninguna', 
        'varios', 'entre', 'tras', 'hacia', 'desde', 'durante', 
        'antes', 'después', 'porque', 'aunque', 'mientras', 'según', 
        'tal', 'cual', 'donde', 'cuando', 'por qué', 'para que', 
        'a pesar de', 'en vez de', 'en cuanto a', 'a través de', 
        '-', '.', ',', 'ha', 'han', 'las', 'le', 'lo', 'ni', 'tan', 
        'unos', 'una', 'un', 'libro', 'bastante', 'leer', 'book', 
        'it.', 'one', 'know', 'say', 'see', 'im', 'also', 'after', 
        'before', 'between', 'during', 'while', 'such', 'these', 
        'those', 'each', 'few', 'many', 'much', 'most', 'some', 
        'any', 'none', 'all', 'whole', 'part', 'half', 'each', 'every', 
        'either', 'neither', 'both', 'few', 'many', 'much', 'most', 
        'some', 'any', 'none', 'all', 'whole', 'part', 'half', 'each', 
        'every','can', 'have', 'it\'s', 'her', 'him', 'they', 'them', 'he', 
        'she' ,'she\'s', 'he\'s', 'read','reading', 'had', 'has','because',
        'didn\'t', 'his', 'were', 'been', 'get', 'really', 'never', 'can\'t',
        'don\'t','s', 'into'}
        
        filtered_words = [word for word in all_words if word not in stop_words]
        
        word_counts = Counter(filtered_words)
    
        # Crear un DataFrame con las palabras más comunes
        most_common_words = pd.DataFrame(word_counts.most_common(20), columns=['Palabra', 'Frecuencia'])
        
        # Ordenar el DataFrame en orden descendente por 'Frecuencia'
        most_common_words = most_common_words.sort_values(by='Frecuencia', ascending=False)
        
        # Crear el gráfico de barras con Plotly
        fig = px.bar(most_common_words, 
                     x='Palabra', 
                     y='Frecuencia', 
                     title='Palabras Más Frecuentes en las Reseñas',
                     labels={'Palabra': 'Palabra', 'Frecuencia': 'Frecuencia'},
                     color='Frecuencia', 
                     color_continuous_scale='Viridis')
        
        # Mostrar el gráfico en Streamlit
        st.plotly_chart(fig)
    
        # Mostrar la nube de palabras
        st.subheader('Palabras Destacadas de las Reseñas')
        wordcloud = WordCloud(width=800, height=400, background_color='black', colormap='autumn', contour_color='black', stopwords=stop_words).generate(' '.join(filtered_words))
        plt.figure(figsize=(30, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        st.pyplot(plt)
        
        st.subheader('Reseñas Populares (Top 30)')

    # Seleccionar la reseña a mostrar
        if reviews:
        # Crear las opciones para el selectbox
            options = [f"📖 Reseña #{i + 1}" for i in range(len(reviews))]
        
            # Mostrar el selectbox con las opciones visuales
            review_selection = st.selectbox(
                'Selecciona una reseña',
                options
            )
        
            # Ajustar la selección, ya que selectbox usa índices base 0
            review_index = options.index(review_selection)  # Obtener el índice de la reseña seleccionada
            selected_review = reviews[review_index]
            sentiment = sentiments[review_index]
        
            # Mostrar la reseña seleccionada
            if selected_review['rating']:
                st.write(f"**Rating:** {'★' * selected_review['rating']}")
            else:
                st.write('**Sin calificación: Pendiente de lectura**')
                
            st.write(f"**Análisis de opinión de acuerdo al texto (puede no ser preciso):** {sentiment}")
            with st.expander("**Ver reseña**"):
                st.write(selected_review['content'])
        else:
            st.write("No hay reseñas disponibles para este libro.")
        
        sentiment_counts = Counter(sentiments)
        
        # Crear un DataFrame para la distribución de sentimientos
        sentiment_df = pd.DataFrame(sentiment_counts.items(), columns=['Sentimiento', 'Cantidad'])
        
        # Ordenar los sentimientos en el orden deseado
        ordered_sentiments = ['Muy positivo', 'Positivo', 'Neutral', 'Negativo', 'Muy negativo']
        sentiment_df['Sentimiento'] = pd.Categorical(sentiment_df['Sentimiento'], categories=ordered_sentiments, ordered=True)
        
        # Ordenar el DataFrame por la columna 'Sentimiento' de acuerdo al orden
        sentiment_df = sentiment_df.sort_values('Sentimiento')
    
        # Crear un gráfico de barras con Plotly
        fig = px.bar(sentiment_df, 
                     x='Sentimiento', 
                     y='Cantidad', 
                     title='Tipos de Opiniones en las Reseñas',
                     labels={'Sentimiento': 'Opiniones', 'Cantidad': 'Cantidad de Reseñas'},
                     color='Sentimiento', 
                     color_discrete_map={
                         'Muy positivo': 'green', 
                         'Positivo': 'lightgreen', 
                         'Neutral': 'gray', 
                         'Negativo': 'orange', 
                         'Muy negativo': 'red'
                     })
        
        # Mostrar el gráfico en Streamlit
        st.plotly_chart(fig)
        
        color_map={
            'Muy positivo': 'green', 
            'Positivo': 'lightgreen', 
            'Neutral': 'gray', 
            'Negativo': 'orange', 
            'Muy negativo': 'red'
        }
        sentiment_general = sentiment_counts.most_common(1)[0][0]
        sentiment_color = color_map[sentiment_general]
    
        st.markdown(
                f"""
                <div style="background-color: {sentiment_color}; color: black; padding: 10px; border-radius: 5px; text-align: center; font-size: 18px;">
                    Opinion general de "{book_title}": <b>{sentiment_general}</b>
                </div>
                """, 
                unsafe_allow_html=True
                )    
    else:
        st.rerun()
        
# Función para analizar el sentimiento de las reseñas
def analyze_sentiment(reviews):
    analyzer = SentimentIntensityAnalyzer()
    sentiments = []
    for review in reviews:
        score = analyzer.polarity_scores(review['content'])
        if score['compound'] >= 0.7:
            sentiments.append('Muy positivo')
        elif 0.05 <= score['compound'] < 0.7:
            sentiments.append('Positivo')
        elif -0.05 < score['compound'] < 0.05:
            sentiments.append('Neutral')
        elif -0.7 <= score['compound'] <= -0.05:
            sentiments.append('Negativo')
        else:
            sentiments.append('Muy negativo')
    return sentiments

def get_csv_files():
    return [f for f in os.listdir() if f.endswith('.csv')]

# Main Streamlit app
def main():
    st.title('Estadísticas de Goodreads')

    # Lista de archivos CSV en el directorio
    csv_files = get_csv_files()

    # Sidebar para scraping de nuevos datos
    st.sidebar.header('Scraping de Libros')
    country = st.sidebar.selectbox('Selecciona país', list(countries.keys()))

    # Mapeo de duración
    duration_labels = {'y': 'Últimos 12 meses', 'm': 'Este mes', 'w': 'Esta semana'}
    duration_display = list(duration_labels.values())
    selected_duration_label = st.sidebar.selectbox('Selecciona duración', duration_display)
    selected_duration = [key for key, value in duration_labels.items() if value == selected_duration_label][0]

    # Al hacer clic en "Scrapear y Guardar CSV"
    if st.sidebar.button('Scrapear y Guardar CSV'):
        try:
            with st.sidebar:
                with st.spinner('Scrapeando datos, suele tardar alrededor de 2 minutos...'):
                    # Perform the scraping and get the filename
                    new_file_name = scrape_and_save(countries[country], selected_duration)
    
                    if new_file_name:
                        # Update the list of CSV files and check if the file exists
                        csv_files = get_csv_files()
                        if new_file_name in csv_files:
                            selected_file = new_file_name
                        else:
                            selected_file = None
    
                        st.success(f'¡Scraping completado! Archivo guardado como: {new_file_name}')
                    else:
                        st.error('El scraping no generó ningún archivo válido.')
    
        except Exception as e:
            st.error(f"Error: {str(e)}")


    # Mostrar opciones solo si no hay archivo cargado
    if 'uploaded_file' in st.session_state and st.session_state.uploaded_file is not None:
        uploaded_file = st.session_state.uploaded_file
        st.sidebar.empty()  # Eliminar los componentes del sidebar para mostrar solo el archivo cargado
        
        # Leer el archivo CSV cargado
        df = pd.read_csv(uploaded_file)
        st.session_state.df = df  # Guardar el DataFrame en session_state

        # Mostrar los insights
        show_main_insights(df)
        analyze_book_reviews(df)
    else:
        # Si no hay archivo cargado, mostrar las opciones del sidebar
        st.sidebar.markdown(
        "<div style='color:grey;text-align:center'><br><br> — &nbsp;&nbsp;&nbsp;o también puedes &nbsp;&nbsp;&nbsp; — \n \n<br><br></span>",
        unsafe_allow_html=True
        )
        selected_file = st.sidebar.selectbox('Cargar un archivo CSV', [''] + csv_files)
        uploaded_file = st.sidebar.file_uploader("Subir tu propio archivo CSV", type=["csv"])

        # Verificar si se ha cargado un archivo
        if uploaded_file is not None:
           st.sidebar.empty()  # Eliminar los componentes del sidebar para mostrar solo el archivo cargado
           # Leer el archivo CSV cargado
           df = pd.read_csv(uploaded_file)
           st.session_state.df = df  # Guardar el DataFrame en session_state
           # Mostrar los insights
           show_main_insights(df)
           analyze_book_reviews(df)

        elif selected_file:
            # Si se ha seleccionado un archivo desde la lista
            df = pd.read_csv(selected_file)
            st.session_state.df = df  # Guardar el archivo en session_state
            show_main_insights(df)
            analyze_book_reviews(df)

        elif 'df' in st.session_state:
            # Si hay un archivo almacenado en session_state (como resultado de scraping o selección previa)
            df = st.session_state.df
            show_main_insights(df)
            analyze_book_reviews(df)

        else:
            # Si no se ha seleccionado ni subido ningún archivo
            st.write("Por favor, scrapea los datos o selecciona un archivo CSV desde tu ordenador.")


if __name__ == '__main__':
    main()