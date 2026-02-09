import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:usb_serial/usb_serial.dart';

void main() => runApp(const MyApp());

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Arm Controller',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: Colors.cyanAccent,
          brightness: Brightness.dark,
          surface: const Color(0xFF121212),
        ),
        textTheme: GoogleFonts.outfitTextTheme(ThemeData.dark().textTheme),
      ),
      home: const ArmControlPage(),
    );
  }
}

class ArmControlPage extends StatefulWidget {
  const ArmControlPage({super.key});

  @override
  State<ArmControlPage> createState() => _ArmControlPageState();
}

class _ArmControlPageState extends State<ArmControlPage> {
  // USB Serial
  UsbPort? _port;
  UsbDevice? _connectedDevice; // Track connected device explicitly
  String _status = "Disconnected";
  List<UsbDevice> _devices = [];

  // Servo States
  final Map<int, int> _angles = {
    1: 90, // Base
    2: 90, // Shoulder
    3: 90, // Elbow
    4: 90, // Wrist
    5: 90, // Gripper
  };

  final Map<int, String> _labels = {
    1: "Base",
    2: "Shoulder",
    3: "Elbow",
    4: "Wrist",
    5: "Gripper",
  };

  // Timers
  final Map<int, Timer> _holdTimers = {};
  Timer? _animTimer;

  @override
  void initState() {
    super.initState();
    UsbSerial.usbEventStream?.listen((UsbEvent event) {
      _getPorts();
      // Auto-Disconnect Logic
      if (event.event == UsbEvent.ACTION_USB_DETACHED &&
          _connectedDevice != null) {
        if (event.device?.deviceId == _connectedDevice!.deviceId) {
          _connectTo(null);
        }
      }
    });
    _getPorts();
  }

  @override
  void dispose() {
    _connectTo(null);
    for (var timer in _holdTimers.values) {
      timer.cancel();
    }
    _animTimer?.cancel();
    super.dispose();
  }

  void _getPorts() async {
    _devices = await UsbSerial.listDevices();
    if (!mounted) return;
    setState(() {});
  }

  Future<bool> _connectTo(UsbDevice? device) async {
    _animTimer?.cancel(); // Stop any animations

    if (_port != null) {
      _port!.close();
      _port = null;
    }
    _connectedDevice = null;

    if (device == null) {
      setState(() {
        _status = "Disconnected";
      });
      return true;
    }

    try {
      _port = await device.create();
      if (await (_port!.open()) != true) {
        setState(() {
          _status = "Failed to open port";
        });
        return false;
      }

      _connectedDevice = device;

      await _port!.setDTR(true);
      await _port!.setRTS(true);
      await _port!.setPortParameters(
          9600, UsbPort.DATABITS_8, UsbPort.STOPBITS_1, UsbPort.PARITY_NONE);

      setState(() {
        _status = "Connected to ${device.productName ?? 'Unknown Device'}";
      });
    } catch (e) {
      setState(() {
        _status = "Error: $e";
      });
      return false;
    }

    return true;
  }

  void _sendCommand(int id, int angle) async {
    if (_port == null) return;
    String cmd = "S$id:$angle\n";
    try {
      await _port!.write(Uint8List.fromList(utf8.encode(cmd)));
    } catch (e) {
      // Ignore write errors to prevent crash during rapid multi-touch
    }
  }

  void _updateServo(int id, int delta) {
    if (_angles.containsKey(id)) {
      int newVal = (_angles[id]! + delta).clamp(0, 180);
      _setServoAngle(id, newVal);
    }
  }

  void _setServoAngle(int id, int angle) {
    if (angle != _angles[id]) {
      setState(() {
        _angles[id] = angle;
      });
      _sendCommand(id, angle);
    }
  }

  void _startHold(int id, int delta) {
    _animTimer?.cancel(); // Stop any auto-animation if user interacts
    _updateServo(id, delta);
    _holdTimers[id]?.cancel();
    _holdTimers[id] = Timer.periodic(const Duration(milliseconds: 40), (timer) {
      _updateServo(id, delta);
    });
  }

  void _stopHold(int id) {
    _holdTimers[id]?.cancel();
    _holdTimers.remove(id);
  }

  // Smooth Home Transition
  void _presetHome() {
    _animTimer?.cancel();
    // Stop any manual holds
    for (var timer in _holdTimers.values) {
      timer.cancel();
    }
    _holdTimers.clear();

    const int steps = 20;
    const int durationMs = 1000;
    const int intervalMs = durationMs ~/ steps;
    int currentStep = 0;

    // Capture start positions
    Map<int, int> starts = Map.from(_angles);
    Map<int, int> targets = {};
    for (var k in _angles.keys) {
      targets[k] = 90;
    }

    _animTimer =
        Timer.periodic(const Duration(milliseconds: intervalMs), (timer) {
      currentStep++;
      double progress = currentStep / steps;

      if (progress >= 1.0) {
        timer.cancel();
        // Ensure final exact values
        targets.forEach((id, target) => _setServoAngle(id, target));
      } else {
        targets.forEach((id, target) {
          int start = starts[id]!;
          int newAngle = (start + (target - start) * progress).round();
          _setServoAngle(id, newAngle);
        });
      }
    });
  }

