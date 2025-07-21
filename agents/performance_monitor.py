#!/usr/bin/env python3
"""
Performance Monitoring and Optimization for CrewAI Integration
Provides comprehensive monitoring, metrics collection, and optimization recommendations
"""

import json
import logging
import time
import asyncio
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics
import psutil
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of performance metrics"""
    EXECUTION_TIME = "execution_time"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    DATABASE_QUERIES = "database_queries"
    AGENT_INTERACTIONS = "agent_interactions"
    ERROR_RATE = "error_rate"
    SUCCESS_RATE = "success_rate"

@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    metric_type: MetricType
    value: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    unit: str = ""

@dataclass
class PerformanceSnapshot:
    """Performance snapshot at a point in time"""
    timestamp: datetime
    metrics: Dict[MetricType, PerformanceMetric]
    system_info: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PerformanceReport:
    """Comprehensive performance report"""
    start_time: datetime
    end_time: datetime
    total_executions: int
    successful_executions: int
    failed_executions: int
    average_execution_time: float
    peak_memory_usage: float
    average_cpu_usage: float
    database_query_count: int
    agent_interaction_count: int
    recommendations: List[str] = field(default_factory=list)
    detailed_metrics: Dict[str, Any] = field(default_factory=dict)

class PerformanceMonitor:
    """Performance monitoring and optimization for CrewAI"""
    
    def __init__(self, enable_system_monitoring: bool = True):
        """Initialize performance monitor"""
        self.logger = logger
        self.enable_system_monitoring = enable_system_monitoring
        
        # Metrics storage
        self.metrics_history: List[PerformanceMetric] = []
        self.snapshots: List[PerformanceSnapshot] = []
        self.execution_times: List[float] = []
        self.error_counts: Dict[str, int] = {}
        
        # Monitoring state
        self.is_monitoring = False
        self.monitor_thread = None
        self.start_time = None
        
        # Performance thresholds
        self.thresholds = {
            "execution_time_warning": 30.0,  # seconds
            "execution_time_critical": 60.0,  # seconds
            "memory_usage_warning": 80.0,  # percentage
            "memory_usage_critical": 95.0,  # percentage
            "cpu_usage_warning": 70.0,  # percentage
            "cpu_usage_critical": 90.0,  # percentage
            "error_rate_warning": 5.0,  # percentage
            "error_rate_critical": 15.0  # percentage
        }
        
        self.logger.info("Performance monitor initialized")
    
    def start_monitoring(self):
        """Start performance monitoring"""
        if self.is_monitoring:
            self.logger.warning("Performance monitoring already active")
            return
        
        self.is_monitoring = True
        self.start_time = datetime.now()
        
        if self.enable_system_monitoring:
            self.monitor_thread = threading.Thread(target=self._system_monitoring_loop, daemon=True)
            self.monitor_thread.start()
        
        self.logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        if not self.is_monitoring:
            self.logger.warning("Performance monitoring not active")
            return
        
        self.is_monitoring = False
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        
        self.logger.info("Performance monitoring stopped")
    
    def _system_monitoring_loop(self):
        """System monitoring loop"""
        while self.is_monitoring:
            try:
                # Collect system metrics
                snapshot = self._collect_system_snapshot()
                self.snapshots.append(snapshot)
                
                # Check for critical conditions
                self._check_performance_alerts(snapshot)
                
                # Wait before next collection
                time.sleep(5)  # Collect every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Error in system monitoring loop: {str(e)}")
                time.sleep(10)  # Wait longer on error
    
    def _collect_system_snapshot(self) -> PerformanceSnapshot:
        """Collect system performance snapshot"""
        try:
            # Get system metrics
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Create metrics
            metrics = {
                MetricType.MEMORY_USAGE: PerformanceMetric(
                    metric_type=MetricType.MEMORY_USAGE,
                    value=memory.percent,
                    timestamp=datetime.now(),
                    unit="%",
                    metadata={"total_gb": memory.total / (1024**3), "available_gb": memory.available / (1024**3)}
                ),
                MetricType.CPU_USAGE: PerformanceMetric(
                    metric_type=MetricType.CPU_USAGE,
                    value=cpu_percent,
                    timestamp=datetime.now(),
                    unit="%"
                )
            }
            
            # System info
            system_info = {
                "memory_total_gb": memory.total / (1024**3),
                "memory_available_gb": memory.available / (1024**3),
                "memory_used_gb": memory.used / (1024**3),
                "cpu_count": psutil.cpu_count(),
                "process_id": os.getpid()
            }
            
            return PerformanceSnapshot(
                timestamp=datetime.now(),
                metrics=metrics,
                system_info=system_info
            )
            
        except Exception as e:
            self.logger.error(f"Error collecting system snapshot: {str(e)}")
            return PerformanceSnapshot(timestamp=datetime.now(), metrics={}, system_info={})
    
    def _check_performance_alerts(self, snapshot: PerformanceSnapshot):
        """Check for performance alerts"""
        try:
            for metric_type, metric in snapshot.metrics.items():
                if metric_type == MetricType.MEMORY_USAGE:
                    if metric.value >= self.thresholds["memory_usage_critical"]:
                        self.logger.critical(f"Critical memory usage: {metric.value}%")
                    elif metric.value >= self.thresholds["memory_usage_warning"]:
                        self.logger.warning(f"High memory usage: {metric.value}%")
                
                elif metric_type == MetricType.CPU_USAGE:
                    if metric.value >= self.thresholds["cpu_usage_critical"]:
                        self.logger.critical(f"Critical CPU usage: {metric.value}%")
                    elif metric.value >= self.thresholds["cpu_usage_warning"]:
                        self.logger.warning(f"High CPU usage: {metric.value}%")
                        
        except Exception as e:
            self.logger.error(f"Error checking performance alerts: {str(e)}")
    
    def record_execution(self, execution_time: float, success: bool, 
                        customer_id: Optional[str] = None, error_type: Optional[str] = None):
        """Record execution metrics"""
        try:
            # Record execution time
            self.execution_times.append(execution_time)
            
            # Record error if applicable
            if not success and error_type:
                self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
            
            # Create execution metric
            metric = PerformanceMetric(
                metric_type=MetricType.EXECUTION_TIME,
                value=execution_time,
                timestamp=datetime.now(),
                unit="seconds",
                metadata={
                    "success": success,
                    "customer_id": customer_id,
                    "error_type": error_type
                }
            )
            
            self.metrics_history.append(metric)
            
            # Check for performance alerts
            if execution_time >= self.thresholds["execution_time_critical"]:
                self.logger.critical(f"Critical execution time: {execution_time}s for customer {customer_id}")
            elif execution_time >= self.thresholds["execution_time_warning"]:
                self.logger.warning(f"Slow execution time: {execution_time}s for customer {customer_id}")
                
        except Exception as e:
            self.logger.error(f"Error recording execution: {str(e)}")
    
    def record_database_query(self, query_type: str, execution_time: float, success: bool):
        """Record database query metrics"""
        try:
            metric = PerformanceMetric(
                metric_type=MetricType.DATABASE_QUERIES,
                value=execution_time,
                timestamp=datetime.now(),
                unit="seconds",
                metadata={
                    "query_type": query_type,
                    "success": success
                }
            )
            
            self.metrics_history.append(metric)
            
        except Exception as e:
            self.logger.error(f"Error recording database query: {str(e)}")
    
    def record_agent_interaction(self, agent_type: str, interaction_time: float, success: bool):
        """Record agent interaction metrics"""
        try:
            metric = PerformanceMetric(
                metric_type=MetricType.AGENT_INTERACTIONS,
                value=interaction_time,
                timestamp=datetime.now(),
                unit="seconds",
                metadata={
                    "agent_type": agent_type,
                    "success": success
                }
            )
            
            self.metrics_history.append(metric)
            
        except Exception as e:
            self.logger.error(f"Error recording agent interaction: {str(e)}")
    
    def get_performance_report(self, start_time: Optional[datetime] = None, 
                             end_time: Optional[datetime] = None) -> PerformanceReport:
        """Generate comprehensive performance report"""
        try:
            # Set time range
            if not start_time:
                start_time = self.start_time or datetime.now() - timedelta(hours=1)
            if not end_time:
                end_time = datetime.now()
            
            # Filter metrics by time range
            filtered_metrics = [
                m for m in self.metrics_history
                if start_time <= m.timestamp <= end_time
            ]
            
            # Calculate statistics
            execution_metrics = [m for m in filtered_metrics if m.metric_type == MetricType.EXECUTION_TIME]
            memory_metrics = [m for m in filtered_metrics if m.metric_type == MetricType.MEMORY_USAGE]
            cpu_metrics = [m for m in filtered_metrics if m.metric_type == MetricType.CPU_USAGE]
            
            # Calculate totals
            total_executions = len(execution_metrics)
            successful_executions = len([m for m in execution_metrics if m.metadata.get("success", False)])
            failed_executions = total_executions - successful_executions
            
            # Calculate averages
            average_execution_time = statistics.mean([m.value for m in execution_metrics]) if execution_metrics else 0
            average_cpu_usage = statistics.mean([m.value for m in cpu_metrics]) if cpu_metrics else 0
            peak_memory_usage = max([m.value for m in memory_metrics]) if memory_metrics else 0
            
            # Count database queries and agent interactions
            database_query_count = len([m for m in filtered_metrics if m.metric_type == MetricType.DATABASE_QUERIES])
            agent_interaction_count = len([m for m in filtered_metrics if m.metric_type == MetricType.AGENT_INTERACTIONS])
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                total_executions, successful_executions, average_execution_time,
                peak_memory_usage, average_cpu_usage
            )
            
            # Detailed metrics
            detailed_metrics = {
                "execution_times": [m.value for m in execution_metrics],
                "memory_usage": [m.value for m in memory_metrics],
                "cpu_usage": [m.value for m in cpu_metrics],
                "error_counts": self.error_counts.copy(),
                "recent_snapshots": len([s for s in self.snapshots if start_time <= s.timestamp <= end_time])
            }
            
            return PerformanceReport(
                start_time=start_time,
                end_time=end_time,
                total_executions=total_executions,
                successful_executions=successful_executions,
                failed_executions=failed_executions,
                average_execution_time=average_execution_time,
                peak_memory_usage=peak_memory_usage,
                average_cpu_usage=average_cpu_usage,
                database_query_count=database_query_count,
                agent_interaction_count=agent_interaction_count,
                recommendations=recommendations,
                detailed_metrics=detailed_metrics
            )
            
        except Exception as e:
            self.logger.error(f"Error generating performance report: {str(e)}")
            return PerformanceReport(
                start_time=start_time or datetime.now(),
                end_time=end_time or datetime.now(),
                total_executions=0,
                successful_executions=0,
                failed_executions=0,
                average_execution_time=0,
                peak_memory_usage=0,
                average_cpu_usage=0,
                database_query_count=0,
                agent_interaction_count=0,
                recommendations=["Error generating report"],
                detailed_metrics={}
            )
    
    def _generate_recommendations(self, total_executions: int, successful_executions: int,
                                average_execution_time: float, peak_memory_usage: float,
                                average_cpu_usage: float) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []
        
        # Success rate recommendations
        if total_executions > 0:
            success_rate = (successful_executions / total_executions) * 100
            if success_rate < (100 - self.thresholds["error_rate_critical"]):
                recommendations.append("Critical: High error rate detected. Review error handling and system stability.")
            elif success_rate < (100 - self.thresholds["error_rate_warning"]):
                recommendations.append("Warning: Elevated error rate. Monitor system health and review recent changes.")
        
        # Execution time recommendations
        if average_execution_time > self.thresholds["execution_time_critical"]:
            recommendations.append("Critical: Very slow execution times. Consider optimizing database queries and agent interactions.")
        elif average_execution_time > self.thresholds["execution_time_warning"]:
            recommendations.append("Warning: Slow execution times. Review performance bottlenecks in data processing.")
        
        # Memory usage recommendations
        if peak_memory_usage > self.thresholds["memory_usage_critical"]:
            recommendations.append("Critical: Very high memory usage. Consider implementing memory management and cleanup.")
        elif peak_memory_usage > self.thresholds["memory_usage_warning"]:
            recommendations.append("Warning: High memory usage. Monitor memory leaks and optimize data structures.")
        
        # CPU usage recommendations
        if average_cpu_usage > self.thresholds["cpu_usage_critical"]:
            recommendations.append("Critical: Very high CPU usage. Consider scaling horizontally or optimizing algorithms.")
        elif average_cpu_usage > self.thresholds["cpu_usage_warning"]:
            recommendations.append("Warning: High CPU usage. Review computational efficiency and consider parallelization.")
        
        # General recommendations
        if not recommendations:
            recommendations.append("Performance is within acceptable ranges. Continue monitoring for trends.")
        
        return recommendations
    
    def get_realtime_metrics(self) -> Dict[str, Any]:
        """Get real-time performance metrics"""
        try:
            # Get current system metrics
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Calculate recent statistics
            recent_metrics = [m for m in self.metrics_history 
                            if m.timestamp > datetime.now() - timedelta(minutes=5)]
            
            recent_execution_times = [m.value for m in recent_metrics 
                                    if m.metric_type == MetricType.EXECUTION_TIME]
            
            return {
                "timestamp": datetime.now().isoformat(),
                "system": {
                    "memory_usage_percent": memory.percent,
                    "cpu_usage_percent": cpu_percent,
                    "memory_available_gb": memory.available / (1024**3)
                },
                "performance": {
                    "recent_executions": len(recent_execution_times),
                    "average_execution_time": statistics.mean(recent_execution_times) if recent_execution_times else 0,
                    "total_metrics_recorded": len(self.metrics_history)
                },
                "monitoring": {
                    "is_active": self.is_monitoring,
                    "start_time": self.start_time.isoformat() if self.start_time else None
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting real-time metrics: {str(e)}")
            return {"error": str(e)}

def main():
    """Test performance monitor"""
    print("=== Performance Monitor Test ===")
    
    try:
        # Initialize monitor
        monitor = PerformanceMonitor(enable_system_monitoring=True)
        
        # Start monitoring
        monitor.start_monitoring()
        print("✅ Performance monitoring started")
        
        # Simulate some executions
        print("\n📊 Simulating executions...")
        for i in range(5):
            execution_time = 2.0 + (i * 0.5)  # Simulate varying execution times
            success = i < 4  # Simulate some failures
            monitor.record_execution(
                execution_time=execution_time,
                success=success,
                customer_id=f"CUST{i+1:03d}",
                error_type="timeout" if not success else ""
            )
            print(f"   Recorded execution {i+1}: {execution_time:.2f}s, success: {success}")
        
        # Simulate database queries
        print("\n🗄️  Simulating database queries...")
        for i in range(3):
            query_time = 0.1 + (i * 0.05)
            monitor.record_database_query(
                query_type="customer_lookup",
                execution_time=query_time,
                success=True
            )
            print(f"   Recorded query {i+1}: {query_time:.3f}s")
        
        # Simulate agent interactions
        print("\n🤖 Simulating agent interactions...")
        for i in range(4):
            interaction_time = 1.0 + (i * 0.2)
            monitor.record_agent_interaction(
                agent_type="risk_analyst",
                interaction_time=interaction_time,
                success=True
            )
            print(f"   Recorded interaction {i+1}: {interaction_time:.2f}s")
        
        # Wait a bit for system monitoring
        print("\n⏳ Waiting for system monitoring data...")
        time.sleep(10)
        
        # Get performance report
        print("\n📋 Generating performance report...")
        report = monitor.get_performance_report()
        
        print(f"Performance Report:")
        print(f"   Total executions: {report.total_executions}")
        print(f"   Successful: {report.successful_executions}")
        print(f"   Failed: {report.failed_executions}")
        print(f"   Average execution time: {report.average_execution_time:.2f}s")
        print(f"   Peak memory usage: {report.peak_memory_usage:.1f}%")
        print(f"   Average CPU usage: {report.average_cpu_usage:.1f}%")
        print(f"   Database queries: {report.database_query_count}")
        print(f"   Agent interactions: {report.agent_interaction_count}")
        
        print(f"\nRecommendations:")
        for rec in report.recommendations:
            print(f"   • {rec}")
        
        # Get real-time metrics
        print(f"\n📊 Real-time metrics:")
        realtime = monitor.get_realtime_metrics()
        for key, value in realtime.items():
            if isinstance(value, dict):
                print(f"   {key}:")
                for subkey, subvalue in value.items():
                    print(f"     {subkey}: {subvalue}")
            else:
                print(f"   {key}: {value}")
        
        # Stop monitoring
        monitor.stop_monitoring()
        print("\n✅ Performance monitoring stopped")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 