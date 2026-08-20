class VpsConfig {
  VpsConfig({
    required this.vpsId,
    required this.userId,
    required this.vpsName,
    required this.vpsIp,
    required this.username,
    this.vpsPort = 3389,
    this.rdpPort = 3389,
    this.apiPort = 5000,
    this.password = '',
    this.mt5Path = r'C:\Program Files\MetaTrader 5\terminal64.exe',
    this.notes = '',
    this.status = 'disconnected',
    this.lastConnection,
    this.createdAt,
    this.updatedAt,
  });

  final String vpsId;
  final String userId;
  final String vpsName;
  final String vpsIp;
  final String username;
  final int vpsPort;
  final int rdpPort;
  final int apiPort;
  final String password;
  final String mt5Path;
  final String notes;
  final String status;
  final DateTime? lastConnection;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  factory VpsConfig.fromJson(Map<String, dynamic> json) {
    return VpsConfig(
      vpsId: (json['vps_id'] ?? '').toString(),
      userId: (json['user_id'] ?? '').toString(),
      vpsName: (json['vps_name'] ?? '').toString(),
      vpsIp: (json['vps_ip'] ?? '').toString(),
      username: (json['username'] ?? '').toString(),
      vpsPort: int.tryParse(json['vps_port']?.toString() ?? '3389') ?? 3389,
      rdpPort: int.tryParse(json['rdp_port']?.toString() ?? '3389') ?? 3389,
      apiPort: int.tryParse(json['api_port']?.toString() ?? '5000') ?? 5000,
      password: (json['password'] ?? json['password_encrypted'] ?? '').toString(),
      mt5Path: (json['mt5_path'] ?? json['mt5_path'] ?? r'C:\Program Files\MetaTrader 5\terminal64.exe').toString(),
      notes: (json['notes'] ?? '').toString(),
      status: (json['status'] ?? 'disconnected').toString(),
      lastConnection: _parseDateTime(json['last_connection']),
      createdAt: _parseDateTime(json['created_at']),
      updatedAt: _parseDateTime(json['updated_at']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'vps_id': vpsId,
      'vps_name': vpsName,
      'vps_ip': vpsIp,
      'vps_port': vpsPort,
      'username': username,
      if (password.isNotEmpty) 'password': password,
      'rdp_port': rdpPort,
      'api_port': apiPort,
      'mt5_path': mt5Path,
      'notes': notes,
    };
  }

  VpsConfig copyWith({
    String? vpsName,
    String? vpsIp,
    int? vpsPort,
    String? username,
    String? password,
    int? rdpPort,
    int? apiPort,
    String? mt5Path,
    String? notes,
    String? status,
    DateTime? lastConnection,
  }) {
    return VpsConfig(
      vpsId: vpsId,
      userId: userId,
      vpsName: vpsName ?? this.vpsName,
      vpsIp: vpsIp ?? this.vpsIp,
      username: username ?? this.username,
      vpsPort: vpsPort ?? this.vpsPort,
      rdpPort: rdpPort ?? this.rdpPort,
      apiPort: apiPort ?? this.apiPort,
      password: password ?? this.password,
      mt5Path: mt5Path ?? this.mt5Path,
      notes: notes ?? this.notes,
      status: status ?? this.status,
      lastConnection: lastConnection ?? this.lastConnection,
      createdAt: createdAt,
      updatedAt: updatedAt,
    );
  }
}

class VpsStatus {
  VpsStatus({
    required this.vpsId,
    required this.vpsName,
    required this.vpsIp,
    required this.connectionStatus,
    this.lastConnection,
    this.mt5Status = 'offline',
    this.backendRunning = false,
    this.cpuUsage = 0.0,
    this.memoryUsage = 0.0,
    this.uptimeHours = 0,
    this.activeBots = 0,
    this.totalValueLocked = 0.0,
    this.lastCheck,
  });

  final String vpsId;
  final String vpsName;
  final String vpsIp;
  final String connectionStatus;
  final DateTime? lastConnection;
  final String mt5Status;
  final bool backendRunning;
  final double cpuUsage;
  final double memoryUsage;
  final int uptimeHours;
  final int activeBots;
  final double totalValueLocked;
  final DateTime? lastCheck;

  bool get isOnline => connectionStatus == 'connected' || backendRunning;

  factory VpsStatus.fromJson(Map<String, dynamic> json) {
    return VpsStatus(
      vpsId: (json['vps_id'] ?? '').toString(),
      vpsName: (json['vps_name'] ?? '').toString(),
      vpsIp: (json['vps_ip'] ?? '').toString(),
      connectionStatus: (json['connection_status'] ?? json['status'] ?? 'disconnected').toString(),
      lastConnection: _parseDateTime(json['last_connection']),
      mt5Status: (json['mt5_status'] ?? 'offline').toString(),
      backendRunning: bool.tryParse(json['backend_running']?.toString() ?? 'false') ?? false,
      cpuUsage: double.tryParse(json['cpu_usage']?.toString() ?? '0') ?? 0.0,
      memoryUsage: double.tryParse(json['memory_usage']?.toString() ?? '0') ?? 0.0,
      uptimeHours: int.tryParse(json['uptime_hours']?.toString() ?? '0') ?? 0,
      activeBots: int.tryParse(json['active_bots']?.toString() ?? '0') ?? 0,
      totalValueLocked: double.tryParse(json['total_value_locked']?.toString() ?? '0') ?? 0.0,
      lastCheck: _parseDateTime(json['last_check']),
    );
  }

  Map<String, dynamic> toJson() => {
    'vps_id': vpsId,
    'vps_name': vpsName,
    'vps_ip': vpsIp,
    'connection_status': connectionStatus,
    'mt5_status': mt5Status,
    'backend_running': backendRunning,
    'cpu_usage': cpuUsage,
    'memory_usage': memoryUsage,
    'uptime_hours': uptimeHours,
    'active_bots': activeBots,
    'total_value_locked': totalValueLocked,
  };
}

class VpsRemoteAccess {
  VpsRemoteAccess({
    required this.vpsName,
    required this.rdpServer,
    required this.rdpPort,
    required this.username,
    required this.connectionString,
    required this.instructions,
  });

  final String vpsName;
  final String rdpServer;
  final int rdpPort;
  final String username;
  final String connectionString;
  final List<String> instructions;

  factory VpsRemoteAccess.fromJson(Map<String, dynamic> json) {
    return VpsRemoteAccess(
      vpsName: (json['vps_name'] ?? '').toString(),
      rdpServer: (json['rdp_server'] ?? '').toString(),
      rdpPort: int.tryParse(json['rdp_port']?.toString() ?? '3389') ?? 3389,
      username: (json['username'] ?? '').toString(),
      connectionString: (json['connection_string'] ?? '').toString(),
      instructions: (json['instructions'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
    );
  }
}

DateTime? _parseDateTime(dynamic value) {
  final text = value?.toString().trim() ?? '';
  if (text.isEmpty) return null;
  return DateTime.tryParse(text);
}
