#!/usr/bin/env python3
"""
Root Cause Analyzer for Backend Communication Errors
Identifies the underlying reasons for communication failures

Usage: python root_cause_analyzer.py logfile.log
"""

import re
import sys
from collections import defaultdict, Counter
from pathlib import Path

class RootCauseAnalyzer:
    """Analyzes logs to identify root causes of communication errors"""
    
    def __init__(self, log_file):
        self.log_file = Path(log_file)
        if not self.log_file.exists():
            raise FileNotFoundError(f"Log file not found: {log_file}")
        
        # Root cause categories
        self.root_causes = {
            'authentication': [],
            'not_found': [],
            'timeout': [],
            'server_crash': [],
            'network': [],
            'rate_limit': [],
            'bad_request': [],
            'permission': [],
            'service_unavailable': [],
            'unknown': []
        }
        
        self.error_messages = []
        self.error_details = defaultdict(list)
        self.url_errors = defaultdict(lambda: defaultdict(int))
        
    def analyze(self):
        """Analyze log file for root causes"""
        print("\n🔍 Analyzing root causes of errors...")
        
        url_pattern = r'(https?://[^\s\'"<>]+)'
        
        with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                if line_num % 5000 == 0:
                    print(f"  Processing line {line_num:,}...", end='\r')
                
                # Check if line contains error
                if not self._is_error_line(line):
                    continue
                
                # Extract URL
                url_matches = re.findall(url_pattern, line)
                url = url_matches[0].rstrip('.,;:)\'"') if url_matches else "Unknown URL"
                
                # Identify root cause
                root_cause = self._identify_root_cause(line)
                
                # Store error information
                error_info = {
                    'line_num': line_num,
                    'url': url,
                    'line': line.strip()[:200],
                    'root_cause': root_cause
                }
                
                self.root_causes[root_cause].append(error_info)
                self.url_errors[url][root_cause] += 1
                
                # Extract error message
                error_msg = self._extract_error_message(line)
                if error_msg:
                    self.error_messages.append(error_msg)
        
        print("  Analysis complete!                    ")
    
    def _is_error_line(self, line):
        """Check if line contains an error"""
        error_indicators = [
            'error', 'fail', 'exception', 'timeout', 'refused',
            '4[0-9][0-9]', '5[0-9][0-9]',  # 4xx and 5xx status codes
            'unable', 'cannot', 'denied', 'unauthorized'
        ]
        
        line_lower = line.lower()
        return any(re.search(indicator, line_lower) for indicator in error_indicators)
    
    def _identify_root_cause(self, line):
        """Identify the root cause from the error line"""
        line_lower = line.lower()
        
        # Authentication issues
        if any(keyword in line_lower for keyword in 
               ['401', 'unauthorized', 'auth', 'authentication', 'token', 'credentials']):
            return 'authentication'
        
        # Not found / wrong URL
        if any(keyword in line_lower for keyword in 
               ['404', 'not found', 'no route', 'endpoint', 'path not found']):
            return 'not_found'
        
        # Timeout issues
        if any(keyword in line_lower for keyword in 
               ['timeout', 'timed out', 'time out', 'deadline exceeded']):
            return 'timeout'
        
        # Server crashes / internal errors
        if any(keyword in line_lower for keyword in 
               ['500', 'internal server', 'crash', 'exception', 'stack trace', 'panic']):
            return 'server_crash'
        
        # Network issues
        if any(keyword in line_lower for keyword in 
               ['connection', 'refused', 'reset', 'unreachable', 'dns', 'resolve']):
            return 'network'
        
        # Rate limiting
        if any(keyword in line_lower for keyword in 
               ['429', 'rate limit', 'too many requests', 'throttle']):
            return 'rate_limit'
        
        # Bad request / malformed
        if any(keyword in line_lower for keyword in 
               ['400', 'bad request', 'invalid', 'malformed', 'parse error']):
            return 'bad_request'
        
        # Permission issues
        if any(keyword in line_lower for keyword in 
               ['403', 'forbidden', 'permission', 'denied', 'access denied']):
            return 'permission'
        
        # Service unavailable
        if any(keyword in line_lower for keyword in 
               ['503', 'service unavailable', 'unavailable', 'maintenance', 'overload']):
            return 'service_unavailable'
        
        return 'unknown'
    
    def _extract_error_message(self, line):
        """Extract the actual error message from the line"""
        # Common error message patterns
        patterns = [
            r'error[:\s]+([^,\n]+)',
            r'exception[:\s]+([^,\n]+)',
            r'failed[:\s]+([^,\n]+)',
            r'message[:\s]+["\']([^"\']+)["\']',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:150]
        
        return None
    
    def print_report(self):
        """Print detailed root cause analysis"""
        print("\n" + "="*100)
        print("🔍 ROOT CAUSE ANALYSIS OF ERRONEOUS COMMUNICATION")
        print("="*100)
        
        # Count by root cause
        root_cause_counts = {k: len(v) for k, v in self.root_causes.items() if v}
        total_errors = sum(root_cause_counts.values())
        
        if total_errors == 0:
            print("\n✅ No errors found in log file!")
            return
        
        # Sort by frequency
        sorted_causes = sorted(root_cause_counts.items(), key=lambda x: x[1], reverse=True)
        
        print(f"\n📊 TOTAL ERRORS ANALYZED: {total_errors}")
        print("\n" + "="*100)
        print("ROOT CAUSES SUMMARY")
        print("="*100)
        
        # Display each root cause
        for cause, count in sorted_causes:
            percentage = (count / total_errors * 100)
            
            cause_name = self._get_cause_display_name(cause)
            print(f"\n{'='*100}")
            print(f"🔴 {cause_name.upper()}")
            print(f"   Count: {count} errors ({percentage:.1f}%)")
            print(f"{'='*100}")
            
            # Show explanation
            explanation = self._get_cause_explanation(cause)
            print(f"\n📝 Explanation:")
            print(f"   {explanation}")
            
            # Show affected URLs (top 5)
            affected_urls = defaultdict(int)
            for error in self.root_causes[cause][:50]:  # Limit to first 50
                affected_urls[error['url']] += 1
            
            top_urls = sorted(affected_urls.items(), key=lambda x: x[1], reverse=True)[:5]
            
            if top_urls:
                print(f"\n🌐 Most Affected URLs:")
                for url, url_count in top_urls:
                    print(f"   {url_count:3d}x  {url}")
            
            # Show example error messages
            examples = [e for e in self.root_causes[cause] if e['line']][:3]
            if examples:
                print(f"\n💬 Example Error Messages:")
                for i, example in enumerate(examples, 1):
                    print(f"   {i}. Line {example['line_num']}: {example['line'][:120]}...")
            
            # Show resolution
            resolution = self._get_resolution_steps(cause)
            print(f"\n✅ Resolution Steps:")
            for step in resolution:
                print(f"   • {step}")
        
        # Summary recommendations
        print("\n" + "="*100)
        print("🎯 PRIMARY ROOT CAUSES (Top 3)")
        print("="*100)
        
        for i, (cause, count) in enumerate(sorted_causes[:3], 1):
            percentage = (count / total_errors * 100)
            cause_name = self._get_cause_display_name(cause)
            print(f"\n{i}. {cause_name}: {count} errors ({percentage:.1f}%)")
            print(f"   Priority: {'🔴 CRITICAL' if percentage > 30 else '🟡 HIGH' if percentage > 10 else '🟢 MEDIUM'}")
        
        print("\n" + "="*100)
        print("💡 OVERALL RECOMMENDATIONS")
        print("="*100)
        self._print_overall_recommendations(sorted_causes)
    
    def _get_cause_display_name(self, cause):
        """Get readable name for root cause"""
        names = {
            'authentication': 'Authentication Failures',
            'not_found': 'Resource Not Found (404)',
            'timeout': 'Connection Timeouts',
            'server_crash': 'Server Internal Errors',
            'network': 'Network Connectivity Issues',
            'rate_limit': 'Rate Limiting / Throttling',
            'bad_request': 'Bad Request / Malformed Data',
            'permission': 'Permission Denied',
            'service_unavailable': 'Service Unavailable',
            'unknown': 'Unknown / Other Errors'
        }
        return names.get(cause, cause.title())
    
    def _get_cause_explanation(self, cause):
        """Get explanation for the root cause"""
        explanations = {
            'authentication': 'Requests are failing because of invalid or expired authentication credentials (tokens, API keys, passwords).',
            'not_found': 'The requested URLs do not exist. This indicates wrong endpoints, typos in URLs, or deprecated API paths.',
            'timeout': 'Requests are taking too long to complete and timing out. This could be due to slow servers, network issues, or overloaded backends.',
            'server_crash': 'Backend servers are crashing or encountering internal errors while processing requests.',
            'network': 'Network connectivity problems between client and server, including DNS failures, connection refused, or network unreachable.',
            'rate_limit': 'Too many requests are being sent in a short time period, causing the server to rate-limit or throttle requests.',
            'bad_request': 'Requests are malformed or contain invalid data that the server cannot process.',
            'permission': 'Client does not have sufficient permissions to access the requested resources.',
            'service_unavailable': 'Backend service is down for maintenance, overloaded, or temporarily unavailable.',
            'unknown': 'Errors that do not fit into other categories or lack sufficient information to determine the root cause.'
        }
        return explanations.get(cause, 'No explanation available.')
    
    def _get_resolution_steps(self, cause):
        """Get resolution steps for the root cause"""
        resolutions = {
            'authentication': [
                'Verify API keys and tokens are valid and not expired',
                'Check if authentication credentials are correctly configured',
                'Ensure authentication headers are properly formatted',
                'Refresh tokens if using OAuth or similar authentication'
            ],
            'not_found': [
                'Review and update API endpoint URLs',
                'Check API documentation for correct paths',
                'Verify API version being used is still supported',
                'Check for typos in URL configuration'
            ],
            'timeout': [
                'Increase timeout values in client configuration',
                'Check network connectivity and latency',
                'Investigate backend server performance',
                'Consider implementing retry logic with exponential backoff'
            ],
            'server_crash': [
                'Review backend server logs for crash details',
                'Check server resource usage (CPU, memory, disk)',
                'Investigate recent code changes or deployments',
                'Implement better error handling on backend'
            ],
            'network': [
                'Verify network connectivity between client and server',
                'Check DNS resolution is working correctly',
                'Review firewall rules and port accessibility',
                'Test with tools like ping, traceroute, or curl'
            ],
            'rate_limit': [
                'Reduce request frequency or implement rate limiting on client side',
                'Implement request queuing and throttling',
                'Contact backend team about rate limit increases',
                'Cache responses where possible to reduce requests'
            ],
            'bad_request': [
                'Validate request data format before sending',
                'Review API documentation for correct request structure',
                'Check data types and required fields',
                'Add request validation on client side'
            ],
            'permission': [
                'Verify user/service has correct permissions',
                'Review access control policies',
                'Check if IP whitelisting is required',
                'Contact administrator for proper access grants'
            ],
            'service_unavailable': [
                'Check if backend is under maintenance',
                'Monitor server health and uptime',
                'Implement fallback mechanisms',
                'Set up health check endpoints'
            ],
            'unknown': [
                'Enable more detailed logging',
                'Capture full error messages and stack traces',
                'Review complete request/response cycle',
                'Contact backend support team for investigation'
            ]
        }
        return resolutions.get(cause, ['Investigate further to determine specific cause'])
    
    def _print_overall_recommendations(self, sorted_causes):
        """Print overall recommendations based on top causes"""
        if not sorted_causes:
            return
        
        top_cause = sorted_causes[0][0]
        
        print("\nBased on the analysis, immediate actions recommended:")
        print()
        
        if top_cause == 'authentication':
            print("1. 🔑 Review and update authentication credentials across all services")
            print("2. Implement automatic token refresh mechanism")
            print("3. Add authentication failure alerts")
        
        elif top_cause == 'not_found':
            print("1. 📝 Update API endpoint configuration with correct URLs")
            print("2. Review API documentation and version compatibility")
            print("3. Remove references to deprecated endpoints")
        
        elif top_cause == 'timeout':
            print("1. ⏱️  Investigate backend performance issues")
            print("2. Increase timeout values or optimize slow endpoints")
            print("3. Implement retry logic with exponential backoff")
        
        elif top_cause == 'server_crash':
            print("1. 🔥 URGENT: Investigate backend server crashes")
            print("2. Review server logs and error traces")
            print("3. Fix bugs causing server failures")
        
        elif top_cause == 'network':
            print("1. 🌐 Check network connectivity and DNS resolution")
            print("2. Review firewall and network configuration")
            print("3. Test connectivity from different network locations")
        
        print("\n4. 📊 Monitor the situation after implementing fixes")
        print("5. 🔄 Re-run this analysis to verify improvements")

def main():
    print("="*100)
    print("🔍 ROOT CAUSE ANALYZER FOR BACKEND ERRORS")
    print("="*100)
    print("Identifies why backend communications are failing")
    print("="*100)
    
    if len(sys.argv) < 2:
        print("\nUsage: python root_cause_analyzer.py logfile.log")
        sys.exit(1)
    
    try:
        analyzer = RootCauseAnalyzer(sys.argv[1])
        analyzer.analyze()
        analyzer.print_report()
        
        print("\n✅ Root cause analysis complete!")
        
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

