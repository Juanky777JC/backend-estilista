import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:google_fonts/google_fonts.dart';
import 'nueva_cita.dart';
import 'detalle_cita.dart';

const String apiBaseUrl = 'https://backend-estilista.onrender.com';

void main() => runApp(const MayraApp());

class MayraApp extends StatelessWidget {
  const MayraApp({super.key});

  @override
  Widget build(BuildContext context) {
    const Color oroRosa = Color(0xFFE3A89C); 
    return MaterialApp(
      title: 'Mayra Estilista',
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark().copyWith(
        scaffoldBackgroundColor: const Color(0xFF111113),
        primaryColor: oroRosa,
        appBarTheme: const AppBarTheme(elevation: 0, backgroundColor: Color(0xFF111113), foregroundColor: oroRosa),
      ),
      home: const PantallaPrincipalContenedora(),
    );
  }
}

// Helper para evitar errores si la fecha viene mal de la base de datos
String obtenerHoraSegura(String? fechaIso) {
  if (fechaIso == null || fechaIso.length < 16) return '--:--';
  return fechaIso.substring(11, 16);
}

class PantallaPrincipalContenedora extends StatefulWidget {
  const PantallaPrincipalContenedora({super.key});
  @override
  State<PantallaPrincipalContenedora> createState() => _PantallaPrincipalContenedoraState();
}

class _PantallaPrincipalContenedoraState extends State<PantallaPrincipalContenedora> {
  int _indiceActual = 0;
  final GlobalKey<_PantallaInicioState> _agendaKey = GlobalKey();
  final GlobalKey<_PantallaCulminadasState> _culminadasKey = GlobalKey();
  final GlobalKey<_PantallaClientesState> _clientesKey = GlobalKey();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _indiceActual,
        children: [
          PantallaInicio(key: _agendaKey),
          PantallaCulminadas(key: _culminadasKey), 
          PantallaClientes(key: _clientesKey),
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _indiceActual,
        backgroundColor: const Color(0xFF151517),
        selectedItemColor: const Color(0xFFE3A89C),
        unselectedItemColor: Colors.grey.shade600,
        onTap: (index) {
          setState(() => _indiceActual = index);
          if (index == 0) _agendaKey.currentState?.obtenerCitas();
          if (index == 1) _culminadasKey.currentState?.obtenerCitas();
          if (index == 2) _clientesKey.currentState?.obtenerClientes();
        },
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.directions_car), label: 'Ruta'),
          BottomNavigationBarItem(icon: Icon(Icons.fact_check_outlined), label: 'Culminadas'),
          BottomNavigationBarItem(icon: Icon(Icons.people_outline), label: 'Clientas'),
        ],
      ),
    );
  }
}

// ==========================================
// PESTAÑA 1: RUTA ACTIVA
// ==========================================
class PantallaInicio extends StatefulWidget {
  const PantallaInicio({super.key});
  @override
  State<PantallaInicio> createState() => _PantallaInicioState();
}

class _PantallaInicioState extends State<PantallaInicio> {
  List citas = [];
  bool estaCargando = true;

  @override
  void initState() { super.initState(); obtenerCitas(); }

