[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/DevChinoC/sistema_de_horarios/blob/main/LICENSE)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Status](https://img.shields.io/badge/status-en%20desarrollo-yellow)
![Repo Size](https://img.shields.io/github/repo-size/DevChinoC/sistema_de_horarios)
![Last Commit](https://img.shields.io/github/last-commit/DevChinoC/sistema_de_horarios)
# Sistema Generador de Horarios y Planes de Estudio

## Descripción

Este sistema tiene como objetivo la **generación automática de horarios académicos** a partir de planes de estudio previamente definidos, considerando múltiples restricciones como:

- Disponibilidad de docentes  
- Disponibilidad de aulas  
- Distribución por semestres  
- Tipos de materia (tronco / optativa)  

A diferencia de un sistema centrado en la gestión básica de datos, la solución implementa un motor de asignación inteligente orientado a la generación automatizada de horarios válidos, integrando lógica de negocio, restricciones y mecanismos de resolución de conflictos.

------------------------------------------------------------------------

## Stack Tecnológico
 Tecnologias │ Responsabilidades técnicas
  
  --------------------------------------------------------
  | Tecnología     | Rol en la arquitectura  |
  | -------------- | ----------------------  |
  | Python         | Lenguaje principal      |
  | SQLAlchemy     | ORM                     |
  | MySQL          | Persistencia            |
  | Flet           | Capa de presentación    |
  
------------------------------------------------------------------------

## Arquitectura
Se implementa una **arquitectura en capas (Layered Architecture)**:
UI → Application → Domain → Infrastructure

------------------------------------------------------------------------

## ¿Por qué arquitectura en capas?

Se eligió arquitectura en capas por las siguientes razones:

### Separación de responsabilidades
Permite dividir claramente:
- Interfaz (Flet)
- Lógica de negocio (algoritmo de horarios)
- Persistencia (base de datos)

---

### Manejo de lógica compleja
El sistema incluye:
- Restricciones de asignación
- Validaciones múltiples
- Generación de combinaciones válidas

Esto requiere una capa aislada (**Domain**) para evitar acoplamiento.

---
### ✅ Mantenibilidad
Evita:
- Código espagueti
- Mezcla de lógica con UI
- Dependencia directa de la base de datos

---


------------------------------------------------------------------------

## 📁 Estructura del Proyecto

app/
- │── main.py
- │
- ├── ui/
- │ ├──  views
- │ └──components
- ├── application/
- │ ├── services/
- │ └── dto/
- │ └──interfaces/
- │
- ├── domain/
- │ ├── models/
- │ ├── rules/
- │ └── scheduling/
- │
- ├── infrastructure/
- ├── db/
- └── repositories/

test/
- ├──test_domain/
- ├──test_repositories
- ├──test_services/
------------------------------------------------------------------------
## Capas del Sistema
---

## 🖥️ UI (Interfaz de Usuario) → `/ui`

- Interacción con el usuario  
- Formularios y visualización  
- No contiene lógica de negocio ni acceso a base de datos  

---

## Application (Servicios) → `/application`

- Orquesta los casos de uso  
- Llama repositorios  
- Invoca el generador de horarios  

---

##  Domain (Núcleo del sistema) → `/domain`

Contiene la lógica principal:

### Modelos
Representación conceptual del sistema

### Reglas
- No empalmes  
- Restricciones de docentes  
- Uso de aulas  

### Generador de horarios
Algoritmo encargado de construir horarios válidos

---

## Infrastructure → `/infrastructure`

Encargado de la persistencia:

### `/db`
- Conexión a MySQL  
- Modelos SQLAlchemy  

### `/repositories`
- Consultas  
- Inserciones  
- Acceso a datos  

---------------------------------------------------------------------

## 👨‍💻 Autor

© 2026 Marcos David Chino (DevChinoC).

Todos los derechos reservados.
------------------------------------------------------------------------

## ⚖️ Licencia

Este proyecto está bajo la licencia MIT.  
Puedes usar, modificar y distribuir el software siempre que se mantenga el crédito al autor.

Para más detalles, consulta el archivo LICENSE.