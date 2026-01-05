import React, { useState, useMemo, useEffect, useRef } from 'react';
import { TrendingUp, TrendingDown, Filter, Search, Home, Plane, Moon, Sun, Flame, Snowflake, Plus, X, Save, Trash2, ChevronRight, ChevronLeft } from 'lucide-react';
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
    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-gray-800 dark:to-gray-700 rounded-lg shadow-lg p-6 mb-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <TrendingUp className="w-6 h-6 text-blue-600" />
          Quarter Performance Insights
        </h2>

        {/* Team Selectors */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Team 1:</label>
            <select
              value={selectedTeam1}
              onChange={(e) => setSelectedTeam1(e.target.value)}
              className="px-3 py-1.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            >
              {allTeams.map(team => (
                <option key={team} value={team}>{team}</option>
              ))}
            </select>
          </div>

          <span className="text-gray-500 dark:text-gray-400 font-bold">VS</span>

          <div className="flex items-center gap-2">
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Team 2:</label>
            <select
              value={selectedTeam2}
              onChange={(e) => setSelectedTeam2(e.target.value)}
              className="px-3 py-1.5 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            >
              {allTeams.map(team => (
                <option key={team} value={team}>{team}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {loading && (
        <div className="text-center py-8">
          <div className="inline-block w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          <p className="mt-2 text-gray-600 dark:text-gray-400">Loading quarter data...</p>
        </div>
      )}

      {!loading && !quarterData && (
        <div className="text-center py-8 text-gray-600 dark:text-gray-400">
          No quarter data available for this matchup
        </div>
      )}

      {!loading && quarterData && t1Data && t2Data && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            {/* Team 1 */}
            <div className="bg-white dark:bg-gray-900 rounded-lg p-4 shadow">
              <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-3">{t1Data.team}</h3>

          <div className="grid grid-cols-4 gap-2 mb-4">
            <div className="text-center">
              <div className="text-xs text-gray-500 dark:text-gray-400">Q1</div>
              <div className="text-xl font-bold text-blue-600">{t1Data.q1_avg}</div>
            </div>
            <div className="text-center">
              <div className="text-xs text-gray-500 dark:text-gray-400">Q2</div>
              <div className="text-xl font-bold text-blue-600">{t1Data.q2_avg}</div>
            </div>
            <div className="text-center">
              <div className="text-xs text-gray-500 dark:text-gray-400">Q3</div>
              <div className="text-xl font-bold text-blue-600">{t1Data.q3_avg}</div>
            </div>
            <div className="text-center">
              <div className="text-xs text-gray-500 dark:text-gray-400">Q4</div>
              <div className="text-xl font-bold text-blue-600">{t1Data.q4_avg}</div>
            </div>
          </div>

          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">First Half Avg:</span>
              <span className="font-semibold text-gray-900 dark:text-white">{t1Data.first_half_avg} pts</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Second Half Avg:</span>
              <span className="font-semibold text-gray-900 dark:text-white">{t1Data.second_half_avg} pts</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Through 3Q:</span>
              <span className="font-semibold text-gray-900 dark:text-white">{t1Data.three_quarter_avg} pts</span>
            </div>
            <div className="flex justify-between border-t pt-2 mt-2 border-gray-200 dark:border-gray-700">
              <span className="text-gray-600 dark:text-gray-400">Reach 100+ by Q3:</span>
              <span className={`font-bold ${t1Data.reached_100_by_q3_pct >= 50 ? 'text-green-600' : 'text-orange-600'}`}>
                {t1Data.reached_100_by_q3_pct}% ({t1Data.reached_100_by_q3_count}/{t1Data.total_games})
              </span>
            </div>
          </div>
        </div>

        {/* Team 2 */}
        <div className="bg-white dark:bg-gray-900 rounded-lg p-4 shadow">
          <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-3">{t2Data.team}</h3>

          <div className="grid grid-cols-4 gap-2 mb-4">
            <div className="text-center">
              <div className="text-xs text-gray-500 dark:text-gray-400">Q1</div>
              <div className="text-xl font-bold text-purple-600">{t2Data.q1_avg}</div>
            </div>
            <div className="text-center">
              <div className="text-xs text-gray-500 dark:text-gray-400">Q2</div>
              <div className="text-xl font-bold text-purple-600">{t2Data.q2_avg}</div>
            </div>
            <div className="text-center">
              <div className="text-xs text-gray-500 dark:text-gray-400">Q3</div>
              <div className="text-xl font-bold text-purple-600">{t2Data.q3_avg}</div>
            </div>
            <div className="text-center">
              <div className="text-xs text-gray-500 dark:text-gray-400">Q4</div>
              <div className="text-xl font-bold text-purple-600">{t2Data.q4_avg}</div>
            </div>
          </div>

          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">First Half Avg:</span>
              <span className="font-semibold text-gray-900 dark:text-white">{t2Data.first_half_avg} pts</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Second Half Avg:</span>
              <span className="font-semibold text-gray-900 dark:text-white">{t2Data.second_half_avg} pts</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Through 3Q:</span>
              <span className="font-semibold text-gray-900 dark:text-white">{t2Data.three_quarter_avg} pts</span>
            </div>
            <div className="flex justify-between border-t pt-2 mt-2 border-gray-200 dark:border-gray-700">
              <span className="text-gray-600 dark:text-gray-400">Reach 100+ by Q3:</span>
              <span className={`font-bold ${t2Data.reached_100_by_q3_pct >= 50 ? 'text-green-600' : 'text-orange-600'}`}>
                {t2Data.reached_100_by_q3_pct}% ({t2Data.reached_100_by_q3_count}/{t2Data.total_games})
              </span>
            </div>
          </div>
        </div>
      </div>

          {/* Insights */}
          {insights && insights.length > 0 && (
            <div className="bg-blue-100 dark:bg-blue-900 rounded-lg p-4">
              <h4 className="font-semibold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
                <Flame className="w-4 h-4 text-orange-500" />
                Key Insights
              </h4>
              <ul className="space-y-1">
                {insights.map((insight, idx) => (
                  <li key={idx} className="text-sm text-gray-700 dark:text-gray-300">
                    • {insight}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
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
            className="flex items-center gap-1 px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
          >
            {currentBookmaker.bookmaker}
            <svg className={`w-3 h-3 transition-transform ${isOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {/* Dropdown menu */}
          {isOpen && uniqueBookmakers.length > 1 && (
            <div className="absolute right-0 mt-1 w-32 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg shadow-lg z-10">
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
      <div className="mt-2 flex items-center justify-between bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-lg p-2">
        <span className="text-xs text-gray-600 dark:text-gray-400 font-medium">Line:</span>
        <span className="text-lg font-bold text-gray-900 dark:text-white">{currentBookmaker.line}</span>
      </div>
    </div>
  );
};

// Player Detail Modal Component - Full analysis page
const PlayerDetailModal = ({ player, onClose }) => {
  if (!player) return null;

  const [matchupHistory, setMatchupHistory] = React.useState(null);
  const [loadingMatchup, setLoadingMatchup] = React.useState(false);

  // Load matchup history when modal opens
  React.useEffect(() => {
    if (player && player.opponent) {
      loadMatchupHistory();
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

  // Calculate some stats
  const last5Avg = player.last5Games && player.last5Games.length > 0
    ? (player.last5Games.reduce((a, b) => a + b, 0) / player.last5Games.length).toFixed(1)
    : 0;
  const last15Avg = player.last15Games && player.last15Games.length > 0
    ? (player.last15Games.reduce((a, b) => a + b, 0) / player.last15Games.length).toFixed(1)
    : 0;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div
        className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 rounded-t-xl">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-3xl font-bold">{player.name}</h2>
              <div className="flex items-center gap-3 mt-2">
                <span className="px-3 py-1 bg-white/20 rounded-full text-sm font-semibold">
                  {player.team}
                </span>
                <span className="px-3 py-1 bg-white/20 rounded-full text-sm font-semibold">
                  {player.position}
                </span>
                <span className="px-3 py-1 bg-white/20 rounded-full text-sm font-semibold">
                  {player.statType}
                </span>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:bg-white/20 rounded-full p-2 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-3 gap-4 mt-4">
            <div className="bg-white/10 rounded-lg p-3">
              <div className="text-xs opacity-90">Line</div>
              <div className="text-2xl font-bold">{player.line}</div>
            </div>
            <div className="bg-white/10 rounded-lg p-3">
              <div className="text-xs opacity-90">Hit Rate</div>
              <div className="text-2xl font-bold">{player.hitRate}%</div>
            </div>
            <div className="bg-white/10 rounded-lg p-3">
              <div className="text-xs opacity-90">Trust Score</div>
              <div className="text-2xl font-bold">{player.trustScore}</div>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Performance Overview */}
          <div className="mb-6">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Performance Overview</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                <div className="text-sm text-gray-600 dark:text-gray-400">Last 5 Games Average</div>
                <div className="text-3xl font-bold text-gray-900 dark:text-white">{last5Avg}</div>
                <div className={`text-sm font-semibold ${last5Avg > player.line ? 'text-green-600' : 'text-red-600'}`}>
                  {last5Avg > player.line ? `+${(last5Avg - player.line).toFixed(1)} vs line` : `${(last5Avg - player.line).toFixed(1)} vs line`}
                </div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                <div className="text-sm text-gray-600 dark:text-gray-400">Last 15 Games Average</div>
                <div className="text-3xl font-bold text-gray-900 dark:text-white">{last15Avg}</div>
                <div className={`text-sm font-semibold ${last15Avg > player.line ? 'text-green-600' : 'text-red-600'}`}>
                  {last15Avg > player.line ? `+${(last15Avg - player.line).toFixed(1)} vs line` : `${(last15Avg - player.line).toFixed(1)} vs line`}
                </div>
              </div>
            </div>
          </div>

          {/* Performance Charts */}
          <div className="mb-6">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Performance Trends</h3>

            {/* Line Chart - Performance over time */}
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 mb-4">
              <div className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-3">Last 15 Games Performance</div>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={player.last15Games ? player.last15Games.map((stat, idx) => ({
                  game: `G${idx + 1}`,
                  value: stat,
                  line: player.line
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
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <div className="text-sm font-semibold text-gray-600 dark:text-gray-400 mb-3">Over/Under Results</div>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={player.last15Games ? player.last15Games.map((stat, idx) => ({
                  game: `G${idx + 1}`,
                  value: stat,
                  hit: stat > player.line
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
          <div className="mb-6">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Recent Game Log</h3>
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-200 dark:bg-gray-600">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-gray-700 dark:text-gray-300">Game</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold text-gray-700 dark:text-gray-300">{player.statType}</th>
                    <th className="px-4 py-2 text-center text-xs font-semibold text-gray-700 dark:text-gray-300">vs Line</th>
                    <th className="px-4 py-2 text-center text-xs font-semibold text-gray-700 dark:text-gray-300">Result</th>
                  </tr>
                </thead>
                <tbody>
                  {player.last15Games && player.last15Games.slice(0, 10).map((stat, idx) => {
                    const hitLine = stat > player.line;
                    return (
                      <tr key={idx} className="border-t border-gray-200 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-600">
                        <td className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400">Game {idx + 1}</td>
                        <td className="px-4 py-2 text-right text-sm font-bold text-gray-900 dark:text-white">{stat}</td>
                        <td className={`px-4 py-2 text-center text-sm font-semibold ${hitLine ? 'text-green-600' : 'text-red-600'}`}>
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
            <div className="mb-6">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Sportsbook Lines</h3>
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
                    <div key={idx} className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
                      <div className="flex justify-between items-center">
                        <div>
                          <div className="text-sm text-gray-600 dark:text-gray-400 font-medium">{bm.bookmaker}</div>
                          <div className="text-2xl font-bold text-gray-900 dark:text-white mt-1">{bm.line}</div>
                        </div>
                        {bm.over_odds && (
                          <div className="text-right">
                            <div className="text-xs text-gray-500 dark:text-gray-400">Over</div>
                            <div className="text-sm font-semibold text-gray-700 dark:text-gray-300">{bm.over_odds > 0 ? `+${bm.over_odds}` : bm.over_odds}</div>
                          </div>
                        )}
                        {bm.under_odds && (
                          <div className="text-right">
                            <div className="text-xs text-gray-500 dark:text-gray-400">Under</div>
                            <div className="text-sm font-semibold text-gray-700 dark:text-gray-300">{bm.under_odds > 0 ? `+${bm.under_odds}` : bm.under_odds}</div>
                          </div>
                        )}
                      </div>
                    </div>
                  ));
                })()}
              </div>
            </div>
          )}

          {/* Location Split (Home vs Away) */}
          {player.locationSplit && player.locationSplit.has_data && (
            <div className="mb-6">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <span>📍</span> Home vs Away Performance
              </h3>

              {player.locationSplit.warning && (
                <div className={`mb-4 p-3 rounded-lg border ${
                  player.locationSplit.is_significant
                    ? player.locationSplit.favorable_location
                      ? 'bg-green-50 border-green-300 dark:bg-green-900/20 dark:border-green-800'
                      : 'bg-yellow-50 border-yellow-300 dark:bg-yellow-900/20 dark:border-yellow-800'
                    : 'bg-blue-50 border-blue-300 dark:bg-blue-900/20 dark:border-blue-800'
                }`}>
                  <p className={`text-sm font-semibold ${
                    player.locationSplit.is_significant
                      ? player.locationSplit.favorable_location
                        ? 'text-green-700 dark:text-green-300'
                        : 'text-yellow-700 dark:text-yellow-300'
                      : 'text-blue-700 dark:text-blue-300'
                  }`}>
                    {player.locationSplit.warning}
                  </p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                {/* Home Stats */}
                <div className={`rounded-lg p-4 border ${
                  player.isHome
                    ? 'bg-blue-50 border-blue-300 dark:bg-blue-900/30 dark:border-blue-700 ring-2 ring-blue-400'
                    : 'bg-gray-50 border-gray-200 dark:bg-gray-800 dark:border-gray-700'
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
                    {player.locationSplit.home_avg}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {player.locationSplit.home_games} games
                  </div>
                </div>

                {/* Away Stats */}
                <div className={`rounded-lg p-4 border ${
                  !player.isHome
                    ? 'bg-blue-50 border-blue-300 dark:bg-blue-900/30 dark:border-blue-700 ring-2 ring-blue-400'
                    : 'bg-gray-50 border-gray-200 dark:bg-gray-800 dark:border-gray-700'
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
                    {player.locationSplit.away_avg}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {player.locationSplit.away_games} games
                  </div>
                </div>
              </div>

              {/* Difference Indicator */}
              <div className="mt-3 text-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Difference: <span className={`font-bold ${
                    Math.abs(player.locationSplit.difference) >= 3.0
                      ? 'text-orange-600 dark:text-orange-400'
                      : 'text-gray-700 dark:text-gray-300'
                  }`}>
                    {player.locationSplit.difference > 0 ? '+' : ''}{player.locationSplit.difference}
                  </span> {player.statType.toLowerCase()} {player.locationSplit.better_at_home ? 'better at home' : 'better away'}
                </span>
              </div>
            </div>
          )}

          {/* Matchup History vs Opponent */}
          <div className="mb-6">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              Matchup History vs {player.opponent}
            </h3>

            {loadingMatchup && (
              <div className="text-center py-8">
                <div className="inline-block w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                <p className="mt-2 text-gray-600 dark:text-gray-400">Loading matchup history...</p>
              </div>
            )}

            {!loadingMatchup && matchupHistory && matchupHistory.games_played > 0 && (
              <div>
                {/* Matchup Averages */}
                <div className="grid grid-cols-3 gap-3 mb-4">
                  <div className="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-lg p-4 border border-purple-200 dark:border-purple-800">
                    <div className="text-sm text-gray-600 dark:text-gray-400">Games Played</div>
                    <div className="text-2xl font-bold text-gray-900 dark:text-white">{matchupHistory.games_played}</div>
                  </div>
                  <div className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-lg p-4 border border-green-200 dark:border-green-800">
                    <div className="text-sm text-gray-600 dark:text-gray-400">Avg {player.statType}</div>
                    <div className="text-2xl font-bold text-gray-900 dark:text-white">
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
                          'PR': matchupHistory.averages.PR
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
                        'PR': matchupHistory.averages.PR
                      };
                      return (statMap[player.statType] || 0) > player.line ? 'text-green-600' : 'text-red-600';
                    })()}`}>
                      vs Line {player.line}
                    </div>
                  </div>
                  <div className="bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
                    <div className="text-sm text-gray-600 dark:text-gray-400">Avg PRA</div>
                    <div className="text-2xl font-bold text-gray-900 dark:text-white">{matchupHistory.averages.PRA}</div>
                  </div>
                </div>

                {/* All Stats */}
                <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 mb-4">
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
                <div className="bg-gray-50 dark:bg-gray-700 rounded-lg overflow-hidden">
                  <table className="w-full">
                    <thead className="bg-gray-200 dark:bg-gray-600">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-semibold text-gray-700 dark:text-gray-300">Date</th>
                        <th className="px-4 py-2 text-center text-xs font-semibold text-gray-700 dark:text-gray-300">H/A</th>
                        <th className="px-4 py-2 text-right text-xs font-semibold text-gray-700 dark:text-gray-300">PTS</th>
                        <th className="px-4 py-2 text-right text-xs font-semibold text-gray-700 dark:text-gray-300">REB</th>
                        <th className="px-4 py-2 text-right text-xs font-semibold text-gray-700 dark:text-gray-300">AST</th>
                        <th className="px-4 py-2 text-right text-xs font-semibold text-gray-700 dark:text-gray-300">PRA</th>
                        <th className="px-4 py-2 text-right text-xs font-semibold text-gray-700 dark:text-gray-300">MIN</th>
                      </tr>
                    </thead>
                    <tbody>
                      {matchupHistory.games.map((game, idx) => (
                        <tr key={idx} className="border-t border-gray-200 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-600">
                          <td className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400">{game.date}</td>
                          <td className="px-4 py-2 text-center text-sm">
                            {game.is_home ? <Home className="w-4 h-4 mx-auto text-gray-600 dark:text-gray-400" /> : <Plane className="w-4 h-4 mx-auto text-gray-600 dark:text-gray-400" />}
                          </td>
                          <td className="px-4 py-2 text-right text-sm font-bold text-gray-900 dark:text-white">{game.points}</td>
                          <td className="px-4 py-2 text-right text-sm font-bold text-gray-900 dark:text-white">{game.rebounds}</td>
                          <td className="px-4 py-2 text-right text-sm font-bold text-gray-900 dark:text-white">{game.assists}</td>
                          <td className="px-4 py-2 text-right text-sm font-bold text-blue-600 dark:text-blue-400">{game.PRA}</td>
                          <td className="px-4 py-2 text-right text-sm text-gray-600 dark:text-gray-400">{game.minutes ? game.minutes.toFixed(1) : '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {!loadingMatchup && matchupHistory && matchupHistory.games_played === 0 && (
              <div className="text-center py-8 text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-700 rounded-lg">
                No previous games found against {player.opponent} this season
              </div>
            )}

            {!loadingMatchup && !matchupHistory && (
              <div className="text-center py-8 text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-700 rounded-lg">
                Unable to load matchup history
              </div>
            )}
          </div>

          {/* Upcoming Game */}
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">Next Game</h3>
            <div className="flex justify-between items-center">
              <div>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  vs {player.opponent}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  {player.gameDate} • {player.gameTime}
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  {player.isHome ? 'Home' : 'Away'}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const PlayerCard = ({ player, timeRange, onLineAdjust, onClick, onAddToParlay }) => {
  const [customLine, setCustomLine] = React.useState(player.line);
  const [isAdjusting, setIsAdjusting] = React.useState(false);

  const handleLineChange = async () => {
  if (customLine === player.line) return;
  
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
    if (score >= 70) return 'bg-blue-500';
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
      className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-5 hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 cursor-pointer"
      onClick={onClick}
    >
      <div className="flex justify-between items-start mb-3">
        <div className="flex items-center gap-3">
          {/* Team color indicator */}
          <div 
            className="w-1 h-16 rounded-full" 
            style={{ backgroundColor: player.teamColor }}
          />
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
            <p className="text-sm text-gray-600 dark:text-gray-400 flex items-center gap-2">
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

      <div className="mb-4 bg-gray-50 dark:bg-gray-700 rounded-lg p-3" onClick={(e) => e.stopPropagation()}>
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
              className="w-20 px-2 py-1 text-right text-xl font-bold border border-gray-300 dark:border-gray-600 dark:bg-gray-600 dark:text-white rounded focus:ring-2 focus:ring-blue-500"
              disabled={isAdjusting}
            />
            {isAdjusting && <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>}
          </div>
        </div>
        <div className="text-sm text-gray-600 dark:text-gray-400">
          Avg Last {timeRange}: <span className="font-semibold">{player.avgLastN}</span>
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

        {/* Bookmaker Lines - Compact Selector */}
        {player.bookmakerLines && player.bookmakerLines.length > 0 && (
          <BookmakerSelector bookmakerLines={player.bookmakerLines} />
        )}
      </div>

      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm text-gray-600 dark:text-gray-400">Hit Rate</span>
          <div className="text-right">
            <div className="text-lg font-semibold dark:text-white">{player.hitRate}%</div>
            <div className="text-xs text-gray-500 dark:text-gray-500">
              Season: {player.season_hits || Math.round((player.hitRate / 100) * (player.total_games || 20))}/{player.total_games || 20}
            </div>
          </div>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all"
            style={{ width: `${player.hitRate}%` }}
          />
        </div>
        {player.recent_hit_rate !== undefined && player.recent_total >= 5 && (
          <div className="mt-2 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-gray-600 dark:text-gray-400">Last {player.recent_total} Games</span>
              <span className={`font-semibold ${
                player.recent_hit_rate > player.hitRate ? 'text-green-600 dark:text-green-400' :
                player.recent_hit_rate < player.hitRate ? 'text-red-600 dark:text-red-400' :
                'text-gray-700 dark:text-gray-300'
              }`}>
                {player.recent_hit_rate}% ({player.recent_hits}/{player.recent_total})
                {player.recent_hit_rate > player.hitRate && ' ↗'}
                {player.recent_hit_rate < player.hitRate && ' ↘'}
              </span>
            </div>
          </div>
        )}
      </div>

      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm text-gray-600 dark:text-gray-400">Trust Score</span>
          <span className="text-lg font-semibold dark:text-white">{player.trustScore}</span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div 
            className={`h-2 rounded-full transition-all ${getTrustColor(player.trustScore)}`}
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
            return (
              <div
                key={idx}
                className={`flex-1 rounded-t ${isOver ? 'bg-green-400 hover:bg-green-500' : 'bg-red-400 hover:bg-red-500'} transition-all cursor-pointer`}
                style={{ height: `${height}%` }}
                title={`Game ${idx + 1}: ${stat} (${isOver ? 'Over' : 'Under'})`}
              />
            );
          })}
        </div>
        <div className="flex justify-between text-xs text-gray-500 dark:text-gray-500 mt-1">
          <span>Oldest</span>
          <span>Most Recent</span>
        </div>
      </div>

      {/* Add to Parlay Button */}
      {onAddToParlay && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onAddToParlay(player);
          }}
          className="mt-4 w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition-all transform hover:scale-105 flex items-center justify-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Add to Custom Parlay
        </button>
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
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Build Your Parlay</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Target Odds */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Target Odds
            </label>
            <select
              value={targetOdds}
              onChange={(e) => setTargetOdds(Number(e.target.value))}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
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
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
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
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
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
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
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
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
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
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
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
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
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
                  className="inline-flex items-center gap-2 px-3 py-1 bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 rounded-full text-sm"
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
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 max-h-64 overflow-y-auto p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-300 dark:border-gray-600">
              {availableGames.map(game => (
                <label
                  key={game.id}
                  className="flex items-center space-x-3 p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-blue-500 dark:hover:border-blue-400 cursor-pointer transition-colors"
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
          className="mt-6 w-full bg-blue-600 hover:bg-blue-700 dark:bg-blue-700 dark:hover:bg-blue-800 text-white font-semibold py-3 px-6 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
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
        <div className="bg-red-100 dark:bg-red-900 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-200 px-4 py-3 rounded-lg">
          <p className="font-semibold">Error</p>
          <p>{error}</p>
        </div>
      )}

      {/* Parlay Suggestions */}
      {parlays.length > 0 && (
        <div className="space-y-6">
          {/* Regenerate Button */}
          <div className="flex justify-between items-center">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white">
              Parlay Suggestions
            </h3>
            <button
              onClick={generateParlays}
              disabled={loading}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 dark:bg-green-700 dark:hover:bg-green-800 text-white font-semibold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
              </svg>
              {loading ? 'Generating...' : 'Regenerate'}
            </button>
          </div>

          {parlays.map((parlay, index) => {
            // Handle error parlays
            if (parlay.error) {
              return (
                <div key={index} className="bg-yellow-100 dark:bg-yellow-900 border border-yellow-400 dark:border-yellow-700 text-yellow-800 dark:text-yellow-200 px-6 py-4 rounded-lg">
                  <p className="font-semibold">{parlay.error}</p>
                  <p className="text-sm mt-1">{parlay.suggestion}</p>
                  {parlay.available_props && (
                    <p className="text-sm mt-1">Available props: {parlay.available_props}</p>
                  )}
                </div>
              );
            }

            return (
              <div key={index} className="bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden">
                {/* Parlay Header */}
                <div className="bg-gradient-to-r from-green-600 to-green-700 dark:from-green-700 dark:to-green-800 text-white px-6 py-4">
                  <div className="flex justify-between items-center">
                    <h3 className="text-xl font-bold">Parlay #{index + 1}</h3>
                    <div className="text-right">
                      <div className="text-2xl font-bold">{parlay.parlay_odds_display}</div>
                      <div className="text-sm opacity-90">{parlay.num_legs} legs • ${parlay.payout_per_dollar.toFixed(2)} per $1</div>
                    </div>
                  </div>
                  <div className="flex gap-4 mt-3">
                    <div className="bg-white/20 rounded px-3 py-1">
                      <div className="text-xs opacity-75">Avg Trust</div>
                      <div className="font-semibold">{parlay.avg_trust}%</div>
                    </div>
                    <div className="bg-white/20 rounded px-3 py-1">
                      <div className="text-xs opacity-75">True Win Rate</div>
                      <div className="font-semibold">{parlay.true_win_rate}%</div>
                    </div>
                    <div className="bg-white/20 rounded px-3 py-1">
                      <div className="text-xs opacity-75">Safety</div>
                      <div className="font-semibold capitalize">{parlay.safety_level}</div>
                    </div>
                  </div>
                </div>

                {/* Parlay Legs */}
                <div className="p-6 space-y-3">
                  {parlay.legs.map((leg, legIndex) => (
                    <div key={legIndex} className="flex justify-between items-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                      <div>
                        <div className="font-semibold text-gray-900 dark:text-white">{leg.player_name}</div>
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          {leg.team} vs {leg.opponent} • {leg.stat_type} O{leg.line}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-semibold text-gray-900 dark:text-white">
                          {leg.odds > 0 ? `+${leg.odds}` : leg.odds}
                        </div>
                        <div className="text-sm">
                          <span className={`font-medium ${
                            leg.trust_score >= 70 ? 'text-green-600 dark:text-green-400' :
                            leg.trust_score >= 60 ? 'text-yellow-600 dark:text-yellow-400' :
                            'text-red-600 dark:text-red-400'
                          }`}>
                            {leg.trust_score}% trust
                          </span>
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
  const [darkMode, setDarkMode] = useState(false);
  const [players, setPlayers] = useState(mockPlayers);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(30); // Show 30 props per page
  const [showHighConfidenceOnly, setShowHighConfidenceOnly] = useState(false);
  const [showGamesTodayOnly, setShowGamesTodayOnly] = useState(false);
  const [showLiveOddsOnly, setShowLiveOddsOnly] = useState(false);
  const [minMinutes, setMinMinutes] = useState(0);
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

  const removeFromCustomParlay = (legId) => {
    setCustomParlayLegs(prev => prev.filter(leg => leg.id !== legId));
  };

  // Helper: Convert hit rate to American odds
  const hitRateToOdds = (hitRate) => {
    // Convert hit rate (0-100) to probability (0-1)
    const probability = hitRate / 100;

    if (probability >= 0.5) {
      // Favorite odds (negative)
      return Math.round(-100 * (probability / (1 - probability)));
    } else {
      // Underdog odds (positive)
      return Math.round(100 * ((1 - probability) / probability));
    }
  };

  const updateCustomParlayLeg = async (legId, newLine) => {
    const leg = customParlayLegs.find(l => l.id === legId);
    if (!leg) return;

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

    const avgTrust = customParlayLegs.reduce((sum, leg) => sum + leg.trustScore, 0) / customParlayLegs.length;
    const minTrust = Math.min(...customParlayLegs.map(leg => leg.trustScore));

    // Weighted trust - higher odds props have more weight
    const totalWeight = customParlayLegs.reduce((sum, leg) => sum + Math.abs(leg.odds), 0);
    const weightedTrust = customParlayLegs.reduce((sum, leg) => {
      const weight = Math.abs(leg.odds) / totalWeight;
      return sum + (leg.trustScore * weight);
    }, 0);

    // Calculate total American odds
    let totalOdds = customParlayLegs[0]?.odds || -110;
    for (let i = 1; i < customParlayLegs.length; i++) {
      totalOdds = combineTwoAmericanOdds(totalOdds, customParlayLegs[i].odds);
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
    const fetchPlayers = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const response = await fetch(`${API_BASE_URL}/players`);
        const data = await response.json();
        
        if (data.success && data.players) {
          setPlayers(data.players);
        } else {
          throw new Error('Failed to fetch player data');
        }
      } catch (err) {
        console.error('Error fetching players:', err);
        setError('Failed to load player data. Using mock data.');
        setPlayers(mockPlayers); // Fallback to mock data
      } finally {
        setLoading(false);
      }
    };

    fetchPlayers();
  }, []);

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

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-gray-900 dark:to-gray-800 transition-colors duration-300">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-800 dark:from-blue-800 dark:to-blue-950 text-white shadow-lg">
          <div className="max-w-7xl mx-auto px-6 py-8">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h1 className="text-4xl font-bold mb-2">StatScout</h1>
                <p className="text-blue-100">Data-Backed Player Props • NBA</p>
              </div>
              <button
                onClick={() => setDarkMode(!darkMode)}
                className="p-3 rounded-full hover:bg-blue-700 transition-colors"
                aria-label="Toggle dark mode"
              >
                {darkMode ? <Sun className="w-6 h-6" /> : <Moon className="w-6 h-6" />}
              </button>
            </div>

            {/* View Tabs */}
            <div className="flex gap-4">
              <button
                onClick={() => setCurrentView('props')}
                className={`px-6 py-2 rounded-lg font-semibold transition-all ${
                  currentView === 'props'
                    ? 'bg-white text-blue-600'
                    : 'bg-blue-700 text-white hover:bg-blue-600'
                }`}
              >
                Player Props
              </button>
              <button
                onClick={() => setCurrentView('parlay')}
                className={`px-6 py-2 rounded-lg font-semibold transition-all ${
                  currentView === 'parlay'
                    ? 'bg-white text-blue-600'
                    : 'bg-blue-700 text-white hover:bg-blue-600'
                }`}
              >
                Parlay Builder
              </button>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-6 py-8">
          {/* Loading State */}
          {loading && (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <p className="mt-4 text-gray-600 dark:text-gray-400">Loading player data...</p>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="bg-yellow-100 dark:bg-yellow-900 border border-yellow-400 dark:border-yellow-700 text-yellow-700 dark:text-yellow-200 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          {/* Parlay Builder View */}
          {currentView === 'parlay' && (
            <ParlayBuilder darkMode={darkMode} />
          )}

          {/* Player Props View */}
          {currentView === 'props' && !loading && (
            <>
          {/* Stats Overview */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-5 transition-colors">
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Total Props</div>
              <div className="text-3xl font-bold text-gray-900 dark:text-white">{filteredAndSortedPlayers.length}</div>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-5 transition-colors">
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Avg Trust Score</div>
              <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                {Math.round(filteredAndSortedPlayers.reduce((acc, p) => acc + p.trustScore, 0) / filteredAndSortedPlayers.length || 0)}
              </div>
            </div>
            <div
              className={`rounded-lg shadow p-5 transition-all cursor-pointer transform hover:scale-105 ${
                showHighConfidenceOnly
                  ? 'bg-green-600 dark:bg-green-700 ring-4 ring-green-300 dark:ring-green-500'
                  : 'bg-white dark:bg-gray-800 hover:shadow-lg'
              }`}
              onClick={() => setShowHighConfidenceOnly(!showHighConfidenceOnly)}
              title="Click to filter high confidence props only"
            >
              <div className={`text-sm mb-1 ${showHighConfidenceOnly ? 'text-green-100' : 'text-gray-600 dark:text-gray-400'}`}>
                High Confidence {showHighConfidenceOnly && '(Active)'}
              </div>
              <div className={`text-3xl font-bold ${showHighConfidenceOnly ? 'text-white' : 'text-green-600 dark:text-green-400'}`}>
                {players.filter(p => p.trustScore >= 80).length}
              </div>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-5 transition-colors">
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Avg Hit Rate</div>
              <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">
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
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 mb-8 transition-colors">
            <div className="flex items-center gap-2 mb-4">
              <Filter className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Filters & Search</h2>
            </div>
            
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
                    className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-left flex items-center justify-between"
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
                  <div className="absolute z-10 w-full mt-1 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg">
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
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
                  className="w-full"
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
                  className="w-full"
                />
              </div>
            </div>
          </div>

          {/* Player Cards Grid */}
          <div>
            <div className="flex justify-between items-center mb-6">
              <div className="flex items-center gap-4">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                  Player Props ({filteredAndSortedPlayers.length})
                </h2>
                <button
                  onClick={() => setShowGamesTodayOnly(!showGamesTodayOnly)}
                  className={`px-4 py-2 rounded-lg font-semibold text-sm transition-all transform hover:scale-105 ${
                    showGamesTodayOnly
                      ? 'bg-blue-600 text-white shadow-lg ring-2 ring-blue-300'
                      : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
                  }`}
                >
                  {showGamesTodayOnly ? '📅 Games Today (Active)' : '📅 Games Today'}
                </button>
                <button
                  onClick={() => setShowLiveOddsOnly(!showLiveOddsOnly)}
                  className={`px-4 py-2 rounded-lg font-semibold text-sm transition-all transform hover:scale-105 ${
                    showLiveOddsOnly
                      ? 'bg-green-600 text-white shadow-lg ring-2 ring-green-300'
                      : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600'
                  }`}
                >
                  {showLiveOddsOnly ? '🎲 Live Odds Only (Active)' : '🎲 Live Odds Only'}
                </button>
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                Showing {((currentPage - 1) * itemsPerPage) + 1}-{Math.min(currentPage * itemsPerPage, filteredAndSortedPlayers.length)} of {filteredAndSortedPlayers.length}
              </div>
            </div>

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
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
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
                              ? 'bg-blue-600 text-white'
                              : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600'
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
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                >
                  Next
                </button>
              </div>
            )}
          </div>
            </>
          )}
        </div>

        {/* Custom Parlay Builder Sidebar */}
        {currentView === 'props' && (
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
            <div className={`fixed right-0 top-0 h-full w-96 bg-white dark:bg-gray-800 shadow-2xl transform transition-transform duration-300 z-50 ${
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
                      <p className="text-sm">Click "Add to Custom Parlay" on any player card to get started</p>
                    </div>
                  </div>
                ) : (
                  <>
                    {/* Parlay Stats Summary */}
                    <div className="p-4 bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
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
                        <div key={leg.id} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 border border-gray-200 dark:border-gray-600">
                          <div className="flex justify-between items-start mb-2">
                            <div className="flex-1">
                              <div className="font-semibold text-gray-900 dark:text-white">{leg.playerName}</div>
                              <div className="text-xs text-gray-600 dark:text-gray-400">
                                {leg.team} vs {leg.opponent}
                              </div>
                            </div>
                            <button
                              onClick={() => removeFromCustomParlay(leg.id)}
                              className="p-1 hover:bg-red-100 dark:hover:bg-red-900 rounded transition-colors"
                            >
                              <X className="w-4 h-4 text-red-600 dark:text-red-400" />
                            </button>
                          </div>

                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{leg.statType}</span>
                            <span className="text-xs bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded">
                              Trust: {leg.trustScore}
                            </span>
                          </div>

                          <div className="flex items-center gap-2">
                            <label className="text-xs text-gray-600 dark:text-gray-400">Line:</label>
                            <input
                              type="number"
                              step="0.5"
                              value={leg.line}
                              onChange={(e) => updateCustomParlayLeg(leg.id, e.target.value)}
                              className="w-20 px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 dark:bg-gray-600 dark:text-white rounded focus:ring-2 focus:ring-blue-500"
                            />
                            <input
                              type="range"
                              min={Math.max(0.5, leg.originalLine - 10)}
                              max={leg.originalLine + 10}
                              step="0.5"
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
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500"
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