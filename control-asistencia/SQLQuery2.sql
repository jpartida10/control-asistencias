-- 1. Crear base de datos
CREATE DATABASE ControlAsistenciasDB;
GO

USE ControlAsistenciasDB;
GO

-- 2. Tabla: Materias
CREATE TABLE Materias (
    MateriaID INT IDENTITY(1,1) PRIMARY KEY,
    Nombre NVARCHAR(100) NOT NULL,
    Descripcion NVARCHAR(250)
);
GO

-- 3. Tabla: Alumnos
CREATE TABLE Alumnos (
    Matricula INT PRIMARY KEY, -- usamos Matricula como ID
    Nombre NVARCHAR(100) NOT NULL,
    Apellido NVARCHAR(100) NOT NULL
);
GO

-- 4. Tabla: Maestros
CREATE TABLE Maestros (
    MaestroID INT IDENTITY(1,1) PRIMARY KEY,
    Nombre NVARCHAR(100) NOT NULL,
    Apellido NVARCHAR(100) NOT NULL,
    MateriaID INT NOT NULL,
    FOREIGN KEY (MateriaID) REFERENCES Materias(MateriaID)
        ON DELETE CASCADE
);
GO

-- 5. Tabla: ClaseGrupo
CREATE TABLE ClaseGrupo (
    ClaseGrupoID INT IDENTITY(1,1) PRIMARY KEY,
    MaestroID INT NOT NULL,
    Grupo NVARCHAR(50) NOT NULL,
    Horario NVARCHAR(50),
    FOREIGN KEY (MaestroID) REFERENCES Maestros(MaestroID)
        ON DELETE CASCADE
);
GO

-- 6. Tabla: Alumno_ClaseGrupo
CREATE TABLE Alumno_ClaseGrupo (
    Matricula INT NOT NULL,
    ClaseGrupoID INT NOT NULL,
    PRIMARY KEY (Matricula, ClaseGrupoID),
    FOREIGN KEY (Matricula) REFERENCES Alumnos(Matricula)
        ON DELETE CASCADE,
    FOREIGN KEY (ClaseGrupoID) REFERENCES ClaseGrupo(ClaseGrupoID)
        ON DELETE CASCADE
);
GO

-- 7. Tabla: Asistencias
CREATE TABLE Asistencias (
    AsistenciaID INT IDENTITY(1,1) PRIMARY KEY,
    Matricula INT NOT NULL,
    ClaseGrupoID INT NOT NULL,
    Fecha DATE NOT NULL,
    Estado NVARCHAR(20) NOT NULL CHECK (Estado IN ('Presente','Ausente','Tarde')),
    FOREIGN KEY (Matricula) REFERENCES Alumnos(Matricula)
        ON DELETE CASCADE,
    FOREIGN KEY (ClaseGrupoID) REFERENCES ClaseGrupo(ClaseGrupoID)
        ON DELETE CASCADE
);
GO

-- 8. Tabla: Inicio de session
CREATE TABLE Usuarios (
    UsuarioID INT IDENTITY(1,1) PRIMARY KEY,
    NombreUsuario NVARCHAR(50) NOT NULL UNIQUE,
    Contrasena NVARCHAR(100) NOT NULL,
    Rol NVARCHAR(20) CHECK (Rol IN ('profesor', 'alumno')),
    Matricula INT NULL,  -- para relacionar si es alumno
    MaestroID INT NULL   -- para relacionar si es profesor
);
GO

-- 9. Tabla: Usuarios
CREATE TABLE Usuarios (
    UsuarioID INT IDENTITY(1,1) PRIMARY KEY,
    NombreUsuario NVARCHAR(50) NOT NULL UNIQUE,
    Contrasena NVARCHAR(255) NOT NULL,
    Rol NVARCHAR(20) CHECK (Rol IN ('profesor', 'alumno')),
    Matricula INT NULL,   -- si es alumno
    MaestroID INT NULL    -- si es profesor
);
GO