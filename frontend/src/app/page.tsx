import { supabase } from '@/lib/supabase';
import { Briefcase, MapPin, Monitor, Star, Sparkles } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { es } from 'date-fns/locale';

export const revalidate = 60; // Revalidate every minute

async function getDailyInsight() {
  const { data, error } = await supabase
    .from('daily_insights')
    .select('*')
    .order('date', { ascending: false })
    .limit(1)
    .single();

  if (error) return null;
  return data;
}

async function getJobs() {
  const { data, error } = await supabase
    .from('ofertas_empleo')
    .select('*')
    .order('extraido_el', { ascending: false })
    .limit(40);

  if (error) return [];
  return data;
}

export default async function Home() {
  const [insight, jobs] = await Promise.all([getDailyInsight(), getJobs()]);

  return (
    <main className="min-h-screen pb-20 relative overflow-hidden">
      {/* Background Gradients */}
      <div className="absolute top-0 left-0 w-full h-[500px] bg-primary/20 blur-[120px] rounded-full -translate-y-1/2 pointer-events-none" />
      <div className="absolute top-[20%] right-[-10%] w-[400px] h-[400px] bg-accent/20 blur-[100px] rounded-full pointer-events-none" />

      <div className="max-w-7xl mx-auto px-6 pt-24 relative z-10">
        
        {/* PREMIUM HERO */}
        <header className="mb-16 text-center max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-white/10 bg-white/5 backdrop-blur-md mb-6 text-sm text-gray-300 font-medium tracking-wide">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
            </span>
            Real-time Audiovisual Market
          </div>
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6 bg-clip-text text-transparent bg-gradient-to-r from-white via-gray-200 to-gray-500">
            Descubre tu Próximo <br className="hidden md:block" /> Proyecto
          </h1>
          <p className="text-xl text-gray-400 leading-relaxed">
            Las mejores ofertas del sector audiovisual en España, curadas por Inteligencia Artificial y actualizadas al minuto.
          </p>
        </header>

        {/* AI INSIGHT */}
        {insight && (
          <section className="mb-16">
            <div className="glass rounded-3xl p-8 relative overflow-hidden group hover:border-primary/30 transition-colors duration-500">
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary to-accent" />
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 rounded-xl bg-primary/20 text-primary">
                  <Sparkles size={24} />
                </div>
                <h2 className="text-2xl font-semibold">Resumen de Mercado</h2>
                <span className="ml-auto text-xs font-mono text-gray-500 border border-white/10 rounded-md px-2 py-1 bg-white/5">
                  Powered by Llama 3
                </span>
              </div>
              <div 
                className="prose prose-invert max-w-none text-gray-300 [&>p]:mb-4 leading-relaxed"
                dangerouslySetInnerHTML={{ __html: insight.content_html }}
              />
            </div>
          </section>
        )}

        {/* JOB FILTERS (Mockup for now) */}
        <div className="flex flex-col md:flex-row gap-4 mb-8">
          <input 
            type="text" 
            placeholder="Buscar por rol, empresa o palabra clave..." 
            className="flex-1 bg-white/5 border border-white/10 rounded-xl px-5 py-3 focus:outline-none focus:ring-2 focus:ring-primary/50 text-white placeholder-gray-500 transition-all"
          />
          <div className="flex gap-4">
            <select className="bg-white/5 border border-white/10 rounded-xl px-5 py-3 text-white focus:outline-none focus:ring-2 focus:ring-primary/50 appearance-none min-w-[160px]">
              <option value="">Cualquier Rol</option>
              <option value="Producción">Producción</option>
              <option value="Edición">Edición</option>
              <option value="Cámara">Cámara</option>
            </select>
          </div>
        </div>

        {/* JOB GRID */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {jobs.map((job: any) => (
            <a 
              key={job.id} 
              href={job.enlace_fuente}
              target="_blank"
              rel="noopener noreferrer"
              className="glass rounded-2xl p-6 group hover:bg-white/[0.05] transition-all duration-300 hover:-translate-y-1 flex flex-col h-full cursor-pointer"
            >
              <div className="flex justify-between items-start mb-4">
                <div className="bg-white/10 text-xs font-medium px-2 py-1 rounded-md text-gray-300">
                  {job.tipo_fuente.toUpperCase()}
                </div>
                {job.score_confianza && (
                  <div className="flex items-center gap-1 text-xs font-bold text-yellow-500 bg-yellow-500/10 px-2 py-1 rounded-md">
                    <Star size={12} fill="currentColor" /> {Math.round(job.score_confianza * 100)}%
                  </div>
                )}
              </div>
              
              <h3 className="text-xl font-semibold mb-2 group-hover:text-primary transition-colors line-clamp-2">
                {job.titulo_puesto}
              </h3>
              
              <div className="text-gray-400 text-sm mb-4">
                {job.empresa || 'Empresa Confidencial'}
              </div>

              <div className="mt-auto pt-4 border-t border-white/5 flex flex-wrap gap-y-3 gap-x-4 text-xs text-gray-400">
                <div className="flex items-center gap-1.5">
                  <MapPin size={14} className="text-gray-500" />
                  <span className="truncate max-w-[120px]">{job.ubicacion || 'Varias'}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Briefcase size={14} className="text-gray-500" />
                  <span>{job.rol_canonico || 'Audiovisual'}</span>
                </div>
                {job.remoto_espana && (
                  <div className="flex items-center gap-1.5 text-accent">
                    <Monitor size={14} />
                    <span>Remoto</span>
                  </div>
                )}
              </div>
              
              <div className="mt-4 text-[10px] text-gray-600 font-mono text-right">
                {formatDistanceToNow(new Date(job.first_seen_at || job.extraido_el), { addSuffix: true, locale: es })}
              </div>
            </a>
          ))}
        </div>
        
        {jobs.length === 0 && (
          <div className="text-center py-20 text-gray-500">
            No se encontraron ofertas en este momento.
          </div>
        )}

      </div>
    </main>
  );
}
