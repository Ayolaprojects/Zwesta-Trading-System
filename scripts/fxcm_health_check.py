import json
import socket
from pathlib import Path

import requests
from dotenv import load_dotenv


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / '.env')

    import fxcm_service
    import multi_broker_backend_updated as backend

    payload = {
        'username': 'D291208899',
        'login': 'D291208899',
        'password': 'Oaxm3',
        'server': 'demo',
    }

    diagnostics = {
        'candidate_base_urls': fxcm_service._candidate_base_urls(payload.get('server'), payload),
        'dns': [],
    }

    for base_url in diagnostics['candidate_base_urls']:
        host = base_url.split('://', 1)[-1]
        try:
            diagnostics['dns'].append({'base_url': base_url, 'host': host, 'addresses': socket.gethostbyname_ex(host)[2]})
        except Exception as exc:
            diagnostics['dns'].append({'base_url': base_url, 'host': host, 'error': str(exc)})

    try:
        resp = fxcm_service._fxcm_request(
            'GET',
            '/trading/get_model',
            payload=payload,
            params={'models': 'Account'},
            timeout=15,
            content_type=False,
        )
        diagnostics['rest'] = {
            'status_code': resp.status_code,
            'base_url': getattr(resp, 'fxcm_base_url', None),
            'excerpt': resp.text[:300],
        }
    except Exception as exc:
        diagnostics['rest'] = {'error': str(exc)}

    connection = backend.FXCMConnection(
        credentials={
            'username': payload['username'],
            'login': payload['login'],
            'password': payload['password'],
            'server': payload['server'],
            'is_live': False,
            'api_key': '',
            'base_url': payload.get('base_url', ''),
        }
    )
    connected = connection.connect()
    diagnostics['connection'] = {
        'connected': connected,
        'last_error': connection.last_error,
        'resolved_base_url': connection.base_url,
        'account_info': connection.get_account_info() if connected else {},
    }

    try:
        import forexconnect  # type: ignore
        diagnostics['forexconnect_installed'] = True
    except Exception as exc:
        diagnostics['forexconnect_installed'] = False
        diagnostics['forexconnect_error'] = str(exc)

    print(json.dumps(diagnostics, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())