import asyncio
import logging

import voluptuous as vol

from homeassistant.components import light
from homeassistant.const import (
    ATTR_ENTITY_ID
)
from homeassistant.core import HomeAssistant, ServiceCall


from homeassistant.helpers import service
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType

from typing import Any


_LOGGER = logging.getLogger(__name__)

SHORT = 0.5
LONG = 1
BREAK = SHORT
MORSE = {
    'a': [SHORT, LONG],
    'b': [LONG, SHORT, SHORT, SHORT],
    'c': [LONG, SHORT, LONG, SHORT],
    'd': [LONG, SHORT, SHORT],
    'e': [SHORT],
    'f': [SHORT, SHORT, LONG, SHORT],
    'g': [LONG, LONG, SHORT],
    'h': [SHORT, SHORT, SHORT, SHORT],
    'i': [SHORT, SHORT],
    'j': [SHORT, LONG, LONG, LONG],
    'k': [LONG, SHORT, LONG],
    'l': [SHORT, LONG, SHORT, SHORT],
    'm': [LONG, LONG],
    'n': [LONG, SHORT],
    'o': [LONG, LONG, LONG],
    'p': [SHORT, LONG, LONG, SHORT],
    'q': [LONG, LONG, SHORT, LONG],
    'r': [SHORT, LONG, SHORT],
    's': [SHORT, SHORT, SHORT],
    't': [LONG],
    'u': [SHORT, SHORT, LONG],
    'v': [SHORT, SHORT, SHORT, LONG],
    'w': [SHORT, LONG, LONG],
    'x': [LONG, SHORT, SHORT, LONG],
    'y': [LONG, SHORT, LONG, LONG],
    'z': [LONG, LONG, SHORT, SHORT],
}

DOMAIN = 'morse'

DOMAIN_SCHEMA = vol.Schema({
})

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: DOMAIN_SCHEMA
    },
    extra=vol.ALLOW_EXTRA
)

ATTR_MESSAGE = 'message'
ATTR_TARGETS = 'targets'

SERVICE_SAY = 'say'
SAY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_MESSAGE): cv.string,
        vol.Optional(ATTR_TARGETS, default=[]): cv.entities_domain(light.DOMAIN)
    }
)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:

    async def say(call: ServiceCall) -> None:
        message = call.data.get(ATTR_MESSAGE)
        targets = call.data.get(ATTR_TARGETS)

        helper = Helper(hass, targets)
        await helper.say(message)

    service.async_register_admin_service(
        hass,
        DOMAIN,
        SERVICE_SAY,
        say,
        SAY_SCHEMA,
    )

    return True

class Helper():

    def __init__(self, hass: HomeAssistant, targets: [str]):
        self.hass = hass
        self.targets = targets

    def message_to_signals(self, message: str) -> [Any]:
        signals = []
        lower_msg = message.lower()

        for char in lower_msg:
            signals.append((0, BREAK))
            if char in MORSE:
                char_signals = MORSE.get(char)
                for signal_length in char_signals:
                    signals.append((255, signal_length))
                    signals.append((0, BREAK))
            elif char == ' ':
                signals.append((0, BREAK))

        return signals

    async def async_turn_on(self, brightness: int) -> None:
        for target in self.targets:
            data = {
                'brightness': brightness
            }
            data[ATTR_ENTITY_ID] = target

            _LOGGER.debug("Forwarded turn_on command: %s", data)

            await self.hass.services.async_call(
                light.DOMAIN,
                light.SERVICE_TURN_ON,
                data,
                blocking = True,
            )

    async def say(self, message: str):
        signals = self.message_to_signals(message)

        for (brightness, length) in signals:
            await self.async_turn_on(brightness)
            await asyncio.sleep(length)
        

