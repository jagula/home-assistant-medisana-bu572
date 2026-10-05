"""Config flow for Medisana BU 572."""
from typing import Any
import voluptuous as vol
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigFlow,ConfigFlowResult
from homeassistant.const import CONF_ADDRESS
from .const import DOMAIN
def norm(a:str)->str:return a.strip().upper()
class MedisanaBU572ConfigFlow(ConfigFlow,domain=DOMAIN):
    VERSION=1
    def __init__(self): self._disc=None
    async def async_step_bluetooth(self,discovery_info:bluetooth.BluetoothServiceInfoBleak)->ConfigFlowResult:
        a=norm(discovery_info.address); await self.async_set_unique_id(a); self._abort_if_unique_id_configured(); self._disc=discovery_info; self.context["title_placeholders"]={"name":discovery_info.name or "BU 572"}; return await self.async_step_confirm()
    async def async_step_confirm(self,user_input:dict[str,Any]|None=None)->ConfigFlowResult:
        if user_input is not None and self._disc is not None:
            a=norm(self._disc.address); return self.async_create_entry(title=f"Medisana BU 572 ({a[-5:]})",data={CONF_ADDRESS:a})
        return self.async_show_form(step_id="confirm",description_placeholders={"name":self._disc.name if self._disc else "BU 572"})
    async def async_step_user(self,user_input:dict[str,Any]|None=None)->ConfigFlowResult:
        if user_input is not None:
            a=norm(user_input[CONF_ADDRESS]); await self.async_set_unique_id(a); self._abort_if_unique_id_configured(); return self.async_create_entry(title=f"Medisana BU 572 ({a[-5:]})",data={CONF_ADDRESS:a})
        dev={}
        for info in bluetooth.async_discovered_service_info(self.hass,connectable=True):
            if (info.name or '').strip()=='BU 572':
                a=norm(info.address); dev[a]=f"BU 572 – {a} – RSSI {info.rssi} dBm"
        schema=vol.Schema({vol.Required(CONF_ADDRESS):vol.In(dev)}) if dev else vol.Schema({vol.Required(CONF_ADDRESS):str})
        return self.async_show_form(step_id="user",data_schema=schema)
