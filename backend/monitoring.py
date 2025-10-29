"""
Performance Monitoring and Analytics
Provides comprehensive monitoring, logging, and performance analytics.
"""

import time
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from functools import wraps
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None
import os

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Comprehensive performance monitoring system."""
    
    def __init__(self):
        self.metrics = {
            'api_calls': {},
            'model_training': {},
            'predictions': {},
            'system_resources': {},
            'errors': {}
        }
        self.start_time = time.time()
        self.prediction_history = []
        self.error_history = []
    
    def track_api_call(self, endpoint: str, duration: float, success: bool, error: Optional[str] = None):
        """Track API call performance."""
        if endpoint not in self.metrics['api_calls']:
            self.metrics['api_calls'][endpoint] = {
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'total_duration': 0.0,
                'avg_duration': 0.0,
                'max_duration': 0.0,
                'min_duration': float('inf'),
                'errors': []
            }
        
        metrics = self.metrics['api_calls'][endpoint]
        metrics['total_calls'] += 1
        metrics['total_duration'] += duration
        metrics['avg_duration'] = metrics['total_duration'] / metrics['total_calls']
        metrics['max_duration'] = max(metrics['max_duration'], duration)
        metrics['min_duration'] = min(metrics['min_duration'], duration)
        
        if success:
            metrics['successful_calls'] += 1
        else:
            metrics['failed_calls'] += 1
            if error:
                metrics['errors'].append({
                    'timestamp': datetime.now().isoformat(),
                    'error': str(error)
                })
    
    def track_model_training(self, model_type: str, duration: float, accuracy: float, features_count: int):
        """Track model training performance."""
        if model_type not in self.metrics['model_training']:
            self.metrics['model_training'][model_type] = {
                'training_sessions': 0,
                'total_duration': 0.0,
                'avg_duration': 0.0,
                'avg_accuracy': 0.0,
                'avg_features': 0.0,
                'best_accuracy': 0.0
            }
        
        metrics = self.metrics['model_training'][model_type]
        metrics['training_sessions'] += 1
        metrics['total_duration'] += duration
        metrics['avg_duration'] = metrics['total_duration'] / metrics['training_sessions']
        metrics['avg_accuracy'] = (metrics['avg_accuracy'] * (metrics['training_sessions'] - 1) + accuracy) / metrics['training_sessions']
        metrics['avg_features'] = (metrics['avg_features'] * (metrics['training_sessions'] - 1) + features_count) / metrics['training_sessions']
        metrics['best_accuracy'] = max(metrics['best_accuracy'], accuracy)
    
    def track_prediction(self, player_name: str, category: str, prediction: float, confidence: float, 
                        actual: Optional[float] = None, duration: float = 0.0):
        """Track prediction performance."""
        prediction_data = {
            'timestamp': datetime.now().isoformat(),
            'player_name': player_name,
            'category': category,
            'prediction': prediction,
            'confidence': confidence,
            'actual': actual,
            'duration': duration
        }
        
        self.prediction_history.append(prediction_data)
        
        # Keep only last 1000 predictions to prevent memory issues
        if len(self.prediction_history) > 1000:
            self.prediction_history = self.prediction_history[-1000:]
    
    def track_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None):
        """Track system errors."""
        error_data = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'error_message': str(error_message),
            'context': context or {}
        }
        
        self.error_history.append(error_data)
        
        # Keep only last 500 errors
        if len(self.error_history) > 500:
            self.error_history = self.error_history[-500:]
    
    def get_system_resources(self) -> Dict[str, Any]:
        """Get current system resource usage."""
        if not PSUTIL_AVAILABLE:
            return {
                'cpu_percent': 0.0,
                'memory_mb': 0.0,
                'memory_percent': 0.0,
                'threads': 0,
                'open_files': 0,
                'system_cpu_percent': 0.0,
                'system_memory_percent': 0.0,
                'disk_usage_percent': 0.0,
                'note': 'psutil not available'
            }
        
        try:
            process = psutil.Process(os.getpid())
            return {
                'cpu_percent': process.cpu_percent(),
                'memory_mb': process.memory_info().rss / 1024 / 1024,
                'memory_percent': process.memory_percent(),
                'threads': process.num_threads(),
                'open_files': len(process.open_files()),
                'system_cpu_percent': psutil.cpu_percent(),
                'system_memory_percent': psutil.virtual_memory().percent,
                'disk_usage_percent': psutil.disk_usage('/').percent
            }
        except Exception as e:
            logger.error(f"Error getting system resources: {e}")
            return {}
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        uptime = time.time() - self.start_time
        
        # Calculate API success rates
        api_success_rates = {}
        for endpoint, metrics in self.metrics['api_calls'].items():
            if metrics['total_calls'] > 0:
                api_success_rates[endpoint] = metrics['successful_calls'] / metrics['total_calls']
        
        # Calculate prediction accuracy (if we have actual values)
        prediction_accuracy = None
        if self.prediction_history:
            predictions_with_actuals = [p for p in self.prediction_history if p['actual'] is not None]
            if predictions_with_actuals:
                mae = sum(abs(p['prediction'] - p['actual']) for p in predictions_with_actuals) / len(predictions_with_actuals)
                prediction_accuracy = {
                    'mae': mae,
                    'total_predictions': len(predictions_with_actuals)
                }
        
        return {
            'uptime_seconds': uptime,
            'uptime_hours': uptime / 3600,
            'api_success_rates': api_success_rates,
            'total_predictions': len(self.prediction_history),
            'total_errors': len(self.error_history),
            'prediction_accuracy': prediction_accuracy,
            'system_resources': self.get_system_resources(),
            'model_performance': self.metrics['model_training']
        }
    
    def get_recent_errors(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent errors within specified hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            error for error in self.error_history
            if datetime.fromisoformat(error['timestamp']) > cutoff_time
        ]
    
    def get_prediction_analytics(self, hours: int = 24) -> Dict[str, Any]:
        """Get prediction analytics for specified time period."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_predictions = [
            p for p in self.prediction_history
            if datetime.fromisoformat(p['timestamp']) > cutoff_time
        ]
        
        if not recent_predictions:
            return {'message': 'No recent predictions found'}
        
        # Group by category
        by_category = {}
        for pred in recent_predictions:
            category = pred['category']
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(pred)
        
        analytics = {
            'total_predictions': len(recent_predictions),
            'by_category': {}
        }
        
        for category, predictions in by_category.items():
            confidences = [p['confidence'] for p in predictions]
            analytics['by_category'][category] = {
                'count': len(predictions),
                'avg_confidence': sum(confidences) / len(confidences),
                'min_confidence': min(confidences),
                'max_confidence': max(confidences)
            }
        
        return analytics
    
    def export_metrics(self, filepath: str):
        """Export metrics to JSON file."""
        try:
            with open(filepath, 'w') as f:
                json.dump({
                    'metrics': self.metrics,
                    'prediction_history': self.prediction_history[-100:],  # Last 100 predictions
                    'error_history': self.error_history[-50:],  # Last 50 errors
                    'performance_summary': self.get_performance_summary()
                }, f, indent=2, default=str)
            logger.info(f"Metrics exported to {filepath}")
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
    
    def reset_metrics(self):
        """Reset all metrics."""
        self.metrics = {
            'api_calls': {},
            'model_training': {},
            'predictions': {},
            'system_resources': {},
            'errors': {}
        }
        self.prediction_history = []
        self.error_history = []
        self.start_time = time.time()
        logger.info("Metrics reset")

def monitor_performance(func):
    """Decorator to monitor function performance."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Track successful execution
            if hasattr(wrapper, 'monitor'):
                wrapper.monitor.track_prediction(
                    player_name=getattr(args[0], 'player_name', 'unknown') if args else 'unknown',
                    category=getattr(args[0], 'category', 'unknown') if args else 'unknown',
                    prediction=result.get('prediction', 0) if isinstance(result, dict) else 0,
                    confidence=result.get('confidence', 0) if isinstance(result, dict) else 0,
                    duration=duration
                )
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            
            # Track error
            if hasattr(wrapper, 'monitor'):
                wrapper.monitor.track_error(
                    error_type=type(e).__name__,
                    error_message=str(e),
                    context={'function': func.__name__, 'duration': duration}
                )
            
            raise
    return wrapper

# Global performance monitor instance
performance_monitor = PerformanceMonitor()
