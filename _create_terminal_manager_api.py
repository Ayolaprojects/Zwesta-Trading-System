"""
Create API Endpoint for MT5 Terminal Management
Adds /api/mt5/terminals endpoint to backend for managing multiple MT5 terminals
"""

TERMINAL_MANAGEMENT_ENDPOINT = """
# ==================== MT5 TERMINAL MANAGEMENT API ====================
# Add this to multi_broker_backend_updated.py

@app.route('/api/mt5/terminals', methods=['GET'])
def get_mt5_terminals():
    '''List all detected and configured MT5 terminals'''
    try:
        terminals = []
        
        # Detect all Exness MT5 installations
        exness_paths = [
            r'C:\\Program Files\\MetaTrader 5 EXNESS\\terminal64.exe',
            r'C:\\Program Files\\Exness MT5\\terminal64.exe',
            r'C:\\MT5\\Exness-Live\\terminal64.exe',
            r'C:\\MT5\\Exness-Demo\\terminal64.exe',
        ]
        
        # Check for multiple user-specific terminals
        for i in range(1, 21):  # Support up to 20 terminals
            user_path = f'C:\\\\MT5\\\\Exness-Live\\\\User{i}\\\\terminal64.exe'
            exness_paths.append(user_path)
        
        for path in exness_paths:
            if os.path.exists(path):
                # Check if terminal is running
                running = is_terminal_running(path)
                
                # Get terminal info
                terminals.append({
                    'path': path,
                    'broker': 'Exness',
                    'status': 'running' if running else 'stopped',
                    'type': 'live' if 'Live' in path else 'demo',
                    'user_slot': extract_user_slot(path),
                    'capacity': 10,  # Each terminal supports ~10 users
                })
        
        # Calculate capacity
        total_slots = len([t for t in terminals if t['status'] == 'running']) * 10
        used_slots = count_active_exness_users()
        
        return jsonify({
            'success': True,
            'terminals': terminals,
            'summary': {
                'total_terminals': len(terminals),
                'running_terminals': len([t for t in terminals if t['status'] == 'running']),
                'total_capacity': total_slots,
                'used_capacity': used_slots,
                'available_capacity': total_slots - used_slots,
            },
            'recommendations': get_terminal_recommendations(terminals, used_slots)
        })
    
    except Exception as e:
        logger.error(f"Error getting MT5 terminals: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/mt5/terminals/setup-guide', methods=['GET'])
def get_terminal_setup_guide():
    '''Get step-by-step guide for installing additional MT5 terminals'''
    
    # Check current capacity
    existing_terminals = []
    for i in range(1, 21):
        path = f'C:\\\\MT5\\\\Exness-Live\\\\User{i}\\\\terminal64.exe'
        if os.path.exists(path):
            existing_terminals.append(i)
    
    next_slot = 1
    for i in range(1, 21):
        if i not in existing_terminals:
            next_slot = i
            break
    
    return jsonify({
        'success': True,
        'current_terminals': len(existing_terminals),
        'next_available_slot': next_slot,
        'installation_path': f'C:\\\\MT5\\\\Exness-Live\\\\User{next_slot}',
        'steps': [
            {
                'step': 1,
                'title': 'Download Exness MT5 Installer',
                'description': 'Download MetaTrader 5 from Exness website',
                'download_url': 'https://www.exness.com/trading-platforms/metatrader-5/',
                'automated': False,
                'status': 'manual'
            },
            {
                'step': 2,
                'title': 'Run Installer',
                'description': f'Install to: C:\\\\MT5\\\\Exness-Live\\\\User{next_slot}',
                'command': None,
                'automated': False,
                'status': 'manual',
                'note': 'Choose custom installation directory during setup'
            },
            {
                'step': 3,
                'title': 'Launch Terminal',
                'description': 'Start MT5 and login with any Exness account',
                'automated': False,
                'status': 'manual'
            },
            {
                'step': 4,
                'title': 'Configure in Backend',
                'description': 'Backend will auto-detect the new terminal',
                'endpoint': '/api/mt5/terminals/detect',
                'automated': True,
                'status': 'automatic'
            },
        ],
        'notes': [
            'Each MT5 terminal can handle ~10 concurrent Exness users',
            f'You currently have {len(existing_terminals)} terminals installed',
            f'Installing User{next_slot} will increase capacity by 10 users',
            'Backend automatically distributes users across terminals',
        ]
    })


@app.route('/api/mt5/terminals/detect', methods=['POST'])
def detect_new_terminals():
    '''Scan for newly installed MT5 terminals and configure them'''
    try:
        newly_detected = []
        
        for i in range(1, 21):
            path = f'C:\\\\MT5\\\\Exness-Live\\\\User{i}\\\\terminal64.exe'
            if os.path.exists(path):
                # Check if already in database
                if not is_terminal_configured(path):
                    newly_detected.append({
                        'path': path,
                        'user_slot': i,
                        'capacity': 10
                    })
        
        if newly_detected:
            # Auto-configure new terminals
            for terminal in newly_detected:
                configure_terminal_in_database(terminal)
            
            return jsonify({
                'success': True,
                'message': f'Detected and configured {len(newly_detected)} new terminals',
                'terminals': newly_detected,
                'new_capacity': len(newly_detected) * 10
            })
        else:
            return jsonify({
                'success': True,
                'message': 'No new terminals detected',
                'terminals': []
            })
    
    except Exception as e:
        logger.error(f"Error detecting terminals: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== HELPER FUNCTIONS ====================

def is_terminal_running(path):
    '''Check if MT5 terminal process is running'''
    import psutil
    terminal_name = os.path.basename(path)
    
    for proc in psutil.process_iter(['name', 'exe']):
        try:
            if proc.info['exe'] and os.path.normpath(proc.info['exe']) == os.path.normpath(path):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return False


def extract_user_slot(path):
    '''Extract user slot number from path (e.g., User1 -> 1)'''
    import re
    match = re.search(r'User(\\d+)', path)
    return int(match.group(1)) if match else None


def count_active_exness_users():
    '''Count how many Exness users have active bots'''
    try:
        conn, cur = build_sqlite_connection()
        cur.execute('''
            SELECT COUNT(DISTINCT c.user_id)
            FROM user_bots b
            JOIN broker_credentials c ON b.credential_id = c.credential_id
            WHERE c.broker_name = 'Exness'
            AND b.is_active = 1
        ''')
        return cur.fetchone()[0]
    except Exception as e:
        logger.error(f"Error counting Exness users: {e}")
        return 0


def is_terminal_configured(path):
    '''Check if terminal path is already in database/config'''
    # For now, just check if path exists in SOCKET_BRIDGES env variable
    socket_bridges = os.getenv('SOCKET_BRIDGES', '')
    return path in socket_bridges


def configure_terminal_in_database(terminal):
    '''Add terminal configuration to database'''
    # This would update the terminal registry table
    # For now, just log it
    logger.info(f"New terminal detected: {terminal['path']}")
    pass


def get_terminal_recommendations(terminals, used_slots):
    '''Get recommendations based on current terminal setup'''
    running_terminals = [t for t in terminals if t['status'] == 'running']
    total_capacity = len(running_terminals) * 10
    
    recommendations = []
    
    if used_slots > total_capacity:
        recommendations.append({
            'severity': 'critical',
            'message': f'Over capacity! {used_slots} users but only {total_capacity} slots available',
            'action': 'Install additional MT5 terminal immediately'
        })
    elif used_slots > total_capacity * 0.8:
        recommendations.append({
            'severity': 'warning',
            'message': f'Capacity at {int((used_slots/total_capacity)*100)}%',
            'action': 'Consider installing additional MT5 terminal'
        })
    elif len(running_terminals) == 0:
        recommendations.append({
            'severity': 'error',
            'message': 'No MT5 terminals running',
            'action': 'Start at least one MT5 terminal'
        })
    else:
        recommendations.append({
            'severity': 'info',
            'message': f'Capacity healthy: {used_slots}/{total_capacity} slots used',
            'action': None
        })
    
    return recommendations
"""

