# Goodreads-Scraper

# 📚 Goodreads: Análisis de Libros y de Reviews

Este proyecto realiza scraping de Goodreads para analizar los libros más leídos por país y período de tiempo. Permite visualizar tendencias literarias, géneros predominantes, años de publicación, longitud de los libros, y realizar análisis de sentimiento sobre las reseñas más populares.

---

## 🚀 Características principales

- 🧭 Selección interactiva de país y periodo (últimos 12 meses, este mes o esta semana)
- 📊 Visualización de estadísticas de libros (géneros, fechas, páginas)
- 💬 Análisis de sentimiento con clasificación de reseñas
- ☁️ Nube de palabras basada en reseñas
- 📈 Gráficos dinámicos con Plotly
- 🌐 Scraping automatizado desde Goodreads

---

## 🧰 Tecnologías utilizadas

- Python 3.12
- [Streamlit](https://streamlit.io/)
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)
- [Pandas](https://pandas.pydata.org/)
- [Matplotlib](https://matplotlib.org/)
- [Plotly](https://plotly.com/python/)
- [WordCloud](https://amueller.github.io/word_cloud/)
- [VADER Sentiment Analysis](https://github.com/cjhutto/vaderSentiment)

---

## 📦 Instalación

1. Clona el repositorio:

   ```bash
   git clone https://github.com/tu-usuario/goodreads-analisis.git
   cd goodreads-analisis
   ```

2. (Opcional) Crea y activa un entorno virtual:

   ```bash
   python -m venv venv
   source venv/bin/activate  # o venv\Scripts\activate en Windows
   ```

3. Instala las dependencias necesarias:

   ```bash
   pip install -r requirements.txt
   ```

---

## 🧪 Uso

1. Ejecuta la aplicación en Streamlit:

   ```bash
   streamlit run nombre_del_script.py
   ```

2. Usa la barra lateral para:

   * Elegir país y duración.
   * Scrapear los datos directamente desde Goodreads.
   * Subir tu propio archivo CSV si ya tienes datos.

3. Visualiza:

   * Gráficos de géneros, fechas, páginas y palabras clave.
   * Opiniones destacadas y su análisis de sentimiento.
   * Nube de palabras generada a partir de reseñas reales.

---

## 📊 Visualizaciones incluidas

* 🔟 Top 10 géneros más populares (barras + polar)
* 📚 Libros publicados por año
* 🕰️ Evolución de géneros por año
* 📐 Relación entre páginas y géneros
* 💬 Palabras más mencionadas en reseñas
* ☁️ Nube de palabras de las reseñas
* 📈 Distribución de opiniones (muy positivo → muy negativo)
* 🧠 Opinión general por libro (color destacado)

---

## ✅ Requisitos

Para ejecutar el proyecto asegúrate de tener instalados los siguientes paquetes:

```
streamlit
pandas
beautifulsoup4
matplotlib
plotly
wordcloud
vaderSentiment
requests
```

Guárdalos en un archivo `requirements.txt` para instalación rápida.

---

## 📌 Notas

* Los datos provienen de Goodreads y pueden cambiar según disponibilidad pública.
* El scraping está limitado a los 50 libros más leídos por país y periodo.
* El análisis de sentimiento es automático y puede no ser 100% preciso.

---

## 🖋️ Autoría

Proyecto desarrollado como práctica de análisis de datos con Python y Streamlit.
