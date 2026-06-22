from fastapi import FastAPI
import psycopg2
import os
from psycopg2.extras import RealDictCursor

app = FastAPI()

# Configuramos CORS para permitir peticiones desde cualquier lugar
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def obtener_conexion():
    # Render usa la variable DATABASE_URL que configuraremos abajo
    url = os.environ['DATABASE_URL']
    return psycopg2.connect(url)

@app.get("/citas")
def obtener_citas():
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(cursor_factory=RealDictCursor)
        # Asegúrate que la tabla se llama 'citas'
        cursor.execute("SELECT * FROM citas") 
        datos = cursor.fetchall()
        cursor.close()
        conexion.close()
        return datos
    except Exception as e:
        # Si esto falla, verás el error detallado en el navegador en lugar de "Internal Server Error"
        return {"error_detallado": str(e)}

@app.get("/")
def home():
    return {"mensaje": "Servidor funcionando correctamente"}
