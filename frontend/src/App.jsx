import React, { useState, useMemo, useEffect, useRef } from 'react';
import { TrendingUp, TrendingDown, Filter, Search, Home, Plane, Moon, Sun, Flame, Snowflake, Plus, X, Save, Trash2, ChevronRight, ChevronLeft, RefreshCw } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Cell } from 'recharts';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL
  ? `${import.meta.env.VITE_API_BASE_URL}/api`
  : 'http://localhost:5000/api';

// Keeping mock data as fallback
const mockPlayers = [
  {
    id: 1,
    name: "LeBron James",
    team: "LAL",
    teamColor: "#552583",
    position: "SF",
    statType: "Points",
    line: 24.5,
    hitRate: 70,
    trustScore: 83,
    lastGames: [28, 26, 22, 30, 25, 23, 27, 21, 29, 24],
    last5Games: [27, 21, 29, 24, 28],
    last15Games: [28, 26, 22, 30, 25, 23, 27, 21, 29, 24, 26, 28, 25, 27, 23],
    recentForm: "hot",
    opponent: "GSW",
    opponentRank: 18,
    opponentDefStat: "112.3 PPG",
    gameDate: "Nov 14, 2025",
    gameTime: "7:30 PM",
    isHome: true,
    avgLastN: 25.8,
    streak: 5,
    streakType: "over"
  },
  {
    id: 2,
    name: "Luka Dončić",
    team: "DAL",
    teamColor: "#00538C",
    position: "PG",
    statType: "Assists",
    line: 8.5,
    hitRate: 60,
    trustScore: 75,
    lastGames: [9, 7, 10, 8, 9, 7, 11, 6, 9, 8],
    last5Games: [11, 6, 9, 8, 9],
    last15Games: [9, 7, 10, 8, 9, 7, 11, 6, 9, 8, 10, 9, 8, 7, 9],
    recentForm: "neutral",
    opponent: "PHX",
    opponentRank: 12,
    opponentDefStat: "24.8 APG",
    gameDate: "Nov 14, 2025",
    gameTime: "8:00 PM",
    isHome: false,
    avgLastN: 8.6,
    streak: 0
  },
  {
    id: 3,
    name: "Jayson Tatum",
    team: "BOS",
    teamColor: "#007A33",
    position: "SF",
    statType: "Rebounds",
    line: 7.5,
    hitRate: 55,
    trustScore: 68,
    lastGames: [8, 6, 7, 9, 6, 7, 8, 5, 7, 8],
    last5Games: [8, 5, 7, 8, 8],
    last15Games: [8, 6, 7, 9, 6, 7, 8, 5, 7, 8, 7, 6, 8, 7, 9],
    recentForm: "neutral",
    opponent: "MIA",
    opponentRank: 8,
    opponentDefStat: "42.1 RPG",
    gameDate: "Nov 15, 2025",
    gameTime: "7:00 PM",
    isHome: true,
    avgLastN: 7.1,
    streak: 3,
    streakType: "over"
  },
  {
    id: 4,
    name: "Giannis Antetokounmpo",
    team: "MIL",
    teamColor: "#00471B",
    position: "PF",
    statType: "Points",
    line: 30.5,
    hitRate: 75,
    trustScore: 88,
    lastGames: [34, 32, 28, 35, 31, 33, 29, 36, 32, 31],
    last5Games: [29, 36, 32, 31, 34],
    last15Games: [34, 32, 28, 35, 31, 33, 29, 36, 32, 31, 33, 35, 32, 30, 34],
    recentForm: "hot",
    opponent: "CHI",
    opponentRank: 22,
    opponentDefStat: "118.2 PPG",
    gameDate: "Nov 14, 2025",
    gameTime: "8:30 PM",
    isHome: false,
    avgLastN: 32.1,
    streak: 7,
    streakType: "over"
  },
  {
    id: 5,
    name: "Stephen Curry",
    team: "GSW",
    teamColor: "#1D428A",
    position: "PG",
    statType: "Points",
    line: 27.5,
    hitRate: 65,
    trustScore: 79,
    lastGames: [30, 25, 28, 24, 29, 26, 31, 23, 27, 28],
    last5Games: [31, 23, 27, 28, 30],
    last15Games: [30, 25, 28, 24, 29, 26, 31, 23, 27, 28, 29, 26, 28, 25, 30],
    recentForm: "hot",
    opponent: "LAL",
    opponentRank: 15,
    opponentDefStat: "114.7 PPG",
    gameDate: "Nov 14, 2025",
    gameTime: "7:30 PM",
    isHome: false,
    avgLastN: 27.8,
    streak: 0
  },
  {
    id: 6,
    name: "Nikola Jokić",
    team: "DEN",
    teamColor: "#0E2240",
    position: "C",
    statType: "Rebounds",
    line: 11.5,
    hitRate: 80,
    trustScore: 91,
    lastGames: [13, 12, 14, 11, 13, 12, 15, 12, 13, 14],
    last5Games: [15, 12, 13, 14, 13],
    last15Games: [13, 12, 14, 11, 13, 12, 15, 12, 13, 14, 13, 12, 14, 13, 12],
    recentForm: "hot",
    opponent: "MIN",
    opponentRank: 10,
    opponentDefStat: "44.2 RPG",
    gameDate: "Nov 15, 2025",
    gameTime: "9:00 PM",
    isHome: true,
    avgLastN: 12.9,
    streak: 8,
    streakType: "over"
  },
  {
    id: 7,
    name: "Kevin Durant",
    team: "PHX",
    teamColor: "#E56020",
    position: "SF",
    statType: "Points",
    line: 28.5,
    hitRate: 45,
    trustScore: 58,
    lastGames: [26, 24, 31, 25, 27, 23, 29, 22, 26, 24],
    last5Games: [29, 22, 26, 24, 26],
    last15Games: [26, 24, 31, 25, 27, 23, 29, 22, 26, 24, 25, 27, 24, 26, 23],
    recentForm: "cold",
    opponent: "DAL",
    opponentRank: 14,
    opponentDefStat: "115.8 PPG",
    gameDate: "Nov 14, 2025",
    gameTime: "8:00 PM",
    isHome: true,
    avgLastN: 25.4,
    streak: 4,
    streakType: "under"
  },
  {
    id: 8,
    name: "Joel Embiid",
    team: "PHI",
    teamColor: "#006BB6",
    position: "C",
    statType: "Points",
    line: 32.5,
    hitRate: 50,
    trustScore: 64,
    lastGames: [35, 30, 34, 28, 31, 29, 36, 27, 33, 30],
    last5Games: [36, 27, 33, 30, 35],
    last15Games: [35, 30, 34, 28, 31, 29, 36, 27, 33, 30, 32, 31, 29, 34, 30],
    recentForm: "neutral",
    opponent: "BKN",
    opponentRank: 20,
    opponentDefStat: "116.5 PPG",
    gameDate: "Nov 15, 2025",
    gameTime: "7:30 PM",
    isHome: true,
    avgLastN: 31.3,
    streak: 0
  }
];

