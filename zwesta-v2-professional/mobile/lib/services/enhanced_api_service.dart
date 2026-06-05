import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Enhanced API Service with comprehensive error handling, token refresh, and interceptors
class EnhancedApiService {
  static final EnhancedApiService _instance = EnhancedApiService._internal();
  
  late Dio _dio;
  final _secureStorage = const FlutterSecureStorage();
  
  factory EnhancedApiService() {
    return _instance;
  }
  
  EnhancedApiService._internal() {
    _initDio();
  }
  
  void _initDio() {
    _dio = Dio(
      BaseOptions(
        baseUrl: 'http://localhost:8000/api',
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(seconds: 30),
        sendTimeout: const Duration(seconds: 30),
      ),
    );
    
    // Add interceptors for token management and error handling
    _dio.interceptors.add(TokenInterceptor(_secureStorage, _dio));
    _dio.interceptors.add(ErrorInterceptor());
    _dio.interceptors.add(LoggingInterceptor());
  }
  
  // AUTHENTICATION
  Future<Map<String, dynamic>> login(String username, String password) async {
    try {
      final response = await _dio.post(
        '/auth/login',
        data: {'username': username, 'password': password},
      );
      
      // Validate response
      if (response.statusCode == 200 && response.data['token'] != null) {
        return {
          'success': true,
          'token': response.data['token'],
          'message': 'Login successful',
        };
      }
      
      return {
        'success': false,
        'message': response.data['message'] ?? 'Login failed',
      };
    } on DioException catch (e) {
      return _handleDioError(e);
    } catch (e) {
      return {
        'success': false,
        'message': 'Unexpected error: $e',
      };
    }
  }
  
  Future<Map<String, dynamic>> logout() async {
    try {
      await _dio.post('/auth/logout');
      await _secureStorage.delete(key: 'auth_token');
      return {'success': true};
    } catch (e) {
      await _secureStorage.delete(key: 'auth_token');
      return {'success': true}; // Always clear locally even if request fails
    }
  }
  
  // TRADING DATA
  Future<Map<String, dynamic>> getTrades({int page = 1, int limit = 20}) async {
    try {
      final response = await _dio.get(
        '/trades',
        queryParameters: {'page': page, 'limit': limit},
      );
      
      return {
        'success': true,
        'trades': response.data['trades'] ?? [],
        'total': response.data['total'] ?? 0,
      };
    } on DioException catch (e) {
      return _handleDioError(e);
    } catch (e) {
      return {
        'success': false,
        'message': 'Failed to fetch trades: $e',
        'trades': [],
      };
    }
  }
  
  Future<Map<String, dynamic>> getPositions() async {
    try {
      final response = await _dio.get('/positions');
      
      return {
        'success': true,
        'positions': response.data['positions'] ?? [],
      };
    } on DioException catch (e) {
      return _handleDioError(e);
    } catch (e) {
      return {
        'success': false,
        'message': 'Failed to fetch positions: $e',
        'positions': [],
      };
    }
  }
  
  Future<Map<String, dynamic>> closePosition(String positionId) async {
    try {
      final response = await _dio.post('/positions/$positionId/close');
      
      return {
        'success': response.statusCode == 200,
        'message': response.data['message'] ?? 'Position closed',
      };
    } on DioException catch (e) {
      return _handleDioError(e);
    } catch (e) {
      return {
        'success': false,
        'message': 'Failed to close position: $e',
      };
    }
  }
  
  // ERROR HANDLING
  Map<String, dynamic> _handleDioError(DioException error) {
    String message = 'An error occurred';
    
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
        message = 'Connection timeout. Check your internet connection.';
        break;
      case DioExceptionType.sendTimeout:
        message = 'Request timeout. Please try again.';
        break;
      case DioExceptionType.receiveTimeout:
        message = 'Response timeout. Please try again.';
        break;
      case DioExceptionType.badResponse:
        message = _handleHttpError(error.response?.statusCode);
        break;
      case DioExceptionType.cancel:
        message = 'Request was cancelled.';
        break;
      case DioExceptionType.unknown:
        if (error.error is SocketException) {
          message = 'No internet connection.';
        } else {
          message = 'Network error: ${error.message}';
        }
        break;
      default:
        message = error.message ?? 'Unknown error';
    }
    
