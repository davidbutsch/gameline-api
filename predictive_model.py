"""Advanced NBA Player Predictor module."""
import numpy as np
import pandas as pd
from datetime import datetime 
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, GridSearchCV, KFold, RandomizedSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy.stats import norm
from scipy.sparse import csr_matrix
from nba_api.stats.endpoints import leaguedashteamstats
import bet_calculations as bc
import logging
from joblib import Parallel, delayed
import hashlib
# Add XGBoost and LightGBM imports
try:
    from xgboost import XGBRegressor
except ImportError:
    XGBRegressor = None
try:
    from lightgbm import LGBMRegressor
except ImportError:
    LGBMRegressor = None
from sklearn.linear_model import LinearRegression, Ridge

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# pylint: disable=too-many-instance-attributes, too-many-locals, too-many-branches, too-many-statements, broad-exception-caught, unused-argument, no-member

class AdvancedNBAPlayerPredictor:
    """Predicts NBA player performance using advanced features and models."""
    def __init__(self, n_components=0.95):
        """Initialize the predictor."""
        self.gb_regressors = {}
        self.rf_regressors = {}
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=n_components)
        self.stat_categories = ['PTS', 'REB', 'AST', 'BLK', 'STL']
        self.feature_cols = None
        self.ensemble_weights_rf = {}
        self.xgb_regressors = {}
        self.lgbm_regressors = {}
        self.ensemble_weights = {}  # Dict of stat: (rf, gb, xgb, lgbm) weights
        self.stat_mapping = {
            'POINTS': 'PTS',
            'REBOUNDS': 'REB',
            'ASSISTS': 'AST',
            'BLOCKS': 'BLK',
            'STEALS': 'STL',
            'POINTS+REBOUNDS+ASSISTS': ['PTS', 'REB', 'AST'],
            'REBOUNDS+ASSISTS': ['REB', 'AST'],
            'POINTS+REBOUNDS': ['PTS', 'REB'],
            'POINTS+ASSISTS': ['PTS', 'AST'],
            'BLOCKS+STEALS': ['BLK', 'STL']
        }
        self.opponent_stats_cache = {}
        self.model_cache = {}
        self.x_train = None  # Renamed from X_train for snake_case
        self.stacking_meta_models = {}  # stat: LinearRegression

    def compute_data_hash(self, all_games):
        """Compute SHA-256 hash of game log data."""
        data_str = all_games.to_json()
        return hashlib.sha256(data_str.encode()).hexdigest()

    def prepare_data(self, player_id, seasons=None, season_type='Regular Season'):
        """Prepare player game log data for modeling."""
        if seasons is None:
            seasons = ['2024-25', '2025-26']
        game_logs = []
        for season in seasons:
            for st in ['Regular Season', 'Playoffs']:
                try:
                    gamelog = bc.playergamelog.PlayerGameLog(
                        player_id=player_id,
                        season=season,
                        season_type_all_star=st,
                        timeout=60
                    )
                    df = gamelog.get_data_frames()[0]
                    df['SEASON'] = season
                    df['SEASON_TYPE'] = st
                    game_logs.append(df)
                except Exception as e:
                    logger.warning("Error fetching game log for season %s, type %s: %s", season, st, e)
                    continue
        if not game_logs:
            logger.warning("No game logs found for player_id %s", player_id)
            columns = ['GAME_DATE', 'MATCHUP', 'SEASON', 'SEASON_TYPE', 'MIN'] + self.stat_categories
            return pd.DataFrame(columns=pd.Index(columns))
        all_games = pd.concat(game_logs).reset_index(drop=True)
        all_games['GAME_DATE'] = pd.to_datetime(all_games['GAME_DATE'], format='mixed', errors='coerce').dt.date
        all_games = all_games.sort_values('GAME_DATE', ascending=True)
        current_date = datetime.now().date()
        all_games['days_ago'] = (current_date - all_games['GAME_DATE']).apply(lambda x: x.days)
        all_games['OPPONENT'] = all_games['MATCHUP'].apply(
            lambda x: x.split(' vs. ')[1] if ' vs. ' in x else x.split(' @ ')[1]
        )
        all_games['HOME_AWAY'] = all_games['MATCHUP'].apply(lambda x: 1 if 'vs.' in x else 0)
        all_games = all_games[(all_games['PTS'] <= 50.0) & (all_games['MIN'] >= 10.0)]
        for stat in self.stat_categories + ['MIN']:
            all_games[stat] = all_games.get(stat, 0.0)
            
        # Calculate minutes-related features
        if 'MIN' in all_games.columns and len(all_games) > 0:
            # Per-minute efficiency stats
            for stat in self.stat_categories:
                all_games[f'{stat}_per_min'] = all_games[stat] / (all_games['MIN'] + 1e-6)  # Avoid division by zero
            
            # Minutes trend (recent vs historical)
            all_games['min_trend'] = all_games['MIN'].rolling(window=5, min_periods=1).mean() - all_games['MIN'].expanding().mean()
            
            # Minutes consistency (lower std = more consistent playing time)
            all_games['min_consistency'] = 1.0 / (all_games['MIN'].rolling(window=10, min_periods=3).std() + 1.0)
            
        return all_games

    def fetch_all_team_stats(self, seasons, season_type):
        """Batch fetch team stats for all teams."""
        for season in seasons:
            if (season, season_type) not in self.opponent_stats_cache:
                try:
                    team_stats = leaguedashteamstats.LeagueDashTeamStats(
                        season=season,
                        season_type_all_star=season_type,
                        measure_type_detailed_defense='Defense',
                        last_n_games='82',
                        timeout=60
                    ).get_data_frames()[0]
                    for _, row in team_stats.iterrows():
                        team_id = row['TEAM_ID']
                        games_played = row.get('GP', 82)
                        stats = {
                            f'opp_{stat}': row.get(api_stat, default_val) / games_played
                            for stat, api_stat, default_val in [
                                ('PTS', 'OPP_PTS', 110.0), ('REB', 'DREB', 43.0), ('AST', 'OPP_AST', 25.0),
                                ('BLK', 'BLK', 5.0), ('STL', 'STL', 7.0)
                            ]
                        }
                        stats.update({
                            'PACE': row.get('PACE', 100.0),
                            'DEF_RATING': row.get('DEF_RATING', 110.0)
                        })
                        self.opponent_stats_cache[(team_id, season)] = pd.Series(stats).astype(float)
                    logger.debug("Fetched team stats for season %s", season)
                except Exception as e:
                    logger.warning("Error fetching team stats for season %s: %s", season, e)

    def compute_h2h_features(self, games, stat):
        """Compute H2H averages using prefix sums."""
        if games.empty:
            return np.zeros(len(games))
        cumsum = games[stat].cumsum().shift(1).fillna(0)
        counts = np.arange(len(games)).astype(float)
        counts[0] = 1
        return cumsum / counts

    def create_features(self, all_games, opponent_abbr, season_type, category_type='offensive'):
        """Create features for modeling."""
        if len(all_games) < 5:
            raise ValueError("Insufficient game data (less than 5 games) to create reliable features")

        lambda_ = -np.log(0.5) / 30
        all_games['recency_weight'] = np.exp(-lambda_ * all_games['days_ago'])

        seasons = all_games['SEASON'].unique()
        self.fetch_all_team_stats(seasons, 'Regular Season')
        league_avgs = {season: bc.get_league_defensive_averages(season, 'Regular Season') for season in seasons}
        for season in league_avgs:
            league_avgs[season] = pd.Series({
                f'opp_{k}': v for k, v in league_avgs[season].items() if k in self.stat_categories
            }).combine_first(pd.Series({
                'PACE': 100.0,
                'DEF_RATING': 110.0
            })).to_dict()

        opponent_stats = {}
        for opp in all_games['OPPONENT'].unique():
            try:
                team_id = bc.get_team_id(opp)
                for season in seasons:
                    cached_stats = self.opponent_stats_cache.get((team_id, season))
                    if cached_stats is not None:
                        opponent_stats[(opp, season)] = cached_stats
                    else:
                        team_stats = bc.get_team_recent_stats(
                            team_id, season, 'Regular Season', 'Defense', num_games=82
                        )
                        opponent_stats[(opp, season)] = pd.Series({
                            f'opp_{stat}': team_stats.get(stat, league_avgs[season][f'opp_{stat}'])
                            for stat in self.stat_categories
                        }).combine_first(pd.Series({
                            'PACE': team_stats.get('PACE', 100.0),
                            'DEF_RATING': team_stats.get('DEF_RATING', 110.0)
                        }))
                        self.opponent_stats_cache[(team_id, season)] = opponent_stats[(opp, season)]
            except Exception as e:
                logger.warning("Error fetching stats for %s, season %s: %s", opp, season, e)
                for season in seasons:
                    opponent_stats[(opp, season)] = league_avgs[season]

        opp_data = pd.DataFrame([
            {
                'OPPONENT': opp,
                'SEASON': season,
                **opponent_stats[(opp, season)].to_dict()
            }
            for opp, season in [(row['OPPONENT'], row['SEASON']) for _, row in all_games.iterrows()]
        ], index=all_games.index)
        logger.debug("opp_data columns: %s", opp_data.columns)
        all_games = all_games.join(opp_data.drop(columns=['OPPONENT', 'SEASON']))
        logger.debug("all_games columns after join: %s", all_games.columns)

        # Get league averages for normalization using the new function
        league_team_stats = bc.get_league_team_averages('2025-26', 'Regular Season')
        
        # Create normalized opponent strength features
        for stat in self.stat_categories:
            # Normalize to league average (ratio-based)
            league_avg = league_team_stats[stat]
            all_games[f'opp_strength_{stat}'] = all_games[f'opp_{stat}'] / league_avg
            
            # Create standardized features (standard deviations from mean)
            league_std = league_team_stats[f'{stat}_std']
            all_games[f'opp_normalized_{stat}'] = (all_games[f'opp_{stat}'] - league_avg) / league_std
        
        all_games['opp_pace'] = all_games.get('PACE', 100.0)
        all_games['opp_rating'] = all_games.get('DEF_RATING', 110.0)

        def compute_h2h_opp(opp):
            mask = all_games['OPPONENT'] == opp
            games = all_games[mask].sort_values('GAME_DATE')
            return {stat: (games.index, self.compute_h2h_features(games, stat)) for stat in self.stat_categories}

        h2h_results = Parallel(n_jobs=-1)(delayed(compute_h2h_opp)(opp) for opp in all_games['OPPONENT'].unique())
        h2h_avgs = {stat: pd.Series(0.0, index=all_games.index) for stat in self.stat_categories}
        for result in h2h_results:
            if result is not None:
                for stat, (idx, values) in result.items():
                    h2h_avgs[stat].loc[idx] = values
        for stat in self.stat_categories:
            all_games[f'h2h_avg_{stat}'] = h2h_avgs[stat]
        all_games['has_h2h'] = (all_games[[f'h2h_avg_{stat}' for stat in self.stat_categories]].sum(axis=1) > 0).astype(int)

        player_id = all_games['Player_ID'].iloc[0]
        advanced_stats = bc.get_player_advanced_stats(player_id, '2025-26', season_type)
        usg_pct = advanced_stats.get('USG_PCT', 0.2)
        ts_pct = advanced_stats.get('TS_PCT', 0.5)
        fatigue_metrics = bc.get_player_fatigue_metrics(player_id, '2025-26', season_type, num_games=10)
        avg_min = fatigue_metrics.get('AVG_MIN', 30.0)
        avg_rest_days = fatigue_metrics.get('AVG_REST_DAYS', 2.0)
        injury_risk = 1 if avg_min > 38.0 or avg_rest_days < 1.0 else 0
        
        # Get league average minutes for normalization
        league_min_stats = bc.get_league_average_minutes('2025-26', season_type)
        if isinstance(league_min_stats, dict):
            league_avg_mpg = league_min_stats.get('avg_mpg', 24.0)
            league_std_mpg = league_min_stats.get('std_mpg', 8.0)
        else:
            # Handle case where function returns just a float (backward compatibility)
            league_avg_mpg = float(league_min_stats) if league_min_stats else 24.0
            league_std_mpg = 8.0
        
        # Calculate minutes-related features
        min_vs_league = (avg_min - league_avg_mpg) / league_std_mpg  # Standard deviations from league average
        
        # Recent minutes trend and efficiency
        if len(all_games) >= 5:
            recent_min_avg = all_games['MIN'].head(5).mean()
            season_min_avg = all_games['MIN'].mean()
            min_recent_trend = (recent_min_avg - season_min_avg) / (season_min_avg + 1e-6)
            
            # Calculate efficiency metrics (stats per 36 minutes)
            min_efficiency = {}
            for stat in self.stat_categories:
                if f'{stat}_per_min' in all_games.columns:
                    min_efficiency[f'{stat}_per_36'] = all_games[f'{stat}_per_min'].mean() * 36
                else:
                    min_efficiency[f'{stat}_per_36'] = 0.0
        else:
            min_recent_trend = 0.0
            min_efficiency = {f'{stat}_per_36': 0.0 for stat in self.stat_categories}

        recent_games = all_games.tail(10)
        ema_trends = {}
        for stat in self.stat_categories:
            if not recent_games.empty:
                ema = recent_games[stat].ewm(span=5, adjust=False).mean().iloc[-1]
                ema_trends[stat] = ema - recent_games[stat].mean() if len(recent_games) > 1 else 0.0
            else:
                ema_trends[stat] = 0.0

        all_games['same_opponent'] = (all_games['OPPONENT'] == opponent_abbr).astype(int)
        all_games['is_playoff'] = (all_games['SEASON_TYPE'] == 'Playoffs').astype(int)
        for stat in self.stat_categories:
            all_games[f'weighted_{stat}'] = all_games['recency_weight'] * all_games[stat]
            all_games[f'opp_interaction_{stat}'] = all_games['same_opponent'] * all_games[f'opp_normalized_{stat}']
            all_games[f'recent_form_{stat}'] = all_games[stat].rolling(window=5, min_periods=1).mean().fillna(0)
            all_games[f'opp_recent_{stat}'] = all_games[f'opp_strength_{stat}'] * league_team_stats[stat]
            all_games[f'ema_trend_{stat}'] = ema_trends[stat]
        
        # Add minutes-related features
        all_games['usg_pct'] = usg_pct
        all_games['ts_pct'] = ts_pct
        all_games['avg_min'] = avg_min
        all_games['avg_rest_days'] = avg_rest_days
        all_games['injury_risk'] = injury_risk
        all_games['min_vs_league'] = min_vs_league
        all_games['min_recent_trend'] = min_recent_trend
        
        # Add per-36 minute efficiency features
        for stat in self.stat_categories:
            all_games[f'{stat}_per_36'] = min_efficiency[f'{stat}_per_36']
        
        # Add minutes interaction with usage rate (higher usage + more minutes = more opportunities)
        all_games['min_usage_interaction'] = all_games['MIN'] * usg_pct
        
        # Add minutes-based fatigue indicator (games with high minutes followed by low performance)
        if len(all_games) > 1:
            all_games['high_min_fatigue'] = (
                (all_games['MIN'].shift(1) > all_games['MIN'].quantile(0.8)) & 
                (all_games['PTS'] < all_games['PTS'].quantile(0.4))
            ).astype(int)
        else:
            all_games['high_min_fatigue'] = 0

        self.feature_cols = [
            'recency_weight', 'same_opponent', 'is_playoff', 'opp_pace', 'opp_rating', 'usg_pct', 'ts_pct',
            'avg_min', 'avg_rest_days', 'injury_risk', 'HOME_AWAY', 'has_h2h',
            'MIN', 'min_vs_league', 'min_recent_trend', 'min_usage_interaction', 'high_min_fatigue'
        ] + [f'weighted_{stat}' for stat in self.stat_categories] + \
          [f'opp_strength_{stat}' for stat in self.stat_categories] + \
          [f'opp_normalized_{stat}' for stat in self.stat_categories] + \
          [f'opp_interaction_{stat}' for stat in self.stat_categories] + \
          [f'recent_form_{stat}' for stat in self.stat_categories] + \
          [f'h2h_avg_{stat}' for stat in self.stat_categories] + \
          [f'opp_recent_{stat}' for stat in self.stat_categories] + \
          [f'ema_trend_{stat}' for stat in self.stat_categories] + \
          [f'{stat}_per_min' for stat in self.stat_categories] + \
          [f'{stat}_per_36' for stat in self.stat_categories] + \
          ['min_trend', 'min_consistency']

        X = all_games[self.feature_cols].fillna(0)
        variances = X.var()
        self.feature_cols = variances[variances > 0.01].index.tolist()
        X = X[self.feature_cols]
        X_sparse = csr_matrix(X.values)
        y = all_games[self.stat_categories].fillna(0).values
        return {
            'X_sparse': X_sparse,
            'y': y,
            'opponent_stats': opponent_stats,
            'usg_pct': usg_pct,
            'avg_rest_days': avg_rest_days,
            'avg_min': avg_min,
            'ts_pct': ts_pct,
            'min_vs_league': min_vs_league,
            'min_recent_trend': min_recent_trend,
            'min_efficiency': min_efficiency
        }

    def train_stat_model(self, stat_idx, stat, x_scaled, x_pca, y, data_hash):
        y_stat = y[:, stat_idx]
        n_samples = x_pca.shape[0]
        kf = KFold(n_splits=5, shuffle=True, random_state=42)
        # Prepare OOF predictions for stacking
        oof_preds = []
        for _ in range(4):
            oof_preds.append(np.zeros(n_samples))
        # Hyperparameter grids
        rf_param_dist = {
            'n_estimators': [50, 100, 200],
            'max_depth': [5, 10, 15, None],
            'min_samples_split': [2, 5, 10]
        }
        gb_param_dist = {
            'n_estimators': [50, 100, 200],
            'max_depth': [3, 5, 7],
            'learning_rate': [0.01, 0.05, 0.1, 0.2]
        }
        xgb_param_dist = {
            'n_estimators': [50, 100, 200],
            'max_depth': [3, 5, 7],
            'learning_rate': [0.01, 0.05, 0.1, 0.2]
        }
        lgbm_param_dist = {
            'n_estimators': [50, 100, 200],
            'max_depth': [3, 5, 7, -1],
            'learning_rate': [0.01, 0.05, 0.1, 0.2]
        }
        # Fit base models with OOF predictions
        for train_idx, val_idx in kf.split(x_pca):
            X_train, X_val = x_pca[train_idx], x_pca[val_idx]
            y_train, y_val = y_stat[train_idx], y_stat[val_idx]
            # RF
            rf = RandomizedSearchCV(RandomForestRegressor(random_state=42), rf_param_dist, n_iter=5, cv=2, n_jobs=-1, scoring='neg_mean_squared_error', random_state=42)
            rf.fit(X_train, y_train)
            oof_preds[0][val_idx] = rf.predict(X_val)
            # GB
            gb = RandomizedSearchCV(GradientBoostingRegressor(random_state=42), gb_param_dist, n_iter=5, cv=2, n_jobs=-1, scoring='neg_mean_squared_error', random_state=42)
            gb.fit(X_train, y_train)
            oof_preds[1][val_idx] = gb.predict(X_val)
            # XGB
            if XGBRegressor is not None:
                xgb = XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42, verbosity=0)
                xgb.fit(X_train, y_train)
                oof_preds[2][val_idx] = xgb.predict(X_val)
            else:
                xgb = None
            # LGBM
            if LGBMRegressor is not None:
                lgbm = LGBMRegressor(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42, verbose=-1)
                lgbm.fit(X_train, y_train)
                oof_preds[3][val_idx] = lgbm.predict(X_val)
            else:
                lgbm = None
        # Train meta-model on OOF predictions
        X_stack = np.vstack(oof_preds).T  # shape: (n_samples, n_models)
        meta_model = Ridge(alpha=1.0)  # Slight regularization for stability
        meta_model.fit(X_stack, y_stat)
        self.stacking_meta_models[stat] = meta_model
        # Fit final base models on all data for prediction use
        rf_final = RandomizedSearchCV(RandomForestRegressor(random_state=42), rf_param_dist, n_iter=5, cv=2, n_jobs=-1, scoring='neg_mean_squared_error', random_state=42)
        rf_final.fit(x_pca, y_stat)
        gb_final = RandomizedSearchCV(GradientBoostingRegressor(random_state=42), gb_param_dist, n_iter=5, cv=2, n_jobs=-1, scoring='neg_mean_squared_error', random_state=42)
        gb_final.fit(x_pca, y_stat)
        if XGBRegressor is not None:
            xgb_final = XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42, verbosity=0)
            xgb_final.fit(x_pca, y_stat)
        else:
            xgb_final = None
        if LGBMRegressor is not None:
            lgbm_final = LGBMRegressor(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42, verbose=-1)
            lgbm_final.fit(x_pca, y_stat)
        else:
            lgbm_final = None
        self.rf_regressors[stat] = rf_final.best_estimator_
        self.gb_regressors[stat] = gb_final.best_estimator_
        self.xgb_regressors[stat] = xgb_final
        self.lgbm_regressors[stat] = lgbm_final
        return stat, rf_final.best_estimator_, gb_final.best_estimator_, xgb_final, lgbm_final, meta_model

    def train_model(self, x, y, data_hash):
        """Train all stat models."""
        if x is not None and hasattr(x, 'toarray'):
            x_scaled = self.scaler.fit_transform(x.toarray())
        elif isinstance(x, (list, np.ndarray)):
            x_scaled = self.scaler.fit_transform(np.array(x))
        elif isinstance(x, csr_matrix):
            x_scaled = self.scaler.fit_transform(x.toarray())
        else:
            x_scaled = self.scaler.fit_transform(x)
        x_pca = self.pca.fit_transform(x_scaled)
        try:
            results = Parallel(n_jobs=-1)(
                delayed(self.train_stat_model)(stat_idx, stat, x_scaled, x_pca, y, data_hash)
                for stat_idx, stat in enumerate(self.stat_categories)
            )
            for stat, rf_model, gb_model, xgb_model, lgbm_model, meta_model in results:
                self.rf_regressors[stat] = rf_model
                self.gb_regressors[stat] = gb_model
                self.xgb_regressors[stat] = xgb_model
                self.lgbm_regressors[stat] = lgbm_model
                self.stacking_meta_models[stat] = meta_model
        except Exception as e:
            logger.error("Error in parallel training: %s", e)

    def calculate_opponent_impact(self, category, opp_avgs):
        """
        Calculate weighted opponent impact based on normalized team stats.
        
        Uses the weighted adjustment system based on opponent team averages
        relative to league means and standard deviations.
        """
        # Get league averages and standard deviations for normalization
        league_stats = bc.get_league_team_averages('2025-26', 'Regular Season')
        
        # Extract league averages and standard deviations
        league_means = {
            'PTS': league_stats['PTS'],
            'REB': league_stats['REB'],
            'AST': league_stats['AST'],
            'BLK': league_stats['BLK'],
            'STL': league_stats['STL']
        }
        
        league_stds = {
            'PTS': league_stats['PTS_std'],
            'REB': league_stats['REB_std'],
            'AST': league_stats['AST_std'],
            'BLK': league_stats['BLK_std'],
            'STL': league_stats['STL_std']
        }
        
        # Normalize opponent stats to standard deviations from league mean
        normalized_opp_stats = {}
        for stat in ['PTS', 'REB', 'AST', 'BLK', 'STL']:
            opp_value = opp_avgs.get(stat, league_means[stat])
            std_devs_from_mean = (opp_value - league_means[stat]) / league_stds[stat]
            normalized_opp_stats[stat] = std_devs_from_mean
            
        # Define weighted impact matrix based on specifications
        # Rows: Player stats, Columns: Opponent stats (PPG, RPG, APG, SPG, BPG)
        impact_weights = {
            'Points': {'PTS': +0.40, 'REB': -0.25, 'AST': +0.08, 'STL': -0.12, 'BLK': -0.15},
            'Rebounds': {'PTS': +0.20, 'REB': -0.60, 'AST': +0.00, 'STL': -0.10, 'BLK': -0.05},
            'Assists': {'PTS': +0.25, 'REB': -0.10, 'AST': +0.35, 'STL': -0.10, 'BLK': -0.05},
            'Steals': {'PTS': +0.15, 'REB': -0.05, 'AST': +0.05, 'STL': +0.30, 'BLK': -0.05},
            'Blocks': {'PTS': +0.10, 'REB': -0.05, 'AST': +0.00, 'STL': -0.05, 'BLK': +0.35}
        }
        
        # Map category to player stat(s)
        category_mapping = {
            'POINTS': ['Points'],
            'REBOUNDS': ['Rebounds'], 
            'ASSISTS': ['Assists'],
            'BLOCKS': ['Blocks'],
            'STEALS': ['Steals'],
            'POINTS+REBOUNDS+ASSISTS': ['Points', 'Rebounds', 'Assists'],
            'REBOUNDS+ASSISTS': ['Rebounds', 'Assists'],
            'POINTS+REBOUNDS': ['Points', 'Rebounds'],
            'POINTS+ASSISTS': ['Points', 'Assists'],
            'BLOCKS+STEALS': ['Blocks', 'Steals']
        }
        
        # Get the relevant player stats for this category
        player_stats = category_mapping.get(category.upper(), ['Points'])
        
        # Calculate weighted impact for each player stat in the category
        total_impact = 0.0
        num_stats = len(player_stats)
        
        for player_stat in player_stats:
            stat_impact = 0.0
            
            # Apply weights for each opponent stat
            for opp_stat, weight in impact_weights[player_stat].items():
                std_devs = normalized_opp_stats[opp_stat]
                weighted_impact = weight * std_devs
                stat_impact += weighted_impact
                
                logger.debug(f"{player_stat} vs Opp {opp_stat}: "
                           f"normalized={std_devs:.3f}, weight={weight:+.2f}, "
                           f"impact={weighted_impact:+.4f}")
            
            total_impact += stat_impact
            logger.debug(f"{player_stat} total impact: {stat_impact:+.4f}")
        
        # Average the impact across multiple stats in combined categories
        if num_stats > 1:
            total_impact = total_impact / num_stats
        
        # Cap the impact between -0.5 and +0.5 (50% max adjustment)
        total_impact = max(-0.5, min(0.5, total_impact))
        
        logger.info(f"Opponent impact calculation for {category}:")
        logger.info(f"  Normalized opponent stats (std devs from league mean):")
        for stat, norm_val in normalized_opp_stats.items():
            logger.info(f"    {stat}: {norm_val:+.3f} ({opp_avgs.get(stat, 0):.1f} vs {league_means[stat]:.1f})")
        logger.info(f"  Final weighted impact: {total_impact:+.4f}")
        
        return total_impact

    def predict_performance(self, features, category, season_type, season_avgs, recent_avgs, h2h_avgs, opp_avgs, usg_pct, avg_rest_days):
        """Predict player performance."""
        features_scaled = self.scaler.transform(features.toarray())
        features_pca = self.pca.transform(features_scaled)
        stats_needed = self.stat_mapping.get(category.upper(), [category.upper()])
        if isinstance(stats_needed, str):
            stats_needed = [stats_needed]
        model_pred = 0.0
        pred_stats = {}
        base_model_outputs = {}
        for stat in self.stat_categories:
            preds = []
            base_preds = []
            # RF
            rf_model = self.rf_regressors.get(stat)
            if rf_model is not None:
                rf_pred = rf_model.predict(features_pca)[0]
                preds.append(rf_pred)
                base_preds.append(rf_pred)
            # GB
            gb_model = self.gb_regressors.get(stat)
            if gb_model is not None:
                gb_pred = gb_model.predict(features_pca)[0]
                preds.append(gb_pred)
                base_preds.append(gb_pred)
            # XGB
            xgb_model = self.xgb_regressors.get(stat)
            if xgb_model is not None:
                xgb_pred = xgb_model.predict(features_pca)[0]
                preds.append(xgb_pred)
                base_preds.append(xgb_pred)
            # LGBM
            lgbm_model = self.lgbm_regressors.get(stat)
            if lgbm_model is not None:
                lgbm_pred = lgbm_model.predict(features_pca)[0]
                preds.append(lgbm_pred)
                base_preds.append(lgbm_pred)
            # Stacking meta-model
            if stat in self.stacking_meta_models and len(base_preds) > 1:
                meta_model = self.stacking_meta_models[stat]
                X_stack = np.array(base_preds).reshape(1, -1)
                ensemble_pred = meta_model.predict(X_stack)[0]
            elif preds:
                weights = np.array([1] * len(preds)) / len(preds)
                ensemble_pred = np.average(preds, weights=weights)
            else:
                ensemble_pred = 0.0
            pred_stats[stat] = ensemble_pred
            base_model_outputs[stat] = {
                'rf': preds[0] if len(preds) > 0 else None,
                'gb': preds[1] if len(preds) > 1 else None,
                'xgb': preds[2] if len(preds) > 2 else None,
                'lgbm': preds[3] if len(preds) > 3 else None,
                'stacked': ensemble_pred
            }
            if stat in stats_needed:
                model_pred += ensemble_pred
        # Calculate averages for weighted sum
        season_avg = sum(season_avgs.get(stat, 0.0) for stat in stats_needed)
        recent_avg = sum(recent_avgs.get(stat, 0.0) for stat in stats_needed)
        season_long_avg = sum(season_avgs.get(stat, 0.0) for stat in stats_needed)  # Use season_averages as season_long_averages
        h2h_avg = sum(h2h_avgs.get(stat, 0.0) for stat in stats_needed)
        opp_stats = ['PTS', 'REB', 'AST', 'BLK', 'STL']
        opp_avg = np.mean([opp_avgs.get(stat, 0.0) for stat in opp_stats]) if opp_avgs else 0.0
        # Calculate opponent impact based on category type
        opponent_impact = self.calculate_opponent_impact(category, opp_avgs)
        
        # New weights: recent_avg=0.3, season_avg=0.3, season_long_avg=0.2, h2h_avg=0.1, opp_avg=0.1
        weighted_avg = 0.3 * recent_avg + 0.3 * season_avg + 0.2 * season_long_avg + 0.1 * h2h_avg + 0.1 * opp_avg
        
        # Apply opponent impact to weighted average
        weighted_avg_with_impact = weighted_avg * (1 + opponent_impact)
        
        # Blend weighted average with model output
        final_pred = 0.5 * weighted_avg_with_impact + 0.5 * model_pred
        # Diagnostics
        logger.info(f"Prediction diagnostics for {category}:\n"
                    f"  season_avg={season_avg}, recent_avg={recent_avg}, season_long_avg={season_long_avg}, h2h_avg={h2h_avg}, opp_avg={opp_avg}\n"
                    f"  opponent_impact={opponent_impact:.3f}, weighted_avg={weighted_avg:.2f}, weighted_avg_with_impact={weighted_avg_with_impact:.2f}\n"
                    f"  base_model_outputs={base_model_outputs}\n"
                    f"  model_pred={model_pred:.2f}, final_pred={final_pred:.2f}")

        residuals = []
        if hasattr(self.x_train, 'toarray'):
            X_train_scaled = self.scaler.transform(self.x_train.toarray())
        elif isinstance(self.x_train, (list, np.ndarray)):
            X_train_scaled = self.scaler.transform(np.array(self.x_train))
        elif isinstance(self.x_train, csr_matrix):
            X_train_scaled = self.scaler.transform(self.x_train.toarray())
        else:
            X_train_scaled = self.scaler.transform(self.x_train)
        X_train_pca = self.pca.transform(X_train_scaled)
        for stat in stats_needed:
            stat_idx = self.stat_categories.index(stat)
            preds = []
            model_weights = []
            rf_model = self.rf_regressors.get(stat)
            if rf_model is not None:
                rf_train_preds = rf_model.predict(X_train_pca)
                preds.append(rf_train_preds)
                model_weights.append(1)
            gb_model = self.gb_regressors.get(stat)
            if gb_model is not None:
                gb_train_preds = gb_model.predict(X_train_pca)
                preds.append(gb_train_preds)
                model_weights.append(1)
            xgb_model = self.xgb_regressors.get(stat)
            if xgb_model is not None:
                xgb_train_preds = xgb_model.predict(X_train_pca)
                preds.append(xgb_train_preds)
                model_weights.append(1)
            lgbm_model = self.lgbm_regressors.get(stat)
            if lgbm_model is not None:
                lgbm_train_preds = lgbm_model.predict(X_train_pca)
                preds.append(lgbm_train_preds)
                model_weights.append(1)
            if preds:
                weights = np.array(model_weights) / np.sum(model_weights)
                ensemble_train_preds = np.average(preds, axis=0, weights=weights)
            else:
                if isinstance(self.y_train, np.ndarray) and len(self.y_train.shape) > 1:
                    ensemble_train_preds = np.zeros_like(self.y_train[:, stat_idx])
                else:
                    ensemble_train_preds = np.zeros(len(self.y_train))
            if hasattr(self.y_train, '__getitem__') and hasattr(self.y_train, 'shape'):
                try:
                    if len(self.y_train.shape) > 1:
                        residuals.append(ensemble_train_preds - self.y_train[:, stat_idx])
                    else:
                        residuals.append(ensemble_train_preds - self.y_train[stat_idx])
                except (IndexError, TypeError):
                    residuals.append(ensemble_train_preds - self.y_train[stat_idx])
            else:
                residuals.append(ensemble_train_preds - self.y_train[stat_idx])
        residuals = np.sum(residuals, axis=0)
        sigma = np.std(residuals) if np.std(residuals) > 0 else 1.0
        sigma = max(float(sigma), 1.0 if len(stats_needed) == 1 else 1.5)
        ci_lower, ci_upper = norm.interval(0.95, loc=final_pred, scale=sigma)
        return final_pred, sigma, (ci_lower, ci_upper)

    def predict_over_under(self, player_id, category, opponent_abbr, season_type, betting_line, category_type='offensive', seasons=None):
        """Predict over/under for a player and category."""
        if seasons is None:
            seasons = ['2024-25', '2025-26']
        all_games = self.prepare_data(player_id, seasons, season_type)
        if all_games.empty:
            raise ValueError("No game data available to make prediction")
        all_games['Player_ID'] = player_id
        data_hash = self.compute_data_hash(all_games)

        features = self.create_features(all_games, opponent_abbr, season_type, category_type)
        x, y, opponent_strengths, usg_pct, avg_rest_days, avg_min, ts_pct, min_vs_league, min_recent_trend, min_efficiency = (
            features['X_sparse'], features['y'], features['opponent_stats'], features['usg_pct'],
            features['avg_rest_days'], features['avg_min'], features['ts_pct'],
            features['min_vs_league'], features['min_recent_trend'], features['min_efficiency']
        )
        self.x_train, _, self.y_train, _ = train_test_split(x, y, test_size=0.2, random_state=42)
        self.train_model(self.x_train, self.y_train, data_hash)

        averages = bc.get_player_season_recent_averages(player_id, '2025-26', season_type)
        season_avgs = averages['season_averages']
        recent_avgs = averages['recent_averages']
        season_long_avgs = averages['season_long_averages']  # New key for season-long averages
        h2h_stats, h2h_games = bc.get_head_to_head_stats(player_id, opponent_abbr, seasons)
        if isinstance(h2h_stats, pd.DataFrame) and not h2h_stats.empty:
            h2h_avgs = h2h_stats[self.stat_categories].mean()
            if hasattr(h2h_avgs, 'fillna') and callable(getattr(h2h_avgs, 'fillna', None)):
                h2h_avgs = h2h_avgs.fillna(0)
            else:
                h2h_avgs = pd.Series({stat: 0.0 for stat in self.stat_categories})
        else:
            h2h_avgs = pd.Series({stat: 0.0 for stat in self.stat_categories})

        # Get opponent team averages for current season
        opp_avgs = bc.get_opponent_team_averages(opponent_abbr, '2025-26', season_type)
        if opp_avgs is None:
            logger.warning(f"Could not fetch opponent averages for {opponent_abbr}, using defaults")
            opp_avgs = {
                'PTS': 110.0,
                'REB': 43.0,
                'AST': 25.0,
                'BLK': 5.0,
                'STL': 7.0,
                'PACE': 100.0,
                'OFF_RATING': 110.0,
                'DEF_RATING': 110.0,
                'GP': 82
            }

        recent_means = {f'recent_form_{stat}': y[:, self.stat_categories.index(stat)].ravel()[-5:].mean() for stat in self.stat_categories}
        
        # Calculate recent means for minutes-related features from game data
        recent_games_data = all_games.tail(5)
        if not recent_games_data.empty:
            recent_means['MIN'] = recent_games_data['MIN'].mean()
            for stat in self.stat_categories:
                if f'{stat}_per_min' in recent_games_data.columns:
                    recent_means[f'{stat}_per_min'] = recent_games_data[f'{stat}_per_min'].mean()
                else:
                    recent_means[f'{stat}_per_min'] = 0.0
        else:
            recent_means['MIN'] = avg_min
            for stat in self.stat_categories:
                recent_means[f'{stat}_per_min'] = 0.0
        ema_trends = {}
        recent_games = all_games.tail(10)
        for stat in self.stat_categories:
            if not recent_games.empty and hasattr(recent_games[stat], 'ewm'):
                try:
                    if hasattr(recent_games[stat], 'ewm') and callable(getattr(recent_games[stat], 'ewm', None)):
                        ema = recent_games[stat].ewm(span=5, adjust=False).mean().iloc[-1]
                        ema_trends[stat] = ema - recent_games[stat].mean() if len(recent_games) > 1 else 0.0
                    else:
                        ema_trends[stat] = 0.0
                except (AttributeError, TypeError, IndexError):
                    ema_trends[stat] = 0.0
            else:
                ema_trends[stat] = 0.0

        logger.debug("opponent_strengths keys: %s", list(opponent_strengths.keys()))
        
        stat_type = 'Defensive' if category_type == 'offensive' else 'Offensive'
        if stat_type == 'Defensive':
            opp_avgs['RATING'] = opp_avgs['DEF_RATING']
        else:
            opp_avgs['RATING'] = opp_avgs['OFF_RATING']
            
        # Get league stats for normalization in upcoming features
        league_team_stats = bc.get_league_team_averages('2025-26', season_type)
        
        # Calculate normalized opponent features for upcoming game
        opp_normalized_features = {}
        for stat in self.stat_categories:
            league_avg = league_team_stats[stat]
            league_std = league_team_stats[f'{stat}_std']
            opp_normalized_features[f'opp_normalized_{stat}'] = [(opp_avgs.get(stat, league_avg) - league_avg) / league_std]
        
        # Calculate predicted minutes for upcoming game (use recent average)
        predicted_min = recent_means.get('MIN', avg_min) if 'MIN' in recent_means else avg_min
        
        upcoming_features = pd.DataFrame({
            'recency_weight': [1.0],
            'same_opponent': [1],
            'is_playoff': [1 if season_type == 'Playoffs' else 0],
            'opp_pace': [opponent_strengths.get('PACE', 100.0)],
            'opp_rating': [opp_avgs['RATING']],
            'usg_pct': [usg_pct],
            'ts_pct': [ts_pct],
            'avg_min': [avg_min],
            'avg_rest_days': [avg_rest_days],
            'injury_risk': [1 if avg_min > 38.0 or avg_rest_days < 1.0 else 0],
            'HOME_AWAY': [1],
            'has_h2h': [1 if len(h2h_stats) > 0 else 0],
            'MIN': [predicted_min],
            'min_vs_league': [(avg_min - league_team_stats.get('avg_mpg', 24.0)) / league_team_stats.get('std_mpg', 8.0)],
            'min_recent_trend': [0.0],  # Will be calculated from recent games trend
            'min_usage_interaction': [predicted_min * usg_pct],
            'high_min_fatigue': [0],  # Assume no fatigue for upcoming game
            **{f'weighted_{stat}': [y[:, self.stat_categories.index(stat)].mean()] for stat in self.stat_categories},
            **{f'opp_strength_{stat}': [opp_avgs.get(stat, league_team_stats[stat]) / league_team_stats[stat]] for stat in self.stat_categories},
            **opp_normalized_features,
            **{f'opp_interaction_{stat}': [1 * (opp_avgs.get(stat, league_team_stats[stat]) / league_team_stats[stat])] for stat in self.stat_categories},
            **{f'recent_form_{stat}': [recent_means[f'recent_form_{stat}']] for stat in self.stat_categories},
            **{f'h2h_avg_{stat}': [h2h_avgs[stat]] for stat in self.stat_categories},
            **{f'opp_recent_{stat}': [opp_avgs[stat]] for stat in self.stat_categories},
            **{f'ema_trend_{stat}': [ema_trends[stat]] for stat in self.stat_categories},
            **{f'{stat}_per_min': [recent_means.get(f'{stat}_per_min', 0.0)] for stat in self.stat_categories},
            **{f'{stat}_per_36': [recent_means.get(f'{stat}_per_min', 0.0) * 36] for stat in self.stat_categories},
            'min_trend': [0.0],  # Calculated from rolling averages
            'min_consistency': [1.0]  # Default consistency value
        }, index=pd.Index([0]))[self.feature_cols].fillna(0)

        upcoming_features_sparse = csr_matrix(upcoming_features.values)
        pred, sigma, ci = self.predict_performance(
            upcoming_features_sparse, category, season_type, season_avgs, recent_avgs, h2h_avgs, opp_avgs, usg_pct, avg_rest_days
        )

        final_pred = pred

        p_over = 1 - norm.cdf(betting_line, final_pred, sigma)
        if p_over >= 0.5:
            confidence_pct = p_over * 100
            bet_on = 'over'
        else:
            confidence_pct = (1 - p_over) * 100
            bet_on = 'under'
        if bet_on == 'over' and confidence_pct < 50:
            confidence_pct = 50
        elif bet_on == 'under' and confidence_pct < 50:
            confidence_pct = 50

        pred_rounded = int(round(final_pred))
        ci_lower_rounded = int(round(ci[0]))
        ci_upper_rounded = int(round(ci[1]))
        message = f"Head-to-Head Matchups vs. {opponent_abbr}:\n"
        if h2h_games:
            for game in h2h_games:
                message += (f"  Date: {game['Game_Date']}, Matchup: {game['Matchup']}, "
                           f"PTS: {game['PTS']:.1f}, REB: {game['REB']:.1f}, AST: {game['AST']:.1f}, "
                           f"BLK: {game['BLK']:.1f}, STL: {game['STL']:.1f}\n")
        else:
            message += "  No matchups found.\n"
        def safe_float(value):
            if value is None:
                return 0.0
            try:
                return float(value)
            except (ValueError, TypeError):
                return 0.0
        stats_needed = self.stat_mapping.get(category.upper(), [category.upper()])
        if isinstance(stats_needed, str):
            stats_needed = [stats_needed]
        season_avg = sum(safe_float(season_avgs.get(stat, 0.0)) for stat in stats_needed)
        recent_avg = sum(safe_float(recent_avgs.get(stat, 0.0)) for stat in stats_needed)
        h2h_avg = sum(safe_float(h2h_avgs.get(stat, 0.0)) for stat in stats_needed)
        # Calculate opponent impact for display
        opponent_impact = self.calculate_opponent_impact(category, opp_avgs)
        
        message += (f"\nPlayer Averages for {category}:\n"
                   f"  Season: {season_avg:.1f}\n"
                   f"  Last 10 Games: {recent_avg:.1f}\n"
                   f"  vs. {opponent_abbr}: {h2h_avg:.1f}\n"
                   f"\nOpponent Team Averages (Current Season):\n"
                   f"  Points: {opp_avgs['PTS']:.1f}\n"
                   f"  Rebounds: {opp_avgs['REB']:.1f}\n"
                   f"  Assists: {opp_avgs['AST']:.1f}\n"
                   f"  Blocks: {opp_avgs['BLK']:.1f}\n"
                   f"  Steals: {opp_avgs['STL']:.1f}\n"
                   f"  Pace: {opp_avgs.get('PACE', 100.0):.1f}\n"
                   f"\nOpponent Impact Analysis:\n"
                   f"  Impact Factor: {opponent_impact:+.1%}\n"
                   f"  Analysis: {'Favorable matchup' if opponent_impact > 0.05 else 'Unfavorable matchup' if opponent_impact < -0.05 else 'Neutral matchup'}\n"
                   f"\nPredicted {category}: {pred_rounded} (95% CI: {ci_lower_rounded}-{ci_upper_rounded})\n"
                   f"P(Over {betting_line}): {p_over*100:.1f}%\n"
                   f"{confidence_pct:.1f}% confident bet on {bet_on.upper()}")
        return {'bet_on': bet_on, 'confidence': confidence_pct, 'predicted_value': pred_rounded, 'message': message, 'opp_averages': opp_avgs, 'confidence_interval': f'{ci_lower_rounded}-{ci_upper_rounded}'}
