#!/usr/bin/env python3
"""
Clean Log Viewer - Shows URLs and errors in a readable format
Usage: python clean_log_viewer.py logfile.log
"""

import re
import sys
from collections import defaultdict
from pathlib import Path

class CleanLogViewer:
    def __init__(self, log_file):
        self.log_file = Path(log_file)
        if not self.log_file.exists():
            raise FileNotFoundError(f"Log file not found: {log_file}")
        
        self.url_stats = defaultdict(lambda: {
            'success': 0,
            'errors': 0,
            'total': 0,
            'error_types': defaultdict(int),
            'error_examples': []
        })
    
    def clean_url(self, url):
        """Clean and normalize URLs"""
        # Remove trailing punctuation
        url = url.rstrip('.,;:)\'"[]')
        
        # Fix common issues
        url = re.sub(r':443\].*$', ':443', url)  # Remove garbage after port
        url = re.sub(r'\[.*$', '', url)  # Remove any [brackets] at end
        
        return url
    
    def analyze(self):
        """Analyze log file"""
        print("\n🔍 Analyzing log file...")
        
        url_pattern = r'(https?://[^\s\'"<>\[\]]+)'
        status_pattern = r'\b(\d{3})\b'
        
        with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                if line_num % 5000 == 0:
                    print(f"  Processing line {line_num:,}...", end='\r')
                
                # Find URLs
                url_matches = re.findall(url_pattern, line)
                if not url_matches:
                    continue
                
                for url in url_matches:
                    url = self.clean_url(url)
                    
                    # Skip if URL is too short or invalid
                    if len(url) < 10:
                        continue
                    
                    self.url_stats[url]['total'] += 1
                    
                    # Check for success
                    if re.search(r'\b(200|201|202|204|success|OK)\b', line, re.IGNORECASE):
                        self.url_stats[url]['success'] += 1
                    
                    # Check for errors
                    if re.search(r'\b(4\d{2}|5\d{2}|error|fail|timeout)\b', line, re.IGNORECASE):
                        self.url_stats[url]['errors'] += 1
                        
                        # Get status code
                        status_match = re.search(status_pattern, line)
                        if status_match:
                            code = int(status_match.group(1))
                            if 400 <= code < 600:
                                self.url_stats[url]['error_types'][code] += 1
                        
                        # Store example (limit to 3)
                        if len(self.url_stats[url]['error_examples']) < 3:
                            error_snippet = line.strip()[:150]
                            self.url_stats[url]['error_examples'].append(error_snippet)
        
        print("  Analysis complete!                    ")
    
    def print_clean_report(self):
        """Print a clean, readable report"""
        print("\n" + "="*120)
        print("CLEAN LOG ANALYSIS REPORT")
        print("="*120)
        
        # Successful URLs
        print("\n" + "="*120)
        print("✅ SUCCESSFUL BACKEND COMMUNICATION")
        print("="*120)
        
        successful = [(url, stats) for url, stats in self.url_stats.items() if stats['success'] > 0]
        successful.sort(key=lambda x: x[1]['success'], reverse=True)
        
        if successful:
            print(f"\n{'Success Count':<15} {'Total':<10} {'Rate':<10} URL")
            print("-"*120)
            for url, stats in successful:
                success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
                print(f"{stats['success']:<15} {stats['total']:<10} {success_rate:>5.1f}%    {url}")
        else:
            print("\n⚠️  No successful communications found")
        
        # Error URLs
        print("\n" + "="*120)
        print("❌ ERRONEOUS BACKEND COMMUNICATION")
        print("="*120)
        
        errors = [(url, stats) for url, stats in self.url_stats.items() if stats['errors'] > 0]
        errors.sort(key=lambda x: x[1]['errors'], reverse=True)
        
        if errors:
            print(f"\n{'Error Count':<15} {'Total':<10} {'Rate':<10} URL")
            print("-"*120)
            for url, stats in errors:
                error_rate = (stats['errors'] / stats['total'] * 100) if stats['total'] > 0 else 0
                print(f"{stats['errors']:<15} {stats['total']:<10} {error_rate:>5.1f}%    {url}")
                
                # Show error types
                if stats['error_types']:
                    error_codes = ", ".join([f"{code}: {count}x" for code, count in 
                                           sorted(stats['error_types'].items())])
                    print(f"{'':38}Error codes: {error_codes}")
                
                # Show one example
                if stats['error_examples']:
                    print(f"{'':38}Example: {stats['error_examples'][0]}")
                
                print()  # Empty line between URLs
        else:
            print("\n✅ No errors found!")
        
        # Summary
        print("="*120)
        print("📊 SUMMARY")
        print("="*120)
        
        total_urls = len(self.url_stats)
        total_requests = sum(s['total'] for s in self.url_stats.values())
        total_success = sum(s['success'] for s in self.url_stats.values())
        total_errors = sum(s['errors'] for s in self.url_stats.values())
        
        print(f"\nTotal unique URLs: {total_urls}")
        print(f"Total requests: {total_requests}")
        print(f"Successful: {total_success} ({total_success/total_requests*100:.1f}%)")
        print(f"Failed: {total_errors} ({total_errors/total_requests*100:.1f}%)")
        
        reliability = (total_success / total_requests * 100) if total_requests > 0 else 0
        print(f"\n🎯 Overall Reliability: {reliability:.2f}%")
        
        if reliability >= 95:
            print("   Status: ✅ EXCELLENT")
        elif reliability >= 80:
            print("   Status: ✅ GOOD")
        elif reliability >= 60:
            print("   Status: ⚠️  NEEDS IMPROVEMENT")
        else:
            print("   Status: ❌ POOR - CRITICAL ISSUES")
    
    def export_to_file(self, output_file=None):
        """Export clean report to text file"""
        if output_file is None:
            output_file = self.log_file.with_suffix('.clean_analysis.txt')
        
        original_stdout = sys.stdout
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                sys.stdout = f
                self.print_clean_report()
            sys.stdout = original_stdout
            print(f"\n💾 Clean report saved to: {output_file}")
            return True
        except Exception as e:
            sys.stdout = original_stdout
            print(f"❌ Error saving report: {e}")
            return False
    
    def export_urls_only(self):
        """Export just the URLs in clean format"""
        output_file = self.log_file.with_suffix('.urls_only.txt')
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("="*120 + "\n")
                f.write("SUCCESSFUL URLS\n")
                f.write("="*120 + "\n\n")
                
                successful = [(url, stats) for url, stats in self.url_stats.items() if stats['success'] > 0]
                successful.sort(key=lambda x: x[1]['success'], reverse=True)
                
                for url, stats in successful:
                    f.write(f"{url}\n")
                    f.write(f"  Success: {stats['success']}/{stats['total']} requests\n\n")
                
                f.write("\n" + "="*120 + "\n")
                f.write("ERROR URLS\n")
                f.write("="*120 + "\n\n")
                
                errors = [(url, stats) for url, stats in self.url_stats.items() if stats['errors'] > 0]
                errors.sort(key=lambda x: x[1]['errors'], reverse=True)
                
                for url, stats in errors:
                    f.write(f"{url}\n")
                    f.write(f"  Errors: {stats['errors']}/{stats['total']} requests\n")
                    if stats['error_types']:
                        error_codes = ", ".join([f"{code}: {count}x" for code, count in 
                                               sorted(stats['error_types'].items())])
                        f.write(f"  Error codes: {error_codes}\n")
                    f.write("\n")
            
            print(f"💾 Clean URLs saved to: {output_file}")
            return True
        except Exception as e:
            print(f"❌ Error saving URLs: {e}")
            return False

def main():
    print("="*120)
    print("🔍 CLEAN LOG VIEWER")
    print("="*120)
    print("Displays URLs and errors in a clean, readable format")
    print("="*120)
    
    if len(sys.argv) < 2:
        print("\nUsage: python clean_log_viewer.py logfile.log")
        sys.exit(1)
    
    try:
        viewer = CleanLogViewer(sys.argv[1])
        viewer.analyze()
        viewer.print_clean_report()
        
        print("\n" + "="*120)
        save = input("\n💾 Save clean report to file? (y/n): ").strip().lower()
        if save in ['y', 'yes']:
            viewer.export_to_file()
            viewer.export_urls_only()
        
        print("\n✅ Done!")
        
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

