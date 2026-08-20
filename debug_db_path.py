import os, sys, types
os.environ['ZWESTA_SKIP_PYTHON_REEXEC'] = '1'
os.environ['DATABASE_BACKEND'] = 'sqlite'
os.environ['DATABASE_URL'] = ''
os.environ['DATABASE_PATH'] = os.path.join(r'C:\zwesta-trader\Zwesta Flutter App', 'zwesta_trading_test.db')
os.environ['USE_FLASK_DEV'] = '1'
os.environ['FLASK_DEBUG'] = '0'

sys.path.insert(0, os.getcwd())
import types
sys.modules['dotenv'] = types.SimpleNamespace(load_dotenv=lambda *args, **kwargs: None)
import multi_broker_backend_updated as backend
print('DB PATH ENV', os.getenv('DATABASE_PATH'))
print('BACKEND DATABASE_PATH', backend.DATABASE_PATH)
print('get_database_path()', backend.get_database_path())
print('using_postgres()', backend.using_postgres())
print('get_database_url()', backend.get_database_url())
print('db file exists', os.path.exists(os.getenv('DATABASE_PATH')))
