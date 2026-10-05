"""Medisana BU 572 integration."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN,PLATFORMS
from .coordinator import MedisanaBU572Coordinator
async def async_setup_entry(hass:HomeAssistant,entry:ConfigEntry)->bool:
    c=MedisanaBU572Coordinator(hass,entry); await c.async_setup(); hass.data.setdefault(DOMAIN,{})[entry.entry_id]=c; await hass.config_entries.async_forward_entry_setups(entry,PLATFORMS); return True
async def async_unload_entry(hass:HomeAssistant,entry:ConfigEntry)->bool:
    ok=await hass.config_entries.async_unload_platforms(entry,PLATFORMS)
    if ok:
        c=hass.data[DOMAIN].pop(entry.entry_id); await c.async_shutdown()
    return ok