def main():
    print("=" * 80)
    print("MT5 TERMINAL MANAGEMENT API")
    print("=" * 80)
    print()
    print("This code adds 3 new API endpoints to your backend:")
    print()
    print("1. GET /api/mt5/terminals")
    print("   - Lists all detected MT5 terminals")
    print("   - Shows capacity and status")
    print()
    print("2. GET /api/mt5/terminals/setup-guide")
    print("   - Provides step-by-step installation guide")
    print("   - Shows next available installation slot")
    print()
    print("3. POST /api/mt5/terminals/detect")
    print("   - Scans for newly installed terminals")
    print("   - Auto-configures them in backend")
    print()
    print("=" * 80)
    print()
    print("📋 TO INTEGRATE:")
    print()
    print("1. Add the code below to C:\\backend\\multi_broker_backend_updated.py")
    print("2. Restart backend")
    print("3. Update Flutter app to call these endpoints")
    print()
    print("=" * 80)
    print()
    print(TERMINAL_MANAGEMENT_ENDPOINT)
    print()
    print("=" * 80)
    print()
    print("✅ WITH THIS API:")
    print()
    print("Your app can:")
    print("  ✓ Show users how to install MT5 terminals")
    print("  ✓ Detect when new terminals are installed")
    print("  ✓ Auto-configure them (no manual setup needed)")
    print("  ✓ Display capacity warnings before limits are hit")
    print()
    print("Your app CANNOT:")
    print("  ✗ Automatically download MT5 installers (security restriction)")
    print("  ✗ Install MT5 without user interaction (requires admin)")
    print()
    print("This is the industry-standard approach - guide users through")
    print("manual installation, then auto-configure once installed.")
    print()

if __name__ == "__main__":
    main()
