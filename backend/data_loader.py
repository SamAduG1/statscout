"""
StatScout Data Loader Module
Handles loading and processing player data from CSV files
"""

import pandas as pd
import os
from typing import Dict, List, Any


class DataLoader:
    """Load and process player statistics from CSV files"""
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize the data loader
        
        Args:
            data_dir: Directory containing CSV files
        """
        self.data_dir = data_dir
        self.player_stats_file = os.path.join(data_dir, "player_stats.csv")
        self.df = None
        
    def load_data(self) -> pd.DataFrame:
        """
        Load player stats from CSV file
        
        Returns:
            DataFrame with player statistics
        """
        if not os.path.exists(self.player_stats_file):
            raise FileNotFoundError(f"Player stats file not found: {self.player_stats_file}")
        
        self.df = pd.read_csv(self.player_stats_file)
        
        # Convert date to datetime
        self.df['date'] = pd.to_datetime(self.df['date'])
        
        # Sort by player and date (oldest first)
        self.df = self.df.sort_values(['player_name', 'date'])
        
        print(f"✅ Loaded {len(self.df)} game records for {self.df['player_name'].nunique()} players")
        
        return self.df
    
    def get_player_names(self) -> List[str]:
        """Get list of all unique player names"""
        if self.df is None:
            self.load_data()
        return sorted(self.df['player_name'].unique().tolist())
    
    def get_teams(self) -> List[str]:
        """Get list of all unique teams"""
        if self.df is None:
            self.load_data()
        return sorted(self.df['team'].unique().tolist())
    
    def get_player_info(self, player_name: str) -> Dict[str, Any]:
        """
        Get basic info about a player
        
        Args:
            player_name: Player's name
            
        Returns:
            Dictionary with player info
        """
        if self.df is None:
            self.load_data()
        
        player_data = self.df[self.df['player_name'] == player_name]
        
        if player_data.empty:
            return None
        
        return {
            "name": player_name,
            "team": player_data.iloc[0]['team'],
            "position": player_data.iloc[0]['position'],
            "games_played": len(player_data)
        }
    
    def get_player_stat_history(
        self, 
        player_name: str, 
        stat_column: str, 
        num_games: int = None
    ) -> List[float]:
        """
        Get a player's stat history
        
        Args:
            player_name: Player's name
            stat_column: Stat column name (e.g., 'points', 'rebounds')
            num_games: Number of recent games to return (None = all games)
            
        Returns:
            List of stat values (oldest to newest)
        """
        if self.df is None:
            self.load_data()
        
        player_data = self.df[self.df['player_name'] == player_name].copy()
        
        if player_data.empty:
            return []
        
        # Get the stat column
        if stat_column not in player_data.columns:
            return []
        
        stats = player_data[stat_column].tolist()
        
        # Return last N games if specified
        if num_games:
            stats = stats[-num_games:]
        
        return stats
    
    def get_combined_stat_history(
        self,
        player_name: str,
        stat_columns: List[str],
        num_games: int = None
    ) -> List[float]:
        """
        Get combined stat history (e.g., points + rebounds + assists)
        
        Args:
            player_name: Player's name
            stat_columns: List of stat columns to combine
            num_games: Number of recent games
            
        Returns:
            List of combined stat values
        """
        if self.df is None:
            self.load_data()
        
        player_data = self.df[self.df['player_name'] == player_name].copy()
        
        if player_data.empty:
            return []
        
        # Sum the specified columns
        combined = player_data[stat_columns].sum(axis=1).tolist()
        
        if num_games:
            combined = combined[-num_games:]
        
        return combined
    
    def get_all_available_stats(self, player_name: str) -> Dict[str, List[float]]:
        """
        Get all stat types available for a player
        
        Args:
            player_name: Player's name
            
        Returns:
            Dictionary mapping stat names to value lists
        """
        if self.df is None:
            self.load_data()
        
        player_data = self.df[self.df['player_name'] == player_name]
        
        if player_data.empty:
            return {}
        
        stat_columns = [
            'points', 'rebounds', 'assists', 'steals', 
            'blocks', 'three_pm'
        ]
        
        stats_dict = {}
        
        # Individual stats
        for col in stat_columns:
            if col in player_data.columns:
                stats_dict[col] = player_data[col].tolist()
        
        # Combined stats
        if 'points' in player_data.columns and 'rebounds' in player_data.columns and 'assists' in player_data.columns:
            stats_dict['PRA'] = (player_data['points'] + player_data['rebounds'] + player_data['assists']).tolist()
        
        if 'points' in player_data.columns and 'assists' in player_data.columns:
            stats_dict['PA'] = (player_data['points'] + player_data['assists']).tolist()
        
        if 'points' in player_data.columns and 'rebounds' in player_data.columns:
            stats_dict['PR'] = (player_data['points'] + player_data['rebounds']).tolist()
        
        if 'rebounds' in player_data.columns and 'assists' in player_data.columns:
            stats_dict['RA'] = (player_data['rebounds'] + player_data['assists']).tolist()
        
        return stats_dict


# Example usage
if __name__ == "__main__":
    loader = DataLoader()
    
    try:
        df = loader.load_data()
        
        print("\n=== Available Players ===")
        players = loader.get_player_names()
        for player in players:
            info = loader.get_player_info(player)
            print(f"{player} ({info['team']}, {info['position']}) - {info['games_played']} games")
        
        print("\n=== LeBron James Stats ===")
        lebron_points = loader.get_player_stat_history("LeBron James", "points", num_games=10)
        print(f"Last 10 games (Points): {lebron_points}")
        
        lebron_pra = loader.get_combined_stat_history("LeBron James", ["points", "rebounds", "assists"], num_games=10)
        print(f"Last 10 games (P+R+A): {lebron_pra}")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("Make sure to create the 'data' folder and 'player_stats.csv' file!")