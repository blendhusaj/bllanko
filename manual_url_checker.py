#!/usr/bin/env python3
"""
Manual URL Checker - Simple tool to manually identify successful vs erroneous URLs
Usage: python manual_url_checker.py your_logfile.log
"""

import re
import sys
from pathlib import Path

def check_url_status():
    """Simple manual URL status checker"""
    
    if len(sys.argv) < 2:
        print("Usage: python manual_url_checker.py your_logfile.log")
        return
    
    log_file = Path(sys.argv[1])
    if not log_file.exists():
        print(f"❌ Log file not found: {log_file}")
        return
    
    print("="*80)
    print("🔍 MANUAL URL STATUS CHECKER")
    print("="*80)
    print(f"📁 File: {log_file}")
    print("\nSearching for URLs with success/error indicators...")
    
    # URL pattern
    url_pattern = r'(https?://[^\s\'"<>\[\]]+)'
    
    successful_urls = set()
    error_urls = set()
    
    # Success indicators
    success_patterns = [
        r'\b20[0-9]\b',  # HTTP 2xx
        r'\bsuccess\b',
        r'\bcompleted\b',
        r'\baccepted\b',
        r'\bok\b',
        r'CAI registration successful'
    ]
    
    # Error indicators
    error_patterns = [
        r'\b[45][0-9][0-9]\b',  # HTTP 4xx/5xx
        r'\berror\b',
        r'\bfailed\b',
        r'\btimeout\b',
        r'\bexception\b',
        r'\bdenied\b',
        r'\brefused\b',
        r'\bunreachable\b',
        r'\bnot found\b'
    ]
    
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                if line_num % 1000 == 0:
                    print(f"  Processed {line_num:,} lines...", end='\r')
                
                # Find URLs in line
                urls = re.findall(url_pattern, line)
                if not urls:
                    continue
                
                # Clean URLs
                cleaned_urls = []
                for url in urls:
                    url = url.rstrip('.,;:)\'"[]')
                    if len(url) > 10 and 'http' in url:
                        cleaned_urls.append(url)
                
                if not cleaned_urls:
                    continue
                
                line_lower = line.lower()
                
                # Check for success indicators
                is_success = any(re.search(pattern, line_lower) for pattern in success_patterns)
                
                # Check for error indicators  
                is_error = any(re.search(pattern, line_lower) for pattern in error_patterns)
                
                # Categorize URLs
                for url in cleaned_urls:
                    if is_success:
                        successful_urls.add(url)
                    elif is_error:
                        error_urls.add(url)
        
        print(f"  Processed {line_num:,} lines - Done!        ")
        
        # Print results
        print("\n" + "="*80)
        print("✅ SUCCESSFUL BACKEND COMMUNICATION")
        print("="*80)
        
        if successful_urls:
            for url in sorted(successful_urls):
                print(f"✅ {url}")
        else:
            print("⚠️  No successful URLs found")
        
        print("\n" + "="*80)
        print("❌ ERRONEOUS BACKEND COMMUNICATION")
        print("="*80)
        
        if error_urls:
            for url in sorted(error_urls):
                print(f"❌ {url}")
        else:
            print("✅ No error URLs found")
        
        print("\n" + "="*80)
        print("📊 SUMMARY")
        print("="*80)
        print(f"Successful URLs: {len(successful_urls)}")
        print(f"Error URLs: {len(error_urls)}")
        print(f"Total unique URLs: {len(successful_urls) + len(error_urls)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_url_status()
