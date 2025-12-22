"""
Team Quarter Analytics Calculator
Analyzes team quarter performance trends, averages, and insights
"""

from models import TeamGame, get_engine, get_session
from sqlalchemy import func
from typing import Dict, List, Any


class TeamQuarterAnalytics:
    """Calculate team quarter performance analytics"""

    def __init__(self):
        self.engine = get_engine()
        self.session = get_session(self.engine)

    def get_team_quarter_averages(self, team_abbr: str, season: str = "2025-26") -> Dict[str, Any]:
        """Get team's average points per quarter"""

        games = self.session.query(TeamGame).filter_by(
            team=team_abbr,
            season=season
        ).all()

        if not games:
            return None

        # Calculate averages
        q1_avg = sum(g.q1_points for g in games if g.q1_points) / len([g for g in games if g.q1_points])
        q2_avg = sum(g.q2_points for g in games if g.q2_points) / len([g for g in games if g.q2_points])
        q3_avg = sum(g.q3_points for g in games if g.q3_points) / len([g for g in games if g.q3_points])
        q4_avg = sum(g.q4_points for g in games if g.q4_points) / len([g for g in games if g.q4_points])

        # First and second half averages
        h1_games = [g.first_half_points for g in games if g.first_half_points is not None]
        h2_games = [g.second_half_points for g in games if g.second_half_points is not None]

        h1_avg = sum(h1_games) / len(h1_games) if h1_games else 0
        h2_avg = sum(h2_games) / len(h2_games) if h2_games else 0

        # Three quarter average
        three_q_games = [g.three_quarter_points for g in games if g.three_quarter_points is not None]
        three_q_avg = sum(three_q_games) / len(three_q_games) if three_q_games else 0

        # How often they reach 100+ by Q3
        reached_100_count = sum(1 for g in games if g.reached_100_by_q3)
        reached_100_pct = (reached_100_count / len(games)) * 100 if games else 0

        return {
            'team': team_abbr,
            'total_games': len(games),
            'q1_avg': round(q1_avg, 1),
            'q2_avg': round(q2_avg, 1),
            'q3_avg': round(q3_avg, 1),
            'q4_avg': round(q4_avg, 1),
            'first_half_avg': round(h1_avg, 1),
            'second_half_avg': round(h2_avg, 1),
            'three_quarter_avg': round(three_q_avg, 1),
            'reached_100_by_q3_count': reached_100_count,
            'reached_100_by_q3_pct': round(reached_100_pct, 1)
        }

    def get_quarter_win_correlation(self, team_abbr: str, season: str = "2025-26") -> Dict[str, Any]:
        """Analyze correlation between leading after each quarter and winning"""

        games = self.session.query(TeamGame).filter_by(
            team=team_abbr,
            season=season
        ).all()

        if not games:
            return None

        # Track wins when leading after each quarter
        q1_leads = []
        q2_leads = []  # Halftime
        q3_leads = []

        for game in games:
            # Get opponent game data to compare
            opponent_game = self.session.query(TeamGame).filter_by(
                game_id=game.game_id.replace(f"_{team_abbr}", f"_{game.opponent}"),
                season=season
            ).first()

            if not opponent_game:
                continue

            # Q1 lead
            if game.q1_points and opponent_game.q1_points:
                leading_q1 = game.q1_points > opponent_game.q1_points
                q1_leads.append({'leading': leading_q1, 'won': game.won})

            # Halftime lead
            if game.first_half_points and opponent_game.first_half_points:
                leading_h1 = game.first_half_points > opponent_game.first_half_points
                q2_leads.append({'leading': leading_h1, 'won': game.won})

            # Q3 lead
            if game.three_quarter_points and opponent_game.three_quarter_points:
                leading_q3 = game.three_quarter_points > opponent_game.three_quarter_points
                q3_leads.append({'leading': leading_q3, 'won': game.won})

        # Calculate win percentages when leading
        q1_lead_wins = sum(1 for x in q1_leads if x['leading'] and x['won'])
        q1_lead_total = sum(1 for x in q1_leads if x['leading'])

        h1_lead_wins = sum(1 for x in q2_leads if x['leading'] and x['won'])
        h1_lead_total = sum(1 for x in q2_leads if x['leading'])

        q3_lead_wins = sum(1 for x in q3_leads if x['leading'] and x['won'])
        q3_lead_total = sum(1 for x in q3_leads if x['leading'])

        return {
            'team': team_abbr,
            'when_leading_after_q1': {
                'record': f"{q1_lead_wins}-{q1_lead_total - q1_lead_wins}",
                'win_pct': round((q1_lead_wins / q1_lead_total) * 100, 1) if q1_lead_total > 0 else 0
            },
            'when_leading_at_halftime': {
                'record': f"{h1_lead_wins}-{h1_lead_total - h1_lead_wins}",
                'win_pct': round((h1_lead_wins / h1_lead_total) * 100, 1) if h1_lead_total > 0 else 0
            },
            'when_leading_after_q3': {
                'record': f"{q3_lead_wins}-{q3_lead_total - q3_lead_wins}",
                'win_pct': round((q3_lead_wins / q3_lead_total) * 100, 1) if q3_lead_total > 0 else 0
            }
        }

    def get_matchup_quarter_analysis(self, team1: str, team2: str, season: str = "2025-26") -> Dict[str, Any]:
        """Get quarter analysis for a team vs team matchup"""

        team1_avg = self.get_team_quarter_averages(team1, season)
        team2_avg = self.get_team_quarter_averages(team2, season)

        if not team1_avg or not team2_avg:
            return None

        # Get head-to-head history if exists
        h2h_games = self.session.query(TeamGame).filter_by(
            team=team1,
            opponent=team2,
            season=season
        ).all()

        h2h_summary = None
        if h2h_games:
            avg_q1 = sum(g.q1_points for g in h2h_games if g.q1_points) / len(h2h_games)
            avg_total = sum(g.total_points for g in h2h_games) / len(h2h_games)
            wins = sum(1 for g in h2h_games if g.won)

            h2h_summary = {
                'games_played': len(h2h_games),
                'record': f"{wins}-{len(h2h_games) - wins}",
                'avg_q1_vs_opponent': round(avg_q1, 1),
                'avg_total_vs_opponent': round(avg_total, 1)
            }

        return {
            'matchup': f"{team1} vs {team2}",
            'team1': team1_avg,
            'team2': team2_avg,
            'head_to_head': h2h_summary,
            'insights': self._generate_matchup_insights(team1_avg, team2_avg)
        }

    def _generate_matchup_insights(self, team1_avg: Dict, team2_avg: Dict) -> List[str]:
        """Generate insights for a matchup"""

        insights = []

        # Q1 comparison
        if team1_avg['q1_avg'] > team2_avg['q1_avg'] + 3:
            insights.append(f"{team1_avg['team']} averages {team1_avg['q1_avg']} pts in Q1 vs {team2_avg['team']}'s {team2_avg['q1_avg']}")

        # 100 by Q3 comparison
        if team1_avg['reached_100_by_q3_pct'] > 50:
            insights.append(f"{team1_avg['team']} reaches 100+ by Q3 in {team1_avg['reached_100_by_q3_pct']}% of games")

        if team2_avg['reached_100_by_q3_pct'] > 50:
            insights.append(f"{team2_avg['team']} reaches 100+ by Q3 in {team2_avg['reached_100_by_q3_pct']}% of games")

        # Fast starters
        if team1_avg['first_half_avg'] > team1_avg['second_half_avg'] + 5:
            insights.append(f"{team1_avg['team']} is a fast starter (better first half)")

        if team2_avg['second_half_avg'] > team2_avg['first_half_avg'] + 5:
            insights.append(f"{team2_avg['team']} is a slow starter (better second half)")

        return insights

    def close(self):
        """Close database session"""
        self.session.close()