  void _showConnectionDialog() {
    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setStateDialog) {
          return SimpleDialog(
            title: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text("Select Device"),
                IconButton(
                  icon: const Icon(Icons.refresh),
                  onPressed: () async {
                    _devices = await UsbSerial.listDevices();
                    setStateDialog(() {}); // Rebuild dialog to show new devices
                  },
                )
              ],
            ),
            children: [
              if (_devices.isEmpty)
                const Padding(
                  padding: EdgeInsets.all(16.0),
                  child: Text("No devices found."),
                ),
              ..._devices.map((device) => SimpleDialogOption(
                    onPressed: () {
                      Navigator.pop(ctx);
                      _connectTo(device);
                    },
                    child: Padding(
                      padding: const EdgeInsets.symmetric(vertical: 8.0),
                      child: Text(
                        device.productName ?? device.deviceName,
                        style: const TextStyle(fontSize: 16),
                      ),
                    ),
                  )),
            ],
          );
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Robotic Arm'),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.usb),
            onPressed: () {
              _getPorts(); // Refresh list before showing
              _showConnectionDialog();
            },
          ),
          // Removed standalone Refresh button as requested
        ],
      ),
      body: Column(
        children: [
          // Connection Status
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(8.0),
            // Fixed withAlpha usage: 0.2 * 255 ~= 51
            color: _port != null
                ? Colors.green.withAlpha(51)
                : Colors.red.withAlpha(51),
            child: Text(
              _status,
              textAlign: TextAlign.center,
              style: TextStyle(
                color: _port != null ? Colors.greenAccent : Colors.redAccent,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),

          Expanded(
            child: OrientationBuilder(
              builder: (context, orientation) {
                bool isLandscape = orientation == Orientation.landscape;
                return GridView.count(
                  padding: const EdgeInsets.all(16),
                  crossAxisCount: isLandscape
                      ? 3
                      : 1, // 3 columns in landscape, 1 in portrait
                  childAspectRatio:
                      isLandscape ? 1.4 : 2.5, // Adjust aspect ratio for shape
                  crossAxisSpacing: 16,
                  mainAxisSpacing: 16,
                  children: _angles.entries
                      .map((entry) => _buildControlCard(entry.key, entry.value))
                      .toList(),
                );
              },
            ),
          ),

          // Bottom Bar (Home Button)
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: SizedBox(
              width: double.infinity,
              height: 60,
              child: ElevatedButton.icon(
                onPressed: _presetHome,
                icon: const Icon(Icons.home, size: 28),
                label: const Text("HOME POSITION",
                    style:
                        TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                style: ElevatedButton.styleFrom(
                  backgroundColor:
                      Theme.of(context).colorScheme.primaryContainer,
                  foregroundColor:
                      Theme.of(context).colorScheme.onPrimaryContainer,
                  elevation: 4,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildControlCard(int id, int angle) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              "${_labels[id]} (ID $id)",
              style: const TextStyle(fontSize: 16, color: Colors.white70),
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                // MINUS BUTTON
                _buildActionButton(
                  icon: Icons.remove,
                  onPressStart: () => _startHold(id, -1),
                  onPressEnd: () => _stopHold(id),
                  color: Colors.redAccent.withAlpha(204), // 0.8 * 255
                ),

                // VALUE DISPLAY
                Container(
                  width: 70,
                  alignment: Alignment.center,
                  child: Text(
                    "$angle°",
                    style: const TextStyle(
                      fontSize: 32,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                ),

                // PLUS BUTTON
                _buildActionButton(
                  icon: Icons.add,
                  onPressStart: () => _startHold(id, 1),
                  onPressEnd: () => _stopHold(id),
                  color: Colors.greenAccent.withAlpha(204), // 0.8 * 255
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildActionButton({
    required IconData icon,
    required VoidCallback onPressStart,
    required VoidCallback onPressEnd,
    required Color color,
  }) {
    // Using GestureDetector for Multi-Touch support
    // Each button has its own GestureDetector and callbacks
    return GestureDetector(
      onLongPressStart: (_) => onPressStart(),
      onLongPressEnd: (_) => onPressEnd(),
      onTapDown: (_) => onPressStart(),
      onTapUp: (_) => onPressEnd(),
      onTapCancel: onPressEnd,
      child: Container(
        width: 64, // Big touch target
        height: 64,
        decoration: BoxDecoration(
          color: color,
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
              color: color.withAlpha(102), // 0.4 * 255
              blurRadius: 8,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Icon(icon, size: 36, color: Colors.white),
      ),
    );
  }
}
