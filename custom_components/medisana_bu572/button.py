"""Button for Medisana BU 572."""
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from .const import DOMAIN
from .entity import MedisanaBU572Entity
async def async_setup_entry(hass:HomeAssistant,entry:ConfigEntry,async_add_entities): async_add_entities([Sync(hass.data[DOMAIN][entry.entry_id])])
class Sync(MedisanaBU572Entity,ButtonEntity):
    _attr_translation_key='sync'; _attr_entity_category=EntityCategory.CONFIG
    def __init__(self,c):super().__init__(c);self._attr_unique_id=f'{c.address}_sync'
    async def async_press(self):await self.coordinator.async_sync()
