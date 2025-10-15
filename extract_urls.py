#!/usr/bin/env python3
"""
URL Extractor - Extracts successful and error URLs from log files
Simple and clean output for manual review

Usage: python extract_urls.py logfile.log
"""

import re
import sys
from pathlib import Path
from collections import defaultdict

class URLExtractor:
    def __init__(self, log_file):
        self.log_file = Path(log_file)
        if not self.log_file.exists():
            raise FileNotFoundError(f"Log file not found: {log_file}")
        
        self.successful_urls = defaultdict(int)
        self.error_urls = defaultdict(int)
    
    def clean_url(self, url):
        """Clean URL from common artifacts"""
        # Remove @ at start
        url = url.lstrip('@')
        
        # Remove trailing punctuation
        url = url.rstrip('.,;:)\'"[]')
        
        # Fix HTML encoding
        url = url.replace('&amp;', '&')
        
        # Remove port artifacts
        url = re.sub(r':443\].*$', ':443', url)
        url = re.sub(r'\[.*$', '', url)
        
        return url
    
    def is_successful(self, line):
        """Check if line indicates success"""
        # HTTP 2xx status codes
        if re.search(r'\b20[0-9]\b', line):
            return True
        
        # Success keywords
        line_lower = line.lower()
        if any(word in line_lower for word in ['success', ' ok ', 'completed', 'accepted']):
            return True
        
        return False
    
    def is_error(self, line):
        """Check if line indicates error"""
        # HTTP 4xx/5xx status codes
        if re.search(r'\b[45][0-9][0-9]\b', line):
            return True
        
        # Android logcat error tag
        if re.match(r'^\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d+\s+\d+\s+\d+\s+E\s', line):
            return True
        
        # Error keywords
        line_lower = line.lower()
        error_keywords = [
            'error', 'fail', 'timeout', 'exception', 'denied', 
            'refused', 'unreachable', 'unavailable', 'not found'
        ]
        if any(word in line_lower for word in error_keywords):
            return True
        
        return False
    
    def extract_urls_from_line(self, line):
        """Extract all URLs from a line"""
        # URL pattern
        pattern = r'(https?://[^\s\'"<>\[\]]+)'
        urls = re.findall(pattern, line)
        
        # Clean and filter
        cleaned_urls = []
        for url in urls:
            url = self.clean_url(url)
            
            # Filter out invalid/placeholder URLs
            if len(url) < 10:
                continue
            if url in ['http://unused', 'http://localhost', 'http://test', 'https://mod3']:
                continue
            if not re.match(r'https?://[a-zA-Z0-9]', url):
                continue
            
            cleaned_urls.append(url)
        
        return cleaned_urls
    
    def analyze(self):
        """Analyze log file and extract URLs"""
        print("\n🔍 Extracting URLs from log file...")
        
        with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                if line_num % 5000 == 0:
                    print(f"  Processing line {line_num:,}...", end='\r')
                
                # Extract URLs
                urls = self.extract_urls_from_line(line)
                if not urls:
                    continue
                
                # Categorize
                is_success = self.is_successful(line)
                is_error = self.is_error(line)
                
                for url in urls:
                    if is_success:
                        self.successful_urls[url] += 1
                    elif is_error:
                        self.error_urls[url] += 1
        
        print("  Extraction complete!                    ")
    
    def print_report(self):
        """Print clean URL report"""
        print("\n" + "="*120)
        print("URL EXTRACTION REPORT")
        print("="*120)
        
        # Successful URLs
        print("\n" + "="*120)
        print("✅ SUCCESSFUL URLS")
        print("="*120)
        
        if self.successful_urls:
            sorted_success = sorted(self.successful_urls.items(), key=lambda x: x[1], reverse=True)
            
            print(f"\n{'Count':<10} URL")
            print("-"*120)
            
            for url, count in sorted_success:
                print(f"{count:<10} {url}")
            
            print(f"\nTotal unique successful URLs: {len(self.successful_urls)}")
        else:
            print("\n⚠️  No successful URLs found")
        
        # Error URLs
        print("\n" + "="*120)
        print("❌ ERROR URLS")
        print("="*120)
        
        if self.error_urls:
            sorted_errors = sorted(self.error_urls.items(), key=lambda x: x[1], reverse=True)
            
            print(f"\n{'Count':<10} URL")
            print("-"*120)
            
            for url, count in sorted_errors:
                print(f"{count:<10} {url}")
            
            print(f"\nTotal unique error URLs: {len(self.error_urls)}")
        else:
            print("\n⚠️  No error URLs found")
        
        # Summary
        print("\n" + "="*120)
        print("📊 SUMMARY")
        print("="*120)
        
        total_success_requests = sum(self.successful_urls.values())
        total_error_requests = sum(self.error_urls.values())
        total_requests = total_success_requests + total_error_requests
        
        if total_requests > 0:
            success_rate = (total_success_requests / total_requests * 100)
            print(f"\nTotal unique URLs: {len(self.successful_urls) + len(self.error_urls)}")
            print(f"Successful requests: {total_success_requests} ({success_rate:.1f}%)")
            print(f"Error requests: {total_error_requests} ({100-success_rate:.1f}%)")
        else:
            print("\n⚠️  No URL data found")
    
    def export_to_files(self):
        """Export URLs to separate text files"""
        # Export successful URLs
        success_file = self.log_file.with_suffix('.successful_urls.txt')
        try:
            with open(success_file, 'w', encoding='utf-8') as f:
                f.write("SUCCESSFUL URLS\n")
                f.write("="*80 + "\n\n")
                
                sorted_success = sorted(self.successful_urls.items(), key=lambda x: x[1], reverse=True)
                for url, count in sorted_success:
                    f.write(f"{url}\n")
                    f.write(f"  Count: {count} requests\n\n")
            
            print(f"\n💾 Successful URLs saved to: {success_file}")
        except Exception as e:
            print(f"❌ Error saving successful URLs: {e}")
        
        # Export error URLs
        error_file = self.log_file.with_suffix('.error_urls.txt')
        try:
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write("ERROR URLS\n")
                f.write("="*80 + "\n\n")
                
                sorted_errors = sorted(self.error_urls.items(), key=lambda x: x[1], reverse=True)
                for url, count in sorted_errors:
                    f.write(f"{url}\n")
                    f.write(f"  Count: {count} requests\n\n")
            
            print(f"💾 Error URLs saved to: {error_file}")
        except Exception as e:
            print(f"❌ Error saving error URLs: {e}")

def main():
    print("="*120)
    print("🔗 URL EXTRACTOR")
    print("="*120)
    print("Extracts successful and error URLs from log files")
    print("="*120)
    
    if len(sys.argv) < 2:
        print("\nUsage: python extract_urls.py logfile.log")
        sys.exit(1)
    
    try:
        extractor = URLExtractor(sys.argv[1])
        extractor.analyze()
        extractor.print_report()
        
        print("\n" + "="*120)
        save = input("\n💾 Save URLs to separate files? (y/n): ").strip().lower()
        if save in ['y', 'yes']:
            extractor.export_to_files()
        
        print("\n✅ URL extraction complete!")
        
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

