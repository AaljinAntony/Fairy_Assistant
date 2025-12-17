import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:socket_io_client/socket_io_client.dart' as io;
import 'package:record/record.dart';
import 'package:path_provider/path_provider.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:flutter_tts/flutter_tts.dart';

void main() {
  runApp(const FairyAssistantApp());
}

class FairyAssistantApp extends StatelessWidget {
  const FairyAssistantApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Fairy Assistant',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF6C63FF),
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
      ),
      home: const FairyHomePage(),
    );
  }
}

class FairyHomePage extends StatefulWidget {
  const FairyHomePage({super.key});

  @override
  State<FairyHomePage> createState() => _FairyHomePageState();
}

class _FairyHomePageState extends State<FairyHomePage>
    with SingleTickerProviderStateMixin {
  // ========== Configuration ==========
  // 10.0.2.2 is the Android Emulator's special IP alias for the host PC's localhost.
  // This allows the emulator to connect to a server running on your development machine.
  static const String serverUrl = 'http://10.0.2.2:5000';

  // ========== State ==========
  late io.Socket socket;
  final AudioRecorder _recorder = AudioRecorder();
  final FlutterTts _tts = FlutterTts();

  bool _isConnected = false;
  bool _isRecording = false;
  String _transcript = '';
  String _response = '';
  String _statusMessage = 'Connecting...';
  List<String> _logs = [];

  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    _initAnimations();
    _initTts();
    _requestPermissions();
    _connectToServer();
  }

  void _initAnimations() {
    _pulseController = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    );
    _pulseAnimation = Tween<double>(begin: 1.0, end: 1.15).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
  }

  Future<void> _initTts() async {
    await _tts.setLanguage('en-US');
    await _tts.setSpeechRate(0.5);
    await _tts.setVolume(1.0);
  }

  Future<void> _requestPermissions() async {
    final status = await Permission.microphone.request();
    if (status.isDenied) {
      _addLog('Microphone permission denied');
    }
  }

  void _connectToServer() {
    socket = io.io(
      serverUrl,
      io.OptionBuilder()
          .setTransports(['websocket'])
          .disableAutoConnect()
          .build(),
    );

    socket.onConnect((_) {
      setState(() {
        _isConnected = true;
        _statusMessage = 'Connected to Fairy';
      });
      _addLog('Connected to server');
    });

    socket.onDisconnect((_) {
      setState(() {
        _isConnected = false;
        _statusMessage = 'Disconnected';
      });
      _addLog('Disconnected from server');
    });

    socket.onConnectError((error) {
      setState(() {
        _statusMessage = 'Connection failed';
      });
      _addLog('Connection error: $error');
    });

    // Listen for server actions
    socket.on('server_action', (data) {
      _handleServerAction(data);
    });

    socket.connect();
  }

  void _handleServerAction(dynamic data) {
    if (data is! Map) return;

    final type = data['type'] as String?;
    final message = data['message'] as String?;

    switch (type) {
      case 'speak':
        setState(() => _response = message ?? '');
        _speak(message ?? '');
        _addLog('Fairy: ${message?.substring(0, (message.length > 50 ? 50 : message.length))}...');
        break;
      case 'transcript':
        setState(() => _transcript = message ?? '');
        _addLog('You said: $message');
        break;
      case 'log':
        _addLog(message ?? '');
        break;
      case 'trigger_intent':
        _handleIntent(data);
        break;
    }
  }

  void _handleIntent(Map<dynamic, dynamic> data) {
    final intent = data['intent'] as String?;
    _addLog('Intent received: $intent');
    // TODO: Implement intent handling (SMS, Call, etc.)
  }

  Future<void> _speak(String text) async {
    await _tts.speak(text);
  }

  void _addLog(String message) {
    setState(() {
      _logs.insert(0, '[${DateTime.now().toString().substring(11, 19)}] $message');
      if (_logs.length > 50) _logs.removeLast();
    });
  }

  // ========== Recording ==========
  Future<void> _startRecording() async {
    if (!await _recorder.hasPermission()) {
      _addLog('No microphone permission');
      return;
    }

    final tempDir = await getTemporaryDirectory();
    final filePath = '${tempDir.path}/fairy_audio.wav';

    await _recorder.start(
      const RecordConfig(encoder: AudioEncoder.wav),
      path: filePath,
    );

    setState(() {
      _isRecording = true;
      _transcript = '';
      _response = '';
    });
    _pulseController.repeat(reverse: true);
    _addLog('Recording started...');
  }

  Future<void> _stopRecording() async {
    final path = await _recorder.stop();
    _pulseController.stop();
    _pulseController.reset();

    setState(() => _isRecording = false);

    if (path != null) {
      final file = File(path);
      final bytes = await file.readAsBytes();
      _addLog('Sending ${bytes.length} bytes...');
      socket.emit('audio_command', bytes);
    }
  }

  // ========== Text Command ==========
  void _sendTextCommand(String text) {
    if (text.isEmpty) return;
    socket.emit('client_command', {'text': text});
    _addLog('Sent: $text');
  }

  @override
  void dispose() {
    socket.dispose();
    _recorder.dispose();
    _tts.stop();
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0D0D1A),
      body: SafeArea(
        child: Column(
          children: [
            _buildHeader(),
            Expanded(child: _buildMainContent()),
            _buildLogPanel(),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader() {
    return Container(
      padding: const EdgeInsets.all(20),
      child: Row(
        children: [
          Container(
            width: 12,
            height: 12,
            decoration: BoxDecoration(
              color: _isConnected ? Colors.greenAccent : Colors.redAccent,
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: (_isConnected ? Colors.greenAccent : Colors.redAccent)
                      .withOpacity(0.5),
                  blurRadius: 8,
                  spreadRadius: 2,
                ),
              ],
            ),
          ),
          const SizedBox(width: 12),
          Text(
            _statusMessage,
            style: TextStyle(
              color: Colors.white.withOpacity(0.8),
              fontSize: 14,
            ),
          ),
          const Spacer(),
          IconButton(
            icon: const Icon(Icons.settings, color: Colors.white54),
            onPressed: () => _showSettingsDialog(),
          ),
        ],
      ),
    );
  }

  Widget _buildMainContent() {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        // Title
        const Text(
          'FAIRY',
          style: TextStyle(
            fontSize: 48,
            fontWeight: FontWeight.w200,
            color: Colors.white,
            letterSpacing: 16,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'Your AI Assistant',
          style: TextStyle(
            fontSize: 14,
            color: Colors.white.withOpacity(0.5),
            letterSpacing: 4,
          ),
        ),
        const SizedBox(height: 60),

        // Push to Talk Button
        GestureDetector(
          onTapDown: (_) => _startRecording(),
          onTapUp: (_) => _stopRecording(),
          onTapCancel: () => _stopRecording(),
          child: AnimatedBuilder(
            animation: _pulseAnimation,
            builder: (context, child) {
              return Transform.scale(
                scale: _isRecording ? _pulseAnimation.value : 1.0,
                child: Container(
                  width: 160,
                  height: 160,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: _isRecording
                          ? [const Color(0xFFFF6B6B), const Color(0xFFFF8E53)]
                          : [const Color(0xFF6C63FF), const Color(0xFF4ECDC4)],
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: (_isRecording
                                ? const Color(0xFFFF6B6B)
                                : const Color(0xFF6C63FF))
                            .withOpacity(0.4),
                        blurRadius: 30,
                        spreadRadius: 5,
                      ),
                    ],
                  ),
                  child: Icon(
                    _isRecording ? Icons.mic : Icons.mic_none,
                    size: 64,
                    color: Colors.white,
                  ),
                ),
              );
            },
          ),
        ),
        const SizedBox(height: 24),
        Text(
          _isRecording ? 'Listening...' : 'Hold to Speak',
          style: TextStyle(
            fontSize: 16,
            color: Colors.white.withOpacity(0.6),
          ),
        ),
        const SizedBox(height: 40),

        // Response Display
        if (_response.isNotEmpty)
          Container(
            margin: const EdgeInsets.symmetric(horizontal: 32),
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.05),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: Colors.white.withOpacity(0.1),
              ),
            ),
            child: Text(
              _response,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 16,
                height: 1.5,
              ),
              textAlign: TextAlign.center,
              maxLines: 5,
              overflow: TextOverflow.ellipsis,
            ),
          ),
      ],
    );
  }

  Widget _buildLogPanel() {
    return Container(
      height: 120,
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.3),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white.withOpacity(0.1)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Activity Log',
            style: TextStyle(
              color: Colors.white.withOpacity(0.5),
              fontSize: 12,
            ),
          ),
          const SizedBox(height: 8),
          Expanded(
            child: ListView.builder(
              itemCount: _logs.length,
              itemBuilder: (context, index) {
                return Text(
                  _logs[index],
                  style: TextStyle(
                    color: Colors.white.withOpacity(0.7),
                    fontSize: 11,
                    fontFamily: 'monospace',
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  void _showSettingsDialog() {
    final controller = TextEditingController();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF1A1A2E),
        title: const Text('Send Text Command', style: TextStyle(color: Colors.white)),
        content: TextField(
          controller: controller,
          style: const TextStyle(color: Colors.white),
          decoration: InputDecoration(
            hintText: 'Type a command...',
            hintStyle: TextStyle(color: Colors.white.withOpacity(0.5)),
            enabledBorder: OutlineInputBorder(
              borderSide: BorderSide(color: Colors.white.withOpacity(0.3)),
            ),
            focusedBorder: const OutlineInputBorder(
              borderSide: BorderSide(color: Color(0xFF6C63FF)),
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              _sendTextCommand(controller.text);
              Navigator.pop(context);
            },
            child: const Text('Send'),
          ),
        ],
      ),
    );
  }
}
