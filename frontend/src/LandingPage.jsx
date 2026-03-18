import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { TrendingUp, Target, BarChart2, Globe, ChevronRight, Shield, Zap, Layers } from 'lucide-react';

const SPORTS = [
  {
    key: 'nba',
    label: 'NBA',
    path: '/nba/props',
    icon: TrendingUp,
    accent: 'from-blue-600 to-blue-500',
    border: 'border-blue-500/30',
    glow: 'group-hover:shadow-blue-500/20',
    description: 'Player props across all 30 teams. Points, rebounds, assists, PRA combos, and more.',
    stat: '450+ players tracked',
  },
  {
    key: 'soccer',
    label: 'Soccer',
    path: '/soccer/pl/matches',
    icon: Globe,
    accent: 'from-emerald-600 to-emerald-500',
    border: 'border-emerald-500/30',
    glow: 'group-hover:shadow-emerald-500/20',
    description: 'Match totals and player props across Premier League, La Liga, Bundesliga, Serie A, and Ligue 1.',
    stat: '5 leagues covered',
  },
];

const PILLARS = [
  {
    icon: Shield,
    title: 'Trust Score',
    body: 'Every prop gets a 0-100 score weighing hit rate, sample size, consistency, and market odds. No gut feels.',
  },
  {
    icon: Zap,
    title: 'Live line adjustments',
    body: 'Drag any line up or down and watch the hit rate and trust score recalculate instantly from real game logs.',
  },
  {
    icon: Layers,
    title: 'Parlay builder',
    body: 'Stack legs from any sport. The combined implied probability updates in real time as you build.',
  },
];

const TICKER_ITEMS = [
  'NBA player props', 'Premier League match totals', 'La Liga player props',
  'Bundesliga fixtures', 'Serie A match cards', 'Ligue 1 over/under',
  'Parlay builder', 'Trust scores', 'Live line adjustment',
];

export default function LandingPage() {
  const navigate = useNavigate();
  const [tickerOffset, setTickerOffset] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setTickerOffset(prev => (prev + 1) % TICKER_ITEMS.length);
    }, 2200);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col">

      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
        <div className="text-2xl font-bold tracking-tight">
          <span className="text-blue-500">Stat</span>Scout
        </div>
        <button
          onClick={() => navigate('/nba/props')}
          className="text-sm text-gray-400 hover:text-white transition-colors"
        >
          Skip to app
        </button>
      </header>

      {/* Hero */}
      <section className="flex-1 flex flex-col items-center justify-center text-center px-6 pt-20 pb-16">

        {/* Eyebrow */}
        <div className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/20 rounded-full px-4 py-1.5 mb-8">
          <Target className="w-3.5 h-3.5 text-blue-400" />
          <span className="text-xs font-medium text-blue-400 tracking-wide uppercase">Sports analytics, not guesswork</span>
        </div>

        {/* Headline */}
        <h1 className="text-5xl sm:text-6xl font-extrabold tracking-tight leading-none mb-5 max-w-3xl">
          Find the props worth<br />
          <span className="text-blue-500">betting on.</span>
        </h1>

        {/* Subline */}
        <p className="text-lg text-gray-400 max-w-xl mb-10 leading-relaxed">
          StatScout scores every NBA player prop and soccer match using historical hit rates,
          form weighting, and market odds - so you know what the data actually says.
        </p>

        {/* CTAs */}
        <div className="flex flex-col sm:flex-row items-center gap-3">
          <button
            onClick={() => navigate('/nba/props')}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold px-8 py-3.5 rounded-xl transition-all shadow-lg shadow-blue-500/20 hover:shadow-blue-500/30"
          >
            Explore StatScout
            <ChevronRight className="w-4 h-4" />
          </button>
          <button
            onClick={() => navigate('/nba/props', { state: { startTour: true } })}
            className="flex items-center gap-2 border border-gray-700 hover:border-gray-500 text-gray-300 hover:text-white font-medium px-8 py-3.5 rounded-xl transition-all"
          >
            How it works
          </button>
        </div>

        {/* Scrolling ticker */}
        <div className="mt-14 flex items-center gap-2 text-xs text-gray-600 overflow-hidden max-w-lg">
          <span className="shrink-0 text-gray-700 uppercase tracking-widest text-[10px]">Covering</span>
          <div className="flex gap-3 flex-wrap justify-center">
            {TICKER_ITEMS.map((item, i) => (
              <span
                key={item}
                className={`transition-colors duration-500 ${i === tickerOffset ? 'text-blue-400' : 'text-gray-600'}`}
              >
                {item}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Sport entry cards */}
      <section className="max-w-4xl mx-auto w-full px-6 pb-20">
        <p className="text-center text-xs uppercase tracking-widest text-gray-600 mb-6">Choose your sport</p>
        <div className="grid sm:grid-cols-2 gap-4">
          {SPORTS.map(({ key, label, path, icon: Icon, accent, border, glow, description, stat }) => (
            <button
              key={key}
              onClick={() => navigate(path)}
              className={`group relative bg-gray-900 border ${border} rounded-2xl p-6 text-left hover:bg-gray-800 transition-all shadow-xl ${glow} hover:shadow-2xl hover:-translate-y-0.5`}
            >
              <div className={`inline-flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br ${accent} mb-4`}>
                <Icon className="w-5 h-5 text-white" />
              </div>
              <div className="text-lg font-bold mb-1">{label}</div>
              <div className="text-sm text-gray-400 leading-relaxed mb-4">{description}</div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-600">{stat}</span>
                <ChevronRight className="w-4 h-4 text-gray-600 group-hover:text-gray-300 transition-colors group-hover:translate-x-0.5" />
              </div>
            </button>
          ))}
        </div>
      </section>

      {/* How it works pillars */}
      <section className="border-t border-gray-800 py-16 px-6">
        <div className="max-w-4xl mx-auto">
          <p className="text-center text-xs uppercase tracking-widest text-gray-600 mb-10">How StatScout works</p>
          <div className="grid sm:grid-cols-3 gap-6">
            {PILLARS.map(({ icon: Icon, title, body }) => (
              <div key={title} className="text-center">
                <div className="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-gray-800 border border-gray-700 mb-4">
                  <Icon className="w-5 h-5 text-blue-400" />
                </div>
                <div className="font-semibold mb-2">{title}</div>
                <p className="text-sm text-gray-500 leading-relaxed">{body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-800 py-6 px-6 text-center">
        <span className="text-xs text-gray-700">
          StatScout - data-driven props analysis. Not financial or betting advice.
        </span>
      </footer>

    </div>
  );
}
