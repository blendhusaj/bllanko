#!/usr/bin/env python3
"""
Secure Local Log Analyzer for Backend Communication
Analyzes log files completely offline - no data is sent anywhere!
All processing happens locally on your machine.

Usage:
    python log_analyzer.py logfile.log
    
    Or drag and drop your log file onto this script.
"""

import re
import sys
from collections import defaultdict
from pathlib import Path

class SecureLogAnalyzer:
    """
    100% Local Log Analyzer - No network access, completely confidential
    """
    
    def __init__(self, log_file):
        self.log_file = Path(log_file)
        if not self.log_file.exists():
            raise FileNotFoundError(f"Log file not found: {log_file}")
        
        # Data structures
        self.url_stats = defaultdict(lambda: {
            'success_count': 0,
            'client_error_count': 0,  # 4xx
            'server_error_count': 0,  # 5xx
            'timeout_count': 0,
            'unknown_count': 0,
            'total_count': 0,
            'status_codes': defaultdict(int),
            'error_messages': []
        })
        
        self.total_lines = 0
        self.lines_with_urls = 0
    
    def analyze(self):
        """Analyze the log file completely offline"""
        print(f"\n🔒 Analyzing log file securely (100% local, no network access)")
        print(f"📁 File: {self.log_file}")
        print(f"📊 Size: {self.log_file.stat().st_size / 1024:.2f} KB")
        print("\n⏳ Processing...")
        
        # Regex patterns
        url_pattern = r'(https?://[^\s\'"<>]+)'
        status_pattern = r'\b(\d{3})\b'  # HTTP status codes
        
        try:
            with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    self.total_lines += 1
                    
                    # Progress indicator for large files
                    if line_num % 10000 == 0:
                        print(f"  Processed {line_num:,} lines...", end='\r')
                    
                    # Extract URL
                    url_matches = re.findall(url_pattern, line)
                    if not url_matches:
                        continue
                    
                    self.lines_with_urls += 1
                    
                    for url in url_matches:
                        # Clean URL
                        url = url.rstrip('.,;:)\'"')
                        
                        self.url_stats[url]['total_count'] += 1
                        
                        # Extract HTTP status code
                        status_matches = re.findall(status_pattern, line)
                        status_code = None
                        
                        for code in status_matches:
                            code_int = int(code)
                            if 100 <= code_int < 600:  # Valid HTTP status codes
                                status_code = code_int
                                self.url_stats[url]['status_codes'][status_code] += 1
                                break
                        
                        # Categorize by status code
                        if status_code:
                            if 200 <= status_code < 300:
                                self.url_stats[url]['success_count'] += 1
                            elif 400 <= status_code < 500:
                                self.url_stats[url]['client_error_count'] += 1
                            elif 500 <= status_code < 600:
                                self.url_stats[url]['server_error_count'] += 1
                        
                        # Check for error keywords
                        line_lower = line.lower()
                        if any(keyword in line_lower for keyword in 
                               ['error', 'failed', 'timeout', 'exception', 'refused']):
                            if 'timeout' in line_lower:
                                self.url_stats[url]['timeout_count'] += 1
                            elif status_code is None:
                                self.url_stats[url]['unknown_count'] += 1
                            
                            # Store error message (truncated for privacy)
                            if len(self.url_stats[url]['error_messages']) < 3:
                                error_snippet = line.strip()[:100]
                                self.url_stats[url]['error_messages'].append(error_snippet)
                        
                        # If no status code found, check for success keywords
                        if status_code is None:
                            if any(keyword in line_lower for keyword in 
                                   ['success', 'ok', 'completed', '200']):
                                self.url_stats[url]['success_count'] += 1
        
        except Exception as e:
            print(f"\n❌ Error reading file: {e}")
            sys.exit(1)
        
        print(f"  Processed {self.total_lines:,} lines - Done!        ")
    
    def print_report(self):
        """Generate and print the analysis report"""
        print("\n" + "="*100)
        print("BACKEND COMMUNICATION ANALYSIS REPORT")
        print("="*100)
        print(f"📁 File: {self.log_file.name}")
        print(f"📝 Total lines: {self.total_lines:,}")
        print(f"🔗 Lines with URLs: {self.lines_with_urls:,}")
        print(f"🌐 Unique URLs found: {len(self.url_stats)}")
        
        # Successful URLs
        print("\n" + "="*100)
        print("✅ SUCCESSFUL BACKEND COMMUNICATION (2xx Status Codes)")
        print("="*100)
        
        successful = [(url, stats) for url, stats in self.url_stats.items() 
                     if stats['success_count'] > 0]
        successful.sort(key=lambda x: x[1]['success_count'], reverse=True)
        
        if successful:
            print(f"\n{'Count':<8} {'Success Rate':<15} {'URL'}")
            print("-"*100)
            for url, stats in successful:
                total = stats['total_count']
                success = stats['success_count']
                rate = (success / total * 100) if total > 0 else 0
                print(f"{success:<8} {rate:>5.1f}% ({success}/{total}){' '*3} {url}")
        else:
            print("\n⚠️  No successful communications found")
        
        # Error URLs
        print("\n" + "="*100)
        print("❌ ERRONEOUS BACKEND COMMUNICATION (4xx/5xx/Timeout/Errors)")
        print("="*100)
        
        errors = [(url, stats) for url, stats in self.url_stats.items() 
                 if (stats['client_error_count'] + stats['server_error_count'] + 
                     stats['timeout_count'] + stats['unknown_count']) > 0]
        errors.sort(key=lambda x: (x[1]['client_error_count'] + x[1]['server_error_count'] + 
                                   x[1]['timeout_count'] + x[1]['unknown_count']), reverse=True)
        
        if errors:
            print(f"\n{'Count':<8} {'Error Rate':<15} {'URL'}")
            print("-"*100)
            for url, stats in errors:
                total = stats['total_count']
                total_errors = (stats['client_error_count'] + stats['server_error_count'] + 
                              stats['timeout_count'] + stats['unknown_count'])
                rate = (total_errors / total * 100) if total > 0 else 0
                print(f"{total_errors:<8} {rate:>5.1f}% ({total_errors}/{total}){' '*3} {url}")
                
                # Show error breakdown
                if stats['client_error_count'] > 0:
                    print(f"{'':10}└─ {stats['client_error_count']} client errors (4xx)")
                if stats['server_error_count'] > 0:
                    print(f"{'':10}└─ {stats['server_error_count']} server errors (5xx)")
                if stats['timeout_count'] > 0:
                    print(f"{'':10}└─ {stats['timeout_count']} timeouts")
                if stats['unknown_count'] > 0:
                    print(f"{'':10}└─ {stats['unknown_count']} other errors")
                
                # Show most common status codes
                if stats['status_codes']:
                    common_codes = sorted(stats['status_codes'].items(), 
                                        key=lambda x: x[1], reverse=True)[:3]
                    codes_str = ", ".join([f"{code}: {count}x" for code, count in common_codes])
                    print(f"{'':10}└─ Status codes: {codes_str}")
                
                print()  # Empty line between URLs
        else:
            print("\n✅ No errors found!")
        
        # Summary statistics
        print("="*100)
        print("📊 SUMMARY STATISTICS")
        print("="*100)
        
        total_requests = sum(s['total_count'] for s in self.url_stats.values())
        total_success = sum(s['success_count'] for s in self.url_stats.values())
        total_client_errors = sum(s['client_error_count'] for s in self.url_stats.values())
        total_server_errors = sum(s['server_error_count'] for s in self.url_stats.values())
        total_timeouts = sum(s['timeout_count'] for s in self.url_stats.values())
        total_errors = total_client_errors + total_server_errors + total_timeouts
        
        print(f"\n{'Metric':<30} {'Count':<15} {'Percentage'}")
        print("-"*100)
        print(f"{'Total URLs observed':<30} {len(self.url_stats):<15} {'-'}")
        print(f"{'Total requests':<30} {total_requests:<15} {100.0:.1f}%")
        print(f"{'Successful (2xx)':<30} {total_success:<15} {(total_success/total_requests*100 if total_requests > 0 else 0):.1f}%")
        print(f"{'Client errors (4xx)':<30} {total_client_errors:<15} {(total_client_errors/total_requests*100 if total_requests > 0 else 0):.1f}%")
        print(f"{'Server errors (5xx)':<30} {total_server_errors:<15} {(total_server_errors/total_requests*100 if total_requests > 0 else 0):.1f}%")
        print(f"{'Timeouts':<30} {total_timeouts:<15} {(total_timeouts/total_requests*100 if total_requests > 0 else 0):.1f}%")
        print(f"{'Total errors':<30} {total_errors:<15} {(total_errors/total_requests*100 if total_requests > 0 else 0):.1f}%")
        
        # Reliability score
        reliability = (total_success / total_requests * 100) if total_requests > 0 else 0
        print("\n" + "="*100)
        print(f"🎯 OVERALL BACKEND RELIABILITY: {reliability:.2f}%")
        if reliability >= 95:
            print("   Status: ✅ EXCELLENT")
        elif reliability >= 80:
            print("   Status: ✅ GOOD")
        elif reliability >= 60:
            print("   Status: ⚠️  NEEDS IMPROVEMENT")
        else:
            print("   Status: ❌ POOR - CRITICAL ISSUES")
        print("="*100)
    
    def save_report(self, output_file=None):
        """Save report to a text file"""
        if output_file is None:
            output_file = self.log_file.with_suffix('.analysis.txt')
        
        # Redirect stdout to file
        original_stdout = sys.stdout
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                sys.stdout = f
                self.print_report()
            sys.stdout = original_stdout
            print(f"\n💾 Report saved to: {output_file}")
            return True
        except Exception as e:
            sys.stdout = original_stdout
            print(f"❌ Error saving report: {e}")
            return False

def main():
    print("="*100)
    print("🔒 SECURE LOCAL LOG ANALYZER")
    print("="*100)
    print("✓ 100% offline processing - no network access")
    print("✓ All data stays on your computer")
    print("✓ Completely confidential")
    print("="*100)
    
    # Get log file from command line or prompt
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
    else:
        print("\nPlease provide a log file:")
        print("Usage: python log_analyzer.py your_logfile.log")
        print("\nOr enter the path now:")
        log_file = input("Log file path: ").strip().strip('"\'')
        
        if not log_file:
            print("❌ No file provided. Exiting.")
            sys.exit(1)
    
    try:
        # Create analyzer and run
        analyzer = SecureLogAnalyzer(log_file)
        analyzer.analyze()
        analyzer.print_report()
        
        # Ask if user wants to save report
        print("\n" + "="*100)
        save = input("\n💾 Save report to file? (y/n): ").strip().lower()
        if save in ['y', 'yes']:
            analyzer.save_report()
        
        print("\n✅ Analysis complete!")
        print("🔒 All data remained local - nothing was sent anywhere.")
        
    except FileNotFoundError as e:
        print(f"\n❌ {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Analysis interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