if __name__ == "__main__":
    analytics = TeamQuarterAnalytics()

    # Test with Lakers
    print("Testing Lakers Quarter Analytics:")
    print("=" * 70)

    lakers_avg = analytics.get_team_quarter_averages("LAL")
    if lakers_avg:
        print(f"\nLakers Quarter Averages:")
        print(f"  Q1: {lakers_avg['q1_avg']} pts")
        print(f"  Q2: {lakers_avg['q2_avg']} pts")
        print(f"  Q3: {lakers_avg['q3_avg']} pts")
        print(f"  Q4: {lakers_avg['q4_avg']} pts")
        print(f"  First Half: {lakers_avg['first_half_avg']} pts")
        print(f"  Second Half: {lakers_avg['second_half_avg']} pts")
        print(f"  Through 3Q: {lakers_avg['three_quarter_avg']} pts")
        print(f"  Reach 100+ by Q3: {lakers_avg['reached_100_by_q3_pct']}% ({lakers_avg['reached_100_by_q3_count']}/{lakers_avg['total_games']} games)")

    lakers_corr = analytics.get_quarter_win_correlation("LAL")
    if lakers_corr:
        print(f"\nLakers Win Correlation:")
        print(f"  When leading after Q1: {lakers_corr['when_leading_after_q1']['record']} ({lakers_corr['when_leading_after_q1']['win_pct']}%)")
        print(f"  When leading at halftime: {lakers_corr['when_leading_at_halftime']['record']} ({lakers_corr['when_leading_at_halftime']['win_pct']}%)")
        print(f"  When leading after Q3: {lakers_corr['when_leading_after_q3']['record']} ({lakers_corr['when_leading_after_q3']['win_pct']}%)")

    analytics.close()
