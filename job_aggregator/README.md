# Job Aggregator

Buscador de empleo que agrega ofertas de múltiples portales de España.

## Instalación

```bash
cd job_aggregator
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Uso

### Búsqueda básica (scraping nativo)
```bash
python main.py "python developer"
```

### Búsqueda avanzada (con Apify)
```bash
# Configurar API key
export APIFY_API_KEY=tu_api_key

# Buscar con Apify
python main.py "python developer" --use-apify
```

### Opciones

- `--limit, -n`: Límite de resultados por fuente (default: 25)
- `--location, -l`: Ubicación (default: Spain)
- `--search, -s`: Buscar en DB existente
- `--stats`: Ver estadísticas
- `--json`: Salida en JSON
- `--source`: Filtrar por fuente

### Ejemplos

```bash
# Ver ofertas guardadas
python main.py

# Buscar en DB
python main.py --search python

# Ver estadísticas
python main.py --stats

# Buscar en Barcelona
python main.py "desarrollador" -l Barcelona
```

## Portales soportados

- InfoJobs
- Indeed
- LinkedIn
- Tecnoempleo
- Jooble

## Notas

Los portales principales (InfoJobs, LinkedIn, Indeed) tienen protecciones anti-bot很强. Para mejores resultados:

1. Usa `--use-apify` con una API key de Apify
2. Crea una cuenta en apify.com
3. Consigue un actor de scraping para los portales que necesites

## Estructura

```
job_aggregator/
├── scrapers/         # Módulos de scraping
├── models/           # Modelos de datos
├── db/               # Base de datos
├── aggregator.py     # Agregador principal
└── main.py           # CLI
```
