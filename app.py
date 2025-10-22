import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
from db_conexion import get_connection
import bcrypt
from datetime import date

# ==============================
# CONFIGURACIÓN INICIAL
# ==============================
st.set_page_config(page_title="Control de Asistencias", layout="wide")

# ==============================
# FUNCIONES DE BASE DE DATOS
# ==============================
def ejecutar_sql(query, params=None):
    conn = get_connection()
    cursor = conn.cursor()
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    conn.commit()
    conn.close()

def obtener_datos(query):
    conn = get_connection()
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# ==============================
# FUNCIONES DE USUARIOS
# ==============================
def verificar_usuario(nombre_usuario, contrasena):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Usuarios WHERE NombreUsuario = ?", (nombre_usuario,))
    user = cursor.fetchone()
    conn.close()
    if user:
        hashed = user[2].encode('utf-8')
        if bcrypt.checkpw(contrasena.encode('utf-8'), hashed):
            return {
                "UsuarioID": user[0],
                "NombreUsuario": user[1],
                "Rol": user[3],
                "Matricula": user[4],
                "MaestroID": user[5]
            }
    return None

def registrar_usuario(nombre_usuario, contrasena, rol, matricula=None, maestro_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Usuarios WHERE NombreUsuario = ?", (nombre_usuario,))
    existente = cursor.fetchone()
    if existente:
        conn.close()
        return "⚠️ El nombre de usuario ya existe."
    hashed = bcrypt.hashpw(contrasena.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cursor.execute("""
        INSERT INTO Usuarios (NombreUsuario, Contrasena, Rol, Matricula, MaestroID)
        VALUES (?, ?, ?, ?, ?)
    """, (nombre_usuario, hashed, rol, matricula, maestro_id))
    conn.commit()
    conn.close()
    return "✅ Usuario registrado correctamente."

# ==============================
# FUNCIONES DE ELIMINACIÓN SEGURA
# ==============================
def eliminar_alumno(matricula):
    ejecutar_sql("DELETE FROM Asistencias WHERE Matricula = ?", (matricula,))
    ejecutar_sql("DELETE FROM Alumno_ClaseGrupo WHERE Matricula = ?", (matricula,))
    ejecutar_sql("DELETE FROM Alumnos WHERE Matricula = ?", (matricula,))

def eliminar_maestro(maestro_id):
    ejecutar_sql("DELETE FROM ClaseGrupo WHERE MaestroID = ?", (maestro_id,))
    ejecutar_sql("DELETE FROM Maestros WHERE MaestroID = ?", (maestro_id,))

def eliminar_materia(materia_id):
    ejecutar_sql("DELETE FROM Maestros WHERE MateriaID = ?", (materia_id,))
    ejecutar_sql("DELETE FROM Materias WHERE MateriaID = ?", (materia_id,))

# ==============================
# LOGIN Y REGISTRO
# ==============================
if "usuario" not in st.session_state:
    st.session_state.usuario = None

if st.session_state.usuario is None:
    st.image("https://cdn-icons-png.flaticon.com/512/2922/2922510.png", width=100)
    st.title("🎓 Sistema de Control de Asistencias")

    tab_login, tab_registro = st.tabs(["🔐 Iniciar Sesión", "🆕 Crear Cuenta"])

    # --- INICIO DE SESIÓN ---
    with tab_login:
        st.subheader("Inicio de sesión")
        usuario = st.text_input("👤 Usuario")
        contrasena = st.text_input("🔒 Contraseña", type="password")

        if st.button("Iniciar Sesión"):
            user = verificar_usuario(usuario, contrasena)
            if user:
                st.session_state.usuario = user
                st.success(f"Bienvenido, {user['NombreUsuario']} 👋 ({user['Rol']})")
                st.experimental_rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos")

    # --- REGISTRO DE NUEVO USUARIO ---
    with tab_registro:
        st.subheader("Registro de nuevo usuario")
        nuevo_usuario = st.text_input("👤 Nuevo nombre de usuario")
        nueva_contrasena = st.text_input("🔒 Nueva contraseña", type="password")
        rol_sel = st.selectbox("🎭 Rol", ["profesor", "alumno"])

        if rol_sel == "alumno":
            matriculas = obtener_datos("SELECT Matricula, Nombre || ' ' || Apellido AS NombreCompleto FROM Alumnos")
            if matriculas.empty:
                st.warning("⚠️ No hay alumnos registrados. Registra uno primero desde el rol de profesor.")
                matricula_sel = None
            else:
                matricula_sel = st.selectbox("Selecciona tu matrícula", matriculas["Matricula"])
            maestro_sel = None
        else:
            maestros = obtener_datos("SELECT MaestroID, Nombre || ' ' || Apellido AS NombreCompleto FROM Maestros")
            if maestros.empty:
                st.warning("⚠️ No hay maestros registrados. Registra uno primero.")
                maestro_sel = None
            else:
                maestro_sel = st.selectbox("Selecciona tu nombre", maestros["NombreCompleto"])
            matricula_sel = None

        if st.button("🆕 Crear Cuenta"):
            if not nuevo_usuario or not nueva_contrasena:
                st.error("❌ Debes llenar todos los campos.")
            else:
                maestro_id = None
                matricula = None
                if rol_sel == "profesor" and maestro_sel:
                    maestro_id = int(maestros.loc[maestros["NombreCompleto"] == maestro_sel, "MaestroID"].iloc[0])
                elif rol_sel == "alumno" and matricula_sel:
                    matricula = int(matriculas.loc[matriculas["Matricula"] == matricula_sel, "Matricula"].iloc[0])

                resultado = registrar_usuario(nuevo_usuario, nueva_contrasena, rol_sel, matricula, maestro_id)
                if "✅" in resultado:
                    st.success(resultado)
                else:
                    st.warning(resultado)

    st.stop()

# ==============================
# MENÚ PRINCIPAL
# ==============================
usuario_actual = st.session_state.usuario
rol = usuario_actual["Rol"]

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2922/2922510.png", width=100)
    st.title(f"👋 Bienvenido, {usuario_actual['NombreUsuario']}")

    if rol == "profesor":
        opciones = ["Inicio", "Maestros", "Alumnos", "Materias", "Clases", "Asignar Alumnos", "Consultar Clases", "Asistencias"]
    elif rol == "alumno":
        opciones = ["Inicio", "Mis Clases", "Mis Asistencias"]

    selected = option_menu(
        menu_title="Menú Principal",
        options=opciones,
        icons=["house", "book", "people", "calendar", "clipboard-check", "book-open", "users"],
        menu_icon="cast",
        default_index=0
    )

    if st.button("🚪 Cerrar Sesión"):
        st.session_state.usuario = None
        st.experimental_rerun()


# --SECCIONES PRINCIPALES--
# ----- INICIO -----
if selected == "Inicio":
    st.title("🎓 Sistema de Control de Asistencias")
    st.markdown("Administra alumnos, maestros, materias y asistencias con inicio de sesión y control de roles.")
    st.image("C:/Users/javier alberto/Desktop/Programacion web/control-asistencia/inicio.jpg", width=400)


# ----- MATERIAS -----
elif selected == "Materias" and rol == "profesor":
    st.title("📚 Registro de Materias")
    with st.form("form_materia"):
        nombre = st.text_input("Nombre de la materia")
        descripcion = st.text_input("Descripción")
        agregar = st.form_submit_button("➕ Agregar Materia")
        if agregar and nombre:
            ejecutar_sql("INSERT INTO Materias (Nombre, Descripcion) VALUES (?, ?)", (nombre, descripcion))
            st.success("✅ Materia agregada correctamente")
    materias = obtener_datos("SELECT * FROM Materias")
    for _, row in materias.iterrows():
        col1, col2 = st.columns([6, 1])
        col1.write(row.to_frame().T.to_html(index=False, escape=False), unsafe_allow_html=True)
        if col2.button("🗑️ Eliminar", key=f"del_materia_{row['MateriaID']}"):
            eliminar_materia(row["MateriaID"])
            st.success("✅ Materia eliminada correctamente")
            st.experimental_rerun()


# ----- MAESTROS -----
elif selected == "Maestros" and rol == "profesor":
    st.title("👨‍🏫 Registro de Maestros")
    materias = obtener_datos("SELECT * FROM Materias")
    with st.form("form_maestro"):
        nombre = st.text_input("Nombre del maestro")
        apellido = st.text_input("Apellido del maestro")
        materia_sel = st.selectbox("Materia", materias["Nombre"] if not materias.empty else [])
        agregar = st.form_submit_button("➕ Agregar Maestro")
        if agregar and nombre and apellido and materia_sel:
            materia_id = int(materias.loc[materias["Nombre"] == materia_sel, "MateriaID"].iloc[0])
            ejecutar_sql("INSERT INTO Maestros (Nombre, Apellido, MateriaID) VALUES (?, ?, ?)", (nombre, apellido, materia_id))
            st.success("✅ Maestro agregado correctamente")
    maestros = obtener_datos("SELECT * FROM Maestros")
    for _, row in maestros.iterrows():
        col1, col2 = st.columns([6, 1])
        col1.write(row.to_frame().T.to_html(index=False, escape=False), unsafe_allow_html=True)
        if col2.button("🗑️ Eliminar", key=f"del_maestro_{row['MaestroID']}"):
            eliminar_maestro(row["MaestroID"])
            st.success("✅ Maestro eliminado correctamente")
            st.experimental_rerun()


# ----- ALUMNOS -----
elif selected == "Alumnos" and rol == "profesor":
    st.title("👩‍🎓 Registro de Alumnos")
    with st.form("form_alumno"):
        matricula = st.number_input("Matrícula", min_value=1)
        nombre = st.text_input("Nombre del alumno")
        apellido = st.text_input("Apellido del alumno")
        agregar = st.form_submit_button("➕ Agregar Alumno")
        if agregar and nombre and apellido and matricula:
            ejecutar_sql("INSERT INTO Alumnos (Matricula, Nombre, Apellido) VALUES (?, ?, ?)", (matricula, nombre, apellido))
            st.success("✅ Alumno agregado correctamente")
    alumnos = obtener_datos("SELECT * FROM Alumnos")
    for _, row in alumnos.iterrows():
        col1, col2 = st.columns([6, 1])
        col1.write(row.to_frame().T.to_html(index=False, escape=False), unsafe_allow_html=True)
        if col2.button("🗑️ Eliminar", key=f"del_alumno_{row['Matricula']}"):
            eliminar_alumno(row["Matricula"])
            st.success("✅ Alumno eliminado correctamente")
            st.experimental_rerun()


# ----- CLASES -----
elif selected == "Clases" and rol == "profesor":
    st.title("🗓️ Registro de Clases")
    maestros = obtener_datos("SELECT MaestroID, Nombre + ' ' + Apellido AS NombreCompleto FROM Maestros")
    if maestros.empty:
        st.warning("⚠️ Registra maestros primero.")
    else:
        with st.form("form_clase"):
            maestro = st.selectbox("Selecciona Maestro", maestros["NombreCompleto"])
            grupos = ["A", "B", "C", "D", "F"]
            grupo = st.selectbox("Selecciona Grupo", grupos)
            horarios = [
                "07:00-07:50", "07:50-08:40", "08:40-09:10", "09:10-10:00",
                "10:00-10:50", "10:50-11:40", "11:40-12:30", "12:30-13:20",
                "13:20-14:10", "14:10-15:00", "15:00-15:50"
            ]
            horario = st.selectbox("Selecciona Horario", horarios)
            agregar = st.form_submit_button("➕ Agregar Clase")
            if agregar:
                maestro_id = int(maestros.loc[maestros["NombreCompleto"] == maestro, "MaestroID"].iloc[0])
                existente = obtener_datos(f"""
                    SELECT * FROM ClaseGrupo WHERE MaestroID={maestro_id} AND Grupo='{grupo}' AND Horario='{horario}'
                """)
                if not existente.empty:
                    st.error("⚠️ Ese horario ya está reservado para este grupo y maestro.")
                else:
                    ejecutar_sql(
                        "INSERT INTO ClaseGrupo (MaestroID, Grupo, Horario) VALUES (?, ?, ?)",
                        (maestro_id, grupo, horario)
                    )
                    st.success("✅ Clase registrada correctamente")

    clases = obtener_datos("SELECT * FROM ClaseGrupo")
    st.dataframe(clases)


# ----- ASIGNAR ALUMNOS -----
elif selected == "Asignar Alumnos" and rol == "profesor":
    st.title("👥 Asignar Alumnos a Clases")
    alumnos = obtener_datos("SELECT Matricula, Nombre + ' ' + Apellido AS NombreCompleto FROM Alumnos")
    clases = obtener_datos("""
        SELECT C.ClaseGrupoID, M.Nombre + ' - ' + C.Grupo AS ClaseNombre
        FROM ClaseGrupo C
        JOIN Maestros Ma ON C.MaestroID = Ma.MaestroID
        JOIN Materias M ON Ma.MateriaID = M.MateriaID
    """)
    if alumnos.empty or clases.empty:
        st.warning("⚠️ Debes registrar alumnos y clases primero.")
    else:
        with st.form("form_asignar"):
            alumno = st.selectbox("Selecciona Alumno", alumnos["NombreCompleto"])
            clase = st.selectbox("Selecciona Clase", clases["ClaseNombre"])
            agregar = st.form_submit_button("➕ Asignar Alumno")
            if agregar:
                matricula = int(alumnos.loc[alumnos["NombreCompleto"] == alumno, "Matricula"].iloc[0])
                clase_id = int(clases.loc[clases["ClaseNombre"] == clase, "ClaseGrupoID"].iloc[0])
                existe = obtener_datos(
                    f"SELECT * FROM Alumno_ClaseGrupo WHERE Matricula={matricula} AND ClaseGrupoID={clase_id}"
                )
                if not existe.empty:
                    st.warning("⚠️ El alumno ya está asignado a esta clase.")
                else:
                    ejecutar_sql(
                        "INSERT INTO Alumno_ClaseGrupo (Matricula, ClaseGrupoID) VALUES (?, ?)",
                        (matricula, clase_id)
                    )
                    st.success("✅ Alumno asignado correctamente")


# ----- CONSULTAR CLASES -----
elif selected == "Consultar Clases" and rol == "profesor":
    st.title("📋 Consultar Clases con Alumnos")
    clases = obtener_datos("""
        SELECT C.ClaseGrupoID, M.Nombre + ' - ' + C.Grupo AS ClaseNombre
        FROM ClaseGrupo C
        JOIN Maestros Ma ON C.MaestroID = Ma.MaestroID
        JOIN Materias M ON Ma.MateriaID = M.MateriaID
    """)
    if clases.empty:
        st.warning("⚠️ No hay clases registradas.")
    else:
        clase = st.selectbox("Selecciona Clase", clases["ClaseNombre"])
        clase_id = int(clases.loc[clases["ClaseNombre"] == clase, "ClaseGrupoID"].iloc[0])
        alumnos = obtener_datos(f"""
            SELECT A.Matricula, A.Nombre, A.Apellido
            FROM Alumno_ClaseGrupo AC
            JOIN Alumnos A ON AC.Matricula = A.Matricula
            WHERE AC.ClaseGrupoID = {clase_id}
        """)
        if alumnos.empty:
            st.info("Esta clase no tiene alumnos asignados.")
        else:
            st.dataframe(alumnos)


# ----- ASISTENCIAS -----
elif selected == "Asistencias" and rol == "profesor":
    st.title("📝 Registro de Asistencias")
    alumnos = obtener_datos("SELECT Matricula, Nombre + ' ' + Apellido AS NombreCompleto FROM Alumnos")
    clases = obtener_datos("""
        SELECT C.ClaseGrupoID, M.Nombre AS Materia, C.Grupo, Ma.Nombre + ' ' + Ma.Apellido AS Maestro
        FROM ClaseGrupo C
        JOIN Maestros Ma ON C.MaestroID = Ma.MaestroID
        JOIN Materias M ON Ma.MateriaID = M.MateriaID
    """)
    if alumnos.empty or clases.empty:
        st.warning("⚠️ Registra primero alumnos y clases.")
    else:
        with st.form("form_asistencia"):
            alumno = st.selectbox("Selecciona Alumno", alumnos["NombreCompleto"])
            clase = st.selectbox(
                "Selecciona Clase",
                clases.apply(lambda x: f"{x['Materia']} - {x['Grupo']} ({x['Maestro']})", axis=1)
            )
            fecha = st.date_input("Fecha")
            estado = st.selectbox("Estado", ["Presente", "Ausente", "Tarde"])
            registrar = st.form_submit_button("✅ Registrar Asistencia")
            if registrar:
                matricula = int(alumnos.loc[alumnos["NombreCompleto"] == alumno, "Matricula"].iloc[0])
                clase_id = int(clases.loc[
                    clases.apply(lambda x: f"{x['Materia']} - {x['Grupo']} ({x['Maestro']})", axis=1) == clase,
                    "ClaseGrupoID"
                ].iloc[0])
                ejecutar_sql(
                    "INSERT INTO Asistencias (Matricula, ClaseGrupoID, Fecha, Estado) VALUES (?, ?, ?, ?)",
                    (matricula, clase_id, fecha, estado)
                )
                st.success("✅ Asistencia registrada correctamente")


# ----- VISTA ALUMNO -----
elif selected == "Mis Clases" and rol == "alumno":
    st.title("📘 Mis Clases")
    matricula = usuario_actual["Matricula"]
    clases = obtener_datos(f"""
        SELECT M.Nombre AS Materia, C.Grupo, C.Horario, Ma.Nombre + ' ' + Ma.Apellido AS Maestro
        FROM Alumno_ClaseGrupo AC
        JOIN ClaseGrupo C ON AC.ClaseGrupoID = C.ClaseGrupoID
        JOIN Maestros Ma ON C.MaestroID = Ma.MaestroID
        JOIN Materias M ON Ma.MateriaID = M.MateriaID
        WHERE AC.Matricula = {matricula}
    """)
    if clases.empty:
        st.info("⚠️ No estás inscrito en ninguna clase.")
    else:
        st.dataframe(clases)


elif selected == "Mis Asistencias" and rol == "alumno":
    st.title("📋 Mis Asistencias")
    matricula = usuario_actual["Matricula"]
    asistencias = obtener_datos(f"""
        SELECT M.Nombre AS Materia, C.Grupo, A.Fecha, A.Estado
        FROM Asistencias A
        JOIN ClaseGrupo C ON A.ClaseGrupoID = C.ClaseGrupoID
        JOIN Maestros Ma ON C.MaestroID = Ma.MaestroID
        JOIN Materias M ON Ma.MateriaID = M.MateriaID
        WHERE A.Matricula = {matricula}
    """)
    if asistencias.empty:
        st.info("⚠️ No hay asistencias registradas aún.")
    else:
        st.dataframe(asistencias)