  Future<void> obtenerCitas() async {
    if (!mounted) return;
    setState(() => estaCargando = true);
    try {
      final respuesta = await http.get(Uri.parse('$apiBaseUrl/citas'));
      if (respuesta.statusCode == 200 && mounted) {
        final List todas = json.decode(respuesta.body);
        setState(() {
          citas = todas.where((c) => c['estado'] == 'Pendiente' || c['estado'] == 'Confirmada').toList();
          estaCargando = false;
        });
      }
    } catch (e) { 
      if (mounted) setState(() => estaCargando = false); 
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        toolbarHeight: 70,
        title: Row(
          children: [
            ClipRRect(borderRadius: BorderRadius.circular(8), child: Image.asset('assets/logo.jpg', height: 48, fit: BoxFit.cover)),
            const SizedBox(width: 15),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text('Mayra', style: GoogleFonts.dancingScript(fontSize: 34, height: 1.0, fontWeight: FontWeight.bold, color: const Color(0xFFE3A89C))),
                Text('Estilista Profesional', style: GoogleFonts.dancingScript(fontSize: 22, height: 1.0, fontWeight: FontWeight.bold, color: const Color(0xFFE3A89C))),
              ],
            )
          ],
        ),
      ),
      body: estaCargando
          ? const Center(child: CircularProgressIndicator(color: Color(0xFFE3A89C)))
          : citas.isEmpty
              ? Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [Icon(Icons.directions_car_filled, size: 80, color: Colors.grey.shade800), const SizedBox(height: 20), Text('Ruta libre.\nEs el momento de agendar.', textAlign: TextAlign.center, style: TextStyle(fontSize: 16, color: Colors.grey.shade600))]))
              : ListView.builder(
                  padding: const EdgeInsets.all(12), itemCount: citas.length,
                  itemBuilder: (context, index) {
                    final cita = citas[index];
                    final horaInicio = obtenerHoraSegura(cita['fecha_hora_inicio']?.toString());
                    final horaFin = obtenerHoraSegura(cita['fecha_hora_fin']?.toString());
                    final estado = cita['estado'] ?? 'Pendiente';

                    return Card(
                      elevation: 4, color: const Color(0xFF1C1C1E), margin: const EdgeInsets.only(bottom: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15), side: const BorderSide(color: Colors.white10)),
                      child: ListTile(
                        contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 15),
                        leading: Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(color: estado == 'Confirmada' ? const Color(0x26FFC107) : const Color(0x26E3A89C), borderRadius: BorderRadius.circular(10)),
                          child: Icon(estado == 'Confirmada' ? Icons.thumb_up : Icons.schedule, color: estado == 'Confirmada' ? Colors.amber : const Color(0xFFE3A89C)),
                        ),
                        title: Text(cita['cliente'] ?? 'Sin nombre', style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Colors.white)),
                        subtitle: Padding(padding: const EdgeInsets.only(top: 8.0), child: Text('📍 ${cita['direccion'] ?? 'No registrada'}\n⏰ $horaInicio - $horaFin hrs', style: TextStyle(color: Colors.grey.shade400))),
                        trailing: const Icon(Icons.chevron_right, color: Colors.grey),
                        onTap: () async {
                          final resultado = await Navigator.push(context, MaterialPageRoute(builder: (context) => PantallaDetalleCita(cita: cita)));
                          if (resultado == true && mounted) obtenerCitas();
                        },
                      ),
                    );
                  },
                ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () async {
          final resultado = await Navigator.push(context, MaterialPageRoute(builder: (context) => const PantallaNuevaCita()));
          if (resultado == true && mounted) obtenerCitas();
        },
        backgroundColor: const Color(0xFFE3A89C), foregroundColor: const Color(0xFF111113), icon: const Icon(Icons.add), label: const Text('Crear Cita', style: TextStyle(fontWeight: FontWeight.bold)),
      ),
    );
  }
}

// ==========================================
// PESTAÑA 2: CITAS CULMINADAS 
// ==========================================
class PantallaCulminadas extends StatefulWidget {
  const PantallaCulminadas({super.key});
  @override
  State<PantallaCulminadas> createState() => _PantallaCulminadasState();
}

class _PantallaCulminadasState extends State<PantallaCulminadas> {
  List citas = [];
  bool estaCargando = true;

  @override
  void initState() { super.initState(); obtenerCitas(); }

  Future<void> obtenerCitas() async {
    if (!mounted) return;
    setState(() => estaCargando = true);
    try {
      final respuesta = await http.get(Uri.parse('$apiBaseUrl/citas'));
      if (respuesta.statusCode == 200 && mounted) {
        final List todas = json.decode(respuesta.body);
        setState(() {
          citas = todas.where((c) => c['estado'] == 'Completada' || c['estado'] == 'No Asistió').toList();
          estaCargando = false;
        });
      }
    } catch (e) { 
      if (mounted) setState(() => estaCargando = false); 
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('CITAS CULMINADAS', style: TextStyle(fontSize: 18, letterSpacing: 1.5))),
      body: estaCargando
          ? const Center(child: CircularProgressIndicator(color: Color(0xFFE3A89C)))
          : citas.isEmpty
              ? Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [Icon(Icons.fact_check, size: 80, color: Colors.grey.shade800), const SizedBox(height: 20), Text('Aún no hay citas culminadas.', textAlign: TextAlign.center, style: TextStyle(fontSize: 16, color: Colors.grey.shade600))]))
              : ListView.builder(
                  padding: const EdgeInsets.all(12), itemCount: citas.length,
                  itemBuilder: (context, index) {
                    final cita = citas[index];
                    final fechaStr = cita['fecha_hora_inicio']?.toString() ?? '';
                    final fecha = fechaStr.length >= 10 ? fechaStr.substring(0, 10) : 'N/A';
                    final estado = cita['estado'] ?? 'Pendiente';

                    return Card(
                      color: const Color(0xFF111113), margin: const EdgeInsets.only(bottom: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15), side: BorderSide(color: Colors.grey.shade800)),
                      child: ListTile(
                        leading: Icon(estado == 'Completada' ? Icons.check_circle : Icons.cancel, color: estado == 'Completada' ? Colors.green : Colors.redAccent),
                        title: Text(cita['cliente'] ?? 'Desconocido', style: TextStyle(fontWeight: FontWeight.bold, decoration: estado == 'No Asistió' ? TextDecoration.lineThrough : null, color: estado == 'No Asistió' ? Colors.red.shade300 : Colors.white)),
                        subtitle: Text('📅 $fecha\n💰 S/ ${cita['precio_total']}'),
                        onTap: () async {
                          final resultado = await Navigator.push(context, MaterialPageRoute(builder: (context) => PantallaDetalleCita(cita: cita)));
                          if (resultado == true && mounted) obtenerCitas();
                        },
                      ),
                    );
                  },
                ),
    );
  }
}

