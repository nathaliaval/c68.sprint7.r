import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración inicial de la página
st.set_page_config(page_title='Análisis Exploratorio de Datos de Vehículos', layout='wide')

# Nombre del archivo de datos
DATA_PATH = 'vehicles_us.csv'

@st.cache_data
def load_data(path):
    """
    Carga el dataset y realiza el preprocesamiento básico para manejar valores ausentes.
    """
    data = pd.read_csv(path)

    # 1. Imputar 'model_year' con la mediana por 'model'
    data['model_year'] = data.groupby('model')['model_year'].transform(lambda x: x.fillna(x.median()))
    
    # 2. Imputar 'cylinders' con la moda por 'model'
    # Rellenamos con 0 temporalmente para poder usar mode() y luego imputar
    data['cylinders'] = data.groupby('model')['cylinders'].transform(lambda x: x.fillna(x.mode()[0] if not x.mode().empty else x.median()))
    
    # 3. Imputar 'odometer' con la media por 'model_year'
    data['odometer'] = data.groupby('model_year')['odometer'].transform(lambda x: x.fillna(x.mean()))
    
    # 4. Rellenar 'paint_color' y 'is_4wd' con placeholders categóricos
    data['paint_color'].fillna('desconocido', inplace=True)
    data['is_4wd'].fillna(0.0, inplace=True) # 0.0 indica que no es 4WD
    
    # 5. Convertir tipos de datos
    # FIX: Se añade .round(0) antes de la conversión a 'Int64' para asegurar
    # que los valores flotantes imputados se conviertan de forma segura a enteros.
    data['model_year'] = data['model_year'].round(0).astype('Int64')
    data['cylinders'] = data['cylinders'].round(0).astype('Int64')
    data['is_4wd'] = data['is_4wd'].astype(bool) # Convertir a booleano
    
    return data

# Cargar los datos procesados
try:
    data = load_data(DATA_PATH)
except FileNotFoundError:
    st.error(f"Error: El archivo '{DATA_PATH}' no se encontró. Asegúrate de que está en la misma carpeta que app.py.")
    st.stop()


# --- Título y Encabezado ---
st.header('Análisis Exploratorio de Vehículos en Venta 🚗')
st.markdown('Esta aplicación interactiva permite explorar la distribución y las relaciones de las variables del dataset de vehículos.')


# --- Detección de columnas ---
# Columnas numéricas (excluyendo 'days_listed' para el eje X/Y en el scatter plot)
num_cols = data.select_dtypes(include=['int64', 'float64', 'Int64']).columns.tolist()
# Quitar columnas de ID/fecha si existen y 'days_listed' que es resultado
if 'days_listed' in num_cols:
    num_cols.remove('days_listed')
if 'price' in num_cols: # Mover 'price' al inicio para que sea el valor por defecto
    num_cols.remove('price')
    num_cols.insert(0, 'price')

cat_cols = data.select_dtypes(include='object').columns.tolist()
# Incluir 'is_4wd' y 'cylinders' como categorías si se quiere
cat_cols.extend(['is_4wd', 'cylinders'])
if 'model_year' in cat_cols:
    cat_cols.remove('model_year') # 'model_year' se usará como categórica en algunos casos, pero la excluimos de la lista principal de categorías

# Asegurar que tenemos columnas para graficar
if not num_cols:
    st.error('No se encontraron columnas numéricas relevantes para graficar.')
    st.stop()


# --- Sección de Vista Previa de Datos ---
with st.expander('Vista previa de datos (Primeras 50 filas)', expanded=False):
    st.dataframe(data.head(50), use_container_width=True)
    st.caption(f'El dataset cargado tiene {len(data)} filas y {len(data.columns)} columnas.')


# --- Controles de Gráficos ---

st.subheader('Controles de Visualización')
st.divider()

col1, col2 = st.columns(2)

with col1:
    # --- Controles de Histograma ---
    st.markdown('### Histograma')
    col_hist = st.selectbox('Columna para el Histograma', options=num_cols, index=0, key='hist_col_select')
    bins = st.slider('Número de Bins/Barras', 5, 100, 30, key='hist_bins_slider')
    show_hist = st.checkbox('Mostrar Histograma', value=True, key='show_hist_check')

with col2:
    # --- Controles de Dispersión (Scatter Plot) ---
    st.markdown('### Gráfico de Dispersión')
    
    # Asignar valores por defecto para dispersión
    default_x = 'odometer' if 'odometer' in num_cols else num_cols[0]
    default_y = 'price' if 'price' in num_cols else num_cols[0]
    
    x_scatter = st.selectbox('Eje X', options=num_cols, 
                             index=num_cols.index(default_x) if default_x in num_cols else 0, key='scatter_x_select')
    y_scatter = st.selectbox('Eje Y', options=num_cols, 
                             index=num_cols.index(default_y) if default_y in num_cols else 0, key='scatter_y_select')
    
    color_by_options = ['(ninguno)'] + cat_cols
    color_by = st.selectbox('Color (Variable Categórica)', options=color_by_options, key='scatter_color_select')
    show_scatter = st.checkbox('Mostrar Dispersión', value=True, key='show_scatter_check')

st.divider()


# --- Generación y Despliegue de Gráficos ---

# Usamos otra columna para mostrar los gráficos uno al lado del otro
plot_col1, plot_col2 = st.columns(2)

# 1. Histograma
with plot_col1:
    if show_hist and col_hist:
        st.markdown(f'#### Distribución de **{col_hist}**')
        
        # Generar Histograma
        fig_hist = px.histogram(
            data, 
            x=col_hist, 
            nbins=bins, 
            title=f'Histograma de {col_hist.capitalize()}',
            color_discrete_sequence=['#1f77b4'] # Azul de Plotly por defecto
        )
        
        # Personalizar layout
        fig_hist.update_layout(
            xaxis_title=col_hist.capitalize(),
            yaxis_title='Frecuencia',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False),
            bargap=0.05
        )
        
        # Mostrar gráfico
        st.plotly_chart(fig_hist, use_container_width=True)

# 2. Gráfico de Dispersión
with plot_col2:
    if show_scatter and x_scatter and y_scatter:
        st.markdown(f'#### Relación entre **{x_scatter}** y **{y_scatter}**')

        # Determinar si se usa color
        if color_by == '(ninguno)':
            color_param = None
            title_suffix = ''
        else:
            color_param = color_by
            title_suffix = f' por {color_by.capitalize()}'

        # Generar Gráfico de Dispersión
        fig_scatter = px.scatter(
            data, 
            x=x_scatter, 
            y=y_scatter, 
            color=color_param,
            title=f'Gráfico de Dispersión: {y_scatter.capitalize()} vs {x_scatter.capitalize()}{title_suffix}',
            opacity=0.6 # Opacidad para manejar el overplotting
        )
        
        # Personalizar layout
        fig_scatter.update_layout(
            xaxis_title=x_scatter.capitalize(),
            yaxis_title=y_scatter.capitalize(),
            plot_bgcolor='white',
            xaxis=dict(showgrid=True, gridcolor='lightgrey'),
            yaxis=dict(showgrid=True, gridcolor='lightgrey')
        )
        
        # Mostrar gráfico
        st.plotly_chart(fig_scatter, use_container_width=True)

if not show_hist and not show_scatter:
    st.info("Selecciona al menos un gráfico para visualizar el análisis de datos.")