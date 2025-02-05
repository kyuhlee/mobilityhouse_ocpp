import asyncio
import logging
from datetime import datetime
from argparse import Namespace
from pyjfuzz.lib import *

try:
    import websockets
except ModuleNotFoundError:
    print("This example relies on the 'websockets' package.")
    print("Please install it by running: ")
    print()
    print(" $ pip install websockets")
    import sys

    sys.exit(1)

from ocpp.routing import on
from ocpp.v201 import ChargePoint as cp
from ocpp.v201 import call_result
from ocpp.v201 import call

logging.basicConfig(level=logging.INFO)

# Heartbeat: '[2,"3f2409f0-85a7-426c-982d-77e0e6412356","Heartbeat",{}]'
#fuzz_config = PJFConfiguration(Namespace(json={"test": ["1", 2, True]}, nologo=True, level=6))
fuzz_config = PJFConfiguration(Namespace(json=[1, "A", "Heartbeat", {}], nologo=True, level=3, debug=True))
fuzzer = PJFFactory(fuzz_config)


class ChargePoint(cp):
    @on("BootNotification")
    def on_boot_notification(self, charging_station, reason, **kwargs):
        print("Got a BootNotification!")
        return call_result.BootNotification(
            current_time=datetime.utcnow().isoformat(), interval=10, status="Accepted"
        )

    @on("Heartbeat")
    def on_heartbeat(self):
        print("Got a Heartbeat!")
        return call_result.Heartbeat(
            current_time=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S") + "Z"
        )


async def on_connect(websocket, path):
    """For every new charge point that connects, create a ChargePoint
    instance and start listening for messages.
    """
    try:
        requested_protocols = websocket.request_headers["Sec-WebSocket-Protocol"]
    except KeyError:
        logging.error("Client hasn't requested any Subprotocol. Closing Connection")
        return await websocket.close()
    if websocket.subprotocol:
        logging.info("Protocols Matched: %s", websocket.subprotocol)
    else:
        # In the websockets lib if no subprotocols are supported by the
        # client and the server, it proceeds without a subprotocol,
        # so we have to manually close the connection.
        logging.warning(
            "Protocols Mismatched | Expected Subprotocols: %s,"
            " but client supports %s | Closing connection",
            websocket.available_subprotocols,
            requested_protocols,
        )
        return await websocket.close()

    charge_point_id = path.strip("/")
    charge_point = ChargePoint(charge_point_id, websocket)

    await charge_point.start()

def prepare_payload(type=2):
    if type == 1:
        payload = call.Heartbeat()
    elif type == 2:
        payload = call.BootNotification(
            charging_station={"model": "Wallbox XYZ", "vendor_name": "anewone"},
            reason="PowerUp",
        )
    else:
        payload = "invalid"

    print("[KYU] prepare_payload: ", payload)
    return payload

async def main():

    print("[KYU] test wrapper start")
    charge_point_id = "test_cp"

    charge_point = ChargePoint(charge_point_id)

    json_test = False
    fuzz_test = False
    if json_test == True:
        if fuzz_test == True:
            max_loop = 1000
        else:
            max_loop = 1

        for i in range(0, max_loop):
            if fuzz_test == True:
                payload = fuzzer.fuzzed
                payload = "[2" + payload[payload.find(","):]
            else:
                payload = '[4,"3f2409f0-85a7-426c-982d-77e0e6412356","Heartbeat",{}]'
                payload = '[2, false, False, {}]' # cause type error
                #payload = '[2, ["A"], ["Heartbeat"], {}]' # cause unhashable type error
                #payload = '[2,"fc54df3e-16ff-4a17-a96f-5f28f1808aac","BootNotification",{"chargingStation":{"model":"Wallbox XYZ","vendorName":"anewone"},"reason":"PowerUp"}]'
            print("[KYU] Iteration #%d: "% i, payload)
            await charge_point.route_message(payload)
    else:
        payload = prepare_payload(2)
        await charge_point.localcall(payload)


    #await charge_point.start(message)
    #  deepcode ignore BindToAllNetworkInterfaces: <Example Purposes>
    """
    server = await websockets.serve(
        on_connect, "0.0.0.0", 9000, subprotocols=["ocpp2.0.1"]
    )

    logging.info("Server Started listening to new connections...")
    await server.wait_closed()
"""
if __name__ == "__main__":
    # asyncio.run() is used when running this example with Python >= 3.7v
    asyncio.run(main())
