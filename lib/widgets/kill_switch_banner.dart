import 'dart:async';

import 'package:flutter/material.dart';

import '../services/kill_switch_service.dart';

/// Persistent banner shown at the top of dashboards when the user-level
/// emergency kill switch is active. Polls every 15s.
class KillSwitchBanner extends StatefulWidget {
  const KillSwitchBanner({super.key});

  @override
  State<KillSwitchBanner> createState() => _KillSwitchBannerState();
}

class _KillSwitchBannerState extends State<KillSwitchBanner> {
  bool _active = false;
  bool _busy = false;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _refresh();
    _timer = Timer.periodic(const Duration(seconds: 15), (_) => _refresh());
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _refresh() async {
    final result = await KillSwitchService.getStatus();
    if (!mounted) return;
    if (result.ok && _active != result.active) {
      setState(() => _active = result.active);
    }
  }

  Future<void> _clear() async {
    if (_busy) return;
    setState(() => _busy = true);
    final result = await KillSwitchService.clear();
    if (!mounted) return;
    setState(() {
      _busy = false;
      if (result.ok) _active = result.active;
    });
    if (!result.ok) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text('Failed to clear kill switch: ${result.error}'),
        backgroundColor: Colors.red.shade700,
      ));
    }
  }

  @override
  Widget build(BuildContext context) {
    if (!_active) return const SizedBox.shrink();
    return Material(
      color: Colors.red.shade700,
      child: SafeArea(
        bottom: false,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          child: Row(
            children: [
              const Icon(Icons.warning_amber_rounded, color: Colors.white),
              const SizedBox(width: 8),
              const Expanded(
                child: Text(
                  'Emergency kill switch is ACTIVE — all bots are paused.',
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
              TextButton(
                onPressed: _busy ? null : _clear,
                style: TextButton.styleFrom(
                  foregroundColor: Colors.white,
                  backgroundColor: Colors.red.shade900,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
                child: _busy
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(
                          color: Colors.white,
                          strokeWidth: 2,
                        ),
                      )
                    : const Text('Resume'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// A small "Pause All Bots" button that activates the emergency kill switch.
/// Use as a trailing action on dashboard app bars.
class KillSwitchButton extends StatefulWidget {
  const KillSwitchButton({super.key});

  @override
  State<KillSwitchButton> createState() => _KillSwitchButtonState();
}

class _KillSwitchButtonState extends State<KillSwitchButton> {
  bool _busy = false;

  Future<void> _confirmAndActivate() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.warning_amber_rounded, color: Colors.red),
            SizedBox(width: 8),
            Text('Pause all bots?'),
          ],
        ),
        content: const Text(
          'This activates the emergency kill switch and stops every bot you own. '
          'Open positions are NOT closed. You will need to resume manually.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(ctx).pop(false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () => Navigator.of(ctx).pop(true),
            child: const Text('Pause all'),
          ),
        ],
      ),
    );
    if (confirm != true || !mounted) return;
    setState(() => _busy = true);
    final result = await KillSwitchService.activate();
    if (!mounted) return;
    setState(() => _busy = false);
    final messenger = ScaffoldMessenger.of(context);
    if (result.ok) {
      messenger.showSnackBar(SnackBar(
        content: Text(
          result.message ??
              'Kill switch ON — stopped ${result.stoppedBots} bots.',
        ),
        backgroundColor: Colors.red.shade700,
      ));
    } else {
      messenger.showSnackBar(SnackBar(
        content: Text('Failed: ${result.error}'),
        backgroundColor: Colors.red.shade700,
      ));
    }
  }

  @override
  Widget build(BuildContext context) {
    return IconButton(
      tooltip: 'Pause all bots (kill switch)',
      onPressed: _busy ? null : _confirmAndActivate,
      icon: _busy
          ? const SizedBox(
              width: 18,
              height: 18,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
          : Icon(Icons.do_not_disturb_on_outlined,
              color: Colors.red.shade400),
    );
  }
}
