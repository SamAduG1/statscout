"""
StatScout Database Models
Defines the database schema using SQLAlchemy
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Date, ForeignKey
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

    # Statistics
    points = Column(Integer, nullable=False)
    rebounds = Column(Integer, nullable=False)
    assists = Column(Integer, nullable=False)
    steals = Column(Integer, nullable=False)
    blocks = Column(Integer, nullable=False)
    three_pm = Column(Integer, nullable=False)
    minutes = Column(Float, nullable=True)  # Minutes played (can be null for older data)

    # Relationship to player
    player = relationship("Player", back_populates="games")

    def __repr__(self):
        return f"<Game(player_id={self.player_id}, date='{self.date}', opponent='{self.opponent}')>"


class TeamGame(Base):
    """Team game with quarter-by-quarter scoring"""
    __tablename__ = 'team_games'

    id = Column(Integer, primary_key=True)
    game_id = Column(String, unique=True, nullable=False, index=True)  # NBA API game ID
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


# Database connection and session management
def get_engine(db_path='sqlite:///statscout.db'):
    """Create and return database engine"""
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