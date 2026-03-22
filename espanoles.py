import urllib.request
import json
import ssl
import time
import os
import sys
from datetime import datetime
from github import Github

sys.stdout = open(sys.stdout.fileno(), mode='w', buffering=1)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

ARCHIVO_DATOS = "espanoles.json"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO = os.environ.get("GITHUB_REPO")

def subir_a_github(contenido_json):
    try:
        print(f"🔑 Token: {GITHUB_TOKEN[:10]}...", flush=True)
        print(f"📁 Repo: {GITHUB_REPO}", flush=True)
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        contenido = json.dumps(contenido_json, ensure_ascii=False, indent=2)
        try:
            archivo = repo.get_contents(ARCHIVO_DATOS)
            repo.update_file(ARCHIVO_DATOS, "Actualización automática", contenido, archivo.sha)
        except Exception as e2:
            print(f"⚠️ No existe aún, creando: {e2}", flush=True)
            repo.create_file(ARCHIVO_DATOS, "Crear archivo inicial", contenido)
        print("✅ Subido a GitHub correctamente", flush=True)
    except Exception as e:
        print(f"❌ Error subiendo a GitHub: {type(e).__name__}: {e}", flush=True)

def obtener_espanoles():
    espanoles = []
    pagina = 1
    total_revisados = 0
    print(f"[{datetime.now().strftime('%H:%M')}] Actualizando lista de jugadores españoles...", flush=True)
    while total_revisados < 3000:
        start = (pagina - 1) * 200 + 1
        url = f"https://aoe-api.reliclink.com/community/leaderboard/getLeaderBoard2?title=age2&leaderboard_id=3&platformWorldRegion=global&count=200&sortBy=1&start={start}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10, context=ctx) as response:
                datos = json.loads(response.read().decode())
            jugadores_stats = datos.get("leaderboardStats", [])
            grupos = datos.get("statGroups", [])
            if not jugadores_stats:
                break
            info_jugadores = {}
            for grupo in grupos:
                gid = grupo.get("id")
                miembros = grupo.get("members", [])
                if miembros:
                    info_jugadores[gid] = miembros[0]
            for stat in jugadores_stats:
                gid = stat.get("statgroup_id")
                info = info_jugadores.get(gid, {})
                pais = info.get("country", "")
                if pais.lower() == "es":
                    espanoles.append({
                        "rank": stat.get("rank"),
                        "nombre": info.get("alias", "Desconocido"),
                        "elo": stat.get("rating"),
                        "profile_id": info.get("profile_id")
                    })
            total_revisados += len(jugadores_stats)
            pagina += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"Error: {e}", flush=True)
            break
    return espanoles

def guardar_actualizacion(espanoles):
    hora_actual = datetime.now().strftime("%H:%M %d/%m/%Y")
    datos_anteriores = {}
    if os.path.exists(ARCHIVO_DATOS):
        with open(ARCHIVO_DATOS, "r", encoding="utf-8") as f:
            guardado = json.load(f)
            for j in guardado.get("jugadores", []):
                datos_anteriores[j["profile_id"]] = j["elo"]
    jugadores_con_cambio = []
    for j in espanoles:
        elo_anterior = datos_anteriores.get(j["profile_id"])
        cambio = j["elo"] - elo_anterior if elo_anterior is not None else 0
        jugadores_con_cambio.append({
            "rank": j["rank"],
            "nombre": j["nombre"],
            "elo": j["elo"],
            "cambio_elo": cambio,
            "profile_id": j["profile_id"]
        })
    datos_finales = {
        "ultima_actualizacion": hora_actual,
        "jugadores": jugadores_con_cambio
    }
    with open(ARCHIVO_DATOS, "w", encoding="utf-8") as f:
        json.dump(datos_finales, f, ensure_ascii=False, indent=2)
    subir_a_github(datos_finales)
    return jugadores_con_cambio, hora_actual

def mostrar_lista(jugadores, hora):
    print(f"\n=== TOP JUGADORES ESPAÑOLES === (Actualizado: {hora})", flush=True)
    print(f"{'#Rank':<8} {'Nombre':<35} {'ELO':<8} {'Cambio'}", flush=True)
    print("-" * 65, flush=True)
    for j in jugadores:
        cambio = j["cambio_elo"]
        if cambio > 0:
            cambio_str = f"+{cambio} ▲"
        elif cambio < 0:
            cambio_str = f"{cambio} ▼"
        else:
            cambio_str = "="
        print(f"#{j['rank']:<7} {j['nombre']:<35} {j['elo']:<8} {cambio_str}", flush=True)

print("🚀 Script iniciado", flush=True)
while True:
    espanoles = obtener_espanoles()
    jugadores, hora = guardar_actualizacion(espanoles)
    mostrar_lista(jugadores, hora)
    print(f"\nDatos guardados en '{ARCHIVO_DATOS}'", flush=True)
    print(f"Próxima actualización en 1 hora...", flush=True)
    time.sleep(3600)
