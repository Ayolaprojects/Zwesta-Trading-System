import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:provider/provider.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:dio/dio.dart';
import 'package:zwesta/providers/auth_provider.dart';

// Generate mocks: flutter pub run build_runner build
@GenerateMocks([FlutterSecureStorage, Dio])
void main() {
  group('AuthProvider Tests', () {
    late MockFlutterSecureStorage mockStorage;
    late AuthProvider authProvider;

    setUp(() {
      mockStorage = MockFlutterSecureStorage();
      authProvider = AuthProvider(storage: mockStorage);
    });

    // ==================== LOGIN TESTS ====================
    group('Login', () {
      test('Successfully logs in with valid credentials', () async {
        // Arrange
        const username = 'testuser';
        const password = 'TestPass123!';
        const expectedToken = 'test_jwt_token_123';

        // Mock storage to save token
        when(mockStorage.write(key: 'auth_token', value: expectedToken))
            .thenAnswer((_) async => null);

        // Act
        final result = await authProvider.login(username, password);

        // Assert
        expect(result, true);
        expect(authProvider.isAuthenticated, true);
        expect(authProvider.currentUser, isNotNull);
        
        // Verify storage was called
        verify(mockStorage.write(key: 'auth_token', value: anyNamed('value')))
            .called(1);
      });

      test('Login fails with invalid credentials', () async {
        // Arrange
        const username = 'wronguser';
        const password = 'wrong';

        // Act
        final result = await authProvider.login(username, password);

        // Assert
        expect(result, false);
        expect(authProvider.isAuthenticated, false);
        expect(authProvider.errorMessage, isNotEmpty);
      });

      test('Login shows error message on network failure', () async {
        // Arrange
        const username = 'testuser';
        const password = 'TestPass123!';

        // Mock API failure
        when(mockStorage.write(key: anyNamed('key'), value: anyNamed('value')))
            .thenThrow(Exception('Network error'));

        // Act
        final result = await authProvider.login(username, password);

        // Assert
        expect(result, false);
        expect(authProvider.errorMessage, contains('Network'));
      });
    });

    // ==================== TOKEN VALIDATION TESTS ====================
    group('Token Validation', () {
      test('Token is stored after successful login', () async {
        // Arrange
        const username = 'testuser';
        const password = 'TestPass123!';
        const token = 'jwt_token_xyz';

        when(mockStorage.write(key: 'auth_token', value: token))
            .thenAnswer((_) async => null);

        // Act
        await authProvider.login(username, password);

        // Assert
        verify(mockStorage.write(key: 'auth_token', value: token)).called(1);
      });

      test('Token is retrieved on app startup', () async {
        // Arrange
        const savedToken = 'existing_token_123';
        when(mockStorage.read(key: 'auth_token'))
            .thenAnswer((_) async => savedToken);

        // Act
        await authProvider.refreshToken();

        // Assert
        verify(mockStorage.read(key: 'auth_token')).called(1);
      });

      test('Logout clears stored token', () async {
        // Arrange - simulate logged in state
        const username = 'testuser';
        const password = 'TestPass123!';
        when(mockStorage.write(key: anyNamed('key'), value: anyNamed('value')))
            .thenAnswer((_) async => null);

        await authProvider.login(username, password);

        // Mock token deletion
        when(mockStorage.delete(key: 'auth_token'))
            .thenAnswer((_) async => null);

        // Act
        await authProvider.logout();

        // Assert
        expect(authProvider.isAuthenticated, false);
        verify(mockStorage.delete(key: 'auth_token')).called(1);
      });
    });

    // ==================== STATE MANAGEMENT TESTS ====================
    group('State Management', () {
      test('Initial state is not authenticated', () {
        expect(authProvider.isAuthenticated, false);
        expect(authProvider.currentUser, isNull);
        expect(authProvider.token, isNull);
      });

      test('Provider notifies listeners on login', () async {
        // Arrange
        var notifyCount = 0;
        authProvider.addListener(() => notifyCount++);

        // Act
        await authProvider.login('testuser', 'TestPass123!');

        // Assert
        expect(notifyCount, greaterThan(0));
      });

      test('Provider notifies listeners on logout', () async {
        // Arrange - login first
        when(mockStorage.write(key: anyNamed('key'), value: anyNamed('value')))
            .thenAnswer((_) async => null);
        await authProvider.login('testuser', 'TestPass123!');

        var notifyCount = 0;
        authProvider.addListener(() => notifyCount++);

        when(mockStorage.delete(key: 'auth_token'))
            .thenAnswer((_) async => null);

        // Act
        await authProvider.logout();

        // Assert
        expect(notifyCount, greaterThan(0));
      });
    });

    // ==================== ERROR HANDLING TESTS ====================
    group('Error Handling', () {
      test('Shows error message on connection failure', () async {
        // This test assumes connection error is properly handled
        // Mock connection failure scenario
        
        // Act
        await authProvider.login('user', 'pass');

        // Assert
        expect(authProvider.errorMessage.toLowerCase(), 
            anyOf(contains('connection'), contains('network'), contains('error')));
      });

      test('Clears error message on successful login', () async {
        // Arrange
        when(mockStorage.write(key: anyNamed('key'), value: anyNamed('value')))
            .thenAnswer((_) async => null);

        // Act
        await authProvider.login('testuser', 'TestPass123!');

        // Assert
        expect(authProvider.errorMessage, isEmpty);
      });

      test('Updates error message on login failure', () async {
        // Arrange
        final errorMsg = 'Invalid credentials';

        // Act
        await authProvider.login('wrong', 'wrong');

        // Assert
        expect(authProvider.errorMessage, isNotEmpty);
      });
    });
  });
}

// ==================== HELPER FUNCTIONS FOR TESTING ====================

/// Create a test user for testing
Map<String, dynamic> createTestUser({
  String username = 'testuser',
  String email = 'test@example.com',
  double balance = 1000.0,
}) {
  return {
    'id': 'user_123',
    'username': username,
    'email': email,
    'balance': balance,
    'created_at': DateTime.now().toIso8601String(),
  };
}

/// Create mock auth response
Map<String, dynamic> createMockAuthResponse({
  required String token,
  required Map<String, dynamic> user,
}) {
  return {
    'token': token,
    'user': user,
    'expires_in': 86400,
  };
}
