from flask import Flask, request, jsonify
from flask_cors import CORS
from functools import wraps
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import traceback
import os

# Importaciones simuladas - en un entorno real, estos serían módulos reales
# from datatypes import SistemaQuantumBiMoType, PaqueteBiMoType
# from database_module import Database

# ==================== CONFIGURACIÓN DE LA APLICACIÓN ====================

app = Flask(__name__)
CORS(app)  # Permitir CORS para desarrollo frontend

# Configuración
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'quantum-secret-key-dev')
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== SIMULACIÓN DE CLASES (reemplazar por las reales) ====================

class MockSistemaQuantumBiMoType:
    """Simulación de la clase SistemaQuantumBiMoType"""
    def encode_quantum_message(self, message: str) -> Dict[str, Any]:
        return {
            'id_mensaje': 'BiMO-' + str(hash(message))[:8],
            'timestamp': datetime.utcnow().isoformat(),
            'quantum_data': f'encoded_{message}',
            'qubits_count': len(message)
        }
    
    def decode_quantum_transmission(self, paquete: Dict, measurements: list) -> Dict[str, Any]:
        return {
            'mensaje_decodificado': 'QUANTUM MESSAGE DECODED',
            'estado': 'SUCCESS',
            'metricas_cuanticas': {
                'fidelidad': 0.95,
                'error_rate': 0.05,
                'coherencia': 0.92
            }
        }

class MockDatabase:
    """Simulación de la clase Database"""
    def __init__(self):
        self.storage = {}
        self.metrics = {}
    
    def save_transmission_history(self, user_id: str, paquete: Dict) -> bool:
        key = f"{user_id}_{paquete['id_mensaje']}"
        self.storage[key] = paquete
        logger.info(f"Paquete guardado: {key}")
        return True
    
    def get_package_by_id(self, package_id: str) -> Optional[Dict]:
        for key, value in self.storage.items():
            if value['id_mensaje'] == package_id:
                return value
        return None
    
    def update_metrics(self, package_id: str, metrics: Dict) -> bool:
        self.metrics[package_id] = metrics
        logger.info(f"Métricas actualizadas para: {package_id}")
        return True

class MockAuthService:
    """Simulación del servicio de autenticación"""
    def get_user_from_token(self, token: str) -> Optional[Dict]:
        # En producción, aquí validarías el JWT o token de sesión
        if token and token.startswith('valid_'):
            return {
                'id': token.replace('valid_', ''),
                'username': f'user_{token[-4:]}',
                'tier': 'premium'
            }
        return None

# ==================== INICIALIZACIÓN DE SERVICIOS ====================

sistema_bimo = MockSistemaQuantumBiMoType()
db = MockDatabase()
auth_service = MockAuthService()

# ==================== DECORADORES Y MIDDLEWARE ====================

def require_auth(f):
    """Decorador para requerir autenticación"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_token = request.headers.get('Authorization')
        if not auth_token and request.is_json:
            auth_token = request.json.get('auth_token')
        
        if not auth_token:
            return jsonify({
                'status': 'error',
                'message': 'Token de autorización requerido',
                'code': 'UNAUTHORIZED'
            }), 401
        
        # Remover "Bearer " si está presente
        if auth_token.startswith('Bearer '):
            auth_token = auth_token[7:]
        
        user = auth_service.get_user_from_token(auth_token)
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'Token inválido o expirado',
                'code': 'INVALID_TOKEN'
            }), 401
        
        request.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function

def handle_api_errors(f):
    """Decorador para manejo centralizado de errores"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            logger.warning(f"Error de validación: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Datos de entrada inválidos',
                'details': str(e),
                'code': 'VALIDATION_ERROR'
            }), 400
        except Exception as e:
            logger.error(f"Error interno: {str(e)}\n{traceback.format_exc()}")
            return jsonify({
                'status': 'error',
                'message': 'Error interno del servidor',
                'code': 'INTERNAL_ERROR'
            }), 500
    
    return decorated_function

# ==================== RUTAS DE LA API ====================

