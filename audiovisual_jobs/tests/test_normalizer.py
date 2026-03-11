import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from normalization.normalizer import Normalizer


class TestNormalizer(unittest.TestCase):
    def setUp(self):
        self.normalizer = Normalizer()

    def test_limpiar_texto_basic(self):
        texto = "  Hola   mundo  con   espacios  "
        resultado = self.normalizer._limpiar_texto(texto)
        self.assertEqual(resultado, "Hola mundo con espacios")

    def test_limpiar_texto_emojis(self):
        texto = "Hola mundo 🎬 busca editor 📹"
        resultado = self.normalizer._limpiar_texto(texto)
        self.assertNotIn("🎬", resultado)
        self.assertNotIn("📹", resultado)
        self.assertIn("Hola mundo", resultado)

    def test_limpiar_texto_saltos_linea(self):
        texto = "Linea1\n\rLinea2\r\nLinea3"
        resultado = self.normalizer._limpiar_texto(texto)
        self.assertNotIn("\n", resultado)
        self.assertNotIn("\r", resultado)

    def test_extraer_ubicacion_existente(self):
        resultado = self.normalizer._extraer_ubicacion("Barcelona", None)
        self.assertEqual(resultado, "Barcelona")

    def test_extraer_ubicacion_desde_texto_barcelona(self):
        texto = "Buscamos editor para proyecto en Barcelona"
        resultado = self.normalizer._extraer_ubicacion(texto, None)
        self.assertEqual(resultado, "Barcelona")

    def test_extraer_ubicacion_desde_texto_girona(self):
        texto = "Oferta de trabajo en Girona para cámara"
        resultado = self.normalizer._extraer_ubicacion(texto, None)
        self.assertEqual(resultado, "Girona")

    def test_extraer_ubicacion_desde_texto_bcn(self):
        texto = "Buscamos foquista BCN"
        resultado = self.normalizer._extraer_ubicacion(texto, None)
        self.assertEqual(resultado, "Barcelona")

    def test_extraer_ubicacion_sin_encontrar(self):
        texto = "Buscamos editor de video"
        resultado = self.normalizer._extraer_ubicacion(texto, None)
        self.assertEqual(resultado, "Cataluña (Sin especificar)")

    def test_extraer_titulo_existente(self):
        titulo = "Editor de Video Senior"
        resultado = self.normalizer._extraer_titulo(titulo, None)
        self.assertEqual(resultado, "Editor de Video Senior")

    def test_extraer_titulo_desde_texto(self):
        texto = "Buscamos editor de video para proyecto comercial.\nMás detalles aquí."
        resultado = self.normalizer._extraer_titulo(None, texto)
        self.assertEqual(resultado, "Buscamos editor de video para proyecto comercial")

    def test_extraer_titulo_vacio(self):
        resultado = self.normalizer._extraer_titulo(None, None)
        self.assertEqual(resultado, "Sin título")

    def test_normalizar_oferta_completa(self):
        oferta = {
            "titulo_puesto": "  Editor de Video  ",
            "empresa": "  Producciones ABC  ",
            "ubicacion": "Barcelona",
            "descripcion": "Buscamos editor con Premiere 📹\nRequisitos: experiencia",
            "enlace_fuente": "https://ejemplo.com/oferta123",
            "tipo_fuente": "web",
        }

        resultado = self.normalizer.normalizar_oferta(oferta)

        self.assertEqual(resultado["titulo_puesto"], "Editor de Video")
        self.assertEqual(resultado["empresa"], "Producciones ABC")
        self.assertEqual(resultado["ubicacion"], "Barcelona")
        self.assertIn("Premiere", resultado["descripcion"])
        self.assertNotIn("📹", resultado["descripcion"])
        self.assertEqual(resultado["enlace_fuente"], "https://ejemplo.com/oferta123")
        self.assertEqual(resultado["tipo_fuente"], "web")

    def test_normalizar_oferta_minima(self):
        oferta = {
            "descripcion": "Buscamos cámara para documental en Girona",
            "enlace_fuente": "https://ejemplo.com/456",
            "tipo_fuente": "telegram",
        }

        resultado = self.normalizer.normalizar_oferta(oferta)

        self.assertIn("Girona", resultado["ubicacion"])
        self.assertIn("cámara", resultado["titulo_puesto"].lower())

    def test_normalizar_oferta_sin_enlace(self):
        oferta = {"titulo": "Editor", "descripcion": "Texto sin enlace"}

        resultado = self.normalizer.normalizar_oferta(oferta)

        self.assertEqual(resultado["enlace_fuente"], "")

    def test_normalizar_lista_vacia(self):
        resultado = self.normalizer.normalizar_lista([])
        self.assertEqual(resultado, [])

    def test_normalizar_lista_con_algunos_invalidos(self):
        ofertas = [
            {"titulo_puesto": "Editor", "enlace_fuente": "https://ejemplo.com/1"},
            {"descripcion": "Texto sin enlace"},
            {"titulo_puesto": "Cámara", "enlace_fuente": "https://ejemplo.com/2"},
        ]

        resultado = self.normalizer.normalizar_lista(ofertas)

        self.assertEqual(len(resultado), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
