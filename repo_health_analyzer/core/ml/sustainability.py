"""
Sustainability predictor using machine learning.

Predicts repository maintenance probability and sustainability metrics
based on commit history, contributor patterns, and activity trends.
"""

import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from ...models.report import SustainabilityMetrics, RepositoryInfo, AnalysisConfig


class SustainabilityPredictor:
    """
    ML-based predictor for repository sustainability and maintenance probability.
    
    Uses commit history patterns, contributor activity, and repository
    characteristics to predict long-term viability.
    """
    
    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.model = None
        self.scaler = StandardScaler()
        
        # Pre-trained weights (in production, load from file)
        self._initialize_model()
    
    def analyze(
        self, 
        commit_history: List[Dict[str, Any]], 
        repo_info: RepositoryInfo,
        source_files: List[Path]
    ) -> SustainabilityMetrics:
        """
        Analyze repository sustainability and predict maintenance probability.
        
        Args:
            commit_history: List of commit metadata
            repo_info: Repository information
            source_files: List of source files
        
        Returns:
            SustainabilityMetrics: Sustainability analysis results
        """
        # Extract features for ML prediction
        features = self._extract_features(commit_history, repo_info, source_files)
        
        # Predict maintenance probability
        maintenance_probability = self._predict_maintenance_probability(features)
        
        # Calculate individual metrics
        activity_trend = self._analyze_activity_trend(commit_history)
        bus_factor = self._calculate_bus_factor(commit_history)
        recent_activity_score = self._calculate_recent_activity_score(commit_history)
        contributor_diversity = self._calculate_contributor_diversity(commit_history)
        commit_frequency_score = self._calculate_commit_frequency_score(commit_history)
        
        # Calculate overall sustainability score
        score = self._calculate_sustainability_score(
            maintenance_probability, recent_activity_score,
            contributor_diversity, commit_frequency_score, bus_factor
        )
        
        return SustainabilityMetrics(
            score=round(score, 1),
            maintenance_probability=round(maintenance_probability, 3),
            activity_trend=activity_trend,
            bus_factor=bus_factor,
            recent_activity_score=round(recent_activity_score, 2),
            contributor_diversity=round(contributor_diversity, 3),
            commit_frequency_score=round(commit_frequency_score, 2)
        )
    
    def _extract_features(
        self, 
        commit_history: List[Dict[str, Any]], 
        repo_info: RepositoryInfo,
        source_files: List[Path]
    ) -> Dict[str, float]:
        """Extract features for ML model."""
        if not commit_history:
            return self._default_features()
        
        now = datetime.now(timezone.utc)
        
        # Time-based features
        commit_dates = [commit['date'] for commit in commit_history]
        recent_commits = [d for d in commit_dates if (now - d).days <= 30]
        
        # Contributor features
        contributors = set(commit['author'] for commit in commit_history)
        commit_counts = defaultdict(int)
        for commit in commit_history:
            commit_counts[commit['author']] += 1
        
        # Activity features
        total_commits = len(commit_history)
        commits_last_30_days = len(recent_commits)
        commits_last_90_days = len([d for d in commit_dates if (now - d).days <= 90])
        
        # Repository features
        files_per_commit = repo_info.total_files / max(total_commits, 1)
        lines_per_file = repo_info.total_lines / max(repo_info.total_files, 1)
        
        # Change pattern features
        avg_files_changed = sum(commit.get('files_changed', 0) for commit in commit_history) / max(total_commits, 1)
        avg_insertions = sum(commit.get('insertions', 0) for commit in commit_history) / max(total_commits, 1)
        avg_deletions = sum(commit.get('deletions', 0) for commit in commit_history) / max(total_commits, 1)
        
        # Merge vs feature commits
        merge_commits = len([c for c in commit_history if c.get('is_merge', False)])
        merge_ratio = merge_commits / max(total_commits, 1)
        
        return {
            'repo_age_days': repo_info.age_days,
            'total_commits': total_commits,
            'commits_last_30_days': commits_last_30_days,
            'commits_last_90_days': commits_last_90_days,
            'contributor_count': len(contributors),
            'total_files': repo_info.total_files,
            'total_lines': repo_info.total_lines,
            'files_per_commit': files_per_commit,
            'lines_per_file': lines_per_file,
            'avg_files_changed': avg_files_changed,
            'avg_insertions': avg_insertions,
            'avg_deletions': avg_deletions,
            'merge_ratio': merge_ratio,
            'primary_contributor_ratio': max(commit_counts.values()) / max(total_commits, 1),
            'commit_frequency_last_30': commits_last_30_days / 30,
            'language_diversity': len(repo_info.languages),
        }
    
    def _predict_maintenance_probability(self, features: Dict[str, float]) -> float:
        """
        Predict maintenance probability using simple heuristics.
        
        In production, this would use a trained ML model.
        """
        # Simple heuristic-based prediction
        score = 0.5  # Base probability
        
        # Recent activity is very important
        if features['commits_last_30_days'] > 5:
            score += 0.3
        elif features['commits_last_30_days'] > 1:
            score += 0.1
        else:
            score -= 0.2
        
        # Contributor diversity
        if features['contributor_count'] > 3:
            score += 0.2
        elif features['contributor_count'] > 1:
            score += 0.1
        
        # Primary contributor dominance (bus factor)
        if features['primary_contributor_ratio'] > 0.8:
            score -= 0.2
        
        # Repository age and maturity
        if features['repo_age_days'] > 365:
            score += 0.1
        
        # Regular commit frequency
        if features['commit_frequency_last_30'] > 0.5:  # More than every 2 days
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def _analyze_activity_trend(self, commit_history: List[Dict[str, Any]]) -> str:
        """Analyze commit activity trend over time."""
        if len(commit_history) < 10:
            return "insufficient_data"
        
        now = datetime.now(timezone.utc)
        
        # Split commits into time periods
        recent_period = [c for c in commit_history if (now - c['date']).days <= 90]
        older_period = [c for c in commit_history if 90 < (now - c['date']).days <= 180]
        
        if not older_period:
            return "new_project"
        
        recent_rate = len(recent_period) / 90
        older_rate = len(older_period) / 90
        
        if recent_rate > older_rate * 1.2:
            return "increasing"
        elif recent_rate < older_rate * 0.8:
            return "declining"
        else:
            return "stable"
    
    def _calculate_bus_factor(self, commit_history: List[Dict[str, Any]]) -> int:
        """
        Calculate bus factor (number of people who can maintain the project).
        
        Args:
            commit_history: List of commit metadata
        
        Returns:
            int: Bus factor (number of key contributors)
        """
        if not commit_history:
            return 0
        
        # Count commits per contributor
        commit_counts = defaultdict(int)
        for commit in commit_history:
            commit_counts[commit['author']] += 1
        
        total_commits = len(commit_history)
        
        # Contributors who have made at least 10% of commits are considered "key"
        key_contributors = 0
        for author, count in commit_counts.items():
            if count / total_commits >= 0.1:
                key_contributors += 1
        
        return max(1, key_contributors)
    
    def _calculate_recent_activity_score(self, commit_history: List[Dict[str, Any]]) -> float:
        """Calculate recent activity score (0-10)."""
        if not commit_history:
            return 0.0
        
        now = datetime.now(timezone.utc)
        
        # Count commits in different time windows
        commits_7_days = len([c for c in commit_history if (now - c['date']).days <= 7])
        commits_30_days = len([c for c in commit_history if (now - c['date']).days <= 30])
        commits_90_days = len([c for c in commit_history if (now - c['date']).days <= 90])
        
        # Calculate weighted score
        score = (
            commits_7_days * 3 +     # Recent activity weighted heavily
            commits_30_days * 2 +    # Medium-term activity
            commits_90_days * 1      # Longer-term activity
        ) / 6  # Normalize
        
        return min(10.0, score)
    
    def _calculate_contributor_diversity(self, commit_history: List[Dict[str, Any]]) -> float:
        """Calculate contributor diversity (0-1)."""
        if not commit_history:
            return 0.0
        
        commit_counts = defaultdict(int)
        for commit in commit_history:
            commit_counts[commit['author']] += 1
        
        total_commits = len(commit_history)
        
        # Calculate Gini coefficient for contributor distribution
        sorted_counts = sorted(commit_counts.values())
        n = len(sorted_counts)
        
        if n <= 1:
            return 0.0
        
        # Gini coefficient calculation
        cumsum = np.cumsum(sorted_counts)
        gini = (n + 1 - 2 * sum((n + 1 - i) * count for i, count in enumerate(sorted_counts, 1)) / total_commits) / n
        
        # Convert Gini to diversity score (1 - Gini)
        diversity = 1 - gini
        
        return max(0.0, min(1.0, diversity))
    
    def _calculate_commit_frequency_score(self, commit_history: List[Dict[str, Any]]) -> float:
        """Calculate commit frequency consistency score (0-10)."""
        if len(commit_history) < 2:
            return 0.0
        
        # Calculate gaps between commits
        sorted_commits = sorted(commit_history, key=lambda x: x['date'])
        gaps = []
        
        for i in range(1, len(sorted_commits)):
            gap = (sorted_commits[i]['date'] - sorted_commits[i-1]['date']).days
            gaps.append(gap)
        
        if not gaps:
            return 0.0
        
        # Calculate consistency (lower variance = higher score)
        avg_gap = sum(gaps) / len(gaps)
        variance = sum((gap - avg_gap) ** 2 for gap in gaps) / len(gaps)
        std_dev = math.sqrt(variance)
        
        # Score based on frequency and consistency
        frequency_score = min(10, 30 / max(avg_gap, 1))  # Daily commits = 10 points
        consistency_score = max(0, 10 - std_dev / 10)    # Lower variance = higher score
        
        return (frequency_score + consistency_score) / 2
    
    def _calculate_sustainability_score(
        self, maintenance_prob: float, recent_activity: float,
        contributor_diversity: float, commit_frequency: float, bus_factor: int
    ) -> float:
        """Calculate overall sustainability score."""
        
        # Weighted combination of factors
        score = (
            maintenance_prob * 10 * 0.4 +      # 40% weight on ML prediction
            recent_activity * 0.25 +           # 25% weight on recent activity
            contributor_diversity * 10 * 0.15 + # 15% weight on diversity
            commit_frequency * 0.1 +           # 10% weight on frequency
            min(10, bus_factor * 2) * 0.1      # 10% weight on bus factor
        )
        
        return max(0.0, min(10.0, score))
    
    def _initialize_model(self) -> None:
        """Initialize the ML model with default parameters."""
        # In production, this would load a pre-trained model
        self.model = RandomForestClassifier(
            n_estimators=50,
            max_depth=10,
            random_state=42
        )
        
        # For now, we'll use heuristics instead of actual ML
        # The model would be trained on historical repository data
    
    def _default_features(self) -> Dict[str, float]:
        """Return default features for repositories with no history."""
        return {
            'repo_age_days': 0,
            'total_commits': 0,
            'commits_last_30_days': 0,
            'commits_last_90_days': 0,
            'contributor_count': 0,
            'total_files': 0,
            'total_lines': 0,
            'files_per_commit': 0,
            'lines_per_file': 0,
            'avg_files_changed': 0,
            'avg_insertions': 0,
            'avg_deletions': 0,
            'merge_ratio': 0,
            'primary_contributor_ratio': 1,
            'commit_frequency_last_30': 0,
            'language_diversity': 0,
        }
