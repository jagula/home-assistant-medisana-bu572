"""Base entity."""
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from .const import DOMAIN
class MedisanaBU572Entity(Entity):
    _attr_has_entity_name=True
    def __init__(self,c):
        self.coordinator=c; self._attr_device_info=DeviceInfo(identifiers={(DOMAIN,c.address)},name="Medisana BU 572",manufacturer="Medisana",model="BU 572 connect",connections={("bluetooth",c.address)})
    async def async_added_to_hass(self): self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))
