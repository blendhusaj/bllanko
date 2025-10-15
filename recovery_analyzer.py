#!/usr/bin/env python3
"""
Recovery Analyzer - Checks if backend communication recovered over time
Analyzes timestamps to see if error rates improved or worsened

Usage: python recovery_analyzer.py logfile.log
"""

import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

class RecoveryAnalyzer:
    def __init__(self, log_file):
        self.log_file = Path(log_file)
        if not self.log_file.exists():
            raise FileNotFoundError(f"Log file not found: {log_file}")
        
        # Time-based data
        self.timeline = []  # List of (timestamp, is_success) tuples
        self.hourly_stats = defaultdict(lambda: {'success': 0, 'error': 0})
        self.minute_stats = defaultdict(lambda: {'success': 0, 'error': 0})
        
        self.first_timestamp = None
        self.last_timestamp = None
    
    def extract_timestamp(self, line):
        """Extract timestamp from log line"""
        # Android logcat format: 09-22 14:45:58.042
        android_match = re.match(r'^(\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})\.\d+', line)
        if android_match:
            month_day = android_match.group(1)
            time_str = android_match.group(2)
            # Assume current year (2024)
            timestamp_str = f"2024-{month_day} {time_str}"
            try:
                return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        # Common timestamp patterns
        patterns = [
            # ISO format: 2024-10-01T10:23:45 or 2024-10-01 10:23:45
            r'(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2})',
            # [2024-10-01 10:23:45]
            r'\[(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\]',
            # 2024/10/01 10:23:45
            r'(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})',
            # 10/01/2024 10:23:45
            r'(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})',
            # Oct 01 10:23:45
            r'([A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                timestamp_str = match.group(1)
                try:
                    # Try different datetime formats
                    for fmt in [
                        '%Y-%m-%d %H:%M:%S',
                        '%Y-%m-%dT%H:%M:%S',
                        '%Y/%m/%d %H:%M:%S',
                        '%m/%d/%Y %H:%M:%S',
                    ]:
                        try:
                            return datetime.strptime(timestamp_str, fmt)
                        except ValueError:
                            continue
                except:
                    continue
        
        return None
    
    def is_success(self, line):
        """Determine if line indicates success or error"""
        # Look for HTTP status codes
        status_match = re.search(r'\b(\d{3})\b', line)
        if status_match:
            code = int(status_match.group(1))
            if 100 <= code < 600:
                return 200 <= code < 300
        
        # Look for keywords
        line_lower = line.lower()
        if any(word in line_lower for word in ['error', 'fail', 'timeout', '4[0-9][0-9]', '5[0-9][0-9]']):
            return False
        if any(word in line_lower for word in ['success', 'ok', '200', 'completed']):
            return True
        
        return None
    
    def analyze(self):
        """Analyze log file for recovery patterns"""
        print("\n⏱️  Analyzing timeline for recovery patterns...")
        
        url_pattern = r'https?://[^\s\'"<>]+'
        
        with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                if line_num % 5000 == 0:
                    print(f"  Processing line {line_num:,}...", end='\r')
                
                # Check if line has URL (backend communication)
                if not re.search(url_pattern, line):
                    continue
                
                # Extract timestamp
                timestamp = self.extract_timestamp(line)
                if not timestamp:
                    continue
                
                # Track first and last timestamps
                if self.first_timestamp is None:
                    self.first_timestamp = timestamp
                self.last_timestamp = timestamp
                
                # Determine success/error
                is_success = self.is_success(line)
                if is_success is None:
                    continue
                
                # Store in timeline
                self.timeline.append((timestamp, is_success))
                
                # Store in hourly buckets
                hour_key = timestamp.strftime('%Y-%m-%d %H:00')
                if is_success:
                    self.hourly_stats[hour_key]['success'] += 1
                else:
                    self.hourly_stats[hour_key]['error'] += 1
                
                # Store in minute buckets
                minute_key = timestamp.strftime('%Y-%m-%d %H:%M')
                if is_success:
                    self.minute_stats[minute_key]['success'] += 1
                else:
                    self.minute_stats[minute_key]['error'] += 1
        
        print("  Analysis complete!                    ")
    
    def print_report(self):
        """Print recovery analysis report"""
        if not self.timeline:
            print("\n❌ No timestamped data found in log file!")
            print("   The log file may not contain timestamps or backend communication entries.")
            return
        
        print("\n" + "="*100)
        print("⏱️  RECOVERY ANALYSIS - DID COMMUNICATION RECOVER?")
        print("="*100)
        
        # Time range
        duration = self.last_timestamp - self.first_timestamp
        print(f"\n📅 TIME RANGE:")
        print(f"   Start:    {self.first_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   End:      {self.last_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Duration: {duration}")
        print(f"   Total logged communications: {len(self.timeline)}")
        
        # Overall statistics
        total_success = sum(1 for _, success in self.timeline if success)
        total_errors = sum(1 for _, success in self.timeline if not success)
        overall_success_rate = (total_success / len(self.timeline) * 100) if self.timeline else 0
        
        print(f"\n📊 OVERALL STATISTICS:")
        print(f"   Successful: {total_success} ({overall_success_rate:.1f}%)")
        print(f"   Failed:     {total_errors} ({100-overall_success_rate:.1f}%)")
        
        # Timeline analysis
        print("\n" + "="*100)
        print("📈 TIMELINE ANALYSIS (By Hour)")
        print("="*100)
        
        if not self.hourly_stats:
            print("\n⚠️  Not enough hourly data for analysis")
            return
        
        sorted_hours = sorted(self.hourly_stats.items())
        
        print(f"\n{'Time Period':<20} {'Success':<12} {'Errors':<12} {'Success Rate':<15} {'Status'}")
        print("-"*100)
        
        previous_rate = None
        recovery_detected = False
        degradation_detected = False
        
        for hour, stats in sorted_hours:
            total = stats['success'] + stats['error']
            success_rate = (stats['success'] / total * 100) if total > 0 else 0
            
            # Determine trend
            trend = ""
            if previous_rate is not None:
                diff = success_rate - previous_rate
                if diff > 10:
                    trend = "📈 IMPROVING"
                    recovery_detected = True
                elif diff < -10:
                    trend = "📉 DEGRADING"
                    degradation_detected = True
                else:
                    trend = "➡️  STABLE"
            
            status = "✅ GOOD" if success_rate >= 80 else "⚠️  POOR" if success_rate >= 50 else "❌ CRITICAL"
            
            print(f"{hour:<20} {stats['success']:<12} {stats['error']:<12} {success_rate:>6.1f}%        {status:<15} {trend}")
            
            previous_rate = success_rate
        
        # Recovery analysis
        print("\n" + "="*100)
        print("🔍 RECOVERY ASSESSMENT")
        print("="*100)
        
        # Split timeline into quarters
        quarter_size = len(self.timeline) // 4
        if quarter_size > 0:
            quarters = [
                self.timeline[:quarter_size],
                self.timeline[quarter_size:quarter_size*2],
                self.timeline[quarter_size*2:quarter_size*3],
                self.timeline[quarter_size*3:]
            ]
            
            quarter_names = ["First Quarter", "Second Quarter", "Third Quarter", "Fourth Quarter"]
            quarter_rates = []
            
            print(f"\n{'Period':<20} {'Success Rate':<15} {'Trend'}")
            print("-"*100)
            
            for i, (name, quarter) in enumerate(zip(quarter_names, quarters)):
                if quarter:
                    success_count = sum(1 for _, success in quarter if success)
                    rate = (success_count / len(quarter) * 100)
                    quarter_rates.append(rate)
                    
                    trend = ""
                    if i > 0:
                        diff = rate - quarter_rates[i-1]
                        if diff > 5:
                            trend = "📈 Improving"
                        elif diff < -5:
                            trend = "📉 Degrading"
                        else:
                            trend = "➡️  Stable"
                    
                    print(f"{name:<20} {rate:>6.1f}%          {trend}")
            
            # Final verdict
            print("\n" + "="*100)
            print("🎯 CONCLUSION")
            print("="*100)
            
            first_quarter_rate = quarter_rates[0] if quarter_rates else 0
            last_quarter_rate = quarter_rates[-1] if quarter_rates else 0
            improvement = last_quarter_rate - first_quarter_rate
            
            print(f"\nFirst quarter success rate: {first_quarter_rate:.1f}%")
            print(f"Last quarter success rate:  {last_quarter_rate:.1f}%")
            print(f"Change:                     {improvement:+.1f}%")
            
            print("\n" + "-"*100)
            
            if improvement > 10:
                print("✅ RECOVERY DETECTED!")
                print("   The communication quality IMPROVED significantly over time.")
                print(f"   Success rate increased by {improvement:.1f}%")
            elif improvement > 5:
                print("✅ PARTIAL RECOVERY")
                print("   The communication quality improved somewhat.")
                print(f"   Success rate increased by {improvement:.1f}%")
            elif improvement < -10:
                print("❌ DEGRADATION DETECTED!")
                print("   The communication quality WORSENED over time.")
                print(f"   Success rate decreased by {abs(improvement):.1f}%")
            elif improvement < -5:
                print("⚠️  PARTIAL DEGRADATION")
                print("   The communication quality degraded somewhat.")
                print(f"   Success rate decreased by {abs(improvement):.1f}%")
            else:
                print("➡️  NO SIGNIFICANT CHANGE")
                print("   The communication quality remained relatively stable.")
                print("   No clear recovery or degradation pattern.")
            
            # Additional insights
            if last_quarter_rate < 50:
                print("\n⚠️  WARNING: Current communication quality is still POOR (< 50% success rate)")
                print("   System has not recovered to acceptable levels.")
            elif last_quarter_rate >= 80:
                print("\n✅ GOOD: Current communication quality is acceptable (≥ 80% success rate)")
        
        else:
            print("\n⚠️  Not enough data points for quarter analysis")

def main():
    print("="*100)
    print("⏱️  RECOVERY ANALYZER")
    print("="*100)
    print("Analyzes if backend communication recovered over time")
    print("="*100)
    
    if len(sys.argv) < 2:
        print("\nUsage: python recovery_analyzer.py logfile.log")
        sys.exit(1)
    
    try:
        analyzer = RecoveryAnalyzer(sys.argv[1])
        analyzer.analyze()
        analyzer.print_report()
        
        print("\n✅ Recovery analysis complete!")
        
    except FileNotFoundError as e:
        print(f"\n❌ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