@app.route('/', methods=['GET'])
def health_check():
    """Endpoint de verificación de salud"""
    return jsonify({
        'status': 'success',
        'message': 'QuantumLink API está funcionando',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/v1/encode', methods=['POST'])
@require_auth
@handle_api_errors
def api_encode_message():
    """
    Endpoint para codificar un mensaje cuántico.
    
    Body JSON esperado:
    {
        "message": "string - El mensaje a codificar",
        "options": {
            "encoding_type": "BiMO",
            "priority": "high|medium|low"
        }
    }
    """
    data = request.get_json()
    
    if not data:
        raise ValueError("Se requiere un cuerpo JSON válido")
    
    message = data.get('message')
    if not isinstance(message, str) or not message.strip():
        raise ValueError("El campo 'message' debe ser una cadena no vacía")
    
    if len(message) > 1000:  # Límite de caracteres
        raise ValueError("El mensaje no puede exceder 1000 caracteres")
    
    # Opciones adicionales
    options = data.get('options', {})
    encoding_type = options.get('encoding_type', 'BiMO')
    priority = options.get('priority', 'medium')
    
    logger.info(f"Codificando mensaje para usuario {request.current_user['id']}")
    
    # Lógica principal: usar la clase cuántica
    paquete = sistema_bimo.encode_quantum_message(message.strip())
    
    # Agregar metadatos adicionales
    paquete.update({
        'user_id': request.current_user['id'],
        'encoding_type': encoding_type,
        'priority': priority,
        'created_at': datetime.utcnow().isoformat()
    })
    
    # Almacenar en la base de datos
    db.save_transmission_history(request.current_user['id'], paquete)
    
    return jsonify({
        'status': 'success',
        'data': {
            'package_id': paquete['id_mensaje'],
            'timestamp': paquete['timestamp'],
            'qubits_count': paquete.get('qubits_count', 0),
            'encoding_type': encoding_type
        },
        'message': 'Mensaje codificado exitosamente'
    }), 201

@app.route('/api/v1/decode', methods=['POST'])
@require_auth
@handle_api_errors
def api_decode_message():
    """
    Endpoint para decodificar un paquete cuántico.
    
    Body JSON esperado:
    {
        "package_id": "string - ID del paquete a decodificar",
        "measurements": [
            {"energia_medida": 5.5, "timestamp": "..."},
            {"energia_medida": 2.9, "timestamp": "..."}
        ]
    }
    """
    data = request.get_json()
    
    if not data:
        raise ValueError("Se requiere un cuerpo JSON válido")
    
    package_id = data.get('package_id')
    measurements = data.get('measurements')
    
    if not package_id:
        raise ValueError("El campo 'package_id' es requerido")
    
    if not measurements or not isinstance(measurements, list):
        raise ValueError("El campo 'measurements' debe ser una lista no vacía")
    
    logger.info(f"Decodificando paquete {package_id} para usuario {request.current_user['id']}")
    
    # Recuperar el paquete original
    paquete_original = db.get_package_by_id(package_id)
    if not paquete_original:
        return jsonify({
            'status': 'error',
            'message': 'Paquete no encontrado',
            'code': 'PACKAGE_NOT_FOUND'
        }), 404
    
    # Verificar que el paquete pertenezca al usuario actual
    if paquete_original.get('user_id') != request.current_user['id']:
        return jsonify({
            'status': 'error',
            'message': 'No tienes permiso para acceder a este paquete',
            'code': 'FORBIDDEN'
        }), 403
    
    # Lógica principal: decodificar
    resultado = sistema_bimo.decode_quantum_transmission(paquete_original, measurements)
    
    # Almacenar métricas
    db.update_metrics(package_id, resultado.get('metricas_cuanticas', {}))
    
    return jsonify({
        'status': 'success',
        'data': {
            'package_id': package_id,
            'decoded_message': resultado.get('mensaje_decodificado'),
            'transmission_status': resultado.get('estado'),
            'metrics': resultado.get('metricas_cuanticas'),
            'decoded_at': datetime.utcnow().isoformat()
        },
        'message': 'Mensaje decodificado exitosamente'
    })

@app.route('/api/v1/packages', methods=['GET'])
@require_auth
@handle_api_errors
def get_user_packages():
    """Obtener el historial de paquetes del usuario"""
    user_id = request.current_user['id']
    
    # Filtrar paquetes del usuario
    user_packages = []
    for key, paquete in db.storage.items():
        if paquete.get('user_id') == user_id:
            package_summary = {
                'package_id': paquete['id_mensaje'],
                'timestamp': paquete['timestamp'],
                'encoding_type': paquete.get('encoding_type', 'BiMO'),
                'qubits_count': paquete.get('qubits_count', 0),
                'status': 'encoded'
            }
            
            # Agregar métricas si existen
            if paquete['id_mensaje'] in db.metrics:
                package_summary['metrics'] = db.metrics[paquete['id_mensaje']]
                package_summary['status'] = 'decoded'
            
            user_packages.append(package_summary)
    
    return jsonify({
        'status': 'success',
        'data': {
            'packages': user_packages,
            'total_count': len(user_packages)
        },
        'message': f'Se encontraron {len(user_packages)} paquetes'
    })

@app.route('/api/v1/packages/<package_id>', methods=['GET'])
@require_auth
@handle_api_errors
def get_package_details(package_id: str):
    """Obtener detalles específicos de un paquete"""
    paquete = db.get_package_by_id(package_id)
    
    if not paquete:
        return jsonify({
            'status': 'error',
            'message': 'Paquete no encontrado',
            'code': 'PACKAGE_NOT_FOUND'
        }), 404
    
    if paquete.get('user_id') != request.current_user['id']:
        return jsonify({
            'status': 'error',
            'message': 'No tienes permiso para acceder a este paquete',
            'code': 'FORBIDDEN'
        }), 403
    
    # Agregar métricas si existen
    metrics = db.metrics.get(package_id)
    
    return jsonify({
        'status': 'success',
        'data': {
            'package': paquete,
            'metrics': metrics
        }
    })

# ==================== MANEJO DE ERRORES GLOBALES ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'status': 'error',
        'message': 'Endpoint no encontrado',
        'code': 'NOT_FOUND'
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'status': 'error',
        'message': 'Método HTTP no permitido',
        'code': 'METHOD_NOT_ALLOWED'
    }), 405

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'status': 'error',
        'message': 'Error interno del servidor',
        'code': 'INTERNAL_ERROR'
    }), 500

# ==================== FUNCIÓN PRINCIPAL ====================

def create_app():
    """Factory para crear la aplicación Flask"""
    return app

if __name__ == '__main__':
    logger.info("Iniciando QuantumLink SaaS API...")
    
    # Configuración para desarrollo
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )