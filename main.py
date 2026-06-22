from fastapi import FastAPI
import psycopg2
import os
from psycopg2.extras import RealDictCursor

app = FastAPI()

def obtener_conexion():
    # Render lee automáticamente la variable que guardaste en "Environment"
    url = os.environ.get('DATABASE_URL')
    if not url:
        raise Exception("DATABASE_URL no configurada en Render")
    return psycopg2.connect(url)

@app.get("/citas")
def obtener_citas():
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM citas") 
        datos = cursor.fetchall()
        cursor.close()
        conexion.close()
        return datos
    except Exception as e:
        # Si esto falla, ahora el navegador te dirá EXACTAMENTE el error
        return {"error_detallado_del_servidor": str(e)}

@app.get("/")
def home():
    return {"mensaje": "Servidor funcionando"}
```

**Haz esto ahora:**
1. Guarda el `main.py` en GitHub.
2. Espera a que Render termine el nuevo despliegue.
3. Entra a `https://backend-estilista.onrender.com/citas`.

**¿Qué ves en el navegador ahora?**
*   ¿Ves una lista de datos (JSON)? -> **¡La app ya debería funcionar en tu celular!**
*   ¿Ves un error con un texto largo (`error_detallado_del_servidor`)? -> **Copia ese texto y pégamelo aquí** para darte la solución definitiva.
