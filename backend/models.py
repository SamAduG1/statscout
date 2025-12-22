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
    
    # Relationship to player
    player = relationship("Player", back_populates="games")
    
    def __repr__(self):
        return f"<Game(player_id={self.player_id}, date='{self.date}', opponent='{self.opponent}')>"


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