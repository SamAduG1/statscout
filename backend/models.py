"""
StatScout Database Models
Defines the database schema using SQLAlchemy
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Date, ForeignKey, UniqueConstraint
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


class Player(Base):
    """Player information table"""
    __tablename__ = 'players'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)
    team = Column(String, nullable=False, index=True)
    position = Column(String, nullable=False)
    
    # Relationship to games
    games = relationship("Game", back_populates="player", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Player(name='{self.name}', team='{self.team}', position='{self.position}')>"


class Game(Base):
    """Individual game statistics table"""
    __tablename__ = 'games'

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    opponent = Column(String, nullable=False)
    is_home = Column(Boolean, nullable=False)

    # Full Game Statistics
    points = Column(Integer, nullable=False)
    rebounds = Column(Integer, nullable=False)
    assists = Column(Integer, nullable=False)
    steals = Column(Integer, nullable=False)
    blocks = Column(Integer, nullable=False)
    three_pm = Column(Integer, nullable=False)
    minutes = Column(Float, nullable=True)  # Minutes played (can be null for older data)

    # Quarter-by-Quarter Statistics (nullable for backward compatibility)
    q1_points = Column(Integer, nullable=True)
    q2_points = Column(Integer, nullable=True)
    q3_points = Column(Integer, nullable=True)
    q4_points = Column(Integer, nullable=True)

    q1_rebounds = Column(Integer, nullable=True)
    q2_rebounds = Column(Integer, nullable=True)
    q3_rebounds = Column(Integer, nullable=True)
    q4_rebounds = Column(Integer, nullable=True)

    q1_assists = Column(Integer, nullable=True)
    q2_assists = Column(Integer, nullable=True)
    q3_assists = Column(Integer, nullable=True)
    q4_assists = Column(Integer, nullable=True)

    # Relationship to player
    player = relationship("Player", back_populates="games")

    @property
    def first_half_points(self):
        """Calculate first half points (Q1 + Q2)"""
        if self.q1_points is not None and self.q2_points is not None:
            return self.q1_points + self.q2_points
        return None

    @property
    def second_half_points(self):
        """Calculate second half points (Q3 + Q4)"""
        if self.q3_points is not None and self.q4_points is not None:
            return self.q3_points + self.q4_points
        return None

    @property
    def first_half_total(self):
        """Calculate first half combined stats (P+R+A)"""
        if all(x is not None for x in [self.q1_points, self.q2_points, self.q1_rebounds, self.q2_rebounds, self.q1_assists, self.q2_assists]):
            return (self.q1_points + self.q2_points +
                   self.q1_rebounds + self.q2_rebounds +
                   self.q1_assists + self.q2_assists)
        return None

    def __repr__(self):
        return f"<Game(player_id={self.player_id}, date='{self.date}', opponent='{self.opponent}')>"


class TeamGame(Base):
    """Team game with quarter-by-quarter scoring"""
    __tablename__ = 'team_games'

    id = Column(Integer, primary_key=True)
    game_id = Column(String, nullable=False, index=True)  # NBA API game ID (not unique — two rows per game, one per team)
    team = Column(String, nullable=False, index=True)  # Team abbreviation (e.g., "LAL")
    opponent = Column(String, nullable=False)  # Opponent abbreviation
    date = Column(Date, nullable=False, index=True)
    is_home = Column(Boolean, nullable=False)
    season = Column(String, nullable=False)  # e.g., "2025-26"

    # Quarter scoring
    q1_points = Column(Integer, nullable=True)
    q2_points = Column(Integer, nullable=True)
    q3_points = Column(Integer, nullable=True)
    q4_points = Column(Integer, nullable=True)
    ot_points = Column(Integer, nullable=True, default=0)  # Overtime total

    # Game totals
    total_points = Column(Integer, nullable=False)
    opponent_points = Column(Integer, nullable=False)
    won = Column(Boolean, nullable=False)  # True if won, False if lost

    __table_args__ = (
        UniqueConstraint('game_id', 'team', name='uq_team_game'),
    )

    def __repr__(self):
        return f"<TeamGame(team='{self.team}', opponent='{self.opponent}', date='{self.date}')>"

    @property
    def first_half_points(self):
        """Calculate first half points (Q1 + Q2)"""
        if self.q1_points is not None and self.q2_points is not None:
            return self.q1_points + self.q2_points
        return None

    @property
    def second_half_points(self):
        """Calculate second half points (Q3 + Q4)"""
        if self.q3_points is not None and self.q4_points is not None:
            return self.q3_points + self.q4_points
        return None

    @property
    def three_quarter_points(self):
        """Calculate points through 3 quarters (Q1 + Q2 + Q3)"""
        if self.q1_points is not None and self.q2_points is not None and self.q3_points is not None:
            return self.q1_points + self.q2_points + self.q3_points
        return None

    @property
    def reached_100_by_q3(self):
        """Check if team reached 100+ points by end of Q3"""
        three_q = self.three_quarter_points
        if three_q is not None:
            return three_q >= 100
        return None


class SoccerPlayer(Base):
    """Soccer player information table"""
    __tablename__ = 'soccer_players'

    id           = Column(Integer, primary_key=True)
    understat_id = Column(Integer, unique=True, nullable=False, index=True)
    name         = Column(String, nullable=False)
    team_name    = Column(String, nullable=False, index=True)
    league       = Column(String, nullable=False, index=True)  # 'pl' or 'laliga'
    position     = Column(String, nullable=False)              # 'GK', 'DF', 'MF', 'FW'
    last_updated = Column(Date, nullable=False)

    games = relationship("SoccerPlayerGame", back_populates="player", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SoccerPlayer(name='{self.name}', team='{self.team_name}', pos='{self.position}')>"


class SoccerPlayerGame(Base):
    """Soccer player per-match statistics"""
    __tablename__ = 'soccer_player_games'

    id              = Column(Integer, primary_key=True)
    player_id       = Column(Integer, ForeignKey('soccer_players.id'), nullable=False, index=True)
    match_date      = Column(Date, nullable=False, index=True)
    opponent        = Column(String, nullable=False)
    venue           = Column(String, nullable=False)   # 'home' or 'away'
    goals           = Column(Integer, nullable=False, default=0)
    shots           = Column(Integer, nullable=False, default=0)
    shots_on_target = Column(Integer, nullable=False, default=0)
    assists         = Column(Integer, nullable=False, default=0)
    key_passes      = Column(Integer, nullable=False, default=0)
    minutes_played  = Column(Integer, nullable=False, default=0)
    xG              = Column(Float, nullable=True)     # expected goals from Understat
    xA              = Column(Float, nullable=True)     # expected assists from Understat
    goals_conceded  = Column(Integer, nullable=True)   # GK only: goals conceded in that match
    season          = Column(String, nullable=False)   # e.g. '2025'

    __table_args__ = (
        UniqueConstraint('player_id', 'match_date', name='uq_soccer_player_game'),
    )

    player = relationship("SoccerPlayer", back_populates="games")

    def __repr__(self):
        return f"<SoccerPlayerGame(player_id={self.player_id}, date='{self.match_date}', goals={self.goals})>"


class MLBPlayer(Base):
    """MLB player information"""
    __tablename__ = 'mlb_players'

    id           = Column(Integer, primary_key=True)  # MLB Stats API player ID
    name         = Column(String, nullable=False)
    team         = Column(String, nullable=False, index=True)
    position     = Column(String, nullable=False)  # SP, RP, C, 1B, 2B, 3B, SS, LF, CF, RF, DH, OF
    is_pitcher   = Column(Boolean, nullable=False)
    last_updated = Column(Date, nullable=False)

    games = relationship("MLBPlayerGame", back_populates="player", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<MLBPlayer(name='{self.name}', team='{self.team}', pos='{self.position}')>"


class MLBPlayerGame(Base):
    """MLB player per-game statistics"""
    __tablename__ = 'mlb_player_games'

    id        = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('mlb_players.id'), nullable=False, index=True)
    game_date = Column(Date, nullable=False, index=True)
    opponent  = Column(String, nullable=False)
    is_home   = Column(Boolean, nullable=False)
    season    = Column(String, nullable=False)  # e.g. '2025'

    # Hitting stats (null for pitchers)
    hits         = Column(Integer, nullable=True)
    home_runs    = Column(Integer, nullable=True)
    rbi          = Column(Integer, nullable=True)
    runs         = Column(Integer, nullable=True)
    total_bases  = Column(Integer, nullable=True)
    at_bats      = Column(Integer, nullable=True)
    walks        = Column(Integer, nullable=True)

    # Pitching stats (null for batters)
    strikeouts      = Column(Integer, nullable=True)
    innings_pitched = Column(Float,   nullable=True)
    hits_allowed    = Column(Integer, nullable=True)
    earned_runs     = Column(Integer, nullable=True)
    outs_recorded   = Column(Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint('player_id', 'game_date', name='uq_mlb_player_game'),
    )

    player = relationship("MLBPlayer", back_populates="games")

    def __repr__(self):
        return f"<MLBPlayerGame(player_id={self.player_id}, date='{self.game_date}')>"


# Database connection and session management
def get_engine(db_path=None):
    """
    Create and return database engine
    Uses DATABASE_URL environment variable if available (for PostgreSQL in production)
    Falls back to SQLite for local development
    """
    import os

    if db_path is None:
        # Check for DATABASE_URL (Render PostgreSQL)
        db_path = os.environ.get('DATABASE_URL')

        if db_path:
            # Render uses postgres://, but SQLAlchemy needs postgresql://
            if db_path.startswith('postgres://'):
                db_path = db_path.replace('postgres://', 'postgresql://', 1)
            print(f"[INFO] Using PostgreSQL database")
        else:
            # Fallback to SQLite for local development
            db_path = 'sqlite:///statscout.db'
            print(f"[INFO] Using SQLite database: {db_path}")

    if db_path and db_path.startswith('postgresql'):
        # Use NullPool - Supabase transaction pooler handles pooling on their side
        # This avoids client-side pool exhaustion and circuit breaker issues
        return create_engine(
            db_path,
            echo=False,
            poolclass=NullPool,
            connect_args={"connect_timeout": 10, "sslmode": "require"},
        )

    return create_engine(db_path, echo=False)


def get_session(engine):
    """Create and return database session"""
    Session = sessionmaker(bind=engine)
    return Session()


def init_db(engine):
    """Initialize database - create all tables"""
    Base.metadata.create_all(engine)
    print(" Database tables created successfully")


def drop_all_tables(engine):
    """Drop all tables (use with caution!)"""
    Base.metadata.drop_all(engine)
    print("  All tables dropped")


# Example usage
if __name__ == "__main__":
    # Create database and tables
    engine = get_engine()
    init_db(engine)
    
    # Test: Create a sample player
    session = get_session(engine)
    
    test_player = Player(
        name="Test Player",
        team="TST",
        position="PG"
    )
    
    session.add(test_player)
    session.commit()
    
    # Query test
    players = session.query(Player).all()
    print(f"\nPlayers in database: {len(players)}")
    for player in players:
        print(f"  - {player}")
    
    session.close()
    print("\n Database test completed!")