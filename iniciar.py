"""Levanta el servidor de la API y abre el navegador.

Uso:  python iniciar.py
"""

import threading
import time
import webbrowser

import uvicorn

PUERTO = 8001
DIRECCION = f"http://localhost:{PUERTO}/"


def abrir_el_navegador():
    """Espera a que el servidor levante y luego muestra la pagina."""
    for _ in range(40):
        time.sleep(0.5)
        try:
            import httpx

            if httpx.get(f"{DIRECCION}api/salud", timeout=3).status_code == 200:
                webbrowser.open(DIRECCION)
                return
        except Exception:
            continue


if __name__ == "__main__":
    print("=" * 44)
    print("  API Paraderos SITP Bogota - Python + FastAPI")
    print("=" * 44)
    print(f"  La pagina se abre sola en {DIRECCION}")
    print(f"  Documentacion interactiva: {DIRECCION}docs")
    print("  Para detener el servidor presiona Ctrl+C")
    print("=" * 44)

    threading.Thread(target=abrir_el_navegador, daemon=True).start()
    uvicorn.run("main:app", host="127.0.0.1", port=PUERTO)