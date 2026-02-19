# 🐳 Guía de Docker para Biotasys AI

Esta guía detalla cómo operar el entorno de desarrollo local utilizando Docker. \
El proyecto está configurado para usar **Python 3.12** y **uv** para una gestión de dependencias ultrarrápida.

## 🚀 Comandos Rápidos

### 1. Iniciar el Entorno (Development Mode)
Levanta la aplicación en modo desarrollo con **Hot Reloading** activado.
Cualquier cambio en el código fuente se reflejará inmediatamente.

```bash
docker compose up
```

La API estará disponible en:
- **API:** [http://localhost:8000](http://localhost:8000)
- **Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health:** [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

### 2. Reconstruir (Nuevas Dependencias)
Si agregas paquetes al `pyproject.toml` o `uv.lock`, debes reconstruir la imagen para que `uv` sincronice las nuevas librerías.

```bash
docker compose up --build
```

---

### 3. Ver Logs en Tiempo Real
Si corriste el contenedor en segundo plano (`-d`), usa este comando para seguir los logs.

```bash
docker compose logs -f app
```

---

### 4. Detener el Entorno
Detiene y remueve los contenedores.

```bash
docker compose down
```

---

### 5. Acceder al Contenedor (Shell)
Para ejecutar comandos dentro del entorno aislado (ej. scripts de prueba manual).

```bash
docker compose exec app bash
```

---

## 🛠️ Notas Técnicas

- **Gestor de Paquetes:** Usamos `uv` en lugar de `pip` por velocidad y determinismo.
- **Volúmenes:**
  - `.:/app`: Monta tu código local dentro del contenedor (permite editar desde VS Code y ver cambios al instante).
  - `/app/.venv`: Volumen anónimo para aislar las librerías de Linux (Docker) de las de Windows (Host). **Nunca elimines esto manualmente** a menos que quieras reinstalar todo desde cero.
- **Puertos:** El servicio corre internamente en el `8000` y expone el `8000` en tu localhost.

## ⚠️ Solución de Problemas

**Error: "Address already in use"**
Si el puerto 8000 está ocupado:
1. Identifica el proceso: `netstat -ano | findstr :8000` (Windows) o `lsof -i :8000` (Linux/Mac).
2. Mátalo o cambia el puerto en `docker-compose.yml`.

**Error de Permisos en Scripts**
Si tienes problemas ejecutando scripts, asegúrate de que tengan permisos de ejecución o lánzalos con `python script.py`.
