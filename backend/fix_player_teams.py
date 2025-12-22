"""
Fix team assignments for players on wrong teams
"""
import sys
import io
from models import get_engine, get_session, Player

# Force UTF-8 output
if not isinstance(sys.stdout, io.TextIOWrapper) or sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except:
        pass

# Correct team assignments for 2025-26 season (based on NBA API actual game data)
TEAM_CORRECTIONS = {
    "Kristaps Porziņģis": "ATL",    # Playing for ATL in 2025-26
    "Dillon Brooks": "PHX",          # Playing for PHX in 2025-26
    "Caris LeVert": "DET",           # Playing for DET in 2025-26
    "Brook Lopez": "LAC",            # Playing for LAC in 2025-26
    "CJ McCollum": "WAS",            # Playing for WAS in 2025-26
    "Chris Paul": "LAC",             # Playing for LAC in 2025-26
    "Deandre Ayton": "LAL",          # Playing for LAL in 2025-26
    "Marcus Smart": "LAL",           # Playing for LAL in 2025-26
    "Desmond Bane": "ORL",           # Playing for ORL in 2025-26
    "Jusuf Nurkić": "UTA",           # Playing for UTA in 2025-26
    "Michael Porter Jr.": "BKN",     # Playing for BKN in 2025-26
    "Myles Turner": "MIL",           # Playing for MIL in 2025-26
    "Mark Williams": "PHX",          # Playing for PHX in 2025-26
    "Clint Capela": "HOU",           # Playing for HOU in 2025-26
}


def fix_player_teams():
    """Update team assignments for players"""

    print("=" * 60)
    print("FIXING PLAYER TEAM ASSIGNMENTS")
    print("=" * 60)

    engine = get_engine()
    session = get_session(engine)

    try:
        fixed_count = 0

        for player_name, correct_team in TEAM_CORRECTIONS.items():
            player = session.query(Player).filter_by(name=player_name).first()

            if player:
                old_team = player.team
                if old_team != correct_team:
                    player.team = correct_team
                    print(f"✓ {player_name}: {old_team} → {correct_team}")
                    fixed_count += 1
                else:
                    print(f"  {player_name}: Already correct ({correct_team})")
            else:
                print(f"✗ {player_name}: Not found in database")

        session.commit()

        print("\n" + "=" * 60)
        print(f"Fixed {fixed_count} player team assignments")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] Failed to fix teams: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    fix_player_teams()
