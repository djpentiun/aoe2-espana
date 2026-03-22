import urllib.request
import json
import ssl
import time
import os
from datetime import datetime
from github import Github

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

ARCHIVO_DATOS = "espanoles.json"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO = os.environ.get("GITHUB_REPO")

def subir_a_github(contenido_json):
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        contenido = json.dumps(contenido_json, ensure_ascii=False, indent=2)
        try:
            archivo = repo.get_contents(ARCHIVO_DATOS)
            repo.update_file(ARCHIVO_DATOS, "Actualización automática", contenido, archivo.sha)
        except:
            repo.create_file(ARCHIVO_DATOS, "Crear archivo inicial", contenido)
        print("✅ Subido a GitHub correctamente")
    except Exception as e:
        print(f"❌ Error subiendo a GitHub: {e}")

def obtener_espanoles():
    espanoles = []
    pagina = 1
    total_revisados = 0
    print(f"[{datetime.now().strftime('%H:%M')}] Actualizando lista de jugadores españoles...")
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
            print(f"Error: {e}")
            break
    return espanoles

def guardar_actualizacion(espanoles):
    hora_actual = datetime.now().strftime("%H:%M %d/%m/%Y")
    datos_anteriores = {}
    if os.path.exists(ARCHIVO_DATOS):
        with open(ARCHIVO_DATOS, "r", encoding="utf-8") as f:
            guardado = json.load(f)
            for j in guardado.get("jugadores", []):
                datos_anteriores[j["profile_id"]] = 
