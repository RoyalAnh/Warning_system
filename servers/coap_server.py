"""
CoAP server để nhận dữ liệu từ ESP32
"""

import asyncio
import json
from aiocoap import Context, Message, resource, CHANGED, INTERNAL_SERVER_ERROR, BAD_REQUEST
from config.settings import settings
from services.data_parser import parser
from services.severity_analyzer import analyzer
from database.mongodb import get_sensor_collection
from utils.logger import setup_logger

logger = setup_logger(__name__)


class SensorDataResource(resource.Resource):
    """CoAP resource để nhận dữ liệu sensor"""

    async def render_post(self, request):
        """
        Xử lý POST request từ ESP32
        """

        try:
            client_addr = f"{request.remote.hostinfo}"
            logger.info(f"[CoAP] ===== RECEIVED POST REQUEST =====")
            logger.info(f"[CoAP] Client: {client_addr}")
            logger.info(f"[CoAP] Payload size: {len(request.payload)} bytes")
            logger.info(f"[CoAP] Raw payload: {request.payload[:100]}")  # First 100 bytes

            # Parse payload
            sensor_data = parser.parse_coap_payload(request.payload)

            if sensor_data is None:
                logger.error("[CoAP] Payload parse error")
                return Message(
                    code=BAD_REQUEST,
                    payload=json.dumps({
                        "status": "error",
                        "message": "Invalid payload"
                    }).encode()
                )

            # Analyze severity
            severity = analyzer.calculate_severity(sensor_data)
            sensor_data.severity = severity

            logger.info(
                f"[CoAP] Device={sensor_data.deviceId}, "
                f"Severity={severity}, "
                f"Tilt={sensor_data.data.tilt_angle:.2f}°"
            )

            # Save to MongoDB
            result = get_sensor_collection().insert_one(sensor_data.to_dict())
            logger.info(f"[MongoDB] Saved, ID={result.inserted_id}")

            # Response
            response_data = {
                "status": "success",
                "severity": severity,
                "message": analyzer.get_severity_description(severity)
            }

            return Message(
                code=CHANGED,
                payload=json.dumps(response_data).encode()
            )

        except Exception as e:
            logger.error(f"[CoAP] Error: {e}", exc_info=True)
            return Message(
                code=INTERNAL_SERVER_ERROR,
                payload=json.dumps({
                    "status": "error",
                    "message": str(e)
                }).encode()
            )


async def start_coap_server():
    """
    Khởi động CoAP server (async version)
    """
    root = resource.Site()

    # Register resource
    root.add_resource(['api', 'records', 'upload'], SensorDataResource())

    # Fix Windows: 0.0.0.0 → 127.0.0.1
    host = settings.get_coap_host()
    port = settings.COAP_PORT

    context = None
    try:
        context = await Context.create_server_context(root, bind=(host, port))
        logger.info(f"[CoAP] ===================================")
        logger.info(f"[CoAP] Server started successfully!")
        logger.info(f"[CoAP] Binding to: {host}:{port}")
        logger.info(f"[CoAP] Endpoint: coap://{host}:{port}/api/records/upload")
        logger.info(f"[CoAP] Protocol: UDP")
        logger.info(f"[CoAP] Waiting for POST requests...")
        logger.info(f"[CoAP] ===================================")

    except PermissionError as e:
        logger.error(f"[CoAP] Permission denied - Port {port} requires privileges")
        logger.error(f"[CoAP] Run with CAP_NET_BIND_SERVICE or use port > 1024")
        raise
    except Exception as e:
        logger.error(f"[CoAP] Failed to start: {e}", exc_info=True)
        raise

    # Keep server running forever
    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        logger.info("[CoAP] Server shutting down...")
        if context:
            await context.shutdown()
    except Exception as e:
        logger.error(f"[CoAP] Runtime error: {e}", exc_info=True)
        raise
