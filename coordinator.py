"""Bluetooth communication for Medisana BU 572."""
from __future__ import annotations
import asyncio,time,logging
from copy import deepcopy
from datetime import datetime, timedelta
from typing import Any
from bleak_retry_connector import BleakClientWithServiceCache,establish_connection
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant,callback
from homeassistant.helpers.storage import Store
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util
from .const import *
_LOGGER=logging.getLogger(__name__)

def sfloat(b:bytes):
    if len(b)!=2:return None
    v=int.from_bytes(b,'little'); m=v&0x0fff; e=(v>>12)&0xf
    if m in (0x07ff,0x0800,0x0801,0x0802):return None
    if m&0x0800:m-=0x1000
    if e&0x08:e-=0x10
    return float(m*(10**e))

def parse_bp(data:bytes):
    if len(data)<7:return None
    f=data[0]; pos=1; vals=[]
    for _ in range(3): vals.append(sfloat(data[pos:pos+2])); pos+=2
    if any(v is None for v in vals): return None
    sys,dia,mapv=vals
    if f&1: sys*=7.50061683; dia*=7.50061683; mapv*=7.50061683
    mt=None
    if f&2:
        if len(data)<pos+7:return None
        y=int.from_bytes(data[pos:pos+2],'little'); mo,da,h,mi,se=data[pos+2:pos+7]; pos+=7
        try: mt=datetime(y,mo,da,h,mi,se,tzinfo=dt_util.DEFAULT_TIME_ZONE)
        except ValueError: mt=None
    pulse=None
    if f&4:
        if len(data)<pos+2:return None
        pulse=sfloat(data[pos:pos+2]); pos+=2
    raw=user=None
    if f&8:
        if len(data)<pos+1:return None
        raw=data[pos]; pos+=1
        if raw in (0,1): user=raw+1
    status=None
    if f&16:
        if len(data)<pos+2:return None
        status=int.from_bytes(data[pos:pos+2],'little')
    return {'systolic':round(sys,1),'diastolic':round(dia,1),'map':round(mapv,1),'pulse':None if pulse is None else round(pulse,1),'measurement_time':mt,'user':user,'user_raw':raw,'status':status}

