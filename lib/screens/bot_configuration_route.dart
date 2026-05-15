import 'package:flutter/widgets.dart';

import 'bot_configuration_screen.dart';

class BotConfigurationRoute extends StatelessWidget {
  const BotConfigurationRoute({
    super.key,
    this.botId,
    this.cloneFromBotId,
    this.promoteToLive = false,
    this.focusTestedTemplates = false,
  });

  final String? botId;
  final String? cloneFromBotId;
  final bool promoteToLive;
  final bool focusTestedTemplates;

  @override
  Widget build(BuildContext context) {
    return BotConfigurationScreen(
      botId: botId,
      cloneFromBotId: cloneFromBotId,
      promoteToLive: promoteToLive,
      focusTestedTemplates: focusTestedTemplates,
    );
  }
}