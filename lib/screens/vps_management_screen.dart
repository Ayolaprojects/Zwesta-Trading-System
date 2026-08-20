import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../models/vps_model.dart';
import '../services/vps_service.dart';
import '../widgets/logo_widget.dart';

class VpsManagementScreen extends StatefulWidget {
  const VpsManagementScreen({Key? key}) : super(key: key);

  @override
  State<VpsManagementScreen> createState() => _VpsManagementScreenState();
}

class _VpsManagementScreenState extends State<VpsManagementScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _refresh();
    });
  }

  Future<void> _refresh() async {
    await context.read<VpsService>().fetchVpsConfigs();
  }

  void _showAddEditDialog([VpsConfig? existing]) {
    final isEdit = existing != null;
    final nameController = TextEditingController(text: existing?.vpsName ?? '');
    final ipController = TextEditingController(text: existing?.vpsIp ?? '');
    final portController = TextEditingController(text: existing?.vpsPort.toString() ?? '3389');
    final usernameController = TextEditingController(text: existing?.username ?? '');
    final passwordController = TextEditingController(text: existing?.password ?? '');
    final rdpPortController = TextEditingController(text: existing?.rdpPort.toString() ?? '3389');
    final apiPortController = TextEditingController(text: existing?.apiPort.toString() ?? '5000');
    final mt5PathController = TextEditingController(text: existing?.mt5Path ?? '');
    final notesController = TextEditingController(text: existing?.notes ?? '');

    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        backgroundColor: const Color(0xFF1A1F3A),
        shape: RoundedRectangleBorder(
          side: BorderSide(color: Colors.white.withOpacity(0.1)),
          borderRadius: BorderRadius.circular(18),
        ),
        title: Text(
          isEdit ? 'Edit VPS: ${existing.vpsName}' : 'Add New VPS',          style: GoogleFonts.poppins(color: Colors.white, fontWeight: FontWeight.w600),
        ),
        content: SizedBox(
          width: 500,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                _buildTextField(nameController, 'VPS Name', 'Production VPS'),
                const SizedBox(height: 10),
                _buildTextField(ipController, 'IP Address', '38.247.146.198'),
                const SizedBox(height: 10),
                _buildTextField(portController, 'VPS Port', '3389'),
                const SizedBox(height: 10),
                _buildTextField(usernameController, 'Username', 'Administrator'),
                const SizedBox(height: 10),
                _buildTextField(passwordController, 'Password', '', isPassword: true),
                const SizedBox(height: 10),
                _buildTextField(rdpPortController, 'RDP Port', '3389'),
                const SizedBox(height: 10),
                _buildTextField(apiPortController, 'API Port', '5000'),
                const SizedBox(height: 10),
                _buildTextField(mt5PathController, 'MT5 Terminal Path', r'C:\Program Files\MetaTrader 5\terminal64.exe'),
                const SizedBox(height: 10),
                _buildTextField(notesController, 'Notes', ''),
              ],
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () async {
              final service = context.read<VpsService>();
              final success = await service.saveVpsConfig(
                vpsName: nameController.text.trim(),
                vpsIp: ipController.text.trim(),
                vpsPort: int.tryParse(portController.text.trim()) ?? 3389,
                username: usernameController.text.trim(),
                password: passwordController.text,
                rdpPort: int.tryParse(rdpPortController.text.trim()) ?? 3389,
                apiPort: int.tryParse(apiPortController.text.trim()) ?? 5000,
                mt5Path: mt5PathController.text.trim(),
                notes: notesController.text.trim(),
                vpsId: existing?.vpsId,
              );
              if (success && mounted) {
                Navigator.pop(dialogContext);
                _showSnackBar('VPS ${isEdit ? 'updated' : 'added'} successfully', Colors.green);
              }
            },
            child: Text(isEdit ? 'Update' : 'Create'),
          ),
        ],
      ),
    );
  }

  Widget _buildTextField(TextEditingController controller, String label, String hint, {bool isPassword = false}) {
    return TextField(
      controller: controller,
      obscureText: isPassword,
      style: GoogleFonts.poppins(color: Colors.white70, fontSize: 13),
      decoration: InputDecoration(
        labelText: label,
        labelStyle: GoogleFonts.poppins(color: Colors.white38, fontSize: 12),
        hintText: hint,
        hintStyle: GoogleFonts.poppins(color: Colors.white24, fontSize: 12),
        border: const OutlineInputBorder(),
        enabledBorder: OutlineInputBorder(
          borderSide: BorderSide(color: Colors.white.withOpacity(0.2)),
          borderRadius: BorderRadius.circular(8),
        ),
        focusedBorder: OutlineInputBorder(
          borderSide: const BorderSide(color: Color(0xFF00E5FF)),
          borderRadius: BorderRadius.circular(8),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      ),
    );
  }

  void _showSnackBar(String message, Color color) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: color, duration: const Duration(seconds: 2)),
    );
  }

  @override
  Widget build(BuildContext context) {
    final service = context.watch<VpsService>();

    return Scaffold(
      backgroundColor: const Color(0xFF0A0E21),
      appBar: AppBar(
        backgroundColor: const Color(0xFF111633),
        elevation: 0,
        title: const Row(
          children: [
            LogoWidget(size: 32, showText: false),
            SizedBox(width: 10),
            Text('VPS Management'),
          ],
        ),
        actions: [
          if (service.vpsConfigs.isNotEmpty)
            IconButton(
              tooltip: 'Refresh',
              icon: service.isLoading
                  ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.refresh),
              onPressed: service.isLoading ? null : () => _refresh(),
            ),
        ],
      ),
      body: service.errorMessage != null && service.vpsConfigs.isEmpty
          ? _errorState(service.errorMessage!)
          : service.vpsConfigs.isEmpty
              ? _emptyState()
              : RefreshIndicator(
                  onRefresh: _refresh,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: service.vpsConfigs.length,
                    itemBuilder: (context, index) {
                      final config = service.vpsConfigs[index];
                      return _buildVpsCard(context, config, service);
                    },
                  ),
                ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showAddEditDialog(),
        backgroundColor: const Color(0xFF00E5FF),
        foregroundColor: const Color(0xFF0A0E21),
        icon: const Icon(Icons.add),
        label: Text('Add VPS', style: GoogleFonts.poppins(fontWeight: FontWeight.w600)),
      ),
    );
  }

  Widget _emptyState() => Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.dns, color: Colors.white.withOpacity(0.2), size: 64),
            const SizedBox(height: 16),
            Text(
              'No VPS configured',
              style: GoogleFonts.poppins(color: Colors.white54, fontSize: 16),
            ),
            const SizedBox(height: 8),
            Text(
              'Tap "Add VPS" to configure your VPS deployment',
              style: GoogleFonts.poppins(color: Colors.white30, fontSize: 13),
            ),
          ],
        ),
      );

  Widget _errorState(String error) => Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, color: Colors.redAccent, size: 48),
            const SizedBox(height: 16),
            Text(
              error,
              style: GoogleFonts.poppins(color: Colors.redAccent, fontSize: 13),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () => _refresh(),
              child: Text('Retry', style: GoogleFonts.poppins()),
            ),
          ],
        ),
      );

  Widget _buildVpsCard(BuildContext context, VpsConfig config, VpsService service) {
    final isConnected = config.status == 'connected';
    final statusColor = isConnected ? Colors.green : Colors.grey;
    final accent = const Color(0xFF00E5FF);

    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF1A1F3A),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  config.vpsName,
                  style: GoogleFonts.poppins(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w600),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                decoration: BoxDecoration(
                  color: statusColor.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(999),
                  border: Border.all(color: statusColor.withOpacity(0.35)),
                ),
                child: Row(
                  children: [
                    Container(
                      width: 8,
                      height: 8,
                      decoration: BoxDecoration(color: statusColor, shape: BoxShape.circle),
                    ),
                    const SizedBox(width: 6),
                    Text(
                      config.status.toUpperCase(),
                      style: GoogleFonts.poppins(color: statusColor, fontSize: 11, fontWeight: FontWeight.w600),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            '${config.vpsIp}:${config.vpsPort}',
            style: GoogleFonts.poppins(color: Colors.white54, fontSize: 12).copyWith(fontFamily: 'monospace'),
          ),
          const SizedBox(height: 12),
          if (config.createdAt != null)
            Text(
              'Created: ${DateFormat('MMM d, y').format(config.createdAt!)}',
              style: GoogleFonts.poppins(color: Colors.white30, fontSize: 11),
            ),
          if (config.lastConnection != null)
            Text(
              'Last connection: ${DateFormat('MMM d, y HH:mm').format(config.lastConnection!)}',
              style: GoogleFonts.poppins(color: Colors.white30, fontSize: 11),
            ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 6,
            children: [
              _actionChip(Icons.refresh, 'Refresh', accent, () async {
                final status = await service.refreshAllStatuses();
                if (config.vpsId == service.currentVpsStatus?.vpsId) {
                  if (status && mounted) {
                    _showSnackBar('Status refreshed', Colors.green);
                  }
                } else {
                  final s = await service.fetchVpsStatus(config.vpsId);
                  if (s != null && mounted) {
                    _showStatusDialog(s);
                  } else if (mounted) {
                    _showSnackBar(service.errorMessage ?? 'Failed to fetch status', Colors.red);
                  }
                }
              }),
              _actionChip(Icons.public, 'Test Conn.', accent, () async {
                final success = await service.testVpsConnection(config.vpsId);
                if (success && mounted) {
                  _showSnackBar('Connection test passed', Colors.green);
                } else if (mounted) {
                  _showSnackBar(service.errorMessage ?? 'Connection test failed', Colors.red);
                }
              }),
              _actionChip(Icons.computer, 'RDP', accent, () async {
                final access = await service.fetchVpsRemoteAccess(config.vpsId);
                if (access != null && mounted) {
                  _showRdpDialog(access);
                } else if (mounted) {
                  _showSnackBar(service.errorMessage ?? 'Failed to get RDP details', Colors.red);
                }
              }),
              _actionChip(Icons.edit, 'Edit', const Color(0xFFFFB74D), () => _showAddEditDialog(config)),
              _actionChip(Icons.delete, 'Delete', const Color(0xFFFF5252), () => _confirmDelete(context, config, service)),
            ],
          ),
        ],
      ),
    );
  }

  Widget _actionChip(IconData icon, String label, Color color, VoidCallback onTap) => InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
          decoration: BoxDecoration(
            color: color.withOpacity(0.12),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: color.withOpacity(0.3)),
          ),
          child: Row(
            children: [
              Icon(icon, color: color, size: 14),
              const SizedBox(width: 6),
              Text(
                label,
                style: GoogleFonts.poppins(color: color, fontSize: 11, fontWeight: FontWeight.w600),
              ),
            ],
          ),
        ),
      );

  void _showStatusDialog(VpsStatus status) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1A1F3A),
        shape: RoundedRectangleBorder(
          side: BorderSide(color: Colors.white.withOpacity(0.1)),
          borderRadius: BorderRadius.circular(18),
        ),
        title: Text(
          'VPS Status: ${status.vpsName}',
          style: GoogleFonts.poppins(color: Colors.white, fontWeight: FontWeight.w600),
        ),
        content: SizedBox(
          width: 400,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              _statusRow('IP Address', '${status.vpsIp}', Icons.computer),
              _statusRow('Connection', status.connectionStatus, Icons.wifi),
              _statusRow('MT5 Status', status.mt5Status, Icons.show_chart),
              _statusRow('Backend', status.backendRunning ? 'Running' : 'Stopped', Icons.engineering),
              _statusRow('CPU Usage', '${status.cpuUsage.toStringAsFixed(1)}%', Icons.memory),
              _statusRow('Memory Usage', '${status.memoryUsage.toStringAsFixed(1)}%', Icons.storage),
              _statusRow('Uptime', '${status.uptimeHours}h', Icons.schedule),
              _statusRow('Active Bots', '${status.activeBots}', Icons.smart_toy_outlined),
              _statusRow('TVL', '\$${status.totalValueLocked.toStringAsFixed(2)}', Icons.account_balance_wallet),
              if (status.lastCheck != null)
                _statusRow('Last Check', DateFormat('HH:mm:ss').format(status.lastCheck!), Icons.refresh),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }

  Widget _statusRow(String label, String value, IconData icon) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 6),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              children: [
                Icon(icon, color: Colors.white38, size: 16),
                const SizedBox(width: 8),
                Text(
                  label,
                  style: GoogleFonts.poppins(color: Colors.white60, fontSize: 12),
                ),
              ],
            ),
            Text(
              value,
              style: GoogleFonts.poppins(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w600),
            ),
          ],
        ),
      );

  void _showRdpDialog(VpsRemoteAccess access) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1A1F3A),
        shape: RoundedRectangleBorder(
          side: BorderSide(color: Colors.white.withOpacity(0.1)),
          borderRadius: BorderRadius.circular(18),
        ),
        title: Text(
          'RDP Access: ${access.vpsName}',
          style: GoogleFonts.poppins(color: Colors.white, fontWeight: FontWeight.w600),
        ),
        content: SizedBox(
          width: 400,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              SelectableText(
                access.connectionString,
                style: GoogleFonts.poppins(color: const Color(0xFF00E5FF), fontSize: 14).copyWith(fontFamily: 'monospace'),
              ),
              const SizedBox(height: 12),
              Text(
                'Username: ${access.username}',
                style: GoogleFonts.poppins(color: Colors.white70, fontSize: 12),
              ),
              const SizedBox(height: 12),
              ...access.instructions.map(
                (instruction) => Padding(
                  padding: const EdgeInsets.symmetric(vertical: 2),
                  child: Text(
                    instruction,
                    style: GoogleFonts.poppins(color: Colors.white54, fontSize: 11),
                  ),
                ),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Close'),
          ),
          ElevatedButton.icon(
            icon: const Icon(Icons.open_in_browser),
            label: const Text('Launch RDP'),
            onPressed: () {
              final parts = access.rdpServer.split(':');
              final host = parts.isNotEmpty ? parts[0] : '';
              final uri = Uri.parse('rdp://$host');
              launchUrl(uri);
            },
          ),
        ],
      ),
    );
  }

  void _confirmDelete(BuildContext context, VpsConfig config, VpsService service) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1A1F3A),
        shape: RoundedRectangleBorder(
          side: BorderSide(color: Colors.white.withOpacity(0.1)),
          borderRadius: BorderRadius.circular(18),
        ),
        title: Text(
          'Delete VPS',
          style: GoogleFonts.poppins(color: Colors.white),
        ),
        content: Text(
          'Are you sure you want to delete "${config.vpsName}"? This action cannot be undone.',
          style: GoogleFonts.poppins(color: Colors.white70),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () async {
              Navigator.pop(ctx);
              final success = await service.deleteVpsConfig(config.vpsId);
              if (success && mounted) {
                _showSnackBar('VPS deleted', Colors.green);
              } else if (mounted) {
                _showSnackBar(service.errorMessage ?? 'Failed to delete VPS', Colors.red);
              }
            },
            child: Text('Delete', style: GoogleFonts.poppins()),
          ),
        ],
      ),
    );
  }
}