class MedisanaBU572Coordinator:
    def __init__(self,hass:HomeAssistant,entry:ConfigEntry):
        self.hass=hass; self.entry=entry; self.address=entry.data[CONF_ADDRESS].upper(); self.data={'battery':None,'rssi':None,'last_user':None,'last_sync':None,'users':{'1':{},'2':{}},'history':{'1':[],'2':[]}}; self._listeners=[]; self._cancel=None; self._lock=asyncio.Lock(); self._task=None; self._store=Store(hass,1,f"{DOMAIN}.{entry.entry_id}"); self._event=asyncio.Event(); self._last_pkt=0.0; self._count=0; self._auto_unsub=None; self._last_auto_sync=0.0; self._auto_cooldown=45.0
    async def async_setup(self):
        saved=await self._store.async_load()
        if isinstance(saved,dict): self.data.update(saved)
        self.data.setdefault('users',{}); self.data['users'].setdefault('1',{}); self.data['users'].setdefault('2',{}); self.data.setdefault('history',{}); self.data['history'].setdefault('1',[]); self.data['history'].setdefault('2',[])
        @callback
        def found(info,change):
            self.data['rssi']=info.rssi
            self._notify()
            self._auto_schedule('advertisement')
        self._cancel=bluetooth.async_register_callback(self.hass,found,{'address':self.address},bluetooth.BluetoothScanningMode.ACTIVE,replay=bluetooth.BluetoothCallbackReplay.NEWEST_FIRST,scan_interval=60.0,scan_duration=10.0)
        @callback
        def auto_watch(_now):
            if bluetooth.async_address_present(self.hass, self.address, connectable=True):
                self._auto_schedule('presence poll')

        self._auto_unsub = async_track_time_interval(
            self.hass, auto_watch, timedelta(seconds=10)
        )
        if bluetooth.async_address_present(self.hass,self.address,connectable=True):
            self._auto_schedule('startup presence')
    async def async_shutdown(self):
        if self._cancel:self._cancel();self._cancel=None
        if self._task and not self._task.done():self._task.cancel()
        if self._auto_unsub:
            self._auto_unsub(); self._auto_unsub=None
    @callback
    def async_add_listener(self,l):
        self._listeners.append(l)
        @callback
        def rm():
            if l in self._listeners:self._listeners.remove(l)
        return rm
    @callback
    def _notify(self):
        for l in tuple(self._listeners):l()
    @callback
    def _auto_schedule(self,reason):
        now=time.monotonic()
        if self._task and not self._task.done():
            _LOGGER.debug('BU 572 Auto-Sync skipped (%s): sync already running',reason)
            return
        remaining=self._auto_cooldown-(now-self._last_auto_sync)
        if remaining>0:
            _LOGGER.debug('BU 572 Auto-Sync cooldown (%s): %.1f s remaining',reason,remaining)
            return
        self._last_auto_sync=now
        self._schedule()

    @callback
    def _schedule(self):
        if self._task and not self._task.done():return
        self._task=self.hass.async_create_task(self.async_sync(),f"{DOMAIN}_{self.address}_sync")
    async def async_sync(self):
        if self._lock.locked():return
        async with self._lock:
            dev=bluetooth.async_ble_device_from_address(self.hass,self.address,connectable=True)
            if dev is None: _LOGGER.debug('%s not reachable',self.address); return
            info=bluetooth.async_last_service_info(self.hass,self.address,connectable=True)
            if info:self.data['rssi']=info.rssi
            client=None; self._count=0; self._event.clear(); self._last_pkt=0.0
            try:
                _LOGGER.debug('Connecting to BU 572 %s via best available Bluetooth path',self.address)
                client=await establish_connection(BleakClientWithServiceCache,dev,'Medisana BU 572',max_attempts=3,pair=True,use_services_cache=True,timeout=20.0)
                try:
                    b=await client.read_gatt_char(BATTERY_UUID)
                    if b:self.data['battery']=int(b[0]);self._notify()
                except Exception as e:_LOGGER.debug('Battery read failed: %s',e)
                now=dt_util.now(); ct=bytes([now.year&255,(now.year>>8)&255,now.month,now.day,now.hour,now.minute,now.second,now.isoweekday(),0,1])
                try: await client.write_gatt_char(CURRENT_TIME_UUID,ct,response=True)
                except Exception as e:
                    _LOGGER.debug('Current Time write failed (%s); retry pairing',e)
                    try: await client.pair(); await client.write_gatt_char(CURRENT_TIME_UUID,ct,response=True)
                    except Exception as pe: _LOGGER.warning('BU 572 authentication/current-time failed: %s',pe); return
                def cb(sender,payload):
                    p=parse_bp(bytes(payload))
                    if p is not None:self.hass.loop.call_soon_threadsafe(self._handle,p)
                    else:_LOGGER.warning('Could not decode BU 572 payload: %s',bytes(payload).hex(' '))
                await client.start_notify(BP_MEAS_UUID,cb); _LOGGER.debug('BU 572 indication subscription active')
                start=time.monotonic(); first=start+FIRST_PACKET_TIMEOUT
                while True:
                    n=time.monotonic()
                    if n-start>=MAX_SESSION_SECONDS:break
                    if self._count==0:
                        timeout=max(.1,first-n)
                        if timeout<=.1:break
                    else:
                        q=QUIET_SECONDS-(n-self._last_pkt)
                        if q<=0:break
                        timeout=q
                    self._event.clear()
                    try: await asyncio.wait_for(self._event.wait(),timeout=timeout)
                    except TimeoutError:
                        if self._count==0 or time.monotonic()-self._last_pkt>=QUIET_SECONDS:break
                try: await client.stop_notify(BP_MEAS_UUID)
                except Exception: pass
                self.data['last_sync']=dt_util.utcnow().isoformat(); self._store.async_delay_save(lambda:deepcopy(self.data),1.0); self._notify(); _LOGGER.info('BU 572 sync finished: %d measurement packet(s)',self._count)
                if self._count==0:
                    self._last_auto_sync=max(0.0,time.monotonic()-self._auto_cooldown+10.0)
            except asyncio.CancelledError: raise
            except Exception as e:_LOGGER.warning('BU 572 sync failed: %s',e)
            finally:
                if client is not None and client.is_connected:
                    try: await client.disconnect()
                    except Exception: pass
    @callback
    def _handle(self,m:dict[str,Any]):
        self._count+=1; self._last_pkt=time.monotonic(); self._event.set(); user=m.get('user')
        if user not in (1,2): _LOGGER.warning('Unsupported BU 572 user raw=%s',m.get('user_raw')); return
        key=str(user); old=self.data['users'].get(key,{})
        nt=m.get('measurement_time'); ot=old.get('measurement_time')
        if nt is not None and ot:
            try:
                if datetime.fromisoformat(ot)>nt:return
            except (TypeError,ValueError):pass
        rec=dict(m)
        if isinstance(rec.get('measurement_time'),datetime):rec['measurement_time']=rec['measurement_time'].isoformat()
        self.data['users'][key]=rec; self.data['last_user']=user
        hist=self.data.setdefault('history',{}).setdefault(key,[])
        dkey=(rec.get('measurement_time'),rec.get('systolic'),rec.get('diastolic'),rec.get('map'),rec.get('pulse'),rec.get('user_raw'),rec.get('status'))
        if not any((x.get('measurement_time'),x.get('systolic'),x.get('diastolic'),x.get('map'),x.get('pulse'),x.get('user_raw'),x.get('status'))==dkey for x in hist):
            hist.append(dict(rec)); hist.sort(key=lambda x:x.get('measurement_time') or '',reverse=True); del hist[100:]
        self._store.async_delay_save(lambda:deepcopy(self.data),1.0); self._notify(); _LOGGER.info('BU 572 user %d: SYS %.0f / DIA %.0f mmHg, MAP %.0f, pulse %s, time %s',user,m['systolic'],m['diastolic'],m['map'],m.get('pulse'),m.get('measurement_time'))