// Team Quarter Insights Component - Displays team quarter analytics
const TeamQuarterInsights = ({ allTeams }) => {
  const [quarterData, setQuarterData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedTeam1, setSelectedTeam1] = useState('');
  const [selectedTeam2, setSelectedTeam2] = useState('');
  const [isExpanded, setIsExpanded] = useState(false);

  // Set default teams when component mounts
  useEffect(() => {
    if (allTeams && allTeams.length >= 2 && !selectedTeam1 && !selectedTeam2) {
      setSelectedTeam1(allTeams[0]);
      setSelectedTeam2(allTeams[1]);
    }
  }, [allTeams]);

  useEffect(() => {
    if (selectedTeam1 && selectedTeam2 && selectedTeam1 !== selectedTeam2) {
      fetchQuarterData();
    }
  }, [selectedTeam1, selectedTeam2]);

  const fetchQuarterData = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/quarters/matchup?team1=${selectedTeam1}&team2=${selectedTeam2}&season=2025-26`
      );
      const data = await response.json();

      if (data.success) {
        setQuarterData(data.matchup);
      }
    } catch (err) {
      console.error('Error fetching quarter data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!allTeams || allTeams.length < 2) return null;

  const { team1: t1Data, team2: t2Data, insights } = quarterData || {};

  return (
    <div className="bg-white dark:bg-gray-950 rounded-xl border border-gray-200 dark:border-gray-800 mb-8 overflow-hidden">
      {/* Collapsible Header */}
      <button
        onClick={() => setIsExpanded(prev => !prev)}
        className="w-full flex items-center justify-between p-4 sm:p-5 hover:bg-gray-50 dark:hover:bg-gray-900 transition-colors"
      >
        <h2 className="text-base font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <span className="w-[3px] h-5 bg-blue-500 rounded-full flex-shrink-0" />
          <TrendingUp className="w-4 h-4 text-blue-500 flex-shrink-0" />
          Quarter Performance Insights
        </h2>
        <ChevronRight className={`w-4 h-4 text-gray-400 transition-transform flex-shrink-0 ${isExpanded ? 'rotate-90' : ''}`} />
      </button>

      {isExpanded && (
        <div className="border-t border-gray-200 dark:border-gray-800 p-4 sm:p-5">
          {/* Team Selectors */}
          <div className="flex flex-wrap items-center gap-2 sm:gap-4 mb-5">
            <div className="flex items-center gap-2">
              <label className="text-xs font-medium text-gray-500 dark:text-gray-400 whitespace-nowrap">Team 1:</label>
              <select
                value={selectedTeam1}
                onChange={(e) => setSelectedTeam1(e.target.value)}
                className="px-2 py-1.5 border border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:text-white rounded-lg text-sm focus:ring-2 focus:ring-blue-500 max-w-[130px]"
              >
                {allTeams.map(team => (
                  <option key={team} value={team}>{team}</option>
                ))}
              </select>
            </div>

            <span className="text-xs font-bold text-gray-400 dark:text-gray-500">VS</span>

            <div className="flex items-center gap-2">
              <label className="text-xs font-medium text-gray-500 dark:text-gray-400 whitespace-nowrap">Team 2:</label>
              <select
                value={selectedTeam2}
                onChange={(e) => setSelectedTeam2(e.target.value)}
                className="px-2 py-1.5 border border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:text-white rounded-lg text-sm focus:ring-2 focus:ring-blue-500 max-w-[130px]"
              >
                {allTeams.map(team => (
                  <option key={team} value={team}>{team}</option>
                ))}
              </select>
            </div>
          </div>

          {loading && (
            <div className="py-4 space-y-2 animate-pulse">
              <div className="h-3 bg-gray-200 dark:bg-gray-800 rounded w-3/4" />
              <div className="h-3 bg-gray-200 dark:bg-gray-800 rounded w-1/2" />
              <div className="h-3 bg-gray-200 dark:bg-gray-800 rounded w-2/3" />
            </div>
          )}

          {!loading && !quarterData && (
            <p className="text-sm text-center py-6 text-gray-500 dark:text-gray-400">
              No quarter data available for this matchup
            </p>
          )}

          {!loading && quarterData && t1Data && t2Data && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Team 1 */}
                <div className="bg-gray-50 dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-4">
                  <h3 className="text-sm font-bold text-gray-900 dark:text-white mb-3 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-blue-500 flex-shrink-0" />
                    {t1Data.team}
                  </h3>
                  <div className="grid grid-cols-4 gap-2 mb-4">
                    {[['Q1', t1Data.q1_avg], ['Q2', t1Data.q2_avg], ['Q3', t1Data.q3_avg], ['Q4', t1Data.q4_avg]].map(([q, val]) => (
                      <div key={q} className="text-center">
                        <div className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">{q}</div>
                        <div className="text-xl font-bold tabular-nums text-blue-500">{val}</div>
                      </div>
                    ))}
                  </div>
                  <div className="space-y-1.5 text-sm border-t border-gray-200 dark:border-gray-800 pt-3">
                    <div className="flex justify-between">
                      <span className="text-gray-500 dark:text-gray-400">First Half Avg</span>
                      <span className="font-semibold tabular-nums text-gray-900 dark:text-white">{t1Data.first_half_avg} pts</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500 dark:text-gray-400">Second Half Avg</span>
                      <span className="font-semibold tabular-nums text-gray-900 dark:text-white">{t1Data.second_half_avg} pts</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500 dark:text-gray-400">Through 3Q</span>
                      <span className="font-semibold tabular-nums text-gray-900 dark:text-white">{t1Data.three_quarter_avg} pts</span>
                    </div>
                    <div className="flex justify-between pt-1.5 mt-1 border-t border-gray-200 dark:border-gray-800">
                      <span className="text-gray-500 dark:text-gray-400">100+ by Q3</span>
                      <span className={`font-bold tabular-nums ${t1Data.reached_100_by_q3_pct >= 50 ? 'text-green-500' : 'text-amber-500'}`}>
                        {t1Data.reached_100_by_q3_pct}%
                        <span className="font-normal text-gray-500 dark:text-gray-400 ml-1">({t1Data.reached_100_by_q3_count}/{t1Data.total_games})</span>
                      </span>
                    </div>
                  </div>
                </div>

                {/* Team 2 */}
                <div className="bg-gray-50 dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-4">
                  <h3 className="text-sm font-bold text-gray-900 dark:text-white mb-3 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-amber-500 flex-shrink-0" />
                    {t2Data.team}
                  </h3>
                  <div className="grid grid-cols-4 gap-2 mb-4">
                    {[['Q1', t2Data.q1_avg], ['Q2', t2Data.q2_avg], ['Q3', t2Data.q3_avg], ['Q4', t2Data.q4_avg]].map(([q, val]) => (
                      <div key={q} className="text-center">
                        <div className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">{q}</div>
                        <div className="text-xl font-bold tabular-nums text-amber-500">{val}</div>
                      </div>
                    ))}
                  </div>
                  <div className="space-y-1.5 text-sm border-t border-gray-200 dark:border-gray-800 pt-3">
                    <div className="flex justify-between">
                      <span className="text-gray-500 dark:text-gray-400">First Half Avg</span>
                      <span className="font-semibold tabular-nums text-gray-900 dark:text-white">{t2Data.first_half_avg} pts</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500 dark:text-gray-400">Second Half Avg</span>
                      <span className="font-semibold tabular-nums text-gray-900 dark:text-white">{t2Data.second_half_avg} pts</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500 dark:text-gray-400">Through 3Q</span>
                      <span className="font-semibold tabular-nums text-gray-900 dark:text-white">{t2Data.three_quarter_avg} pts</span>
                    </div>
                    <div className="flex justify-between pt-1.5 mt-1 border-t border-gray-200 dark:border-gray-800">
                      <span className="text-gray-500 dark:text-gray-400">100+ by Q3</span>
                      <span className={`font-bold tabular-nums ${t2Data.reached_100_by_q3_pct >= 50 ? 'text-green-500' : 'text-amber-500'}`}>
                        {t2Data.reached_100_by_q3_pct}%
                        <span className="font-normal text-gray-500 dark:text-gray-400 ml-1">({t2Data.reached_100_by_q3_count}/{t2Data.total_games})</span>
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Key Insights */}
              {insights && insights.length > 0 && (
                <div className="bg-gray-50 dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-4">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-2 flex items-center gap-1.5">
                    <Flame className="w-3.5 h-3.5 text-amber-500" />
                    Key Insights
                  </h4>
                  <ul className="space-y-1">
                    {insights.map((insight, idx) => (
                      <li key={idx} className="text-sm text-gray-700 dark:text-gray-300 flex items-start gap-1.5">
                        <span className="text-blue-500 mt-0.5 flex-shrink-0">•</span>
                        {insight}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Bookmaker Selector Component - Clean dropdown for sportsbook lines
const BookmakerSelector = ({ bookmakerLines }) => {
  const [selectedBookmaker, setSelectedBookmaker] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Get unique bookmakers (combine duplicates)
  const uniqueBookmakers = useMemo(() => {
    const bookmakerMap = {};
    bookmakerLines.forEach(bm => {
      if (!bookmakerMap[bm.bookmaker]) {
        bookmakerMap[bm.bookmaker] = bm;
      }
    });
    return Object.values(bookmakerMap);
  }, [bookmakerLines]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const currentBookmaker = uniqueBookmakers[selectedBookmaker] || uniqueBookmakers[0];

  if (!currentBookmaker) return null;

  return (
    <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600" onClick={(e) => e.stopPropagation()}>
      <div className="flex items-center justify-between">
        <div className="text-xs text-gray-500 dark:text-gray-400 font-semibold">
          SPORTSBOOK LINE
        </div>

        {/* Dropdown selector */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsOpen(!isOpen);
            }}
            className="flex items-center gap-1 px-2 py-1 bg-gray-100 dark:bg-gray-900 rounded text-xs font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
          >
            {currentBookmaker.bookmaker}
            <svg className={`w-3 h-3 transition-transform ${isOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {/* Dropdown menu */}
          {isOpen && uniqueBookmakers.length > 1 && (
            <div className="absolute right-0 mt-1 w-32 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-600 rounded-lg shadow-lg z-10">
              {uniqueBookmakers.map((bm, idx) => (
                <button
                  key={idx}
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedBookmaker(idx);
                    setIsOpen(false);
                  }}
                  className={`w-full text-left px-3 py-2 text-xs hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors ${
                    idx === selectedBookmaker ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 font-semibold' : 'text-gray-700 dark:text-gray-300'
                  } ${idx === 0 ? 'rounded-t-lg' : ''} ${idx === uniqueBookmakers.length - 1 ? 'rounded-b-lg' : ''}`}
                >
                  {bm.bookmaker}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Display the selected line */}
      <div className="mt-2 flex items-center justify-between bg-gray-50 dark:bg-gray-800 border border-gray-100 dark:border-gray-700 rounded-lg p-2">
        <span className="text-xs text-gray-500 dark:text-gray-400 font-medium">Line</span>
        <span className="text-lg font-bold tabular-nums text-gray-900 dark:text-white">{currentBookmaker.line}</span>
      </div>
    </div>
  );
};

// Player Detail Modal Component - Full analysis page
const PlayerDetailModal = ({ player, onClose }) => {
  if (!player) return null;

  const [matchupHistory, setMatchupHistory] = React.useState(null);
  const [loadingMatchup, setLoadingMatchup] = React.useState(false);
  const [locationSplit, setLocationSplit] = React.useState(null);
  const [loadingSplit, setLoadingSplit] = React.useState(false);
  const [halfTendency, setHalfTendency] = React.useState(null);
  const [loadingHalf, setLoadingHalf] = React.useState(false);
  const [liveInput, setLiveInput] = React.useState('');
  const [liveProjection, setLiveProjection] = React.useState(null);
  const [loadingProjection, setLoadingProjection] = React.useState(false);

  // Load matchup history, location split, and half tendency when modal opens
  React.useEffect(() => {
    if (player && player.opponent) {
      loadMatchupHistory();
      loadLocationSplit();
      loadHalfTendency();
    }
  }, [player]);

  const loadMatchupHistory = async () => {
    setLoadingMatchup(true);
    try {
      const response = await fetch(`${API_BASE_URL}/matchup/${encodeURIComponent(player.name)}/${player.opponent}`);
      const data = await response.json();

      if (data.success) {
        setMatchupHistory(data.matchup);
      }
    } catch (error) {
      console.error('Error loading matchup history:', error);
    } finally {
      setLoadingMatchup(false);
    }
  };

  const loadLocationSplit = async () => {
    setLoadingSplit(true);
    try {
      const isHomeInt = player.isHome ? 1 : 0;
      const response = await fetch(`${API_BASE_URL}/location-split/${encodeURIComponent(player.name)}/${encodeURIComponent(player.statType)}/${isHomeInt}`);
      const data = await response.json();

      if (data.success) {
        setLocationSplit(data.split);
      }
    } catch (error) {
      console.error('Error loading location split:', error);
    } finally {
      setLoadingSplit(false);
    }
  };

  const loadHalfTendency = async () => {
    setLoadingHalf(true);
    try {
      const response = await fetch(`${API_BASE_URL}/half-tendency/${encodeURIComponent(player.name)}/${encodeURIComponent(player.statType)}`);
      const data = await response.json();

      if (data.success) {
        setHalfTendency(data.tendency);
      }
    } catch (error) {
      console.error('Error loading half tendency:', error);
    } finally {
      setLoadingHalf(false);
    }
  };

  const calculateLiveProjection = async () => {
    console.log('calculateLiveProjection called with liveInput:', liveInput);

    if (!liveInput || isNaN(parseFloat(liveInput))) {
      console.log('Invalid input, returning early');
      return;
    }

    setLoadingProjection(true);
    try {
      const url = `${API_BASE_URL}/live-projection/${encodeURIComponent(player.name)}/${encodeURIComponent(player.statType)}/${liveInput}`;
      console.log('Fetching projection from:', url);

      const response = await fetch(url);
      const data = await response.json();

      console.log('Projection response:', data);

      if (data.success) {
        setLiveProjection(data.projection);
        console.log('Projection set successfully');
      } else {
        console.error('Projection API returned success=false:', data);
      }
    } catch (error) {
      console.error('Error loading projection:', error);
    } finally {
      setLoadingProjection(false);
    }
  };

  // Calculate some stats
  const last5Avg = player.last5Games && player.last5Games.length > 0
    ? (player.last5Games.reduce((a, b) => a + b, 0) / player.last5Games.length).toFixed(1)
    : 0;
  const last15Avg = player.last15Games && player.last15Games.length > 0
    ? (player.last15Games.reduce((a, b) => a + b, 0) / player.last15Games.length).toFixed(1)
    : 0;

  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div
        className="bg-white dark:bg-gray-950 rounded-xl border border-gray-200 dark:border-gray-800 shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-gray-950 border-b border-gray-200 dark:border-gray-800 p-5 rounded-t-xl z-10">
          <div className="flex justify-between items-start">
            <div>
              <div className="flex items-center gap-2">
                <span className="w-[3px] h-6 bg-blue-500 rounded-full flex-shrink-0" />
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">{player.name}</h2>
                {player.injuryStatus && player.injuryStatus !== 'ACTIVE' && (
                  <span className={`px-2 py-0.5 text-xs font-bold rounded-full border ${
                    player.injuryStatus === 'OUT'
                      ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300 border-red-300 dark:border-red-800'
                      : player.injuryStatus === 'QUESTIONABLE'
                      ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300 border-yellow-300 dark:border-yellow-800'
                      : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 border-blue-300 dark:border-blue-800'
                  }`}>{player.injuryStatus}</span>
                )}
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 flex items-center gap-1.5 ml-3">
                <span className="inline-block w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: player.teamColor }} />
                {player.team} • {player.position} • {player.statType}
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-lg text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors flex-shrink-0"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-3 gap-3 mt-4">
            <div className="bg-gray-50 dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-3">
              <div className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-1">Line</div>
              <div className="text-2xl font-bold tabular-nums text-gray-900 dark:text-white">{player.line}</div>
            </div>
            <div className="bg-gray-50 dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-3">
              <div className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-1">Hit Rate</div>
              <div className={`text-2xl font-bold tabular-nums ${
                player.hitRate >= 70 ? 'text-green-500' : player.hitRate >= 55 ? 'text-blue-500' : 'text-red-400'
              }`}>{player.hitRate}%</div>
            </div>
            <div className="bg-gray-50 dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-3">
              <div className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-1">Trust</div>
              <div className={`text-2xl font-bold tabular-nums ${
                player.trustScore >= 80 ? 'text-green-500' : player.trustScore >= 70 ? 'text-amber-500' : player.trustScore >= 60 ? 'text-yellow-500' : 'text-red-500'
              }`}>{player.trustScore}</div>
              <div className="text-[10px] text-gray-400 dark:text-gray-500 mt-0.5">{getTrustLabel(player.trustScore)}</div>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-5 space-y-6">
          {/* Performance Overview */}
          <div>
            <h3 className="text-base font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-4">
              <span className="w-0.5 h-4 bg-blue-500 rounded-full flex-shrink-0" />
              Performance Overview
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-4">
                <div className="text-sm text-gray-600 dark:text-gray-400">Last 5 Games Average</div>
                <div className="text-3xl font-bold tabular-nums text-gray-900 dark:text-white">{last5Avg}</div>
                <div className={`text-sm font-semibold ${last5Avg > player.line ? 'text-green-600' : 'text-red-600'}`}>
                  {last5Avg > player.line ? `+${(last5Avg - player.line).toFixed(1)} vs line` : `${(last5Avg - player.line).toFixed(1)} vs line`}
                </div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-4">
                <div className="text-sm text-gray-600 dark:text-gray-400">Last 15 Games Average</div>
                <div className="text-3xl font-bold tabular-nums text-gray-900 dark:text-white">{last15Avg}</div>
                <div className={`text-sm font-semibold ${last15Avg > player.line ? 'text-green-600' : 'text-red-600'}`}>
                  {last15Avg > player.line ? `+${(last15Avg - player.line).toFixed(1)} vs line` : `${(last15Avg - player.line).toFixed(1)} vs line`}
                </div>
              </div>
            </div>
          </div>

          {/* Performance Charts */}
          <div>
            <h3 className="text-base font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-4">
              <span className="w-0.5 h-4 bg-blue-500 rounded-full flex-shrink-0" />
              Performance Trends
            </h3>

            {/* Line Chart - Performance over time */}
            <div className="bg-gray-50 dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-4 mb-4">
              <div className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-3">Last 15 Games Performance</div>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={player.last15Games ? player.last15Games.map((stat, idx) => ({
                  game: `G${idx + 1}`,
                  value: stat,
                  line: player.line,
                  date: player.last15GamesDates ? player.last15GamesDates[idx] : null
                })).reverse() : []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
                  <XAxis dataKey="game" stroke="#9CA3AF" style={{ fontSize: '12px' }} />
                  <YAxis stroke="#9CA3AF" style={{ fontSize: '12px' }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1F2937',
                      border: '1px solid #374151',
                      borderRadius: '8px',
                      color: '#F3F4F6'
                    }}
                    labelStyle={{ color: '#9CA3AF' }}
                    itemStyle={{ color: '#F3F4F6' }}
                    labelFormatter={(label, payload) => {
                      const date = payload?.[0]?.payload?.date;
                      return date ? `${label} · ${new Date(date + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}` : label;
                    }}
                    formatter={(value) => [`${value} ${player.statType}`, 'Performance']}
                  />
                  <ReferenceLine
                    y={player.line}
                    stroke="#EF4444"
                    strokeDasharray="3 3"
                    label={{ value: `Line: ${player.line}`, fill: '#EF4444', fontSize: 12 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="value"
                    stroke="#3B82F6"
                    strokeWidth={3}
                    dot={{ fill: '#3B82F6', r: 4 }}
                    activeDot={{ r: 6 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Bar Chart - Hit/Miss Visualization */}
            <div className="bg-gray-50 dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-4">
              <div className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-3">Over/Under Results</div>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={player.last15Games ? player.last15Games.map((stat, idx) => ({
                  game: `G${idx + 1}`,
                  value: stat,
                  hit: stat > player.line,
                  date: player.last15GamesDates ? player.last15GamesDates[idx] : null
                })).reverse() : []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
                  <XAxis dataKey="game" stroke="#9CA3AF" style={{ fontSize: '12px' }} />
                  <YAxis stroke="#9CA3AF" style={{ fontSize: '12px' }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1F2937',
                      border: '1px solid #374151',
                      borderRadius: '8px',
                      color: '#F3F4F6'
                    }}
                    labelStyle={{ color: '#9CA3AF' }}
                    itemStyle={{ color: '#F3F4F6' }}
                    labelFormatter={(label, payload) => {
                      const date = payload?.[0]?.payload?.date;
                      return date ? `${label} · ${new Date(date + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}` : label;
                    }}
                    formatter={(value, name, props) => [
                      `${value} ${player.statType}`,
                      props.payload.hit ? 'OVER ✓' : 'UNDER ✗'
                    ]}
                  />
                  <ReferenceLine y={player.line} stroke="#EF4444" strokeDasharray="3 3" />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                    {player.last15Games && [...player.last15Games].reverse().map((stat, idx) => (
                      <Cell key={idx} fill={stat > player.line ? '#10B981' : '#EF4444'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Game Log */}
          <div>
            <h3 className="text-base font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-4">
              <span className="w-0.5 h-4 bg-blue-500 rounded-full flex-shrink-0" />
              Recent Game Log
            </h3>
            <div className="bg-gray-50 dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-100 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                  <tr>
                    <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Date</th>
                    <th className="px-4 py-2.5 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">{player.statType}</th>
                    <th className="px-4 py-2.5 text-center text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">vs Line</th>
                    <th className="px-4 py-2.5 text-center text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Result</th>
                  </tr>
                </thead>
                <tbody>
                  {player.last15Games && player.last15Games.slice(0, 10).map((stat, idx) => {
                    const hitLine = stat > player.line;
                    const gameDate = player.last15GamesDates?.[idx];
                    const dateLabel = gameDate
                      ? new Date(gameDate + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
                      : `G${idx + 1}`;
                    return (
                      <tr key={idx} className="border-t border-gray-100 dark:border-gray-800 hover:bg-gray-100 dark:hover:bg-gray-800/50">
                        <td className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400">{dateLabel}</td>
                        <td className="px-4 py-2 text-right text-sm font-bold tabular-nums text-gray-900 dark:text-white">{stat}</td>
                        <td className={`px-4 py-2 text-center text-sm font-semibold tabular-nums ${hitLine ? 'text-green-600' : 'text-red-600'}`}>
                          {hitLine ? '+' : ''}{(stat - player.line).toFixed(1)}
                        </td>
                        <td className="px-4 py-2 text-center">
                          {hitLine ? (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                              OVER
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
                              UNDER
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Sportsbook Lines Comparison */}
          {player.bookmakerLines && player.bookmakerLines.length > 0 && (
            <div>
              <h3 className="text-base font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-4">
                <span className="w-0.5 h-4 bg-blue-500 rounded-full flex-shrink-0" />
                Sportsbook Lines
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {(() => {
                  // Get unique bookmakers with their best lines
                  const bookmakerMap = {};
                  player.bookmakerLines.forEach(bm => {
                    if (!bookmakerMap[bm.bookmaker]) {
                      bookmakerMap[bm.bookmaker] = bm;
                    }
                  });
                  return Object.values(bookmakerMap).map((bm, idx) => (
                    <div key={idx} className="bg-gray-50 dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-4">
                      <div className="flex justify-between items-center">
                        <div>
                          <div className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-1">{bm.bookmaker}</div>
                          <div className="text-2xl font-bold tabular-nums text-gray-900 dark:text-white">{bm.line}</div>
                        </div>
                        <div className="text-right space-y-1">
                          {bm.over_odds && <div className="text-xs text-green-500 font-semibold">O {bm.over_odds > 0 ? `+${bm.over_odds}` : bm.over_odds}</div>}
                          {bm.under_odds && <div className="text-xs text-red-400 font-semibold">U {bm.under_odds > 0 ? `+${bm.under_odds}` : bm.under_odds}</div>}
                        </div>
                      </div>
                    </div>
                  ));
                })()}
              </div>
            </div>
          )}

          {/* Location Split (Home vs Away) */}
          <div>
            <h3 className="text-base font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-4">
              <span className="w-0.5 h-4 bg-blue-500 rounded-full flex-shrink-0" />
              Home vs Away Performance
            </h3>

            {loadingSplit && (
              <div className="py-4 space-y-2 animate-pulse">
                <div className="h-3 bg-gray-200 dark:bg-gray-800 rounded w-3/4" />
                <div className="h-3 bg-gray-200 dark:bg-gray-800 rounded w-1/2" />
                <div className="h-3 bg-gray-200 dark:bg-gray-800 rounded w-2/3" />
              </div>
            )}

            {!loadingSplit && locationSplit && locationSplit.has_data && (
              <div>
                {locationSplit.warning && (
                  <div className={`mb-4 p-3 rounded-lg border ${
                    locationSplit.is_significant
                      ? locationSplit.favorable_location
                        ? 'bg-green-50 border-green-300 dark:bg-green-900/20 dark:border-green-800'
                        : 'bg-yellow-50 border-yellow-300 dark:bg-yellow-900/20 dark:border-yellow-800'
                      : 'bg-blue-50 border-blue-300 dark:bg-blue-900/20 dark:border-blue-800'
                  }`}>
                    <p className={`text-sm font-semibold ${
                      locationSplit.is_significant
                        ? locationSplit.favorable_location
                          ? 'text-green-700 dark:text-green-300'
                          : 'text-yellow-700 dark:text-yellow-300'
                        : 'text-blue-700 dark:text-blue-300'
                    }`}>
                      {locationSplit.warning}
                    </p>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4">
                  {/* Home Stats */}
                  <div className={`rounded-xl p-4 border ${
                    player.isHome
                      ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-300 dark:border-blue-700 ring-2 ring-blue-400 dark:ring-blue-600'
                      : 'bg-gray-50 dark:bg-gray-900 border-gray-100 dark:border-gray-800'
                  }`}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-sm font-medium text-gray-600 dark:text-gray-400">🏠 Home</div>
                      {player.isHome && (
                        <span className="text-xs px-2 py-0.5 bg-blue-600 text-white rounded-full font-semibold">
                          Tonight
                        </span>
                      )}
                    </div>
                    <div className="text-2xl font-bold text-gray-900 dark:text-white">
                      {locationSplit.home_avg}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {locationSplit.home_games} games
                    </div>
                  </div>

                  {/* Away Stats */}
                  <div className={`rounded-xl p-4 border ${
                    !player.isHome
                      ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-300 dark:border-blue-700 ring-2 ring-blue-400 dark:ring-blue-600'
                      : 'bg-gray-50 dark:bg-gray-900 border-gray-100 dark:border-gray-800'
                  }`}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-sm font-medium text-gray-600 dark:text-gray-400">✈️ Away</div>
                      {!player.isHome && (
                        <span className="text-xs px-2 py-0.5 bg-blue-600 text-white rounded-full font-semibold">
                          Tonight
                        </span>
                      )}
                    </div>
                    <div className="text-2xl font-bold text-gray-900 dark:text-white">
                      {locationSplit.away_avg}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {locationSplit.away_games} games
                    </div>
                  </div>
                </div>

                {/* Difference Indicator */}
                <div className="mt-3 text-center">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    Difference: <span className={`font-bold ${
                      Math.abs(locationSplit.difference) >= 3.0
                        ? 'text-orange-600 dark:text-orange-400'
                        : 'text-gray-700 dark:text-gray-300'
                    }`}>
                      {locationSplit.difference > 0 ? '+' : ''}{locationSplit.difference}
                    </span> {player.statType.toLowerCase()} {locationSplit.better_at_home ? 'better at home' : 'better away'}
                  </span>
                </div>
              </div>
            )}

            {!loadingSplit && locationSplit && !locationSplit.has_data && (
              <p className="text-center text-gray-500 dark:text-gray-400 py-4">
                Not enough data for location split (minimum 3 home and 3 away games required)
              </p>
            )}
          </div>

          {/* Halftime Betting Tool */}
          <div>
            <h3 className="text-base font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-4">
              <span className="w-0.5 h-4 bg-blue-500 rounded-full flex-shrink-0" />
              Halftime Betting Tool
            </h3>

            {loadingHalf && (
              <div className="py-4 space-y-2 animate-pulse">
                <div className="h-3 bg-gray-200 dark:bg-gray-800 rounded w-3/4" />
                <div className="h-3 bg-gray-200 dark:bg-gray-800 rounded w-1/2" />
                <div className="h-3 bg-gray-200 dark:bg-gray-800 rounded w-2/3" />
              </div>
            )}

            {!loadingHalf && halfTendency && halfTendency.has_data && (
              <div>
                {/* First Half / Second Half Expectations */}
                <div className="bg-gray-50 dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-4 mb-4">
                  <div className="grid grid-cols-3 gap-4 mb-3">
                    <div>
                      <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">Season Avg</div>
                      <div className="text-xl font-bold tabular-nums text-gray-900 dark:text-white">{halfTendency.season_avg}</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">Expected 1H</div>
                      <div className="text-xl font-bold tabular-nums text-blue-500">{halfTendency.first_half_avg}</div>
                      <div className="text-xs text-gray-500">({(halfTendency.first_half_pct * 100).toFixed(0)}%)</div>
                    </div>
                    <div>
                      <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">Expected 2H</div>
                      <div className="text-xl font-bold tabular-nums text-blue-400">{halfTendency.second_half_avg}</div>
                      <div className="text-xs text-gray-500">({(halfTendency.second_half_pct * 100).toFixed(0)}%)</div>
                    </div>
                  </div>
                  {halfTendency.strong_finisher && (
                    <div className="bg-green-100 dark:bg-green-900/30 border border-green-300 dark:border-green-700 rounded px-3 py-2 text-sm">
                      <span className="font-semibold text-green-800 dark:text-green-300">💪 Strong 2H Finisher</span>
                      <span className="text-green-700 dark:text-green-400 ml-2">- Tends to score more in second half</span>
                    </div>
                  )}
                </div>

                {/* Live Projection Calculator */}
                <div className="bg-gray-50 dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-4">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Live Projection Calculator</h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                    Enter player's current {player.statType.toLowerCase()} at halftime:
                  </p>

                  <div className="flex gap-2 mb-4">
                    <input
                      type="number"
                      value={liveInput}
                      onChange={(e) => setLiveInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && calculateLiveProjection()}
                      placeholder={`e.g., ${Math.floor(halfTendency.first_half_avg)}`}
                      className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                    />
                    <button
                      onClick={() => {
                        console.log('Project button clicked, liveInput:', liveInput);
                        calculateLiveProjection();
                      }}
                      disabled={loadingProjection || !liveInput}
                      className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold rounded-lg transition-colors"
                    >
                      {loadingProjection ? 'Calculating...' : 'Project'}
                    </button>
                  </div>

                  {liveProjection && liveProjection.has_projection && (
                    <div className={`rounded-lg p-4 border-2 ${
                      liveProjection.status === 'ahead_of_pace'
                        ? 'bg-green-50 dark:bg-green-900/20 border-green-300 dark:border-green-700'
                        : liveProjection.status === 'behind_pace'
                        ? 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-300 dark:border-yellow-700'
                        : 'bg-blue-50 dark:bg-blue-900/20 border-blue-300 dark:border-blue-700'
                    }`}>
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-2xl">{liveProjection.status === 'ahead_of_pace' ? '🔥' : liveProjection.status === 'behind_pace' ? '❄️' : '📊'}</span>
                        <span className={`font-bold text-lg ${
                          liveProjection.status === 'ahead_of_pace'
                            ? 'text-green-800 dark:text-green-300'
                            : liveProjection.status === 'behind_pace'
                            ? 'text-yellow-800 dark:text-yellow-300'
                            : 'text-blue-800 dark:text-blue-300'
                        }`}>
                          {liveProjection.outlook}
                        </span>
                      </div>

                      <div className="grid grid-cols-2 gap-3 mt-3">
                        <div>
                          <div className="text-xs text-gray-600 dark:text-gray-400">Projected 2H</div>
                          <div className="text-xl font-bold text-gray-900 dark:text-white">+{liveProjection.projected_second_half}</div>
                        </div>
                        <div>
                          <div className="text-xs text-gray-600 dark:text-gray-400">Projected Total</div>
                          <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">{liveProjection.projected_total}</div>
                        </div>
                      </div>

                      <div className="mt-3 pt-3 border-t border-gray-300 dark:border-gray-600 text-sm text-gray-700 dark:text-gray-300">
                        <div className="flex justify-between">
                          <span>Current at Halftime:</span>
                          <span className="font-semibold">{liveProjection.current_stat}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>vs Expected 1H:</span>
                          <span className="font-semibold">{liveProjection.expected_first_half}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Difference:</span>
                          <span className={`font-semibold ${liveProjection.difference_from_pace > 0 ? 'text-green-600' : liveProjection.difference_from_pace < 0 ? 'text-red-600' : ''}`}>
                            {liveProjection.difference_from_pace > 0 ? '+' : ''}{liveProjection.difference_from_pace}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {!loadingHalf && halfTendency && !halfTendency.has_data && (
              <p className="text-center text-gray-500 dark:text-gray-400 py-4">
                Not enough data for halftime analysis (minimum 10 games required)
              </p>
            )}
          </div>

          {/* Matchup History vs Opponent */}
          <div>
            <h3 className="text-base font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-4">
              <span className="w-0.5 h-4 bg-blue-500 rounded-full flex-shrink-0" />
              Matchup History vs {player.opponent}
            </h3>

            {loadingMatchup && (
              <div className="py-4 space-y-2 animate-pulse">
                <div className="h-3 bg-gray-200 dark:bg-gray-800 rounded w-3/4" />
                <div className="h-3 bg-gray-200 dark:bg-gray-800 rounded w-1/2" />
                <div className="h-3 bg-gray-200 dark:bg-gray-800 rounded w-2/3" />
              </div>
            )}

            {!loadingMatchup && matchupHistory && matchupHistory.games_played > 0 && (
              <div>
                {/* Matchup Averages */}
                <div className="grid grid-cols-3 gap-3 mb-4">
                  <div className="bg-gray-50 dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-4">
                    <div className="text-sm text-gray-600 dark:text-gray-400">Games Played</div>
                    <div className="text-2xl font-bold tabular-nums text-gray-900 dark:text-white">{matchupHistory.games_played}</div>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-4">
                    <div className="text-sm text-gray-600 dark:text-gray-400">Avg {player.statType}</div>
                    <div className="text-2xl font-bold tabular-nums text-gray-900 dark:text-white">
                      {(() => {
                        const statMap = {
                          'Points': matchupHistory.averages.points,
                          'Rebounds': matchupHistory.averages.rebounds,
                          'Assists': matchupHistory.averages.assists,
                          'Steals': matchupHistory.averages.steals,
                          'Blocks': matchupHistory.averages.blocks,
                          '3PM': matchupHistory.averages.three_pm,
                          'PRA': matchupHistory.averages.PRA,
                          'PA': matchupHistory.averages.PA,
                          'PR': matchupHistory.averages.PR,
                          'RA': matchupHistory.averages.RA
                        };
                        return statMap[player.statType] || 0;
                      })()}
                    </div>
                    <div className={`text-sm font-semibold ${(() => {
                      const statMap = {
                        'Points': matchupHistory.averages.points,
                        'Rebounds': matchupHistory.averages.rebounds,
                        'Assists': matchupHistory.averages.assists,
                        'Steals': matchupHistory.averages.steals,
                        'Blocks': matchupHistory.averages.blocks,
                        '3PM': matchupHistory.averages.three_pm,
                        'PRA': matchupHistory.averages.PRA,
                        'PA': matchupHistory.averages.PA,
                        'PR': matchupHistory.averages.PR,
                        'RA': matchupHistory.averages.RA
                      };
                      return (statMap[player.statType] || 0) > player.line ? 'text-green-600' : 'text-red-600';
                    })()}`}>
                      vs Line {player.line}
                    </div>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-4">
                    <div className="text-sm text-gray-600 dark:text-gray-400">Avg PRA</div>
                    <div className="text-2xl font-bold tabular-nums text-gray-900 dark:text-white">{matchupHistory.averages.PRA}</div>
                  </div>
                </div>

                {/* All Stats */}
                <div className="bg-gray-50 dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-4 mb-4">
                  <div className="grid grid-cols-6 gap-3">
                    <div className="text-center">
                      <div className="text-xs text-gray-600 dark:text-gray-400">PTS</div>
                      <div className="text-lg font-bold text-gray-900 dark:text-white">{matchupHistory.averages.points}</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xs text-gray-600 dark:text-gray-400">REB</div>
                      <div className="text-lg font-bold text-gray-900 dark:text-white">{matchupHistory.averages.rebounds}</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xs text-gray-600 dark:text-gray-400">AST</div>
                      <div className="text-lg font-bold text-gray-900 dark:text-white">{matchupHistory.averages.assists}</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xs text-gray-600 dark:text-gray-400">STL</div>
                      <div className="text-lg font-bold text-gray-900 dark:text-white">{matchupHistory.averages.steals}</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xs text-gray-600 dark:text-gray-400">BLK</div>
                      <div className="text-lg font-bold text-gray-900 dark:text-white">{matchupHistory.averages.blocks}</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xs text-gray-600 dark:text-gray-400">3PM</div>
                      <div className="text-lg font-bold text-gray-900 dark:text-white">{matchupHistory.averages.three_pm}</div>
                    </div>
                  </div>
                </div>

                {/* Game by Game Breakdown */}
                <div className="bg-gray-50 dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl overflow-hidden">
                  <table className="w-full">
                    <thead className="bg-gray-100 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                      <tr>
                        <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Date</th>
                        <th className="px-4 py-2.5 text-center text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">H/A</th>
                        <th className="px-4 py-2.5 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">PTS</th>
                        <th className="px-4 py-2.5 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">REB</th>
                        <th className="px-4 py-2.5 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">AST</th>
                        <th className="px-4 py-2.5 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">PRA</th>
                        <th className="px-4 py-2.5 text-right text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">MIN</th>
                      </tr>
                    </thead>
                    <tbody>
                      {matchupHistory.games.map((game, idx) => (
                        <tr key={idx} className="border-t border-gray-100 dark:border-gray-800 hover:bg-gray-100 dark:hover:bg-gray-800/50">
                          <td className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400">{game.date}</td>
                          <td className="px-4 py-2 text-center text-sm">
                            {game.is_home ? <Home className="w-4 h-4 mx-auto text-gray-600 dark:text-gray-400" /> : <Plane className="w-4 h-4 mx-auto text-gray-600 dark:text-gray-400" />}
                          </td>
                          <td className="px-4 py-2 text-right text-sm font-bold tabular-nums text-gray-900 dark:text-white">{game.points}</td>
                          <td className="px-4 py-2 text-right text-sm font-bold tabular-nums text-gray-900 dark:text-white">{game.rebounds}</td>
                          <td className="px-4 py-2 text-right text-sm font-bold tabular-nums text-gray-900 dark:text-white">{game.assists}</td>
                          <td className="px-4 py-2 text-right text-sm font-bold tabular-nums text-blue-500">{game.PRA}</td>
                          <td className="px-4 py-2 text-right text-sm tabular-nums text-gray-600 dark:text-gray-400">{game.minutes ? game.minutes.toFixed(1) : '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {!loadingMatchup && matchupHistory && matchupHistory.games_played === 0 && (
              <div className="text-center py-8 text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-900 rounded-lg">
                No previous games found against {player.opponent} this season
              </div>
            )}

            {!loadingMatchup && !matchupHistory && (
              <div className="text-center py-8 text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-900 rounded-lg">
                Unable to load matchup history
              </div>
            )}
          </div>

          {/* Upcoming Game */}
          <div className="bg-gray-50 dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-4 flex justify-between items-center">
            <div>
              <div className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-1">Next Game</div>
              <div className="text-xl font-bold text-gray-900 dark:text-white">{player.team} {player.isHome ? 'vs' : '@'} {player.opponent}</div>
              <div className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{player.gameDate} • {player.gameTime}</div>
            </div>
            <span className={`px-3 py-1.5 rounded-lg text-sm font-semibold ${player.isHome ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300'}`}>
              {player.isHome ? 'Home' : 'Away'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

const SOCCER_MARKETS = [
  { key: 'goals',   label: 'Goals',           arr: 'goalsArr',   min: 0.5, max: 2.5, step: 0.5, defaultLine: 0.5 },
  { key: 'shots',   label: 'Shots',           arr: 'shotsArr',   min: 0.5, max: 4.5, step: 0.5, defaultLine: 1.5 },
  { key: 'assists', label: 'Assists',          arr: 'assistsArr', min: 0.5, max: 1.5, step: 0.5, defaultLine: 0.5 },
  { key: 'ga',      label: 'Score or Assist', arr: 'gaArr',      min: 0.5, max: 2.5, step: 0.5, defaultLine: 0.5 },
  { key: 'gk',      label: 'GK',              arr: 'gcArr',      min: 0.5, max: 2.5, step: 0.5, defaultLine: 0.5 },
];

const POS_BADGE = { GK: 'bg-yellow-500/20 text-yellow-400', DF: 'bg-blue-500/20 text-blue-400', MF: 'bg-green-500/20 text-green-400', FW: 'bg-red-500/20 text-red-400' };

const calcHitRate = (arr, line) => {
  if (!arr || arr.length === 0) return null;
  return Math.round(arr.filter(v => v > line).length / arr.length * 100);
};

const hitRateToOdds = (hitRate) => {
  if (hitRate == null) return -110;
  const p = hitRate / 100;
  if (p >= 0.5) return Math.round(-100 * (p / (1 - p)));
  return Math.round(100 * ((1 - p) / p));
};

const SoccerPlayerCard = ({ player, market, onAddToParlay }) => {
  const mdef = SOCCER_MARKETS.find(m => m.key === market) || SOCCER_MARKETS[0];
  // For GK market, use gcArr and invert (clean sheet = conceded < line)
  const isGkMarket = market === 'gk';
  const [line, setLine] = React.useState(mdef.defaultLine);

  // Reset line when market changes
  React.useEffect(() => { setLine(mdef.defaultLine); }, [market]);

  const arr = player[mdef.arr] || [];
  const hitRate = isGkMarket
    ? (arr.length ? Math.round(arr.filter(v => v < line).length / arr.length * 100) : null)
    : calcHitRate(arr, line);

  const getRateColor = (rate) => {
    if (rate == null) return 'text-gray-400 dark:text-gray-500';
    if (rate >= 70) return 'text-green-500';
    if (rate >= 55) return 'text-blue-500';
    return 'text-red-400';
  };

  // Steps for slider tick marks
  const steps = [];
  for (let v = mdef.min; v <= mdef.max + 0.01; v += mdef.step) steps.push(Math.round(v * 10) / 10);

  // GK secondary: show goals allowed avg
  const gcAvg = isGkMarket && arr.length ? (arr.reduce((a, b) => a + b, 0) / arr.length).toFixed(1) : null;

  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-100 dark:border-gray-800 border-l-[3px] border-l-blue-500 p-4 flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="font-semibold text-gray-900 dark:text-white text-sm leading-tight">{player.name}</p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{player.team}</p>
        </div>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${POS_BADGE[player.position] || 'bg-gray-500/20 text-gray-400'}`}>
            {player.position}
          </span>
          <span className="text-[10px] text-gray-400 bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded">
            {player.gamesPlayed}G
          </span>
        </div>
      </div>

      {/* Hit rate + line label */}
      <div>
        <div className="flex items-baseline gap-1.5">
          <span className={`text-3xl font-bold tabular-nums ${getRateColor(hitRate)}`}>
            {hitRate != null ? `${hitRate}%` : '--'}
          </span>
          <span className="text-xs text-gray-400">
            {isGkMarket ? `Under ${line} goals allowed` : `O/U ${line}`}
          </span>
        </div>
        <div className="h-1.5 bg-gray-100 dark:bg-gray-800 rounded-full mt-1.5 overflow-hidden">
          <div className={`h-full rounded-full transition-all ${hitRate >= 70 ? 'bg-green-500' : hitRate >= 55 ? 'bg-blue-500' : 'bg-red-400'}`}
            style={{ width: `${hitRate ?? 0}%` }} />
        </div>
      </div>

      {/* Line slider */}
      {steps.length > 1 && (
        <div>
          <input type="range" min={mdef.min} max={mdef.max} step={mdef.step} value={line}
            onChange={e => setLine(parseFloat(e.target.value))}
            className="w-full accent-blue-500 h-1.5 cursor-pointer" />
          <div className="flex justify-between mt-0.5">
            {steps.map(s => (
              <span key={s} className={`text-[9px] tabular-nums ${s === line ? 'text-blue-400 font-semibold' : 'text-gray-500'}`}>{s}</span>
            ))}
          </div>
        </div>
      )}

      {/* Bar graph: last N games */}
      {arr.length > 0 && (
        <div className="flex gap-0.5 items-end h-6">
          {arr.map((v, i) => {
            const hit = isGkMarket ? v < line : v > line;
            return (
              <div key={i} title={`${v}`}
                className={`flex-1 rounded-sm ${hit ? 'bg-green-500' : 'bg-red-400'}`}
                style={{ height: `${Math.max(20, Math.min(100, (v / (mdef.max + 0.5)) * 100))}%` }} />
            );
          })}
        </div>
      )}

      {/* GK extra: avg goals allowed */}
      {isGkMarket && gcAvg && (
        <p className="text-[10px] text-gray-400">Avg {gcAvg} goals allowed/game</p>
      )}

      {/* Footer */}
      <div className="border-t border-gray-100 dark:border-gray-700 pt-2 flex items-center justify-between mt-auto">
        <span className="text-[10px] text-gray-400">Avg {player.avgMinutes} min/game</span>
        <span className="text-[10px] text-gray-400 capitalize">{player.teamSide} team</span>
      </div>

      {onAddToParlay && (
        <button
          onClick={() => onAddToParlay({
            id: `sp_${player.id}_${market}_${Date.now()}`,
            sport: 'soccer_player',
            playerName: player.name,
            team: player.team,
            position: player.position,
            statType: isGkMarket ? 'GK Clean Sheet' : `${mdef.label} O/U`,
            line,
            originalLine: line,
            hitRate,
            odds: hitRateToOdds(hitRate),
            arr,
            isGkMarket,
            lineMin: mdef.min,
            lineMax: mdef.max,
            lineStep: mdef.step,
          })}
          className="w-full mt-1 py-1.5 text-xs font-semibold rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition-colors"
        >
          + Add to Parlay
        </button>
      )}
    </div>
  );
};

const SoccerMatchCard = ({ match, onAddToParlay }) => {
  const [customLine, setCustomLine] = React.useState(match.overUnderLine || 2.5);
  const [teamPropsOpen, setTeamPropsOpen] = React.useState(false);
  const [homeTeamLine, setHomeTeamLine] = React.useState(0.5);
  const [awayTeamLine, setAwayTeamLine] = React.useState(0.5);

  const getRateColor = (rate) => {
    if (rate === null || rate === undefined) return 'text-gray-400 dark:text-gray-500';
    if (rate >= 70) return 'text-green-500';
    if (rate >= 55) return 'text-blue-500';
    return 'text-red-400';
  };
  const getTrustColor = (score) => {
    if (score >= 80) return 'bg-green-500/10 text-green-500 border-green-500/30';
    if (score >= 70) return 'bg-amber-500/10 text-amber-500 border-amber-500/30';
    if (score >= 60) return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/30';
    return 'bg-red-500/10 text-red-400 border-red-400/30';
  };
  const fmtOdds = (o) => (o > 0 ? `+${o}` : `${o}`);
  const shortName = (name) => {
    const words = name.split(' ');
    if (words.length <= 2) return name;
    if (name.includes(' and Hove')) return 'Brighton';
    if (name.startsWith('AFC ')) return words[1];
    return words.slice(0, 2).join(' ');
  };
  const calcOverPct = (totals, line) => {
    if (!totals || !totals.length) return null;
    return Math.round(totals.filter(t => t > line).length / totals.length * 100);
  };

  const poisson = (lambda, k) => {
    if (lambda <= 0) return k === 0 ? 1 : 0;
    let p = Math.exp(-lambda);
    for (let i = 1; i <= k; i++) p *= lambda / i;
    return p;
  };
  const calcMatchProbs = (lambdaHome, lambdaAway, maxGoals = 8) => {
    let homeWin = 0, draw = 0, awayWin = 0;
    for (let h = 0; h <= maxGoals; h++) {
      for (let a = 0; a <= maxGoals; a++) {
        const p = poisson(lambdaHome, h) * poisson(lambdaAway, a);
        if (h > a) homeWin += p;
        else if (h === a) draw += p;
        else awayWin += p;
      }
    }
    return { homeWin, draw, awayWin };
  };

  // Convert UTC ISO string to user's local date + time
  const { localDate, localTime } = React.useMemo(() => {
    if (!match.commenceTime) return { localDate: 'TBD', localTime: '' };
    const d = new Date(match.commenceTime);
    return {
      localDate: d.toLocaleDateString([], { month: 'short', day: 'numeric' }),
      localTime: d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }),
    };
  }, [match.commenceTime]);

  // Combined totals for the match O/U slider
  const combinedTotals = React.useMemo(() =>
    [...(match.homeGoalTotals || []), ...(match.awayGoalTotals || [])],
    [match.homeGoalTotals, match.awayGoalTotals]
  );

  const adjustedOverRate = combinedTotals.length > 0
    ? calcOverPct(combinedTotals, customLine)
    : match.overHitRate;
  const lineChanged = customLine !== (match.overUnderLine || 2.5);

  const homeTeamOverRate = calcOverPct(match.homeTeamScoredAtHome, homeTeamLine);
  const awayTeamOverRate = calcOverPct(match.awayTeamScoredAway, awayTeamLine);
  const hasTeamProps = (match.homeTeamScoredAtHome?.length > 0) || (match.awayTeamScoredAway?.length > 0);

  // Dynamic trust score - recomputes whenever the line changes
  const trustScore = React.useMemo(() => {
    const minGames = Math.min(match.homeGames || 0, match.awayGames || 0);
    if (minGames < 5) return null;
    // Factor 1: Over hit rate (30%)
    const fHit = adjustedOverRate != null ? adjustedOverRate : 50;
    // Factor 2: Expected vs line gap (25%) - moves with slider
    const gap = (match.expectedTotal || 0) - customLine;
    const fGap = Math.max(0, Math.min(100, 50 + (gap / 1.5) * 50));
    // Factor 3: Odds market lean (20%) - fixed to bookmaker line
    let fOdds = 50;
    if (match.overOdds != null) {
      fOdds = match.overOdds > 0
        ? (100 / (match.overOdds + 100)) * 100
        : (Math.abs(match.overOdds) / (Math.abs(match.overOdds) + 100)) * 100;
    }
    // Factor 4: Consistency - std dev of totals (15%)
    let fConsistency = 50;
    if (combinedTotals.length >= 2) {
      const mean = combinedTotals.reduce((a, b) => a + b, 0) / combinedTotals.length;
      const stdDev = Math.sqrt(combinedTotals.reduce((s, v) => s + (v - mean) ** 2, 0) / (combinedTotals.length - 1));
      fConsistency = Math.max(0, Math.min(100, 100 - (stdDev - 0.5) * 40));
    }
    // Factor 5: Sample size confidence (10%)
    const fSample = Math.min(100, 40 + (minGames - 5) / 14 * 60);
    const score = fHit * 0.30 + fGap * 0.25 + fOdds * 0.20 + fConsistency * 0.15 + fSample * 0.10;
    return Math.round(score * 10) / 10;
  }, [adjustedOverRate, customLine, match.expectedTotal, match.overOdds, match.homeGames, match.awayGames, combinedTotals]);

  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-100 dark:border-gray-800 border-l-[3px] border-l-blue-500 p-5 flex flex-col">
      {/* Header: teams + trust score badge */}
      <div className="mb-3 flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="text-base font-bold text-gray-900 dark:text-white leading-snug">
            {match.homeTeam} <span className="text-gray-400 dark:text-gray-500 font-normal text-sm">vs</span> {match.awayTeam}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            {localDate}{localTime ? ` · ${localTime}` : ''}
          </div>
        </div>
        {trustScore != null && (
          <div className="flex-shrink-0 flex flex-col items-center gap-0.5">
            <div className={`flex flex-col items-center px-2 py-1 rounded-md border tabular-nums ${getTrustColor(trustScore)}`}
              title="Trust Score: composite confidence rating (0-100) based on historical hit rate, model vs line, odds lean, consistency, and sample size">
              <span className="text-[9px] font-semibold uppercase tracking-wide opacity-70">Trust</span>
              <span className="text-sm font-bold leading-tight">{trustScore}</span>
            </div>
            <span className="text-[9px] text-gray-400 dark:text-gray-500 text-center leading-tight max-w-[64px]">{getTrustLabel(trustScore)}</span>
          </div>
        )}
      </div>

      <div className="border-t border-gray-100 dark:border-gray-800 pt-3 mb-3">
        {/* 3-col stats */}
        <div className="grid grid-cols-3 gap-2 text-center mb-2">
          <div>
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-0.5" title="Total goals over/under line. Drag the slider below to adjust.">O/U Line</div>
            <div className="text-xl font-bold tabular-nums text-gray-900 dark:text-white">{customLine}</div>
            {lineChanged && (
              <div className="text-[10px] text-gray-400">Book line: {match.overUnderLine}</div>
            )}
          </div>
          <div>
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-0.5" title="% of historical games (home team at home + away team away) where total goals exceeded this line">Over %</div>
            <div className={`text-xl font-bold tabular-nums ${getRateColor(adjustedOverRate)}`}>
              {adjustedOverRate != null ? `${adjustedOverRate}%` : '-'}
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-0.5" title="Both Teams Score: % of games where both teams scored at least 1 goal">Both Score %</div>
            <div className={`text-xl font-bold tabular-nums ${getRateColor(match.bttsRate)}`}>
              {match.bttsRate != null ? `${match.bttsRate}%` : '-'}
            </div>
          </div>
        </div>

        {/* Match O/U line adjuster */}
        {combinedTotals.length > 0 && (
          <div className="mb-3">
            <input
              type="range" min="0.5" max="5.5" step="0.5"
              value={customLine}
              onChange={e => setCustomLine(parseFloat(e.target.value))}
              className="w-full h-1.5 accent-blue-500 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-gray-400 mt-0.5 px-0.5">
              <span>0.5</span>
              {lineChanged && (
                <button onClick={() => setCustomLine(match.overUnderLine || 2.5)}
                  className="text-blue-500 hover:underline">Reset to book line</button>
              )}
              <span>5.5</span>
            </div>
          </div>
        )}

        {/* Expected total breakdown */}
        <div className="bg-gray-50 dark:bg-gray-800 rounded-lg px-3 py-2 space-y-1">
          <div className="flex justify-between text-xs">
            <span className="text-gray-500 dark:text-gray-400" title="Model-predicted total goals using each team's attack strength and defensive record">Expected total</span>
            <span className={`font-semibold tabular-nums ${match.expectedTotal > customLine ? 'text-green-500' : 'text-red-400'}`}>
              {match.expectedTotal} {match.expectedTotal > customLine ? '▲ Over' : '▼ Under'}
            </span>
          </div>
          <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400">
            <span>{shortName(match.homeTeam)} avg scored (home)</span>
            <span className="tabular-nums font-medium text-gray-700 dark:text-gray-300">{match.homeAvgGoals}</span>
          </div>
          <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400">
            <span>{shortName(match.awayTeam)} avg scored (away)</span>
            <span className="tabular-nums font-medium text-gray-700 dark:text-gray-300">{match.awayAvgGoals}</span>
          </div>
          {match.expectedHomeGoals > 0 && match.expectedAwayGoals > 0 && (() => {
            const { homeWin, draw, awayWin } = calcMatchProbs(match.expectedHomeGoals, match.expectedAwayGoals);
            const hPct = Math.round(homeWin * 100);
            const dPct = Math.round(draw * 100);
            const aPct = 100 - hPct - dPct;
            return (
              <div className="pt-1">
                <div className="text-[10px] text-gray-400 dark:text-gray-500 mb-1" title="Poisson model win probabilities based on expected goals">Win probability</div>
                <div className="flex rounded overflow-hidden h-4 text-[10px] font-semibold">
                  <div className="flex items-center justify-center bg-blue-600/80 text-white" style={{ width: `${hPct}%` }} title={`${shortName(match.homeTeam)} win`}>
                    {hPct >= 15 ? `${hPct}%` : ''}
                  </div>
                  <div className="flex items-center justify-center bg-gray-500/60 text-gray-200" style={{ width: `${dPct}%` }} title="Draw">
                    {dPct >= 12 ? `${dPct}%` : ''}
                  </div>
                  <div className="flex items-center justify-center bg-purple-600/80 text-white" style={{ width: `${aPct}%` }} title={`${shortName(match.awayTeam)} win`}>
                    {aPct >= 15 ? `${aPct}%` : ''}
                  </div>
                </div>
                <div className="flex justify-between text-[10px] text-gray-400 dark:text-gray-500 mt-0.5">
                  <span className="text-blue-400">{shortName(match.homeTeam)} {hPct}%</span>
                  <span>Draw {dPct}%</span>
                  <span className="text-purple-400">{shortName(match.awayTeam)} {aPct}%</span>
                </div>
              </div>
            );
          })()}
          {(match.homeGames > 0 || match.awayGames > 0) && (
            <div className="text-[10px] text-gray-400 dark:text-gray-600 text-right mt-0.5"
              title="Number of home/away games this data is based on">
              {match.homeGames} home · {match.awayGames} away games
            </div>
          )}
        </div>

        {/* Team Goal Props - collapsible */}
        {hasTeamProps && (
          <div className="mt-2">
            <button
              onClick={() => setTeamPropsOpen(o => !o)}
              className="w-full flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 py-1.5 transition-colors"
            >
              <span className="font-medium">Team Goal Props</span>
              <span className="text-[10px]">{teamPropsOpen ? '▲' : '▼'}</span>
            </button>
            {teamPropsOpen && (
              <div className="bg-gray-50 dark:bg-gray-800 rounded-lg px-3 py-2 space-y-3">
                {(match.homeTeamScoredAtHome?.length > 0) && (
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs font-medium text-gray-700 dark:text-gray-300">{shortName(match.homeTeam)} to score over</span>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold text-gray-600 dark:text-gray-300 tabular-nums">{homeTeamLine}</span>
                        <span className={`text-sm font-bold tabular-nums ${getRateColor(homeTeamOverRate)}`}>
                          {homeTeamOverRate != null ? `${homeTeamOverRate}%` : '-'}
                        </span>
                      </div>
                    </div>
                    <input type="range" min="0.5" max="3.5" step="0.5"
                      value={homeTeamLine}
                      onChange={e => setHomeTeamLine(parseFloat(e.target.value))}
                      className="w-full h-1 accent-blue-500 cursor-pointer" />
                    <div className="text-[10px] text-gray-400 mt-0.5">{match.homeGames} home games this season</div>
                  </div>
                )}
                {(match.awayTeamScoredAway?.length > 0) && (
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-xs font-medium text-gray-700 dark:text-gray-300">{shortName(match.awayTeam)} to score over</span>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold text-gray-600 dark:text-gray-300 tabular-nums">{awayTeamLine}</span>
                        <span className={`text-sm font-bold tabular-nums ${getRateColor(awayTeamOverRate)}`}>
                          {awayTeamOverRate != null ? `${awayTeamOverRate}%` : '-'}
                        </span>
                      </div>
                    </div>
                    <input type="range" min="0.5" max="3.5" step="0.5"
                      value={awayTeamLine}
                      onChange={e => setAwayTeamLine(parseFloat(e.target.value))}
                      className="w-full h-1 accent-blue-500 cursor-pointer" />
                    <div className="text-[10px] text-gray-400 mt-0.5">{match.awayGames} away games this season</div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Odds footer */}
      <div className="mt-auto pt-3 border-t border-gray-100 dark:border-gray-800 flex items-center justify-between gap-2">
        {match.overOdds != null ? (
          <>
            <span className="text-sm font-bold text-green-500 tabular-nums">O {fmtOdds(match.overOdds)}</span>
            <span className="text-xs text-gray-400 truncate">{match.bookmaker || ''}</span>
            <span className="text-sm font-bold text-red-400 tabular-nums">U {fmtOdds(match.underOdds)}</span>
          </>
        ) : (
          <span className="text-xs text-gray-400 w-full text-center">Odds unavailable</span>
        )}
      </div>

      {/* Add to Parlay */}
      {onAddToParlay && (
        <div className="grid grid-cols-2 gap-2 mt-3">
          {[['over', 'Over', match.overOdds, 'bg-green-600 hover:bg-green-700'],
            ['under', 'Under', match.underOdds, 'bg-red-500 hover:bg-red-600']].map(([side, label, odds, cls]) => (
            <button key={side}
              onClick={() => onAddToParlay({
                id: `soccer-${match.id}-${side}-${Date.now()}`,
                sport: 'soccer',
                homeTeam: match.homeTeam,
                awayTeam: match.awayTeam,
                side,
                line: customLine,
                originalLine: match.overUnderLine || 2.5,
                odds: odds ?? null,
                trustScore: trustScore,
                hitRate: adjustedOverRate,
                commenceTime: match.commenceTime,
                bookmaker: match.bookmaker,
              })}
              className={`${cls} text-white text-xs font-semibold py-1.5 rounded-lg transition-colors`}>
              + {label} {customLine}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

const getTrustLabel = (score) => {
  if (score == null) return '';
  if (score >= 80) return 'Strong lean';
  if (score >= 70) return 'Leaning over';
  if (score >= 60) return 'I like these odds';
  if (score >= 50) return 'Slight edge';
  if (score >= 40) return 'Proceed with caution';
  return 'Taking a longshot';
};

const PlayerCard = ({ player, timeRange, onLineAdjust, onClick, onAddToParlay }) => {
  const [customLine, setCustomLine] = React.useState(player.line);
  const [isAdjusting, setIsAdjusting] = React.useState(false);

  // Keep input in sync when parent updates player.line (e.g. after a successful adjustment)
  React.useEffect(() => {
    setCustomLine(player.line);
  }, [player.line]);

  const handleLineChange = async () => {
  if (parseFloat(customLine) === player.line) return;
  
  console.log('Adjusting line for:', player.name, player.statType, 'from', player.line, 'to', customLine);
  
  setIsAdjusting(true);
  try {
    const response = await fetch(`${API_BASE_URL}/calculate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        player_name: player.name,
        stat_type: player.statType,
        custom_line: parseFloat(customLine),
        opponent: player.opponent,
        opponent_rank: player.opponentRank,
        is_home: player.isHome
      })
    });
    
    const data = await response.json();
    console.log('Response from API:', data);
    
    if (data.success && onLineAdjust) {
      console.log('Calling onLineAdjust - ID:', player.id, 'Name:', player.name, 'Stat:', player.statType);
      console.log('Analysis data:', data.analysis);
      onLineAdjust(player.id, player.name, player.statType, data.analysis);
    } else {
      console.error('API call failed:', data);
    }
  } catch (error) {
    console.error('Error adjusting line:', error);
  } finally {
    setIsAdjusting(false);
  }
};
  const getTrustColor = (score) => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 70) return 'bg-amber-500';
    if (score >= 60) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getFormIcon = (form) => {
    if (form === 'hot') return <TrendingUp className="w-4 h-4 text-green-500" />;
    if (form === 'cold') return <TrendingDown className="w-4 h-4 text-red-500" />;
    return null;
  };

  const getStreakBadge = () => {
    if (player.streak >= 3) {
      const Icon = player.streakType === 'over' ? Flame : Snowflake;
      const color = player.streakType === 'over' ? 'bg-orange-100 text-orange-700 border-orange-300' : 'bg-blue-100 text-blue-700 border-blue-300';
      return (
        <div className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold border ${color}`}>
          <Icon className="w-3 h-3" />
          {player.streak} {player.streakType === 'over' ? 'Over' : 'Under'}
        </div>
      );
    }
    return null;
  };

  const displayGames = timeRange === 5 ? player.last5Games : 
                       timeRange === 15 ? player.last15Games : 
                       player.lastGames;

  const lineDiff = (player.avgLastN - player.line).toFixed(1);
  const lineDiffColor = lineDiff > 0 ? 'text-green-600' : lineDiff < 0 ? 'text-red-600' : 'text-gray-600';

  return (
    <div
      className="bg-white dark:bg-gray-900 rounded-xl border border-gray-100 dark:border-gray-800 border-l-[3px] border-l-blue-500 shadow-sm p-5 hover:shadow-lg hover:border-l-blue-400 transition-all duration-300 transform hover:-translate-y-0.5 cursor-pointer flex flex-col"
      onClick={onClick}
    >
      <div className="flex justify-between items-start mb-3">
        <div className="flex items-center gap-2">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-lg text-gray-900 dark:text-white">{player.name}</h3>
              {player.injuryStatus && player.injuryStatus !== 'ACTIVE' && (
                <span className={`px-2 py-0.5 text-xs font-bold rounded-full ${
                  player.injuryStatus === 'OUT'
                    ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300 border border-red-300'
                    : player.injuryStatus === 'QUESTIONABLE'
                    ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300 border border-yellow-300'
                    : player.injuryStatus === 'DOUBTFUL'
                    ? 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300 border border-orange-300'
                    : 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300 border border-blue-300'
                }`}>
                  {player.injuryStatus}
                </span>
              )}
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 flex items-center gap-1.5">
              <span className="inline-block w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: player.teamColor }} />
              {player.team} • {player.position}
              {player.isHome ? <Home className="w-3 h-3" /> : <Plane className="w-3 h-3" />}
            </p>
          </div>
        </div>
        <div className="flex flex-col items-end gap-1">
          {getFormIcon(player.recentForm)}
          {getStreakBadge()}
        </div>
      </div>

      <div className="mb-4 bg-gray-50 dark:bg-gray-800 rounded-lg p-3" onClick={(e) => e.stopPropagation()}>
        <div className="flex justify-between items-center mb-1">
          <div className="flex items-center gap-2">
            <span className="text-gray-700 dark:text-gray-300 font-medium">{player.statType}</span>
            {player.isRealLine && (
              <span className="px-2 py-0.5 text-xs font-semibold bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300 rounded-full border border-green-300 dark:border-green-700">
                Live Odds
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <input
              type="number"
              step="0.5"
              min="0.5"
              value={customLine}
              onChange={(e) => {
                e.stopPropagation();
                setCustomLine(e.target.value);
              }}
              onBlur={handleLineChange}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.target.blur();
                }
              }}
              onClick={(e) => e.stopPropagation()}
              onFocus={(e) => e.stopPropagation()}
              className="w-20 px-2 py-1 text-right text-xl font-bold tabular-nums border border-gray-300 dark:border-gray-600 dark:bg-gray-800 dark:text-white rounded focus:ring-2 focus:ring-blue-500"
              disabled={isAdjusting}
            />
            {isAdjusting && <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>}
          </div>
        </div>
        <div className="text-sm text-gray-600 dark:text-gray-400">
          Avg Last {timeRange}: <span className="font-semibold tabular-nums">{player.avgLastN}</span>
          <span className={`ml-2 font-semibold ${lineDiffColor}`}>
            ({lineDiff > 0 ? '+' : ''}{lineDiff})
          </span>
        </div>
        <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-600">
          <div className="text-xs text-gray-500 dark:text-gray-400 font-semibold mb-1">
            NEXT GAME:
          </div>
          <div className="text-sm text-gray-700 dark:text-gray-300 font-medium">
            {player.team} {player.isHome ? 'vs' : '@'} {player.opponent}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {player.opponent} Defense: Rank #{player.opponentRank} • {player.opponentDefStat}
          </div>
        </div>
        <div className="text-xs text-gray-500 dark:text-gray-500 mt-2 font-medium">
          {player.gameDate} • {player.gameTime}
        </div>

        {/* Bookmaker Lines - always rendered for uniform card height */}
        {player.bookmakerLines && player.bookmakerLines.length > 0 ? (
          <BookmakerSelector bookmakerLines={player.bookmakerLines} />
        ) : (
          <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-800">
            <div className="flex items-center justify-between">
              <div className="text-xs font-semibold text-gray-300 dark:text-gray-600 uppercase tracking-wider">Sportsbook Line</div>
              <span className="text-xs text-gray-300 dark:text-gray-600">No live odds</span>
            </div>
            <div className="mt-2 h-11 bg-gray-50 dark:bg-gray-800 rounded-lg" />
          </div>
        )}
      </div>

      <div className="mb-4">
        <div className="flex justify-between items-center mb-1.5">
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">Hit Rate</span>
          <span className={`text-2xl font-bold tabular-nums ${
            player.hitRate >= 70 ? 'text-green-500' : player.hitRate >= 55 ? 'text-blue-500' : 'text-red-400'
          }`}>
            {player.hitRate}%
          </span>
        </div>
        <div className="w-full bg-gray-100 dark:bg-gray-800 rounded-full h-1.5">
          <div
            className={`h-1.5 rounded-full transition-all ${
              player.hitRate >= 70 ? 'bg-green-500' : player.hitRate >= 55 ? 'bg-blue-500' : 'bg-red-400'
            }`}
            style={{ width: `${Math.min(player.hitRate, 100)}%` }}
          />
        </div>
        <div className="mt-2 text-xs h-4">
          {player.recent_hit_rate !== undefined && player.recent_total >= 5 && (
            <div className="flex justify-between items-center">
              <span className="text-gray-500 dark:text-gray-400">Last {player.recent_total} Games</span>
              <span className={`font-semibold tabular-nums ${
                player.recent_hit_rate > player.hitRate ? 'text-green-500 dark:text-green-400' :
                player.recent_hit_rate < player.hitRate ? 'text-red-500 dark:text-red-400' :
                'text-gray-600 dark:text-gray-300'
              }`}>
                {player.recent_hit_rate}% ({player.recent_hits}/{player.recent_total})
                {player.recent_hit_rate > player.hitRate && ' ↗'}
                {player.recent_hit_rate < player.hitRate && ' ↘'}
              </span>
            </div>
          )}
        </div>
      </div>

      <div className="mb-4">
        <div className="flex justify-between items-center mb-1.5">
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">Trust Score</span>
          <div className="text-right">
            <span className="text-2xl font-bold tabular-nums dark:text-white">{player.trustScore}</span>
            <div className="text-[10px] text-gray-400 dark:text-gray-500">{getTrustLabel(player.trustScore)}</div>
          </div>
        </div>
        <div className="w-full bg-gray-100 dark:bg-gray-800 rounded-full h-1.5">
          <div
            className={`h-1.5 rounded-full transition-all ${getTrustColor(player.trustScore)}`}
            style={{ width: `${player.trustScore}%` }}
          />
        </div>
      </div>

      <div>
        <div className="text-xs text-gray-600 dark:text-gray-400 mb-2">Last {timeRange} Games</div>
        <div className="flex items-end gap-1 h-12">
          {displayGames.map((stat, idx) => {
            const isOver = stat > player.line;
            const height = (stat / Math.max(...displayGames)) * 100;
            const displayDates = timeRange === 5 ? player.last5GamesDates : timeRange === 15 ? player.last15GamesDates : player.lastGamesDates;
            const gameDate = displayDates?.[idx];
            const dateLabel = gameDate
              ? new Date(gameDate + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
              : `G${idx + 1}`;
            return (
              <div
                key={idx}
                className={`flex-1 rounded-t ${isOver ? 'bg-green-400 hover:bg-green-500' : 'bg-red-400 hover:bg-red-500'} transition-all cursor-pointer`}
                style={{ height: `${height}%` }}
                title={`${dateLabel}: ${stat} (${isOver ? 'Over' : 'Under'})`}
              />
            );
          })}
        </div>
        <div className="flex justify-between text-xs text-gray-500 dark:text-gray-500 mt-1">
          <span>Oldest</span>
          <span>Most Recent</span>
        </div>
      </div>

      {/* Add to Parlay Button — mt-auto pins it to the card bottom */}
      {onAddToParlay && (
        <div className="mt-auto pt-4">
        <button
          onClick={(e) => {
            e.stopPropagation();
            onAddToParlay(player);
          }}
          className="w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition-all transform hover:scale-105 flex items-center justify-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Add to Custom Parlay
        </button>
        </div>
      )}
    </div>
  );
};

// Parlay Builder Component
const ParlayBuilder = ({ darkMode }) => {
  const [targetOdds, setTargetOdds] = useState(400);
  const [safetyLevel, setSafetyLevel] = useState('moderate');
  const [gameFilter, setGameFilter] = useState('any');
  const [numSuggestions, setNumSuggestions] = useState(3);
  const [minLegs, setMinLegs] = useState(2);
  const [maxLegs, setMaxLegs] = useState(6);
  const [parlays, setParlays] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [availableGames, setAvailableGames] = useState([]);
  const [selectedGames, setSelectedGames] = useState([]);
  const [bannedPlayers, setBannedPlayers] = useState([]);
  const [banInput, setBanInput] = useState('');

  // Fetch available games on component mount
  useEffect(() => {
    const fetchGames = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/players`);
        const data = await response.json();

        if (data.success && data.players) {
          // Extract unique games from players
          const gamesSet = new Set();
          data.players.forEach(player => {
            if (player.opponent) {
              const gameId = `${player.team}_vs_${player.opponent}`;
              gamesSet.add(gameId);
            }
          });

          // Convert to array and format for display
          const gamesList = Array.from(gamesSet).map(gameId => {
            const [team1, team2] = gameId.split('_vs_');
            return {
              id: gameId,
              display: `${team1} vs ${team2}`
            };
          }).sort((a, b) => a.display.localeCompare(b.display));

          setAvailableGames(gamesList);
        }
      } catch (err) {
        console.error('Error fetching games:', err);
      }
    };

    fetchGames();
  }, []);

  const toggleGameSelection = (gameId) => {
    setSelectedGames(prev =>
      prev.includes(gameId)
        ? prev.filter(id => id !== gameId)
        : [...prev, gameId]
    );
  };

  const addBannedPlayer = () => {
    const trimmed = banInput.trim();
    if (trimmed && !bannedPlayers.includes(trimmed)) {
      setBannedPlayers([...bannedPlayers, trimmed]);
      setBanInput('');
    }
  };

  const removeBannedPlayer = (playerName) => {
    setBannedPlayers(bannedPlayers.filter(p => p !== playerName));
  };

  const handleBanKeyPress = (e) => {
    if (e.key === 'Enter') {
      addBannedPlayer();
    }
  };

  const generateParlays = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/parlay/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          target_odds: targetOdds,
          safety_level: safetyLevel,
          game_filter: gameFilter,
          selected_games: selectedGames,
          num_suggestions: numSuggestions,
          min_legs: minLegs,
          max_legs: maxLegs,
          banned_players: bannedPlayers
        })
      });

      const data = await response.json();

      if (data.success) {
        setParlays(data.suggestions);
      } else {
        setError(data.error || 'Failed to generate parlays');
      }
    } catch (err) {
      console.error('Error generating parlays:', err);
      setError('Failed to connect to server');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Parlay Builder Controls */}
      <div className="bg-white dark:bg-gray-950 rounded-xl border border-gray-200 dark:border-gray-800 p-6">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2 mb-6">
          <span className="w-[3px] h-6 bg-blue-500 rounded-full flex-shrink-0" />
          Build Your Parlay
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Target Odds */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Target Odds
            </label>
            <select
              value={targetOdds}
              onChange={(e) => setTargetOdds(Number(e.target.value))}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
            >
              <option value={200}>+200</option>
              <option value={300}>+300</option>
              <option value={400}>+400</option>
              <option value={500}>+500</option>
              <option value={600}>+600</option>
              <option value={800}>+800</option>
              <option value={1000}>+1000</option>
              <option value={1500}>+1500</option>
              <option value={2000}>+2000</option>
            </select>
          </div>

          {/* Safety Level */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Safety Level
            </label>
            <select
              value={safetyLevel}
              onChange={(e) => setSafetyLevel(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
            >
              <option value="conservative">Conservative (70%+ trust)</option>
              <option value="moderate">Moderate (60%+ trust)</option>
              <option value="aggressive">Aggressive (50%+ trust)</option>
            </select>
          </div>

          {/* Game Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Game Selection
            </label>
            <select
              value={gameFilter}
              onChange={(e) => {
                setGameFilter(e.target.value);
                // Clear selected games when changing filter type
                if (e.target.value !== 'specific') {
                  setSelectedGames([]);
                }
              }}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
            >
              <option value="any">Different Games (avoid correlation)</option>
              <option value="single">Same Game Parlay ⚠️</option>
              <option value="specific">Specific Games</option>
            </select>
          </div>

          {/* Number of Suggestions */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Suggestions
            </label>
            <select
              value={numSuggestions}
              onChange={(e) => setNumSuggestions(Number(e.target.value))}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
            >
              <option value={1}>1 parlay</option>
              <option value={3}>3 parlays</option>
              <option value={5}>5 parlays</option>
              <option value={10}>10 parlays</option>
            </select>
          </div>
        </div>

        {/* Leg Count Selection */}
        <div className="mt-6">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Number of Legs
          </label>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">
                Minimum Legs
              </label>
              <select
                value={minLegs}
                onChange={(e) => {
                  const newMin = Number(e.target.value);
                  setMinLegs(newMin);
                  // Ensure max is always >= min
                  if (newMin > maxLegs) {
                    setMaxLegs(newMin);
                  }
                }}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
              >
                <option value={2}>2 legs</option>
                <option value={3}>3 legs</option>
                <option value={4}>4 legs</option>
                <option value={5}>5 legs</option>
                <option value={6}>6 legs</option>
                <option value={7}>7 legs</option>
                <option value={8}>8 legs</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-600 dark:text-gray-400 mb-1">
                Maximum Legs
              </label>
              <select
                value={maxLegs}
                onChange={(e) => {
                  const newMax = Number(e.target.value);
                  setMaxLegs(newMax);
                  // Ensure min is always <= max
                  if (newMax < minLegs) {
                    setMinLegs(newMax);
                  }
                }}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
              >
                <option value={2}>2 legs</option>
                <option value={3}>3 legs</option>
                <option value={4}>4 legs</option>
                <option value={5}>5 legs</option>
                <option value={6}>6 legs</option>
                <option value={7}>7 legs</option>
                <option value={8}>8 legs</option>
                <option value={9}>9 legs</option>
                <option value={10}>10 legs</option>
              </select>
            </div>
          </div>
          <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            More legs = higher odds, but lower probability of winning
          </p>
        </div>

        {/* Player Ban List */}
        <div className="mt-6">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Banned Players ({bannedPlayers.length})
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={banInput}
              onChange={(e) => setBanInput(e.target.value)}
              onKeyPress={handleBanKeyPress}
              placeholder="Type player name and press Enter..."
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-900 dark:text-white"
            />
            <button
              onClick={addBannedPlayer}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 dark:bg-red-700 dark:hover:bg-red-800 text-white font-semibold rounded-lg transition-colors"
            >
              Ban
            </button>
          </div>
          {bannedPlayers.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {bannedPlayers.map((player, index) => (
                <span
                  key={index}
                  className="inline-flex items-center gap-2 px-3 py-1 bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300 border border-red-200 dark:border-red-800 rounded-full text-sm"
                >
                  {player}
                  <button
                    onClick={() => removeBannedPlayer(player)}
                    className="hover:text-red-600 dark:hover:text-red-400"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
          <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            Props from banned players will not appear in parlay suggestions
          </p>
        </div>

        {/* Game Selection (shown when gameFilter is 'specific') */}
        {gameFilter === 'specific' && availableGames.length > 0 && (
          <div className="mt-6">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Select Games ({selectedGames.length} selected)
            </label>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 max-h-64 overflow-y-auto p-4 bg-gray-50 dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800">
              {availableGames.map(game => (
                <label
                  key={game.id}
                  className="flex items-center space-x-3 p-3 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 hover:border-blue-500 dark:hover:border-blue-500 cursor-pointer transition-colors"
                >
                  <input
                    type="checkbox"
                    checked={selectedGames.includes(game.id)}
                    onChange={() => toggleGameSelection(game.id)}
                    className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
                  />
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    {game.display}
                  </span>
                </label>
              ))}
            </div>
          </div>
        )}

        {/* Generate Button */}
        <button
          onClick={generateParlays}
          disabled={loading || (gameFilter === 'specific' && selectedGames.length === 0)}
          className="mt-6 w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Generating Parlays...' : 'Generate Parlays'}
        </button>

        {gameFilter === 'specific' && selectedGames.length === 0 && (
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 text-center">
            Please select at least one game to generate parlays
          </p>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 px-4 py-3 rounded-xl">
          <p className="font-semibold">Error</p>
          <p>{error}</p>
        </div>
      )}

      {/* Parlay Suggestions */}
      {parlays.length > 0 && (
        <div className="space-y-6">
          {/* Regenerate Button */}
          <div className="flex justify-between items-center">
            <h3 className="text-base font-bold text-gray-900 dark:text-white flex items-center gap-2">
              <span className="w-0.5 h-4 bg-blue-500 rounded-full flex-shrink-0" />
              Parlay Suggestions
            </h3>
            <button
              onClick={generateParlays}
              disabled={loading}
              className="px-4 py-2 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 font-semibold rounded-xl border border-gray-200 dark:border-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              {loading ? 'Generating...' : 'Regenerate'}
            </button>
          </div>

          {parlays.map((parlay, index) => {
            // Handle error parlays
            if (parlay.error) {
              return (
                <div key={index} className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 text-yellow-800 dark:text-yellow-300 px-6 py-4 rounded-xl">
                  <p className="font-semibold">{parlay.error}</p>
                  <p className="text-sm mt-1">{parlay.suggestion}</p>
                  {parlay.available_props && (
                    <p className="text-sm mt-1">Available props: {parlay.available_props}</p>
                  )}
                </div>
              );
            }

            return (
              <div key={index} className="bg-white dark:bg-gray-950 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden">
                {/* Parlay Header */}
                <div className="bg-white dark:bg-gray-950 border-b border-gray-200 dark:border-gray-800 px-6 py-4">
                  <div className="flex justify-between items-start">
                    <div className="flex items-center gap-2">
                      <span className="w-[3px] h-6 bg-green-500 rounded-full flex-shrink-0" />
                      <div>
                        <div className="text-base font-bold text-gray-900 dark:text-white">Parlay #{index + 1}</div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{parlay.num_legs} legs • ${parlay.payout_per_dollar.toFixed(2)} per $1</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold tabular-nums text-green-500">{parlay.parlay_odds_display}</div>
                    </div>
                  </div>
                  <div className="flex gap-3 mt-3">
                    <div className="bg-gray-50 dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-lg px-3 py-1.5">
                      <div className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">Avg Trust</div>
                      <div className="font-bold tabular-nums text-gray-900 dark:text-white">{parlay.avg_trust}%</div>
                    </div>
                    <div className="bg-gray-50 dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-lg px-3 py-1.5">
                      <div className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">Win Rate</div>
                      <div className="font-bold tabular-nums text-gray-900 dark:text-white">{parlay.true_win_rate}%</div>
                    </div>
                    <div className="bg-gray-50 dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-lg px-3 py-1.5">
                      <div className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">Safety</div>
                      <div className="font-bold capitalize text-gray-900 dark:text-white">{parlay.safety_level}</div>
                    </div>
                  </div>
                </div>

                {/* Parlay Legs */}
                <div className="p-5 space-y-2">
                  {parlay.legs.map((leg, legIndex) => (
                    <div key={legIndex} className="flex justify-between items-center p-4 bg-gray-50 dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl">
                      <div>
                        <div className="font-semibold text-gray-900 dark:text-white">{leg.player_name}</div>
                        <div className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                          {leg.team} vs {leg.opponent} • {leg.stat_type} O{leg.line}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-bold tabular-nums text-gray-900 dark:text-white">
                          {leg.odds > 0 ? `+${leg.odds}` : leg.odds}
                        </div>
                        <div className={`text-sm font-semibold tabular-nums ${
                          leg.trust_score >= 70 ? 'text-green-500' :
                          leg.trust_score >= 60 ? 'text-amber-500' :
                          'text-red-500'
                        }`}>
                          {leg.trust_score}% trust
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default function StatScoutDashboard() {
  const [currentSport, setCurrentSport] = useState('nba'); // 'nba' or 'soccer'
  const [soccerLeague, setSoccerLeague] = useState('pl'); // 'pl' or 'laliga'
  const [soccerData, setSoccerData] = useState({ pl: null, laliga: null });
  const [soccerLoading, setSoccerLoading] = useState(false);
  const [soccerError, setSoccerError] = useState(null);
  const [soccerView, setSoccerView] = useState('matchTotals'); // 'matchTotals' or 'playerProps'
  const [selectedSoccerFixture, setSelectedSoccerFixture] = useState(null);
  const [soccerPlayersData, setSoccerPlayersData] = useState({}); // keyed by "home_away"
  const [soccerPropsMarket, setSoccerPropsMarket] = useState('goals');
  const [soccerPropsTeamFilter, setSoccerPropsTeamFilter] = useState(null); // null | 'home' | 'away'
  const [currentView, setCurrentView] = useState('props'); // 'props' or 'parlay'
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTeam, setSelectedTeam] = useState('all');
  const [selectedTeams, setSelectedTeams] = useState([]); // Multi-select teams
  const [teamDropdownOpen, setTeamDropdownOpen] = useState(false);
  const teamDropdownRef = React.useRef(null);
  const [selectedStat, setSelectedStat] = useState('all');
  const [minTrustScore, setMinTrustScore] = useState(0);
  const [sortBy, setSortBy] = useState('trustScore');
  const [homeAwayFilter, setHomeAwayFilter] = useState('all');
  const [timeRange, setTimeRange] = useState(10);
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('statscout-dark-mode');
    return saved !== null ? saved === 'true' : true; // default: dark
  });
  const [players, setPlayers] = useState(mockPlayers);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [refreshMessage, setRefreshMessage] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(30); // Show 30 props per page
  const [showHighConfidenceOnly, setShowHighConfidenceOnly] = useState(false);
  const [showGamesTodayOnly, setShowGamesTodayOnly] = useState(false);
  const [showLiveOddsOnly, setShowLiveOddsOnly] = useState(false);
  const [minMinutes, setMinMinutes] = useState(0);
  const [showMobileFilters, setShowMobileFilters] = useState(false);
  const [selectedPlayer, setSelectedPlayer] = useState(null);

  // Custom Parlay Builder State
  const [customParlayLegs, setCustomParlayLegs] = useState([]);
  const [isParlaySidebarOpen, setIsParlaySidebarOpen] = useState(false);
  const [savedParlays, setSavedParlays] = useState([]);
  const [currentParlayName, setCurrentParlayName] = useState('');

  // Load saved parlays from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('statscout_saved_parlays');
    if (saved) {
      try {
        setSavedParlays(JSON.parse(saved));
      } catch (e) {
        console.error('Failed to load saved parlays:', e);
      }
    }
  }, []);

  // Save parlays to localStorage whenever they change
  useEffect(() => {
    if (savedParlays.length > 0) {
      localStorage.setItem('statscout_saved_parlays', JSON.stringify(savedParlays));
    }
  }, [savedParlays]);

const handleDarkModeToggle = () => {
  const next = !darkMode;
  setDarkMode(next);
  localStorage.setItem('statscout-dark-mode', String(next));
};

// Trigger ESPN stats refresh + cache rebuild
const handleRefreshStats = async () => {
  setIsRefreshing(true);
  setRefreshMessage(null);
  try {
    const response = await fetch(`${API_BASE_URL}/admin/update-stats`, { method: 'POST' });
    const data = await response.json();
    if (data.success) {
      setRefreshMessage('Fetching 90 days from ESPN (~3 min) — data will reload automatically when done');
    } else {
      setRefreshMessage('Update failed. Try again later.');
    }
  } catch (err) {
    setRefreshMessage('Could not reach server.');
  } finally {
    setIsRefreshing(false);
    setTimeout(() => setRefreshMessage(null), 15000);
  }
};

// Handle line adjustment
const handleLineAdjust = (playerId, playerName, statType, newData) => {
  console.log('handleLineAdjust called with:', {playerId, playerName, statType, newData});

  // Reset ALL filters that might hide the adjusted player
  setMinTrustScore(0);
  setShowHighConfidenceOnly(false);
  setShowGamesTodayOnly(false);
  setShowLiveOddsOnly(false);

  setPlayers(prevPlayers => {
    const updated = prevPlayers.map(p => {
      const matches = p.id === playerId && p.name === playerName && p.statType === statType;
      console.log('Checking player:', p.name, p.statType, 'matches:', matches);

      if (matches) {
        console.log('Updating player from:', p, 'to:', { ...p, ...newData, line: newData.line });
        return { ...p, ...newData, line: newData.line };
      }
      return p;
    });
    return updated;
  });
};

  // Custom Parlay Helper Functions
  const addToCustomParlay = (player) => {
    const legId = `${player.name}-${player.statType}-${Date.now()}`;
    const newLeg = {
      id: legId,
      playerName: player.name,
      team: player.team,
      opponent: player.opponent,
      statType: player.statType,
      line: player.line,
      originalLine: player.line,
      trustScore: player.trustScore,
      hitRate: player.hitRate,
      odds: player.bookmakerLines?.[0]?.over_odds || -110,
      gameDate: player.gameDate,
      gameTime: player.gameTime,
      isHome: player.isHome
    };

    setCustomParlayLegs(prev => [...prev, newLeg]);
    setIsParlaySidebarOpen(true);
  };

  const addSoccerLeg = (leg) => {
    setCustomParlayLegs(prev => [...prev, leg]);
    setIsParlaySidebarOpen(true);
  };

  const removeFromCustomParlay = (legId) => {
    setCustomParlayLegs(prev => prev.filter(leg => leg.id !== legId));
  };

  // Helper: Convert hit rate to American odds
  // hitRateToOdds is defined at module level

  const updateCustomParlayLeg = async (legId, newLine) => {
    const leg = customParlayLegs.find(l => l.id === legId);
    if (!leg) return;

    // Soccer match total legs: just update line locally
    if (leg.sport === 'soccer') {
      setCustomParlayLegs(prev => prev.map(l =>
        l.id === legId ? { ...l, line: parseFloat(newLine) } : l
      ));
      return;
    }

    // Soccer player prop legs: recalculate hit rate + estimated odds from stored array
    if (leg.sport === 'soccer_player') {
      const nl = parseFloat(newLine);
      const newHitRate = leg.isGkMarket
        ? (leg.arr?.length ? Math.round(leg.arr.filter(v => v < nl).length / leg.arr.length * 100) : null)
        : calcHitRate(leg.arr || [], nl);
      setCustomParlayLegs(prev => prev.map(l =>
        l.id === legId ? { ...l, line: nl, hitRate: newHitRate, odds: hitRateToOdds(newHitRate) } : l
      ));
      return;
    }

    try {
      // Call API to recalculate trust score with new line
      const response = await fetch(`${API_BASE_URL}/calculate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          player_name: leg.playerName,
          stat_type: leg.statType,
          custom_line: parseFloat(newLine),
          opponent: leg.opponent,
          is_home: leg.isHome
        })
      });

      if (response.ok) {
        const data = await response.json();
        const newHitRate = data.analysis.hitRate;
        const estimatedOdds = hitRateToOdds(newHitRate);

        setCustomParlayLegs(prev => prev.map(l =>
          l.id === legId
            ? {
                ...l,
                line: parseFloat(newLine),
                trustScore: data.analysis.trustScore,
                hitRate: newHitRate,
                odds: estimatedOdds // Update odds based on new hit rate
              }
            : l
        ));
      }
    } catch (error) {
      console.error('Failed to update leg:', error);
    }
  };

  const clearCustomParlay = () => {
    setCustomParlayLegs([]);
    setCurrentParlayName('');
    setIsParlaySidebarOpen(false);
  };

  const saveCustomParlay = () => {
    if (customParlayLegs.length === 0) return;

    const parlayName = currentParlayName || `Parlay ${savedParlays.length + 1}`;
    const newParlay = {
      id: Date.now(),
      name: parlayName,
      legs: customParlayLegs,
      created: new Date().toISOString()
    };

    setSavedParlays(prev => [...prev, newParlay]);
    clearCustomParlay();
  };

  const loadSavedParlay = (parlayId) => {
    const parlay = savedParlays.find(p => p.id === parlayId);
    if (parlay) {
      setCustomParlayLegs(parlay.legs);
      setCurrentParlayName(parlay.name);
      setIsParlaySidebarOpen(true);
    }
  };

  const deleteSavedParlay = (parlayId) => {
    setSavedParlays(prev => prev.filter(p => p.id !== parlayId));
  };

  // Calculate parlay metrics
  const calculateParlayMetrics = () => {
    if (customParlayLegs.length === 0) {
      return { avgTrust: 0, minTrust: 0, weightedTrust: 0, totalOdds: 0, payout: 0 };
    }

    const legsWithTrust = customParlayLegs.filter(l => l.trustScore != null);
    const avgTrust = legsWithTrust.length
      ? legsWithTrust.reduce((sum, leg) => sum + leg.trustScore, 0) / legsWithTrust.length
      : 0;
    const minTrust = legsWithTrust.length
      ? Math.min(...legsWithTrust.map(leg => leg.trustScore))
      : 0;

    // Weighted trust - higher odds props have more weight
    const totalWeight = customParlayLegs.reduce((sum, leg) => sum + Math.abs(leg.odds || 110), 0);
    const weightedTrust = legsWithTrust.length
      ? legsWithTrust.reduce((sum, leg) => {
          const weight = Math.abs(leg.odds || 110) / totalWeight;
          return sum + (leg.trustScore * weight);
        }, 0)
      : 0;

    // Calculate total American odds (fall back to -110 if a leg has no odds)
    let totalOdds = customParlayLegs[0]?.odds || -110;
    for (let i = 1; i < customParlayLegs.length; i++) {
      totalOdds = combineTwoAmericanOdds(totalOdds, customParlayLegs[i].odds || -110);
    }

    // Calculate payout for $10 bet
    const payout = calculatePayout(10, totalOdds);

    return { avgTrust, minTrust, weightedTrust, totalOdds, payout };
  };

  // Helper: Combine two American odds
  const combineTwoAmericanOdds = (odds1, odds2) => {
    const decimal1 = odds1 > 0 ? (odds1 / 100) + 1 : (100 / Math.abs(odds1)) + 1;
    const decimal2 = odds2 > 0 ? (odds2 / 100) + 1 : (100 / Math.abs(odds2)) + 1;
    const combinedDecimal = decimal1 * decimal2;

    if (combinedDecimal >= 2.0) {
      return Math.round((combinedDecimal - 1) * 100);
    } else {
      return Math.round(-100 / (combinedDecimal - 1));
    }
  };

  // Helper: Calculate payout from American odds
  const calculatePayout = (stake, odds) => {
    if (odds > 0) {
      return stake + (stake * (odds / 100));
    } else {
      return stake + (stake * (100 / Math.abs(odds)));
    }
  };

  // Handle click outside team dropdown to close it
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (teamDropdownRef.current && !teamDropdownRef.current.contains(event.target)) {
        setTeamDropdownOpen(false);
      }
    };

    if (teamDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [teamDropdownOpen]);

  // Fetch players from API
  useEffect(() => {
    let retryTimeout = null;

    const fetchPlayers = async (attempt = 1) => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`${API_BASE_URL}/players`);
        const data = await response.json();

        if (data.success && data.players && data.players.length > 0) {
          setPlayers(data.players);
          setLoading(false);
        } else if (attempt < 36) {
          // Backend cache not ready yet - retry every 5 seconds (covers ~180s cold start)
          retryTimeout = setTimeout(() => fetchPlayers(attempt + 1), 5000);
        } else {
          throw new Error('No data after retries');
        }
      } catch (err) {
        console.error('Error fetching players:', err);
        setError('Failed to load player data. Using mock data.');
        setPlayers(mockPlayers);
        setLoading(false);
      }
    };

    fetchPlayers();
    return () => { if (retryTimeout) clearTimeout(retryTimeout); };
  }, []);

  // Fetch soccer data lazily — triggers when sport tab or league changes
  useEffect(() => {
    if (currentSport !== 'soccer') return;
    if (soccerData[soccerLeague] !== null) {
      setSoccerLoading(false);
      setSoccerError(null);
      return;
    }
    setSoccerLoading(true);
    setSoccerError(null);
    let retryTimeout = null;
    const fetchSoccer = async (attempt = 1) => {
      try {
        const res = await fetch(`${API_BASE_URL}/soccer/matches?league=${soccerLeague}`);
        const data = await res.json();
        if (data.success && data.matches && data.matches.length > 0) {
          setSoccerData(prev => ({ ...prev, [soccerLeague]: data.matches }));
          setSoccerLoading(false);
        } else if (attempt < 12) {
          retryTimeout = setTimeout(() => fetchSoccer(attempt + 1), 5000);
        } else {
          setSoccerError('No upcoming matches found.');
          setSoccerLoading(false);
        }
      } catch {
        setSoccerError('Failed to load soccer data.');
        setSoccerLoading(false);
      }
    };
    fetchSoccer();
    return () => { if (retryTimeout) clearTimeout(retryTimeout); };
  }, [currentSport, soccerLeague]);

  // Fetch soccer player props when a fixture is selected
  useEffect(() => {
    if (currentSport !== 'soccer' || soccerView !== 'playerProps' || !selectedSoccerFixture) return;
    const key = `${selectedSoccerFixture.homeTeam}__${selectedSoccerFixture.awayTeam}`;
    if (soccerPlayersData[key]?.players || soccerPlayersData[key]?.loading) return;
    setSoccerPlayersData(prev => ({ ...prev, [key]: { loading: true, error: null } }));
    fetch(`${API_BASE_URL}/soccer/players?league=${soccerLeague}&home_team=${encodeURIComponent(selectedSoccerFixture.homeTeam)}&away_team=${encodeURIComponent(selectedSoccerFixture.awayTeam)}`)
      .then(r => r.json())
      .then(data => {
        if (data.success && data.count > 0) {
          setSoccerPlayersData(prev => ({ ...prev, [key]: { players: data.players, loading: false, error: null } }));
        } else {
          setSoccerPlayersData(prev => ({ ...prev, [key]: { players: [], loading: false, error: 'No player data found for this fixture.' } }));
        }
      })
      .catch(() => {
        setSoccerPlayersData(prev => ({ ...prev, [key]: { players: [], loading: false, error: 'Failed to load player data.' } }));
      });
  }, [currentSport, soccerView, selectedSoccerFixture, soccerLeague]);

  // Apply dark mode to document element
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  const teams = ['all', ...new Set(players.map(p => p.team))];
  const statTypes = ['all', ...new Set(players.map(p => p.statType))];

  const filteredAndSortedPlayers = useMemo(() => {
    let filtered = players.filter(player => {
      const matchesSearch = player.name.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesTeam = selectedTeam === 'all' ||
                          (selectedTeams.length === 0 && player.team === selectedTeam) ||
                          (selectedTeams.length > 0 && selectedTeams.includes(player.team));
      const matchesStat = selectedStat === 'all' || player.statType === selectedStat;
      const matchesTrust = player.trustScore >= minTrustScore;
      const matchesHomeAway = homeAwayFilter === 'all' ||
                              (homeAwayFilter === 'home' && player.isHome) ||
                              (homeAwayFilter === 'away' && !player.isHome);
      const matchesHighConfidence = !showHighConfidenceOnly || player.trustScore >= 80;

      // Check if game is today
      const matchesGamesToday = !showGamesTodayOnly || (() => {
        if (!player.gameDate || player.gameDate === 'TBD') return false;

        const today = new Date();
        const todayStr = today.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });

        // Normalize both dates by removing padding zeros for comparison
        // Backend: "Jan 02, 2026" Frontend: "Jan 2, 2026"
        const normalizeDate = (dateStr) => {
          return dateStr.replace(/(\w+)\s+0(\d),/, '$1 $2,'); // Remove leading zero from day
        };

        return normalizeDate(player.gameDate) === normalizeDate(todayStr);
      })();

      // Check if has live odds
      const matchesLiveOdds = !showLiveOddsOnly || player.isRealLine;

      // Check minutes played filter
      const matchesMinutes = (player.avgMinutes || 0) >= minMinutes;

      return matchesSearch && matchesTeam && matchesStat && matchesTrust && matchesHomeAway && matchesHighConfidence && matchesGamesToday && matchesLiveOdds && matchesMinutes;
    });

    filtered.sort((a, b) => {
      if (sortBy === 'trustScore') return b.trustScore - a.trustScore;
      if (sortBy === 'hitRate') return b.hitRate - a.hitRate;
      if (sortBy === 'name') return a.name.localeCompare(b.name);
      return 0;
    });

    return filtered;
  }, [searchTerm, selectedTeam, selectedTeams, selectedStat, minTrustScore, sortBy, homeAwayFilter, showHighConfidenceOnly, showGamesTodayOnly, showLiveOddsOnly, minMinutes, players]);

  // Pagination
  const totalPages = Math.ceil(filteredAndSortedPlayers.length / itemsPerPage);
  const paginatedPlayers = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    return filteredAndSortedPlayers.slice(startIndex, endIndex);
  }, [filteredAndSortedPlayers, currentPage, itemsPerPage]);

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, selectedTeam, selectedTeams, selectedStat, minTrustScore, homeAwayFilter, showHighConfidenceOnly, showGamesTodayOnly, showLiveOddsOnly, minMinutes]);

  const activeFilterCount = [
    searchTerm !== '',
    selectedTeams.length > 0,
    selectedStat !== 'all',
    homeAwayFilter !== 'all',
    minTrustScore > 0,
    minMinutes > 0,
    timeRange !== 10,
    sortBy !== 'trustScore',
  ].filter(Boolean).length;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 transition-colors duration-300">
        {/* Header */}
        <div className="bg-white dark:bg-gray-950 border-b border-gray-200 dark:border-gray-800 shadow-sm">
          <div className="max-w-7xl mx-auto px-6 py-5">
            <div className="flex justify-between items-center mb-5">
              <div>
                <h1 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-white">
                  <span className="text-blue-500">Stat</span>Scout
                </h1>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">Data-Backed Player Props • NBA</p>
                {refreshMessage && (
                  <p className="text-xs text-amber-500 dark:text-amber-400 mt-1">{refreshMessage}</p>
                )}
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleRefreshStats}
                  disabled={isRefreshing}
                  className="p-2.5 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors disabled:opacity-50"
                  title="Refresh stats"
                >
                  <RefreshCw className={`w-5 h-5 ${isRefreshing ? 'animate-spin' : ''}`} />
                </button>
                <button
                  onClick={handleDarkModeToggle}
                  className="p-2.5 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                  aria-label="Toggle dark mode"
                >
                  {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                </button>
              </div>
            </div>

            {/* Sport Tabs */}
            <div className="flex gap-1 mb-2">
              {['nba', 'soccer'].map(sport => (
                <button
                  key={sport}
                  onClick={() => setCurrentSport(sport)}
                  className={`px-4 py-1.5 rounded-lg text-sm font-semibold transition-colors ${
                    currentSport === sport
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800'
                  }`}
                >
                  {sport === 'nba' ? 'NBA' : 'Soccer'}
                </button>
              ))}
            </div>

            {/* View Tabs — NBA only */}
            <div className={`flex gap-2 ${currentSport !== 'nba' ? 'hidden' : ''}`}>
              <button
                onClick={() => setCurrentView('props')}
                className={`px-5 py-2 rounded-lg text-sm font-semibold transition-all ${
                  currentView === 'props'
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                }`}
              >
                Player Props
              </button>
              <button
                onClick={() => setCurrentView('parlay')}
                className={`px-5 py-2 rounded-lg text-sm font-semibold transition-all ${
                  currentView === 'parlay'
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
                }`}
              >
                Parlay Builder
              </button>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-6 py-8">
          {/* Loading State — Skeleton Cards */}
          {currentSport === 'nba' && loading && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
              {Array.from({ length: 9 }).map((_, i) => (
                <div key={i} className="bg-white dark:bg-gray-900 rounded-xl border border-gray-100 dark:border-gray-800 p-5 animate-pulse">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-32 mb-2" />
                      <div className="h-3 bg-gray-200 dark:bg-gray-800 rounded w-20" />
                    </div>
                    <div className="h-6 bg-gray-200 dark:bg-gray-800 rounded w-16" />
                  </div>
                  <div className="h-24 bg-gray-100 dark:bg-gray-800 rounded-lg mb-4" />
                  <div className="flex justify-between items-center mb-1.5">
                    <div className="h-3 bg-gray-200 dark:bg-gray-800 rounded w-16" />
                    <div className="h-6 bg-gray-200 dark:bg-gray-800 rounded w-12" />
                  </div>
                  <div className="h-1.5 bg-gray-200 dark:bg-gray-800 rounded-full mb-4" />
                  <div className="flex justify-between items-center mb-1.5">
                    <div className="h-3 bg-gray-200 dark:bg-gray-800 rounded w-20" />
                    <div className="h-6 bg-gray-200 dark:bg-gray-800 rounded w-10" />
                  </div>
                  <div className="h-1.5 bg-gray-200 dark:bg-gray-800 rounded-full mb-4" />
                  <div className="h-12 bg-gray-100 dark:bg-gray-800 rounded" />
                </div>
              ))}
            </div>
          )}

          {/* Error State */}
          {currentSport === 'nba' && error && (
            <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl p-4 mb-6 flex items-center gap-3">
              <div className="w-1 h-8 bg-amber-500 rounded-full flex-shrink-0" />
              <div>
                <div className="text-sm font-semibold text-amber-700 dark:text-amber-300">Notice</div>
                <div className="text-sm text-amber-600 dark:text-amber-400">{error}</div>
              </div>
            </div>
          )}

          {/* Parlay Builder View */}
          {currentSport === 'nba' && currentView === 'parlay' && (
            <ParlayBuilder darkMode={darkMode} />
          )}

          {/* Player Props View */}
          {currentSport === 'nba' && currentView === 'props' && !loading && (
            <>
          {/* Stats Overview */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-100 dark:border-gray-800 p-5">
              <div className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-2">Total Props</div>
              <div className="text-3xl font-bold tabular-nums text-gray-900 dark:text-white">{filteredAndSortedPlayers.length}</div>
            </div>
            <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-100 dark:border-gray-800 p-5">
              <div className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-2">Avg Trust</div>
              <div className="text-3xl font-bold tabular-nums text-amber-500">
                {Math.round(filteredAndSortedPlayers.reduce((acc, p) => acc + p.trustScore, 0) / filteredAndSortedPlayers.length || 0)}
              </div>
            </div>
            <div
              className={`rounded-xl border p-5 cursor-pointer transition-all ${
                showHighConfidenceOnly
                  ? 'bg-green-600 border-green-500 ring-2 ring-green-400 ring-offset-2 dark:ring-offset-gray-950'
                  : 'bg-white dark:bg-gray-900 border-gray-100 dark:border-gray-800 hover:border-green-400 dark:hover:border-green-600'
              }`}
              onClick={() => setShowHighConfidenceOnly(!showHighConfidenceOnly)}
              title="Click to filter high confidence props only"
            >
              <div className={`text-xs font-semibold uppercase tracking-wider mb-2 ${showHighConfidenceOnly ? 'text-green-100' : 'text-gray-400 dark:text-gray-500'}`}>
                High Confidence {showHighConfidenceOnly && '✓'}
              </div>
              <div className={`text-3xl font-bold tabular-nums ${showHighConfidenceOnly ? 'text-white' : 'text-green-500'}`}>
                {players.filter(p => p.trustScore >= 80).length}
              </div>
            </div>
            <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-100 dark:border-gray-800 p-5">
              <div className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500 mb-2">Avg Hit Rate</div>
              <div className="text-3xl font-bold tabular-nums text-blue-500">
                {Math.round(filteredAndSortedPlayers.reduce((acc, p) => acc + p.hitRate, 0) / filteredAndSortedPlayers.length || 0)}%
              </div>
            </div>
          </div>

          {/* Team Quarter Insights - Show when teams are present in filtered data */}
          {(() => {
            const allTeamsInData = [...new Set(players.map(p => p.team))].sort();
            if (allTeamsInData.length >= 2) {
              return <TeamQuarterInsights allTeams={allTeamsInData} />;
            }
            return null;
          })()}

          {/* Filters */}
          <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-100 dark:border-gray-800 mb-8">
            <button
              className="w-full flex items-center justify-between px-5 py-4 md:px-6 md:pt-6 md:pb-0 md:cursor-default"
              onClick={() => setShowMobileFilters(f => !f)}
            >
              <div className="flex items-center gap-2">
                <Filter className="w-4 h-4 text-blue-500" />
                <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">Filters & Search</h2>
                {activeFilterCount > 0 && (
                  <span className="px-1.5 py-0.5 bg-blue-600 text-white text-xs rounded-full font-bold tabular-nums">{activeFilterCount}</span>
                )}
              </div>
              <ChevronRight className={`w-5 h-5 text-gray-400 md:hidden transition-transform duration-200 ${showMobileFilters ? 'rotate-90' : ''}`} />
            </button>

            <div className={`${showMobileFilters ? 'block' : 'hidden'} md:block px-5 pb-5 pt-3 md:px-6 md:pb-6 md:pt-4`}>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Search Player</label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div className="relative" ref={teamDropdownRef}>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Team {selectedTeams.length > 0 && `(${selectedTeams.length} selected)`}
                </label>

                {/* Dropdown Button */}
                <button
                  onClick={() => setTeamDropdownOpen(!teamDropdownOpen)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-left flex items-center justify-between"
                >
                  <span>
                    {selectedTeams.length === 0
                      ? 'All Teams'
                      : `${selectedTeams.length} team${selectedTeams.length > 1 ? 's' : ''} selected`}
                  </span>
                  <svg
                    className={`w-5 h-5 transition-transform ${teamDropdownOpen ? 'transform rotate-180' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {/* Dropdown Menu */}
                {teamDropdownOpen && (
                  <div className="absolute z-10 w-full mt-1 bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg">
                    {/* Selected teams pills */}
                    {selectedTeams.length > 0 && (
                      <div className="p-3 border-b border-gray-200 dark:border-gray-600">
                        <div className="flex flex-wrap gap-2 mb-2">
                          {selectedTeams.map(team => (
                            <button
                              key={team}
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedTeams(selectedTeams.filter(t => t !== team));
                              }}
                              className="inline-flex items-center gap-1 px-2 py-1 bg-blue-500 text-white rounded-full text-xs font-medium hover:bg-blue-600"
                            >
                              {team}
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                              </svg>
                            </button>
                          ))}
                        </div>
                        <button
                          onClick={() => setSelectedTeams([])}
                          className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                        >
                          Clear all
                        </button>
                      </div>
                    )}

                    {/* Team selection grid */}
                    <div className="max-h-64 overflow-y-auto p-3">
                      <button
                        onClick={() => {
                          setSelectedTeams([]);
                          setSelectedTeam('all');
                          setTeamDropdownOpen(false);
                        }}
                        className={`w-full px-3 py-2 mb-2 text-left rounded-lg ${
                          selectedTeams.length === 0 && selectedTeam === 'all'
                            ? 'bg-blue-500 text-white'
                            : 'bg-gray-100 dark:bg-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-500'
                        }`}
                      >
                        All Teams
                      </button>

                      <div className="grid grid-cols-3 gap-1">
                        {teams.filter(team => team !== 'all').map(team => {
                          const isSelected = selectedTeams.includes(team);
                          return (
                            <button
                              key={team}
                              onClick={() => {
                                if (isSelected) {
                                  setSelectedTeams(selectedTeams.filter(t => t !== team));
                                } else {
                                  setSelectedTeams([...selectedTeams, team]);
                                  setSelectedTeam('');
                                }
                              }}
                              className={`px-2 py-1.5 text-xs rounded ${
                                isSelected
                                  ? 'bg-blue-500 text-white'
                                  : 'bg-gray-100 dark:bg-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-500'
                              }`}
                            >
                              {team}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Stat Type</label>
                <select
                  value={selectedStat}
                  onChange={(e) => setSelectedStat(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {statTypes.map(stat => (
                    <option key={stat} value={stat}>{stat === 'all' ? 'All Stats' : stat}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Home/Away</label>
                <select
                  value={homeAwayFilter}
                  onChange={(e) => setHomeAwayFilter(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="all">All Games</option>
                  <option value="home">Home Only</option>
                  <option value="away">Away Only</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Time Range</label>
                <select
                  value={timeRange}
                  onChange={(e) => setTimeRange(parseInt(e.target.value))}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value={5}>Last 5 Games</option>
                  <option value={10}>Last 10 Games</option>
                  <option value={15}>Last 15 Games</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Sort By</label>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="trustScore">Trust Score</option>
                  <option value="hitRate">Hit Rate</option>
                  <option value="name">Name</option>
                </select>
              </div>
            </div>

            <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Min Trust Score: {minTrustScore}+
                </label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={minTrustScore}
                  onChange={(e) => setMinTrustScore(parseInt(e.target.value))}
                  className="w-full accent-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Min Minutes Per Game: {minMinutes}+ {minMinutes === 0 && '(All Players)'}
                </label>
                <input
                  type="range"
                  min="0"
                  max="35"
                  step="5"
                  value={minMinutes}
                  onChange={(e) => setMinMinutes(parseInt(e.target.value))}
                  className="w-full accent-blue-500"
                />
              </div>
            </div>
              <div className="mt-5 md:hidden">
                <button
                  onClick={() => setShowMobileFilters(false)}
                  className="w-full py-3 bg-blue-600 text-white font-semibold rounded-xl text-sm"
                >
                  Show {filteredAndSortedPlayers.length} result{filteredAndSortedPlayers.length !== 1 ? 's' : ''}
                </button>
              </div>
            </div>
          </div>

          {/* Player Cards Grid */}
          <div>
            <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-3 mb-6">
              <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
                  <span className="w-1 h-5 bg-blue-500 rounded-full inline-block" />
                  Player Props ({filteredAndSortedPlayers.length})
                </h2>
                <div className="flex gap-2">
                  <button
                    onClick={() => setShowGamesTodayOnly(!showGamesTodayOnly)}
                    className={`flex-1 sm:flex-none px-4 py-2 rounded-lg font-semibold text-sm transition-all ${
                      showGamesTodayOnly
                        ? 'bg-blue-600 text-white shadow-sm ring-2 ring-blue-300'
                        : 'bg-gray-100 dark:bg-gray-900 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-800 border border-gray-200 dark:border-gray-700'
                    }`}
                  >
                    📅 Games Today{showGamesTodayOnly ? ' ✓' : ''}
                  </button>
                  <button
                    onClick={() => setShowLiveOddsOnly(!showLiveOddsOnly)}
                    className={`flex-1 sm:flex-none px-4 py-2 rounded-lg font-semibold text-sm transition-all ${
                      showLiveOddsOnly
                        ? 'bg-green-600 text-white shadow-sm ring-2 ring-green-300'
                        : 'bg-gray-100 dark:bg-gray-900 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-800 border border-gray-200 dark:border-gray-700'
                    }`}
                  >
                    🎲 Live Odds{showLiveOddsOnly ? ' ✓' : ''}
                  </button>
                </div>
              </div>
              <div className="hidden sm:block text-sm text-gray-500 dark:text-gray-400 tabular-nums">
                {((currentPage - 1) * itemsPerPage) + 1}–{Math.min(currentPage * itemsPerPage, filteredAndSortedPlayers.length)} of {filteredAndSortedPlayers.length}
              </div>
            </div>

            {filteredAndSortedPlayers.length === 0 ? (
              <div className="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-12 text-center">
                <div className="flex justify-center mb-4">
                  <Search className="w-10 h-10 text-gray-300 dark:text-gray-700" />
                </div>
                <div className="text-lg font-semibold text-gray-900 dark:text-white mb-1">No props match your filters</div>
                <div className="text-sm text-gray-500 dark:text-gray-400 mb-6">Try broadening your search or clearing some filters</div>
                <button
                  onClick={() => {
                    setSearchTerm('');
                    setSelectedTeams([]);
                    setSelectedTeam('all');
                    setSelectedStat('all');
                    setHomeAwayFilter('all');
                    setMinTrustScore(0);
                    setMinMinutes(0);
                    setTimeRange(10);
                    setSortBy('trustScore');
                    setShowHighConfidenceOnly(false);
                    setShowGamesTodayOnly(false);
                    setShowLiveOddsOnly(false);
                  }}
                  className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl text-sm transition-colors"
                >
                  Clear all filters
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {paginatedPlayers.map(player => (
                  <PlayerCard
                    key={player.id}
                    player={player}
                    timeRange={timeRange}
                    onLineAdjust={handleLineAdjust}
                    onClick={() => setSelectedPlayer(player)}
                    onAddToParlay={addToCustomParlay}
                  />
                ))}
              </div>
            )}

            {/* Player Detail Modal */}
            {selectedPlayer && (
              <PlayerDetailModal
                player={selectedPlayer}
                onClose={() => setSelectedPlayer(null)}
              />
            )}

            {/* Pagination Controls */}
            {totalPages > 1 && (
              <div className="mt-8 flex justify-center items-center gap-2">
                <button
                  onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                  disabled={currentPage === 1}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-200 dark:disabled:bg-gray-800 disabled:text-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  Previous
                </button>

                <div className="flex gap-1">
                  {[...Array(totalPages)].map((_, index) => {
                    const pageNum = index + 1;
                    // Show first page, last page, current page, and pages around current
                    if (
                      pageNum === 1 ||
                      pageNum === totalPages ||
                      (pageNum >= currentPage - 1 && pageNum <= currentPage + 1)
                    ) {
                      return (
                        <button
                          key={pageNum}
                          onClick={() => setCurrentPage(pageNum)}
                          className={`px-4 py-2 rounded-lg transition-colors ${
                            currentPage === pageNum
                              ? 'bg-blue-600 text-white font-semibold shadow-sm'
                              : 'bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 hover:border-blue-400'
                          }`}
                        >
                          {pageNum}
                        </button>
                      );
                    } else if (
                      pageNum === currentPage - 2 ||
                      pageNum === currentPage + 2
                    ) {
                      return <span key={pageNum} className="px-2 py-2 text-gray-500">...</span>;
                    }
                    return null;
                  })}
                </div>

                <button
                  onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                  disabled={currentPage === totalPages}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-200 dark:disabled:bg-gray-800 disabled:text-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  Next
                </button>
              </div>
            )}
          </div>
            </>
          )}

          {/* Soccer View */}
          {currentSport === 'soccer' && (
            <div>
              {/* League + View selectors */}
              <div className="flex flex-wrap items-center gap-3 mb-5">
                {[['pl', 'Premier League'], ['laliga', 'La Liga']].map(([key, label]) => (
                  <button key={key} onClick={() => { setSoccerLeague(key); setSelectedSoccerFixture(null); }}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                      soccerLeague === key
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-800 text-gray-400 hover:text-gray-200'
                    }`}>
                    {label}
                  </button>
                ))}
                <div className="w-px h-5 bg-gray-700 hidden sm:block" />
                {[['matchTotals', 'Match Totals'], ['playerProps', 'Player Props']].map(([key, label]) => (
                  <button key={key} onClick={() => setSoccerView(key)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                      soccerView === key
                        ? 'bg-gray-700 text-white'
                        : 'bg-gray-800/50 text-gray-500 hover:text-gray-300'
                    }`}>
                    {label}
                  </button>
                ))}
              </div>

              <div className="flex items-center gap-2 mb-6">
                <div className="w-1 h-5 bg-blue-500 rounded-full" />
                <h2 className="text-base font-semibold text-gray-900 dark:text-white">
                  {soccerLeague === 'pl' ? 'Premier League' : 'La Liga'}: {soccerView === 'matchTotals' ? 'Match Totals' : 'Player Props'}
                </h2>
              </div>

              {/* MATCH TOTALS VIEW */}
              {soccerView === 'matchTotals' && (
                <>
                  {soccerLoading && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                      {Array.from({ length: 6 }).map((_, i) => (
                        <div key={i} className="bg-white dark:bg-gray-900 rounded-xl border border-gray-100 dark:border-gray-800 p-5 animate-pulse">
                          <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-3/4 mb-2" />
                          <div className="h-3 bg-gray-200 dark:bg-gray-800 rounded w-1/2 mb-4" />
                          <div className="border-t border-gray-100 dark:border-gray-800 pt-3">
                            <div className="grid grid-cols-3 gap-2 mb-3">
                              {[0,1,2].map(j => (
                                <div key={j} className="text-center">
                                  <div className="h-2 bg-gray-200 dark:bg-gray-800 rounded w-2/3 mx-auto mb-2" />
                                  <div className="h-6 bg-gray-200 dark:bg-gray-800 rounded w-1/2 mx-auto" />
                                </div>
                              ))}
                            </div>
                            <div className="h-16 bg-gray-100 dark:bg-gray-800 rounded-lg mb-3" />
                            <div className="h-8 bg-gray-100 dark:bg-gray-800 rounded" />
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                  {(soccerError || (!soccerLoading && !(soccerData[soccerLeague]?.length > 0))) && (
                    <div className="flex flex-col items-center justify-center py-20 text-center gap-2">
                      <p className="text-gray-500 dark:text-gray-400 font-medium">No matches available right now</p>
                      <p className="text-sm text-gray-400 dark:text-gray-500">
                        Odds are not yet posted for upcoming {soccerLeague === 'pl' ? 'Premier League' : 'La Liga'} fixtures. Check back closer to matchday.
                      </p>
                    </div>
                  )}
                  {!soccerLoading && soccerData[soccerLeague]?.length > 0 && (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                      {soccerData[soccerLeague].map(match => (
                        <SoccerMatchCard key={match.id} match={match} onAddToParlay={addSoccerLeg} />
                      ))}
                    </div>
                  )}
                </>
              )}

              {/* PLAYER PROPS VIEW */}
              {soccerView === 'playerProps' && (
                <>
                  {/* Fixture selector */}
                  {soccerLoading && (
                    <p className="text-sm text-gray-400 mb-4">Loading fixtures...</p>
                  )}
                  {!soccerLoading && soccerData[soccerLeague]?.length > 0 && (
                    <div className="mb-5 flex items-center gap-3">
                      <label className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">Fixture:</label>
                      <select
                        value={selectedSoccerFixture ? `${selectedSoccerFixture.homeTeam}__${selectedSoccerFixture.awayTeam}` : ''}
                        onChange={e => {
                          const val = e.target.value;
                          if (!val) { setSelectedSoccerFixture(null); return; }
                          const match = soccerData[soccerLeague].find(m => `${m.homeTeam}__${m.awayTeam}` === val);
                          if (match) { setSelectedSoccerFixture(match); setSoccerPropsTeamFilter(null); }
                        }}
                        className="bg-gray-800 text-gray-200 border border-gray-700 rounded-lg px-3 py-2 text-sm flex-1 max-w-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                      >
                        <option value="">Select a fixture...</option>
                        {soccerData[soccerLeague].map(match => (
                          <option key={match.id} value={`${match.homeTeam}__${match.awayTeam}`}>
                            {match.homeTeam} vs {match.awayTeam} - {match.gameDate}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}
                  {!soccerLoading && !(soccerData[soccerLeague]?.length > 0) && (
                    <div className="flex flex-col items-center justify-center py-20 text-center gap-2">
                      <p className="text-gray-500 dark:text-gray-400 font-medium">No fixtures loaded</p>
                      <p className="text-sm text-gray-400 dark:text-gray-500">Switch to Match Totals to load upcoming fixtures first.</p>
                    </div>
                  )}

                  {selectedSoccerFixture && (() => {
                    const key = `${selectedSoccerFixture.homeTeam}__${selectedSoccerFixture.awayTeam}`;
                    const state = soccerPlayersData[key];
                    return (
                      <div>
                        {/* Market + team filter tabs */}
                        <div className="flex flex-wrap gap-2 mb-4">
                          {SOCCER_MARKETS.map(m => (
                            <button key={m.key} onClick={() => setSoccerPropsMarket(m.key)}
                              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                                soccerPropsMarket === m.key
                                  ? 'bg-blue-600 text-white'
                                  : 'bg-gray-800 text-gray-400 hover:text-gray-200'
                              }`}>
                              {m.label}
                            </button>
                          ))}
                          <div className="w-px h-5 bg-gray-700 self-center hidden sm:block" />
                          {[
                            [null, 'Both Teams'],
                            ['home', selectedSoccerFixture.homeTeam],
                            ['away', selectedSoccerFixture.awayTeam],
                          ].map(([val, label]) => (
                            <button key={String(val)} onClick={() => setSoccerPropsTeamFilter(val)}
                              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                                soccerPropsTeamFilter === val
                                  ? 'bg-gray-700 text-white'
                                  : 'bg-gray-800/50 text-gray-500 hover:text-gray-300'
                              }`}>
                              {label}
                            </button>
                          ))}
                        </div>

                        {/* Loading state */}
                        {(!state || state.loading) && (
                          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                            {Array.from({ length: 8 }).map((_, i) => (
                              <div key={i} className="bg-white dark:bg-gray-900 rounded-xl border border-gray-100 dark:border-gray-800 p-4 animate-pulse h-40">
                                <div className="h-3 bg-gray-200 dark:bg-gray-800 rounded w-3/4 mb-2" />
                                <div className="h-2 bg-gray-200 dark:bg-gray-800 rounded w-1/2 mb-4" />
                                <div className="h-8 bg-gray-200 dark:bg-gray-800 rounded w-1/2 mb-2" />
                                <div className="h-1.5 bg-gray-100 dark:bg-gray-800 rounded-full" />
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Error state */}
                        {state && !state.loading && state.error && (
                          <div className="flex flex-col items-center justify-center py-16 gap-2 text-center">
                            <p className="text-gray-500 dark:text-gray-400 font-medium">{state.error}</p>
                          </div>
                        )}

                        {/* Player cards */}
                        {state && !state.loading && state.players?.length > 0 && (() => {
                          const mdef = SOCCER_MARKETS.find(m => m.key === soccerPropsMarket) || SOCCER_MARKETS[0];
                          const isGk = soccerPropsMarket === 'gk';
                          const visible = state.players
                            .filter(p => {
                              if (soccerPropsTeamFilter && p.teamSide !== soccerPropsTeamFilter) return false;
                              if (isGk && p.position !== 'GK') return false;
                              if (!isGk && p.position === 'GK') return false;
                              return true;
                            })
                            .map(p => {
                              const arr = p[mdef.arr] || [];
                              const hr = isGk
                                ? (arr.length ? Math.round(arr.filter(v => v < mdef.defaultLine).length / arr.length * 100) : null)
                                : calcHitRate(arr, mdef.defaultLine);
                              return { ...p, _sortRate: hr ?? -1 };
                            })
                            .sort((a, b) => b._sortRate - a._sortRate);
                          return visible.length > 0 ? (
                            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                              {visible.map(p => (
                                <SoccerPlayerCard key={p.id} player={p} market={soccerPropsMarket} onAddToParlay={addSoccerLeg} />
                              ))}
                            </div>
                          ) : (
                            <div className="flex flex-col items-center justify-center py-16 gap-2 text-center">
                              <p className="text-gray-500 dark:text-gray-400 font-medium">No players match current filters</p>
                            </div>
                          );
                        })()}
                      </div>
                    );
                  })()}
                </>
              )}
            </div>
          )}
        </div>

        {/* Custom Parlay Builder Sidebar — visible regardless of sport */}
        {(currentSport === 'nba' || customParlayLegs.length > 0) && (
          <>
            {/* Floating Toggle Button (when sidebar is closed) */}
            {!isParlaySidebarOpen && customParlayLegs.length > 0 && (
              <button
                onClick={() => setIsParlaySidebarOpen(true)}
                className="fixed right-0 top-1/2 transform -translate-y-1/2 bg-blue-600 hover:bg-blue-700 text-white px-3 py-4 rounded-l-lg shadow-lg flex items-center gap-2 z-40 transition-all"
              >
                <ChevronLeft className="w-5 h-5" />
                <div className="flex flex-col items-center">
                  <span className="text-xs font-semibold">Parlay</span>
                  <span className="bg-white text-blue-600 rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold">
                    {customParlayLegs.length}
                  </span>
                </div>
              </button>
            )}

            {/* Sidebar Panel */}
            <div className={`fixed right-0 top-0 h-full w-96 bg-white dark:bg-gray-900 shadow-2xl transform transition-transform duration-300 z-50 ${
              isParlaySidebarOpen ? 'translate-x-0' : 'translate-x-full'
            }`}>
              <div className="h-full flex flex-col">
                {/* Header */}
                <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-4 flex justify-between items-center">
                  <h2 className="text-xl font-bold">Custom Parlay</h2>
                  <button
                    onClick={() => setIsParlaySidebarOpen(false)}
                    className="p-2 hover:bg-blue-500 rounded-lg transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                {customParlayLegs.length === 0 ? (
                  <div className="flex-1 flex items-center justify-center p-6 text-center text-gray-500 dark:text-gray-400">
                    <div>
                      <Plus className="w-16 h-16 mx-auto mb-4 opacity-50" />
                      <p className="text-lg font-semibold mb-2">No legs added yet</p>
                      <p className="text-sm">Click "Add to Custom Parlay" on any player card, or use the Over/Under buttons on soccer match cards</p>
                    </div>
                  </div>
                ) : (
                  <>
                    {/* Parlay Stats Summary */}
                    <div className="p-4 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-600">
                      {(() => {
                        const metrics = calculateParlayMetrics();
                        return (
                          <div className="space-y-3">
                            <div className="grid grid-cols-3 gap-2 text-center">
                              <div>
                                <div className="text-xs text-gray-600 dark:text-gray-400">Avg Trust</div>
                                <div className="text-lg font-bold text-blue-600 dark:text-blue-400">
                                  {Math.round(metrics.avgTrust)}
                                </div>
                              </div>
                              <div>
                                <div className="text-xs text-gray-600 dark:text-gray-400">Min Trust</div>
                                <div className="text-lg font-bold text-yellow-600 dark:text-yellow-400">
                                  {Math.round(metrics.minTrust)}
                                </div>
                              </div>
                              <div>
                                <div className="text-xs text-gray-600 dark:text-gray-400">Weighted</div>
                                <div className="text-lg font-bold text-green-600 dark:text-green-400">
                                  {Math.round(metrics.weightedTrust)}
                                </div>
                              </div>
                            </div>

                            <div className="bg-blue-100 dark:bg-blue-900 rounded-lg p-3">
                              <div className="text-sm text-blue-800 dark:text-blue-200 font-semibold mb-1">
                                Total Parlay Odds
                              </div>
                              <div className="text-2xl font-bold text-blue-900 dark:text-blue-100">
                                {metrics.totalOdds > 0 ? '+' : ''}{metrics.totalOdds}
                              </div>
                              <div className="text-xs text-blue-700 dark:text-blue-300 mt-1">
                                $10 → ${metrics.payout.toFixed(2)}
                              </div>
                            </div>
                          </div>
                        );
                      })()}
                    </div>

                    {/* Parlay Legs List */}
                    <div className="flex-1 overflow-y-auto p-4 space-y-3">
                      {customParlayLegs.map((leg, index) => (
                        <div key={leg.id} className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3 border border-gray-200 dark:border-gray-600">
                          <div className="flex justify-between items-start mb-2">
                            <div className="flex-1">
                              {leg.sport === 'soccer' ? (
                                <>
                                  <div className="font-semibold text-gray-900 dark:text-white text-sm">
                                    {leg.homeTeam} vs {leg.awayTeam}
                                  </div>
                                  <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                                    {leg.side === 'over' ? 'Over' : 'Under'} {leg.line} goals
                                    {leg.odds != null && <span className="ml-1 font-medium">{leg.odds > 0 ? `+${leg.odds}` : leg.odds}</span>}
                                  </div>
                                </>
                              ) : leg.sport === 'soccer_player' ? (
                                <>
                                  <div className="font-semibold text-gray-900 dark:text-white text-sm">{leg.playerName}</div>
                                  <div className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                                    {leg.team} - {leg.statType}
                                    {leg.hitRate != null && <span className="ml-1 text-blue-400">{leg.hitRate}% hit</span>}
                                    {leg.odds != null && <span className="ml-1 font-medium text-gray-300">{leg.odds > 0 ? `+${leg.odds}` : leg.odds} <span className="text-gray-500 font-normal">est.</span></span>}
                                  </div>
                                </>
                              ) : (
                                <>
                                  <div className="font-semibold text-gray-900 dark:text-white">{leg.playerName}</div>
                                  <div className="text-xs text-gray-600 dark:text-gray-400">
                                    {leg.team} vs {leg.opponent}
                                  </div>
                                </>
                              )}
                            </div>
                            <button
                              onClick={() => removeFromCustomParlay(leg.id)}
                              className="p-1 hover:bg-red-100 dark:hover:bg-red-900 rounded transition-colors"
                            >
                              <X className="w-4 h-4 text-red-600 dark:text-red-400" />
                            </button>
                          </div>

                          {leg.sport !== 'soccer' && leg.sport !== 'soccer_player' && (
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{leg.statType}</span>
                              <span className="text-xs bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded">
                                Trust: {leg.trustScore}
                              </span>
                            </div>
                          )}

                          {leg.trustScore != null && leg.sport === 'soccer' && (
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-xs bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded">
                                Trust: {leg.trustScore}
                              </span>
                              {leg.hitRate != null && (
                                <span className="text-xs text-gray-500 dark:text-gray-400">Over%: {leg.hitRate}%</span>
                              )}
                            </div>
                          )}

                          <div className="flex items-center gap-2">
                            <label className="text-xs text-gray-600 dark:text-gray-400">Line:</label>
                            <input
                              type="number"
                              step={leg.sport === 'soccer' ? '0.5' : '0.5'}
                              value={leg.line}
                              onChange={(e) => updateCustomParlayLeg(leg.id, e.target.value)}
                              className="w-20 px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-600 dark:text-white rounded focus:ring-2 focus:ring-blue-500"
                            />
                            <input
                              type="range"
                              min={leg.sport === 'soccer' ? '0.5' : leg.sport === 'soccer_player' ? leg.lineMin : Math.max(0.5, leg.originalLine - 10)}
                              max={leg.sport === 'soccer' ? '5.5' : leg.sport === 'soccer_player' ? leg.lineMax : leg.originalLine + 10}
                              step={leg.sport === 'soccer_player' ? leg.lineStep : '0.5'}
                              value={leg.line}
                              onChange={(e) => updateCustomParlayLeg(leg.id, e.target.value)}
                              className="flex-1"
                            />
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Actions Footer */}
                    <div className="p-4 border-t border-gray-200 dark:border-gray-600 space-y-2">
                      <input
                        type="text"
                        placeholder="Parlay Name (optional)"
                        value={currentParlayName}
                        onChange={(e) => setCurrentParlayName(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                      <div className="grid grid-cols-2 gap-2">
                        <button
                          onClick={saveCustomParlay}
                          className="bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded-lg transition-all flex items-center justify-center gap-2"
                        >
                          <Save className="w-4 h-4" />
                          Save
                        </button>
                        <button
                          onClick={clearCustomParlay}
                          className="bg-red-600 hover:bg-red-700 text-white font-semibold py-2 px-4 rounded-lg transition-all flex items-center justify-center gap-2"
                        >
                          <Trash2 className="w-4 h-4" />
                          Clear
                        </button>
                      </div>

                      {/* Saved Parlays */}
                      {savedParlays.length > 0 && (
                        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-600">
                          <div className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                            Saved Parlays ({savedParlays.length})
                          </div>
                          <div className="space-y-2 max-h-40 overflow-y-auto">
                            {savedParlays.map(parlay => (
                              <div key={parlay.id} className="flex items-center justify-between bg-gray-100 dark:bg-gray-600 p-2 rounded">
                                <button
                                  onClick={() => loadSavedParlay(parlay.id)}
                                  className="flex-1 text-left text-sm hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                                >
                                  <div className="font-medium">{parlay.name}</div>
                                  <div className="text-xs text-gray-500 dark:text-gray-400">
                                    {parlay.legs.length} legs
                                  </div>
                                </button>
                                <button
                                  onClick={() => deleteSavedParlay(parlay.id)}
                                  className="p-1 hover:bg-red-100 dark:hover:bg-red-900 rounded transition-colors"
                                >
                                  <Trash2 className="w-4 h-4 text-red-600 dark:text-red-400" />
                                </button>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Overlay (click to close sidebar) */}
            {isParlaySidebarOpen && (
              <div
                onClick={() => setIsParlaySidebarOpen(false)}
                className="fixed inset-0 bg-black bg-opacity-50 z-40"
              />
            )}
          </>
        )}
      </div>
  );
}