    return {
      'success': false,
      'message': message,
      'statusCode': error.response?.statusCode,
    };
  }
  
  String _handleHttpError(int? statusCode) {
    switch (statusCode) {
      case 400:
        return 'Bad request. Please check your input.';
      case 401:
        return 'Unauthorized. Please login again.';
      case 403:
        return 'Access forbidden.';
      case 404:
        return 'Resource not found.';
      case 409:
        return 'Conflict. Please refresh and try again.';
      case 500:
        return 'Server error. Please try again later.';
      case 502:
      case 503:
      case 504:
        return 'Server unavailable. Please try again later.';
      default:
        return 'HTTP Error: $statusCode';
    }
  }
}

/// Interceptor for token management and automatic token refresh
class TokenInterceptor extends QueuedInterceptorsWrapper {
  final FlutterSecureStorage _secureStorage;
  final Dio _dio;
  bool _isRefreshing = false;
  
  TokenInterceptor(this._secureStorage, this._dio);
  
  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    try {
      final token = await _secureStorage.read(key: 'auth_token');
      if (token != null) {
        options.headers['Authorization'] = 'Bearer $token';
      }
    } catch (e) {
      debugPrint('Error reading token: $e');
    }
    
    return handler.next(options);
  }
  
  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    // Handle 401 - token expired
    if (err.response?.statusCode == 401) {
      if (!_isRefreshing) {
        _isRefreshing = true;
        
        try {
          final refreshed = await _refreshToken();
          if (refreshed) {
            // Retry original request
            final token = await _secureStorage.read(key: 'auth_token');
            err.requestOptions.headers['Authorization'] = 'Bearer $token';
            
            final response = await _dio.request(
              err.requestOptions.path,
              options: Options(
                method: err.requestOptions.method,
                headers: err.requestOptions.headers,
              ),
              data: err.requestOptions.data,
              queryParameters: err.requestOptions.queryParameters,
            );
            
            _isRefreshing = false;
            return handler.resolve(response);
          }
        } catch (e) {
          _isRefreshing = false;
          // Logout user if refresh fails
          await _secureStorage.delete(key: 'auth_token');
        }
      }
    }
    
    return handler.next(err);
  }
  
  Future<bool> _refreshToken() async {
    try {
      final response = await _dio.post('/auth/refresh');
      
      if (response.statusCode == 200) {
        final newToken = response.data['token'];
        await _secureStorage.write(key: 'auth_token', value: newToken);
        return true;
      }
      return false;
    } catch (e) {
      debugPrint('Token refresh failed: $e');
      return false;
    }
  }
}

/// Interceptor for logging API calls
class LoggingInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    debugPrint('🔵 REQUEST: ${options.method} ${options.path}');
    debugPrint('Headers: ${options.headers}');
    if (options.data != null) {
      debugPrint('Body: ${options.data}');
    }
    return handler.next(options);
  }
  
  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    debugPrint('🟢 RESPONSE: ${response.statusCode} ${response.requestOptions.path}');
    debugPrint('Data: ${response.data}');
    return handler.next(response);
  }
  
  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    debugPrint('🔴 ERROR: ${err.type} ${err.message}');
    debugPrint('Status Code: ${err.response?.statusCode}');
    return handler.next(err);
  }
}

/// Extension for user-friendly error messages
extension ErrorMessageX on Map<String, dynamic> {
  String get errorMessage => this['message'] ?? 'An error occurred';
  bool get isSuccess => this['success'] == true;
}

// USAGE EXAMPLE IN YOUR PROVIDER:
/*
class TradingProvider extends ChangeNotifier {
  final _apiService = EnhancedApiService();
  
  Future<void> fetchTrades() async {
    _isLoading = true;
    notifyListeners();
    
    try {
      final result = await _apiService.getTrades();
      
      if (result.isSuccess) {
        _trades = (result['trades'] as List)
            .map((t) => TradeModel.fromJson(t))
            .toList();
        _error = null;
      } else {
        _error = result.errorMessage;
      }
    } catch (e) {
      _error = 'Unexpected error: $e';
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }
}

// USAGE IN UI:
// Show error snackbar when error occurs
Consumer<TradingProvider>(
  builder: (context, provider, _) {
    if (provider.error != null) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(provider.error!),
            backgroundColor: Colors.red,
            duration: Duration(seconds: 5),
            action: SnackBarAction(
              label: 'Retry',
              onPressed: () => provider.fetchTrades(),
            ),
          ),
        );
      });
    }
    
    return SizedBox.shrink();
  },
)
*/
