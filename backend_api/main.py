from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import uvicorn

app = FastAPI(title="API Mayra Estilista a Domicilio")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#def obtener_conexion():
#    return psycopg2.connect(
#      dbname="db_estilista",
#        user="postgres",
#        password="juanky10", # <--- ¡PON TU CONTRASEÑA REAL AQUÍ!
#        host="localhost",
#        port="6969"               # <--- CAMBIA A 6969 SI ESE ES TU PUERTO
#    )
# Antes tenías host, port, user... ahora usa la URL directa:
def obtener_conexion():
    return psycopg2.connect("postgresql://neondb_owner:npg_9tEAJac1gmrT@ep-proud-sunset-atfbzsiz-pooler.c-9.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require")

class ClienteCreate(BaseModel):
    nombre: str
    telefono: str
    direccion: str

class CitaCreate(BaseModel):
    id_cliente: int       
    precio_total: float
    fecha_hora_inicio: datetime
    duracion_minutos: int
    notas_adicionales: Optional[str] = None

class CitaModificar(BaseModel):
    nueva_fecha_hora: datetime
    duracion_minutos: int

class EstadoCitaUpdate(BaseModel):
    nuevo_estado: str

@app.get("/clientes")
def obtener_clientes():
    conexion = obtener_conexion()
    cursor = conexion.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT * FROM clientes ORDER BY nombre ASC;")
        return cursor.fetchall()
    finally:
        cursor.close()
        conexion.close()

@app.post("/clientes")
def crear_cliente(cliente: ClienteCreate):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT id_cliente FROM clientes WHERE nombre = %s;", (cliente.nombre,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Esta clienta ya se encuentra registrada.")

        cursor.execute(
            "INSERT INTO clientes (nombre, telefono, direccion) VALUES (%s, %s, %s) RETURNING id_cliente;",
            (cliente.nombre, cliente.telefono, cliente.direccion)
        )
        id_nuevo = cursor.fetchone()[0]
        conexion.commit()
        return {"id_cliente": id_nuevo, "mensaje": "Cliente registrado con éxito."}
    finally:
        cursor.close()
        conexion.close()

@app.put("/clientes/{id_cliente}")
def actualizar_cliente(id_cliente: int, cliente: ClienteCreate):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT id_cliente FROM clientes WHERE nombre = %s AND id_cliente != %s;", (cliente.nombre, id_cliente))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Ya existe otra clienta con ese nombre.")

        cursor.execute(
            "UPDATE clientes SET nombre = %s, telefono = %s, direccion = %s WHERE id_cliente = %s;",
            (cliente.nombre, cliente.telefono, cliente.direccion, id_cliente)
        )
        conexion.commit()
        return {"mensaje": "Cliente actualizado con éxito."}
    finally:
        cursor.close()
        conexion.close()

@app.get("/citas")
def obtener_citas():
    conexion = obtener_conexion()
    cursor = conexion.cursor(cursor_factory=RealDictCursor)
    try:
        query = """
            SELECT c.id_cita, cl.nombre AS cliente, cl.telefono AS telefono, cl.direccion AS direccion, c.fecha_hora_inicio, c.fecha_hora_fin, c.estado, c.notas_adicionales,
                   COALESCE((SELECT SUM(precio_cobrado) FROM detalle_cita WHERE id_cita = c.id_cita), 0) AS precio_total
            FROM citas c
            JOIN clientes cl ON c.id_cliente = cl.id_cliente
            ORDER BY c.fecha_hora_inicio ASC;
        """
        cursor.execute(query)
        return cursor.fetchall()
    finally:
        cursor.close()
        conexion.close()

