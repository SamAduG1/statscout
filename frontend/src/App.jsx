import React, { useState, useMemo, useEffect, useRef } from 'react';
import { TrendingUp, TrendingDown, Filter, Search, Home, Plane, Moon, Sun, Flame, Snowflake } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Cell } from 'recharts';

const API_BASE_URL = 'http://localhost:5000/api';

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
const TeamQuarterInsights = ({ team1, team2 }) => {
  const [quarterData, setQuarterData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (team1 && team2) {
      fetchQuarterData();
    }
  }, [team1, team2]);

  const fetchQuarterData = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/quarters/matchup?team1=${team1}&team2=${team2}&season=2025-26`
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

  if (!quarterData || loading) return null;

  const { team1: t1Data, team2: t2Data, insights } = quarterData;

  return (
    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-gray-800 dark:to-gray-700 rounded-lg shadow-lg p-6 mb-8">
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
        <TrendingUp className="w-6 h-6 text-blue-600" />
        Quarter Performance Insights
      </h2>

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

const PlayerCard = ({ player, timeRange, onLineAdjust, onClick }) => {
  const [customLine, setCustomLine] = React.useState(player.line);
  const [isAdjusting, setIsAdjusting] = React.useState(false);

  const handleLineChange = async () => {
  if (customLine === player.line) return;
  
  console.log('Adjusting line for:', player.name, player.statType, 'from', player.line, 'to', customLine);
  
  setIsAdjusting(true);
  try {
    const response = await fetch('http://localhost:5000/api/calculate', {
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
            <h3 className="font-bold text-lg text-gray-900 dark:text-white">{player.name}</h3>
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
    </div>
  );
};

export default function StatScoutDashboard() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTeam, setSelectedTeam] = useState('all');
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
  const [selectedPlayer, setSelectedPlayer] = useState(null);

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
      const matchesTeam = selectedTeam === 'all' || player.team === selectedTeam;
      const matchesStat = selectedStat === 'all' || player.statType === selectedStat;
      const matchesTrust = player.trustScore >= minTrustScore;
      const matchesHomeAway = homeAwayFilter === 'all' ||
                              (homeAwayFilter === 'home' && player.isHome) ||
                              (homeAwayFilter === 'away' && !player.isHome);
      const matchesHighConfidence = !showHighConfidenceOnly || player.trustScore >= 80;

      // Check if game is today
      const matchesGamesToday = !showGamesTodayOnly || (() => {
        const today = new Date();
        const todayStr = today.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
        // gameDate format is "Dec 18, 2025" - compare just month and day
        return player.gameDate && player.gameDate.startsWith(todayStr.substring(0, 6)); // "Dec 18"
      })();

      // Check if has live odds
      const matchesLiveOdds = !showLiveOddsOnly || player.isRealLine;

      return matchesSearch && matchesTeam && matchesStat && matchesTrust && matchesHomeAway && matchesHighConfidence && matchesGamesToday && matchesLiveOdds;
    });

    filtered.sort((a, b) => {
      if (sortBy === 'trustScore') return b.trustScore - a.trustScore;
      if (sortBy === 'hitRate') return b.hitRate - a.hitRate;
      if (sortBy === 'name') return a.name.localeCompare(b.name);
      return 0;
    });

    return filtered;
  }, [searchTerm, selectedTeam, selectedStat, minTrustScore, sortBy, homeAwayFilter, showHighConfidenceOnly, showGamesTodayOnly, showLiveOddsOnly, players]);

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
  }, [searchTerm, selectedTeam, selectedStat, minTrustScore, homeAwayFilter, showHighConfidenceOnly, showGamesTodayOnly, showLiveOddsOnly]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-gray-900 dark:to-gray-800 transition-colors duration-300">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-800 dark:from-blue-800 dark:to-blue-950 text-white shadow-lg">
          <div className="max-w-7xl mx-auto px-6 py-8">
            <div className="flex justify-between items-center">
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

          {!loading && (
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
            const filteredTeams = [...new Set(filteredAndSortedPlayers.map(p => p.team))];
            if (filteredTeams.length >= 2) {
              return <TeamQuarterInsights team1={filteredTeams[0]} team2={filteredTeams[1]} />;
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

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Team</label>
                <select
                  value={selectedTeam}
                  onChange={(e) => setSelectedTeam(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {teams.map(team => (
                    <option key={team} value={team}>{team === 'all' ? 'All Teams' : team}</option>
                  ))}
                </select>
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

            <div className="mt-4">
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
      </div>
  );
}