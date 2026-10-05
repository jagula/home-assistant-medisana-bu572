"""Sensors for Medisana BU 572."""
from datetime import datetime
from homeassistant.components.sensor import SensorEntity,SensorDeviceClass,SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE,SIGNAL_STRENGTH_DECIBELS_MILLIWATT,UnitOfPressure
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from .const import DOMAIN
from .entity import MedisanaBU572Entity
async def async_setup_entry(hass:HomeAssistant,entry:ConfigEntry,async_add_entities):
    c=hass.data[DOMAIN][entry.entry_id]; es=[Global(c,'battery','battery',SensorDeviceClass.BATTERY,PERCENTAGE,SensorStateClass.MEASUREMENT,EntityCategory.DIAGNOSTIC),Global(c,'rssi','rssi',SensorDeviceClass.SIGNAL_STRENGTH,SIGNAL_STRENGTH_DECIBELS_MILLIWATT,SensorStateClass.MEASUREMENT,EntityCategory.DIAGNOSTIC),Global(c,'last_user','last_user')]
    for u in (1,2):
        es += [User(c,u,'systolic','systolic',SensorDeviceClass.PRESSURE,UnitOfPressure.MMHG,SensorStateClass.MEASUREMENT),User(c,u,'diastolic','diastolic',SensorDeviceClass.PRESSURE,UnitOfPressure.MMHG,SensorStateClass.MEASUREMENT),User(c,u,'map','map',SensorDeviceClass.PRESSURE,UnitOfPressure.MMHG,SensorStateClass.MEASUREMENT),User(c,u,'pulse','pulse',None,'bpm',SensorStateClass.MEASUREMENT),Timestamp(c,u),User(c,u,'status','status',None,None,None,EntityCategory.DIAGNOSTIC),History(c,u)]
    async_add_entities(es)
class Global(MedisanaBU572Entity,SensorEntity):
    def __init__(self,c,key,tkey,dc=None,unit=None,state=None,cat=None): super().__init__(c); self.key=key; self._attr_unique_id=f'{c.address}_{key}'; self._attr_translation_key=tkey; self._attr_device_class=dc; self._attr_native_unit_of_measurement=unit; self._attr_state_class=state; self._attr_entity_category=cat
    @property
    def native_value(self):return self.coordinator.data.get(self.key)
class User(MedisanaBU572Entity,SensorEntity):
    def __init__(self,c,u,key,tkey,dc=None,unit=None,state=None,cat=None): super().__init__(c); self.u=u; self.key=key; self._attr_unique_id=f'{c.address}_user_{u}_{key}'; self._attr_translation_key=tkey; self._attr_translation_placeholders={'user':str(u)}; self._attr_device_class=dc; self._attr_native_unit_of_measurement=unit; self._attr_state_class=state; self._attr_entity_category=cat
    @property
    def native_value(self):return self.coordinator.data.get('users',{}).get(str(self.u),{}).get(self.key)
class Timestamp(MedisanaBU572Entity,SensorEntity):
    _attr_device_class=SensorDeviceClass.TIMESTAMP
    def __init__(self,c,u): super().__init__(c); self.u=u; self._attr_unique_id=f'{c.address}_user_{u}_measurement_time'; self._attr_translation_key='measurement_time'; self._attr_translation_placeholders={'user':str(u)}
    @property
    def native_value(self):
        r=self.coordinator.data.get('users',{}).get(str(self.u),{}).get('measurement_time')
        if not r:return None
        try:return datetime.fromisoformat(r)
        except (TypeError,ValueError):return None


class History(MedisanaBU572Entity,SensorEntity):
    """Expose the most recent stored measurements for dashboard rendering."""
    _attr_entity_category=EntityCategory.DIAGNOSTIC
    _attr_icon='mdi:clipboard-pulse'
    def __init__(self,c,u):
        super().__init__(c); self.u=u
        self._attr_unique_id=f'{c.address}_user_{u}_history'
        self._attr_name=f'Benutzer {u} Messhistorie'
    @property
    def native_value(self):
        return len(self.coordinator.data.get('history',{}).get(str(self.u),[]))
    @property
    def extra_state_attributes(self):
        return {'measurements':self.coordinator.data.get('history',{}).get(str(self.u),[])[:30], 'stored_measurements': len(self.coordinator.data.get('history',{}).get(str(self.u),[]))}