@app.post("/citas")
def agendar_cita(cita: CitaCreate):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        fecha_hora_fin = cita.fecha_hora_inicio + timedelta(minutes=cita.duracion_minutos)
        
        cursor.execute("""
            SELECT cl.nombre FROM citas c
            JOIN clientes cl ON c.id_cliente = cl.id_cliente
            WHERE c.estado != 'Cancelada' 
            AND (%s < c.fecha_hora_fin AND %s > c.fecha_hora_inicio);
        """, (cita.fecha_hora_inicio, fecha_hora_fin))
        
        choque = cursor.fetchone()
        if choque:
            raise HTTPException(status_code=400, detail=f"Este horario se cruza con la cita de {choque[0]}.")

        cursor.execute(
            "INSERT INTO citas (id_cliente, fecha_hora_inicio, fecha_hora_fin, notas_adicionales) VALUES (%s, %s, %s, %s) RETURNING id_cita;",
            (cita.id_cliente, cita.fecha_hora_inicio, fecha_hora_fin, cita.notas_adicionales)
        )
        id_cita_nueva = cursor.fetchone()[0]
        
        cursor.execute("INSERT INTO detalle_cita (id_cita, id_servicio, precio_cobrado) VALUES (%s, %s, %s);",
                       (id_cita_nueva, 1, cita.precio_total))
        
        conexion.commit()
        return {"mensaje": "Cita agendada"}
    finally:
        cursor.close()
        conexion.close()

@app.get("/clientes/historial/{nombre_cliente}")
def obtener_historial_cliente(nombre_cliente: str):
    conexion = obtener_conexion()
    cursor = conexion.cursor(cursor_factory=RealDictCursor)
    try:
        query = """
            SELECT c.fecha_hora_inicio, c.estado, c.notas_adicionales,
                   COALESCE((SELECT SUM(precio_cobrado) FROM detalle_cita WHERE id_cita = c.id_cita), 0) AS precio_total
            FROM citas c
            JOIN clientes cl ON c.id_cliente = cl.id_cliente
            WHERE cl.nombre = %s
            ORDER BY c.fecha_hora_inicio DESC;
        """
        cursor.execute(query, (nombre_cliente,))
        return cursor.fetchall()
    finally:
        cursor.close()
        conexion.close()

@app.put("/citas/{id_cita}/estado")
def actualizar_estado_cita(id_cita: int, data: EstadoCitaUpdate):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute("UPDATE citas SET estado = %s WHERE id_cita = %s;", (data.nuevo_estado, id_cita))
        conexion.commit()
        return {"mensaje": f"Estado actualizado a {data.nuevo_estado}"}
    finally:
        cursor.close()
        conexion.close()

@app.put("/citas/{id_cita}")
def modificar_fecha_hora_cita(id_cita: int, data: CitaModificar):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        nueva_fecha_fin = data.nueva_fecha_hora + timedelta(minutes=data.duracion_minutos)
        cursor.execute("""
            SELECT cl.nombre FROM citas c
            JOIN clientes cl ON c.id_cliente = cl.id_cliente
            WHERE c.id_cita != %s AND c.estado != 'Cancelada' 
            AND (%s < c.fecha_hora_fin AND %s > c.fecha_hora_inicio);
        """, (id_cita, data.nueva_fecha_hora, nueva_fecha_fin))
        
        choque = cursor.fetchone()
        if choque:
            raise HTTPException(status_code=400, detail=f"Este horario se cruza con la cita de {choque[0]}.")
        
        cursor.execute("UPDATE citas SET fecha_hora_inicio = %s, fecha_hora_fin = %s WHERE id_cita = %s;",
                       (data.nueva_fecha_hora, nueva_fecha_fin, id_cita))
        conexion.commit()
        return {"mensaje": "Reprogramada con éxito"}
    finally:
        cursor.close()
        conexion.close()

@app.delete("/citas/{id_cita}")
def borrar_cita(id_cita: int):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    try:
        cursor.execute("DELETE FROM detalle_cita WHERE id_cita = %s;", (id_cita,))
        cursor.execute("DELETE FROM citas WHERE id_cita = %s;", (id_cita,))
        conexion.commit()
        return {"mensaje": "Cita cancelada"}
    finally:
        cursor.close()
        conexion.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)