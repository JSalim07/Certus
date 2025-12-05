from fastapi import FastAPI, WebSocket, Request, Cookie, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from database import Base, engine, SessionLocal
import crud
import auth
from websocket_manager import conectar
from typing import Optional


app = FastAPI()

Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")


# ========== HELPER PARA OBTENER USUARIO DE COOKIE ==========
def get_current_user(token: Optional[str] = None):
    """Obtiene el usuario actual desde el token"""
    if not token:
        return None
    
    payload = auth.decode_access_token(token)
    if not payload:
        return None
    
    db = SessionLocal()
    usuario_id = payload.get("sub")
    if not usuario_id:
        return None
    
    return crud.obtener_usuario(db, int(usuario_id))


# ========== FRONTEND - PÁGINAS PÚBLICAS ==========
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/registro", response_class=HTMLResponse)
def registro_page(request: Request):
    return templates.TemplateResponse("registro.html", {"request": request})


# ========== FRONTEND - PÁGINAS PROTEGIDAS ==========
@app.get("/", response_class=HTMLResponse)
def index(request: Request, auth_token: Optional[str] = Cookie(None)):
    usuario = get_current_user(auth_token)
    if not usuario:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("index.html", {"request": request, "usuario": usuario})


@app.get("/perfil", response_class=HTMLResponse)
def perfil_page(request: Request, auth_token: Optional[str] = Cookie(None)):
    usuario = get_current_user(auth_token)
    if not usuario:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("perfil.html", {"request": request, "usuario": usuario})


@app.get("/subastas", response_class=HTMLResponse)
def subastas_page(request: Request, auth_token: Optional[str] = Cookie(None)):
    usuario = get_current_user(auth_token)
    if not usuario:
        return RedirectResponse(url="/login")
    
    db = SessionLocal()
    lista = crud.obtener_subastas(db)
    return templates.TemplateResponse("subastas.html", {
        "request": request, 
        "subastas": lista,
        "usuario": usuario
    })


@app.get("/subastas/{subasta_id}", response_class=HTMLResponse)
def detalle_subasta_page(request: Request, subasta_id: int, auth_token: Optional[str] = Cookie(None)):
    usuario = get_current_user(auth_token)
    if not usuario:
        return RedirectResponse(url="/login")
    
    return templates.TemplateResponse(
        "detalle_subasta.html",
        {"request": request, "subasta_id": subasta_id, "usuario": usuario}
    )


@app.get("/crear", response_class=HTMLResponse)
def crear_subasta_page(request: Request, auth_token: Optional[str] = Cookie(None)):
    usuario = get_current_user(auth_token)
    if not usuario:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("crear_subasta.html", {"request": request, "usuario": usuario})


# ========== API - AUTENTICACIÓN ==========
@app.post("/api/registro")
def api_registro(data: dict):
    db = SessionLocal()
    resultado = crud.crear_usuario(db, data)
    
    if isinstance(resultado, dict) and "error" in resultado:
        return resultado
    
    # Crear token
    token = auth.create_access_token({"sub": str(resultado.id)})
    
    return {
        "status": "ok",
        "usuario": {
            "id": resultado.id,
            "nombre": resultado.nombre,
            "correo": resultado.correo
        },
        "token": token
    }


@app.post("/api/login")
def api_login(data: dict):
    db = SessionLocal()
    usuario = crud.autenticar_usuario(db, data["correo"], data["password"])
    
    if not usuario:
        return {"error": "Credenciales incorrectas"}
    
    # Crear token
    token = auth.create_access_token({"sub": str(usuario.id)})
    
    return {
        "status": "ok",
        "usuario": {
            "id": usuario.id,
            "nombre": usuario.nombre,
            "correo": usuario.correo
        },
        "token": token
    }


@app.post("/api/logout")
def api_logout(response: Response):
    response.delete_cookie("auth_token")
    return {"status": "ok"}


# ========== API - SUBASTAS ==========
@app.get("/api/subastas")
def api_listar_subastas():
    db = SessionLocal()
    return crud.obtener_subastas(db)


@app.get("/api/subastas/{subasta_id}")
def api_detalle(subasta_id: int):
    db = SessionLocal()
    return crud.obtener_subasta(db, subasta_id)


@app.post("/api/subastas")
def api_crear_subasta(data: dict, auth_token: Optional[str] = Cookie(None)):
    usuario = get_current_user(auth_token)
    if not usuario:
        return {"error": "No autorizado"}
    
    db = SessionLocal()
    return crud.crear_subasta(db, data)


@app.post("/api/pujas")
def api_puja(data: dict, auth_token: Optional[str] = Cookie(None)):
    usuario = get_current_user(auth_token)
    if not usuario:
        return {"error": "No autorizado"}
    
    # Usar el ID del usuario autenticado
    data["usuario_id"] = usuario.id
    
    db = SessionLocal()
    return crud.crear_puja(db, data)


# ========== API - USUARIOS ==========
@app.get("/api/usuario/actual")
def api_usuario_actual(auth_token: Optional[str] = Cookie(None)):
    usuario = get_current_user(auth_token)
    if not usuario:
        return {"error": "No autorizado"}
    
    return {
        "id": usuario.id,
        "nombre": usuario.nombre,
        "correo": usuario.correo
    }


@app.get("/api/usuario/{usuario_id}")
def api_obtener_usuario(usuario_id: int, auth_token: Optional[str] = Cookie(None)):
    usuario_actual = get_current_user(auth_token)
    if not usuario_actual:
        return {"error": "No autorizado"}
    
    db = SessionLocal()
    usuario = crud.obtener_usuario(db, usuario_id)
    if not usuario:
        return {"error": "Usuario no encontrado"}
    return {
        "id": usuario.id,
        "nombre": usuario.nombre,
        "correo": usuario.correo
    }


@app.post("/api/usuario/actualizar")
def api_actualizar_usuario(data: dict, auth_token: Optional[str] = Cookie(None)):
    usuario_actual = get_current_user(auth_token)
    if not usuario_actual:
        return {"error": "No autorizado"}
    
    # Solo puede actualizar su propio perfil
    if usuario_actual.id != data.get("id"):
        return {"error": "No puedes editar otro perfil"}
    
    db = SessionLocal()
    return crud.actualizar_usuario(db, data)


@app.get("/api/usuario/{usuario_id}/pujas")
def api_pujas_usuario(usuario_id: int, auth_token: Optional[str] = Cookie(None)):
    usuario_actual = get_current_user(auth_token)
    if not usuario_actual:
        return {"error": "No autorizado"}
    
    db = SessionLocal()
    return crud.obtener_pujas_usuario(db, usuario_id)


# ========== WEBSOCKETS ==========
@app.websocket("/ws/{subasta_id}")
async def websocket_endpoint(websocket: WebSocket, subasta_id: int):
    await conectar(websocket, subasta_id)