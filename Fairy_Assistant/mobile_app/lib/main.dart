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
      home: const ChatScreen(),
    );
  }
}

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> with SingleTickerProviderStateMixin {
  // ========== Configuration ==========
  // 10.0.2.2 is the Android Emulator's special IP alias for host localhost.
  static const String serverUrl = 'http://10.0.2.2:5000';

  // ========== State ==========
  late io.Socket socket;
  final AudioRecorder _recorder = AudioRecorder();
  final FlutterTts _tts = FlutterTts();
  final TextEditingController _textController = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  bool _isConnected = false;
  bool _isRecording = false;
  String _statusMessage = 'Connecting...';
  
  // Chat History: {role: 'user'|'fairy'|'system', text: '...'}
  final List<Map<String, String>> _messages = [];

  // Animation for Mic
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
      duration: const Duration(milliseconds: 1000),
      vsync: this,
    );
    _pulseAnimation = Tween<double>(begin: 1.0, end: 1.2).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
  }

  Future<void> _initTts() async {
    await _tts.setLanguage('en-US');
    await _tts.setSpeechRate(0.5);
  }

  Future<void> _requestPermissions() async {
    await Permission.microphone.request();
  }

  // ========== SocketIO ==========
  void _connectToServer() {
    socket = io.io(
      serverUrl,
      io.OptionBuilder()
          .setTransports(['websocket'])
          .disableAutoConnect()
          .build(),
    );

    socket.onConnect((_) {
      if (mounted) {
        setState(() {
          _isConnected = true;
          _statusMessage = 'Connected';
          _addMessage('system', 'Connected to Fairy Assistant');
        });
      }
    });

    socket.onDisconnect((_) {
      if (mounted) {
        setState(() {
          _isConnected = false;
          _statusMessage = 'Disconnected';
          _addMessage('system', 'Disconnected from server');
        });
      }
    });

    socket.on('server_response', (data) {
        // Handling streaming content or full text
        // For simplicity with the current server implementation (which emits 'server_response' with chunks)
        // We will adapt.
        // Wait, main.py emits: {'text': chunk, 'done': bool}
        // Let's assume we just want to show the final result or append?
        // Actually, main.py sends chunks. It would be nicer to stream update the last message.
        // But let's look at how main.py handles valid parsed actions log vs speak.
        // main.py emits 'server_action' {type: speak, message: ...} in the original code,
        // BUT in the refactored main.py I see:
        // emit('server_response', {'text': chunk, 'done': False})
        // emit('server_log', ...)
        // Wait, did I remove the 'server_action'='speak' in Phase 2?
        // Let's check main.py again in my thought process.
        // Phase 2 implementation uses `emit('server_response', {'text': chunk})`.
        // It does NOT emit 'speak' type anymore.
        // So the App must listen to `server_response`.
        
        _handleServerResponse(data);
    });

    socket.on('server_log', (data) {
         // Optional: show logs
         print("Server Log: $data");
    });

    socket.connect();
  }

  // Buffering streaming response
  String _currentStreamBuffer = "";
  bool _isStreaming = false;

  void _handleServerResponse(dynamic data) {
    if (data is! Map) return;
    
    String text = data['text'] ?? '';
    bool done = data['done'] ?? false;

    if (!_isStreaming) {
       // Start of a new message
       setState(() {
         _isStreaming = true;
         _currentStreamBuffer = text;
         _messages.add({'role': 'fairy', 'text': _currentStreamBuffer});
       });
    } else {
       // Append to current message
       setState(() {
         _currentStreamBuffer += text;
         _messages.last['text'] = _currentStreamBuffer;
       });
    }

    if (done) {
        setState(() {
            _isStreaming = false;
        });
        // Speak the full response once done
        _speak(_currentStreamBuffer);
        _scrollToBottom();
    }
  }

  Future<void> _speak(String text) async {
    if (text.isNotEmpty) {
      await _tts.speak(text);
    }
  }

  void _addMessage(String role, String text) {
    setState(() {
      _messages.add({'role': role, 'text': text});
    });
    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  // ========== Recording ==========
  Future<void> _startRecording() async {
    if (!await _recorder.hasPermission()) return;

    final tempDir = await getTemporaryDirectory();
    final filePath = '${tempDir.path}/fairy_audio.wav';

    await _recorder.start(
      const RecordConfig(encoder: AudioEncoder.wav),
      path: filePath,
    );

    setState(() => _isRecording = true);
    _pulseController.repeat(reverse: true);
  }

  Future<void> _stopRecording() async {
    final path = await _recorder.stop();
    _pulseController.stop();
    _pulseController.reset();
    setState(() => _isRecording = false);

    if (path != null) {
      final file = File(path);
      final bytes = await file.readAsBytes();
      // Send audio
      socket.emit('audio_command', bytes);
      _addMessage('system', 'Sending Audio...');
    }
  }

  // ========== Text Sending ==========
  void _sendText() {
    final text = _textController.text.trim();
    if (text.isEmpty) return;
    
    _addMessage('user', text);
    socket.emit('client_command', {'text': text});
    _textController.clear();
  }

  @override
  void dispose() {
    socket.dispose();
    _recorder.dispose();
    _tts.stop();
    _pulseController.dispose();
    _textController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF121212),
      appBar: AppBar(
        title: const Text('Fairy Assistant'),
        backgroundColor: const Color(0xFF1F1F1F),
        actions: [
          Center(
            child: Padding(
              padding: const EdgeInsets.only(right: 16.0),
              child: Container(
                width: 10, height: 10,
                decoration: BoxDecoration(
                  color: _isConnected ? Colors.green : Colors.red,
                  shape: BoxShape.circle,
                ),
              ),
            ),
          )
        ],
      ),
      body: Column(
        children: [
          // Chat List
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(16),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final msg = _messages[index];
                final role = msg['role'];
                final text = msg['text'] ?? '';
                
                final isUser = role == 'user';
                final isSystem = role == 'system';
                
                if (isSystem) {
                  return Center(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 8.0),
                      child: Text(text, style: TextStyle(color: Colors.white38, fontSize: 12)),
                    ),
                  );
                }

                return Align(
                  alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.symmetric(vertical: 4),
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                    decoration: BoxDecoration(
                      color: isUser ? const Color(0xFF6C63FF) : const Color(0xFF2C2C2C),
                      borderRadius: BorderRadius.only(
                        topLeft: const Radius.circular(12),
                        topRight: const Radius.circular(12),
                        bottomLeft: isUser ? const Radius.circular(12) : Radius.zero,
                        bottomRight: isUser ? Radius.zero : const Radius.circular(12),
                      ),
                    ),
                    child: Text(
                      text,
                      style: const TextStyle(color: Colors.white),
                    ),
                  ),
                );
              },
            ),
          ),
          
          // Input Area
          Container(
            padding: const EdgeInsets.all(12),
            color: const Color(0xFF1F1F1F),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _textController,
                    style: const TextStyle(color: Colors.white),
                    decoration: const InputDecoration(
                      hintText: 'Message Fairy...',
                      hintStyle: TextStyle(color: Colors.white38),
                      border: InputBorder.none,
                    ),
                    onSubmitted: (_) => _sendText(),
                  ),
                ),
                
                // Mic / Send Button
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
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: _isRecording ? Colors.redAccent : const Color(0xFF6C63FF),
                            shape: BoxShape.circle,
                          ),
                          child: Icon(
                            _isRecording ? Icons.mic : Icons.send, // Send icon if typing? 
                            // Actually let's keep it simple: Mic always active for check, but maybe Send if text?
                            // Plan said "Hold to Talk".
                            // Let's make it intuitive: If text is empty -> Mic, else -> Send.
                            color: Colors.white,
                          ),
                        ),
                      );
                    },
                  ),
                  onTap: () {
                      if (_textController.text.isNotEmpty) {
                          _sendText();
                      }
                  },
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
