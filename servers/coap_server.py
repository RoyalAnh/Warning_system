"""
CoAP server để nhận dữ liệu từ ESP32
"""

import asyncio
import json
from aiocoap import Context, Message, resource, POST
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
            logger.info(f"[CoAP] POST from {client_addr}")

            # Parse payload
            sensor_data = parser.parse_coap_payload(request.payload)

            if sensor_data is None:
                logger.error("[CoAP] Payload parse error")
                return Message(
                    code=POST,
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
                code=POST,
                payload=json.dumps(response_data).encode()
            )

        except Exception as e:
            logger.error(f"[CoAP] Error: {e}", exc_info=True)
            return Message(
                code=POST,
                payload=json.dumps({
                    "status": "error",
                    "message": str(e)
                }).encode()
            )


def start_coap_server():
    """
    Khởi động CoAP server (chạy trong thread riêng)
    """

    async def main():
        root = resource.Site()

        # Register resource
        root.add_resource(['api', 'records', 'upload'], SensorDataResource())

        # Fix Windows: 0.0.0.0 → 127.0.0.1
        host = settings.get_coap_host()
        port = settings.COAP_PORT

        try:
            await Context.create_server_context(root, bind=(host, port))
            logger.info(f"[CoAP] Server started at coap://{host}:{port}/api/records/upload")

        except Exception as e:
            logger.error(f"[CoAP] Failed to start: {e}", exc_info=True)
            return

        # Keep the server alive
        await asyncio.get_running_loop().create_future()

    asyncio.run(main())
