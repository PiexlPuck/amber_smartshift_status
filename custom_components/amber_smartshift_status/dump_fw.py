from coordinator import AmberSmartShiftCoordinator
import asyncio
from homeassistant.core import HomeAssistant

async def main():
    coord = AmberSmartShiftCoordinator(None)
    data = await coord._async_update_data()
    import json
    print(json.dumps(data["Fleet-wide"], indent=2))

asyncio.run(main())
