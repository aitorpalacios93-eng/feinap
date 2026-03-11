#!/usr/bin/env python3
import argparse
import sys
import os
import json
from aggregator import JobAggregator
from scrapers.apify_scraper import ApifyScraper

def main():
    parser = argparse.ArgumentParser(description='Job Aggregator - Busca ofertas de empleo en múltiples portales')
    parser.add_argument('keyword', nargs='?', help='Palabra clave para buscar')
    parser.add_argument('--location', '-l', default='Spain', help='Ubicación (default: Spain)')
    parser.add_argument('--limit', '-n', type=int, default=25, help='Límite por fuente (default: 25)')
    parser.add_argument('--search', '-s', help='Buscar en la base de datos existente')
    parser.add_argument('--source', help='Filtrar por fuente (InfoJobs, Indeed, LinkedIn, Tecnoempleo)')
    parser.add_argument('--stats', action='store_true', help='Mostrar estadísticas')
    parser.add_argument('--json', action='store_true', help='Salida en JSON')
    parser.add_argument('--api-key', help='API key de Apify para scraping avanzado')
    parser.add_argument('--use-apify', action='store_true', help='Usar Apify para scraping (requiere --api-key)')
    
    args = parser.parse_args()
    
    aggregator = JobAggregator()
    
    if args.stats:
        stats = aggregator.get_stats()
        if args.json:
            print(json.dumps(stats, indent=2))
        else:
            print("=== Estadísticas ===")
            print(f"Total de ofertas: {stats['total']}")
            print("\nPor fuente:")
            for source, count in stats['by_source'].items():
                print(f"  {source}: {count}")
        return
    
    if args.search:
        jobs = aggregator.search_jobs(args.search)
        if args.json:
            print(json.dumps([j.to_dict() for j in jobs], indent=2, ensure_ascii=False))
        else:
            print(f"=== Resultados para '{args.search}' ({len(jobs)} ofertas) ===\n")
            for job in jobs:
                print(f"[{job.source}] {job.title}")
                print(f"  Empresa: {job.company}")
                print(f"  Ubicación: {job.location}")
                if job.salary:
                    print(f"  Salario: {job.salary}")
                if job.remote:
                    print(f"  Remoto: Sí")
                print(f"  URL: {job.url}")
                print()
        return
    
    if not args.keyword:
        jobs = aggregator.get_jobs(source=args.source)
        if args.json:
            print(json.dumps([j.to_dict() for j in jobs], indent=2, ensure_ascii=False))
        else:
            print(f"=== Ofertas guardadas ({len(jobs)} ofertas) ===\n")
            for job in jobs[:50]:
                print(f"[{job.source}] {job.title} - {job.company} ({job.location})")
        return
    
    if args.use_apify:
        api_key = args.api_key or os.environ.get('APIFY_API_KEY')
        if not api_key:
            print("Error: Se requiere API key de Apify. Usa --api-key o configura APIFY_API_KEY")
            sys.exit(1)
        
        print(f"Buscando '{args.keyword}' en {args.location} con Apify...")
        apify = ApifyScraper(api_key)
        
        sources = ['indeed', 'linkedin', 'infojobs']
        all_jobs = []
        
        for source in sources:
            print(f"Buscando en {source}...")
            jobs = apify.search(source, args.keyword, args.location, args.limit)
            print(f"  -> {len(jobs)} ofertas")
            all_jobs.extend(jobs)
        
        saved = aggregator.db.save_jobs(all_jobs)
        print(f"Total guardadas: {saved} ofertas")
        
        jobs = aggregator.get_jobs(limit=50)
        
    else:
        print(f"Buscando '{args.keyword}' en {args.location}...")
        print("Nota: Los portales principales tienen protecciones anti-bot.")
        print("Usa --use-apify con una API key de Apify para mejores resultados.")
        print("")
        
        saved = aggregator.search_and_save(args.keyword, args.location, args.limit)
        
        jobs = aggregator.get_jobs(limit=50)
    
    if args.json:
        print(json.dumps([j.to_dict() for j in jobs], indent=2, ensure_ascii=False))
    else:
        print(f"\n=== Últimas {len(jobs)} ofertas ===\n")
        for job in jobs:
            print(f"[{job.source}] {job.title}")
            print(f"  Empresa: {job.company}")
            print(f"  Ubicación: {job.location}")
            if job.salary:
                print(f"  Salario: {job.salary}")
            if job.remote:
                print(f"  Remoto: Sí")
            print(f"  URL: {job.url}")
            print()

if __name__ == '__main__':
    main()
