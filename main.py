from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import os
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta

app = FastAPI(title="Backend Estilista")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Cliente(BaseModel):
    nombre: str
    telefono: str
    direccion: str

class Cita(BaseModel):
    id_cliente: int
    precio_total: float
    fecha_hora_inicio: str
    duracion_minutos: int
    notas_adicionales: str = ""

class EstadoCita(BaseModel):
    nuevo_estado: str

def obtener_conexion():
    url = os.environ.get('DATABASE_URL')
    if not url:
        raise Exception("DATABASE_URL no configurada en Render")
    if "sslmode" not in url:
        url += "?sslmode=require"
    return psycopg2.connect(url)

@app.on_event("startup")
def startup_event():
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id_cliente SERIAL PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                telefono VARCHAR(20),
                direccion TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS citas (
                id_cita SERIAL PRIMARY KEY,
                id_cliente INTEGER REFERENCES clientes(id_cliente) ON DELETE CASCADE,
                precio_total NUMERIC(10, 2),
                fecha_hora_inicio TIMESTAMP,
                fecha_hora_fin TIMESTAMP,
                duracion_minutos INTEGER,
                notas_adicionales TEXT,
                estado VARCHAR(50) DEFAULT 'Pendiente'
            )
        """)
        conexion.commit()
        cursor.close()
        conexion.close()
    except Exception as e:
        print(f"Error inicializando la base de datos: {e}")

@app.get("/")
def home():
    return {"mensaje": "Servidor en línea"}

@app.get("/clientes")
def obtener_clientes():
    conexion = obtener_conexion()
    cursor = conexion.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM clientes ORDER BY nombre ASC")
    datos = cursor.fetchall()
    cursor.close()
    conexion.close()
    return datos

@app.post("/clientes")
def crear_cliente(cliente: Cliente):
    conexion = obtener_conexion()
    cursor = conexion.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        "INSERT INTO clientes (nombre, telefono, direccion) VALUES (%s, %s, %s) RETURNING id_cliente",
        (cliente.nombre, cliente.telefono, cliente.direccion)
    )
    id_nuevo = cursor.fetchone()['id_cliente']
    conexion.commit()
    cursor.close()
    conexion.close()
    return {"id_cliente": id_nuevo, "mensaje": "Cliente creado"}

@app.delete("/clientes/{id_cliente}")
def eliminar_cliente(id_cliente: int):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM clientes WHERE id_cliente = %s", (id_cliente,))
    conexion.commit()
    cursor.close()
    conexion.close()
    return {"mensaje": "Clienta eliminada"}

@app.get("/clientes/historial/{nombre}")
def historial_cliente(nombre: str):
    conexion = obtener_conexion()
    cursor = conexion.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT c.* FROM citas c 
        JOIN clientes cl ON c.id_cliente = cl.id_cliente 
        WHERE cl.nombre = %s ORDER BY c.fecha_hora_inicio DESC
    """, (nombre,))
    datos = cursor.fetchall()
    cursor.close()
    conexion.close()
    return datos

@app.get("/citas")
def obtener_citas():
    try:
        conexion = obtener_conexion()
        cursor = conexion.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT c.id_cita, cl.nombre AS cliente, cl.telefono, cl.direccion, 
                   c.fecha_hora_inicio, c.fecha_hora_fin, c.estado, c.notas_adicionales, c.precio_total
            FROM citas c JOIN clientes cl ON c.id_cliente = cl.id_cliente
            ORDER BY c.fecha_hora_inicio ASC;
        """) 
        datos = cursor.fetchall()
        cursor.close()
        conexion.close()
        return datos if datos else []
    except Exception as e:
        return {"error_detallado_del_servidor": str(e)}

@app.post("/citas")
def crear_cita(cita: Cita):
    try:
        inicio = datetime.fromisoformat(cita.fecha_hora_inicio.replace('Z', ''))
        fin = inicio + timedelta(minutes=cita.duracion_minutos)
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        
        # ALERTA DE CRUCE DE HORARIO CON EL NOMBRE DE LA CLIENTA
        cursor.execute("""
            SELECT cl.nombre FROM citas c
            JOIN clientes cl ON c.id_cliente = cl.id_cliente
            WHERE c.estado IN ('Pendiente', 'Confirmada')
            AND (
                (c.fecha_hora_inicio <= %s AND c.fecha_hora_fin > %s) OR
                (c.fecha_hora_inicio < %s AND c.fecha_hora_fin >= %s) OR
                (c.fecha_hora_inicio >= %s AND c.fecha_hora_fin <= %s)
            )
        """, (inicio, inicio, fin, fin, inicio, fin))
        cruce = cursor.fetchone()
        if cruce:
            raise Exception(f"¡Cruce de horario! Ya tienes una cita con {cruce[0]} en ese lapso.")

        cursor.execute("""
            INSERT INTO citas (id_cliente, precio_total, fecha_hora_inicio, fecha_hora_fin, duracion_minutos, notas_adicionales, estado)
            VALUES (%s, %s, %s, %s, %s, %s, 'Pendiente')
        """, (cita.id_cliente, cita.precio_total, inicio, fin, cita.duracion_minutos, cita.notas_adicionales))
        conexion.commit()
        cursor.close()
        conexion.close()
        return {"mensaje": "Cita agendada"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/citas/{id_cita}")
def borrar_cita(id_cita: int):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM citas WHERE id_cita = %s", (id_cita,))
    conexion.commit()
    cursor.close()
    conexion.close()
    return {"mensaje": "Cita eliminada"}

@app.put("/citas/{id_cita}/estado")
def cambiar_estado(id_cita: int, estado: EstadoCita):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("UPDATE citas SET estado = %s WHERE id_cita = %s", (estado.nuevo_estado, id_cita))
    conexion.commit()
    cursor.close()
    conexion.close()
    return {"mensaje": "Estado actualizado"}