// ==========================================
// PESTAÑA 3: CLIENTAS (AQUÍ ESTÁ EL BOTÓN ELIMINAR)
// ==========================================
class PantallaClientes extends StatefulWidget {
  const PantallaClientes({super.key});
  @override
  State<PantallaClientes> createState() => _PantallaClientesState();
}

class _PantallaClientesState extends State<PantallaClientes> {
  List clientes = [];
  bool cargando = true;

  @override
  void initState() { super.initState(); obtenerClientes(); }

  Future<void> obtenerClientes() async {
    if (!mounted) return;
    try {
      final respuesta = await http.get(Uri.parse('$apiBaseUrl/clientes'));
      if (respuesta.statusCode == 200 && mounted) {
        setState(() { clientes = json.decode(respuesta.body); cargando = false; });
      }
    } catch (e) { 
      if (mounted) setState(() => cargando = false); 
    }
  }

  Future<void> eliminarCliente(int id) async {
    bool confirmar = await showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF1C1C1E),
        title: const Text('¿Eliminar clienta?'),
        content: const Text('Se borrará su perfil y todo su historial de citas. Esta acción no se puede deshacer.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar', style: TextStyle(color: Colors.grey))),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent),
            child: const Text('Sí, eliminar', style: TextStyle(color: Colors.white)),
          )
        ],
      )
    ) ?? false;

    if (confirmar) {
      try {
        final resp = await http.delete(Uri.parse('$apiBaseUrl/clientes/$id'));
        if (resp.statusCode == 200 && mounted) {
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Clienta eliminada', style: TextStyle(color: Colors.white)), backgroundColor: Colors.redAccent));
          obtenerClientes();
        }
      } catch (e) { debugPrint('Error: $e'); }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('CARTERA DE CLIENTAS', style: TextStyle(fontSize: 18, letterSpacing: 1.5))),
      body: cargando
          ? const Center(child: CircularProgressIndicator(color: Color(0xFFE3A89C)))
          : clientes.isEmpty
              ? const Center(child: Text('No hay clientas registradas.', style: TextStyle(color: Colors.grey)))
              : ListView.builder(
                  padding: const EdgeInsets.all(12), itemCount: clientes.length,
                  itemBuilder: (context, index) {
                    final c = clientes[index];
                    return Card(
                      color: const Color(0xFF1C1C1E), margin: const EdgeInsets.only(bottom: 8),
                      child: ListTile(
                        leading: const CircleAvatar(backgroundColor: Color(0xFF2C2C2E), child: Icon(Icons.face_3, color: Color(0xFFE3A89C))),
                        title: Text(c['nombre'] ?? 'Sin nombre', style: const TextStyle(fontWeight: FontWeight.bold)),
                        subtitle: Text('📱 WhatsApp: ${c['telefono'] ?? 'N/A'}\n📍 ${c['direccion'] ?? 'N/A'}'),
                        trailing: IconButton(
                          icon: const Icon(Icons.delete_forever, color: Colors.redAccent), 
                          onPressed: () => eliminarCliente(c['id_cliente'])
                        ),
                      ),
                    );
                  },
                ),
    );
  }
}
