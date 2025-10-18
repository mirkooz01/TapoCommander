# tapo_controller_corretto.py
import asyncio
from kasa import Discover
import getpass

class TapoController:
    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password
        self.dispositivi = {}
    
    async def scopri_prese_con_credenziali(self):
        """Scopri dispositivi con autenticazione - VERSIONE CORRETTA"""
        print("🔍 Ricerca dispositivi TP-Link/Tapo...")
        
        try:
            # Usa discover_single per ogni IP con credenziali
            from kasa import Discover
            
            # Prima scopri senza credenziali per ottenere gli IP
            dispositivi_scoperti = await Discover.discover(timeout=5)
            
            if not dispositivi_scoperti:
                print("❌ Nessun dispositivo trovato nella rete")
                return False
            
            print(f"✅ Trovati {len(dispositivi_scoperti)} dispositivi")
            
            # Ora prova a connetterti a ciascuno con le credenziali
            for ip, dispositivo_base in dispositivi_scoperti.items():
                print(f"\n📡 Tentativo di connessione a {ip}...")
                
                try:
                    # Usa discover_single con le credenziali
                    dispositivo = await Discover.discover_single(
                        host=ip,
                        username=self.username,
                        password=self.password,
                        timeout=10
                    )
                    
                    await dispositivo.update()
                    
                    self.dispositivi[ip] = {
                        'device': dispositivo,
                        'model': dispositivo.model,
                        'alias': dispositivo.alias,
                        'is_on': dispositivo.is_on
                    }
                    
                    print(f"   ✅ Connesso: {dispositivo.alias} ({dispositivo.model})")
                    print(f"   💡 Stato: {'ACCESA' if dispositivo.is_on else 'SPENTA'}")
                    
                except Exception as e:
                    print(f"   ❌ Errore autenticazione {ip}: {e}")
                    # Prova senza credenziali come fallback
                    try:
                        await dispositivo_base.update()
                        self.dispositivi[ip] = {
                            'device': dispositivo_base,
                            'model': dispositivo_base.model,
                            'alias': dispositivo_base.alias,
                            'is_on': dispositivo_base.is_on,
                            'warning': 'Senza autenticazione'
                        }
                        print(f"   ⚠️  Connesso senza auth: {dispositivo_base.alias}")
                    except:
                        self.dispositivi[ip] = {
                            'device': None,
                            'error': str(e),
                            'model': 'Sconosciuto',
                            'alias': 'Sconosciuto'
                        }
            
            return len([d for d in self.dispositivi.values() if d['device']]) > 0
            
        except Exception as e:
            print(f"❌ Errore nella scoperta: {e}")
            return False
    
    async def connetti_dispositivo_singolo(self, ip):
        """Connetti a un singolo dispositivo con autenticazione - VERSIONE CORRETTA"""
        try:
            print(f"🔌 Connessione a {ip}...")
            
            # Usa discover_single con credenziali
            dispositivo = await Discover.discover_single(
                host=ip,
                username=self.username,
                password=self.password,
                timeout=10
            )
            
            await dispositivo.update()
            
            self.dispositivi[ip] = {
                'device': dispositivo,
                'model': dispositivo.model,
                'alias': dispositivo.alias,
                'is_on': dispositivo.is_on
            }
            
            print(f"✅ Connesso a {dispositivo.alias}")
            return True
            
        except Exception as e:
            print(f"❌ Errore connessione a {ip}: {e}")
            
            # Prova senza credenziali come fallback
            try:
                from kasa import SmartDevice
                dispositivo = SmartDevice(ip)
                await dispositivo.update()
                
                self.dispositivi[ip] = {
                    'device': dispositivo,
                    'model': dispositivo.model,
                    'alias': dispositivo.alias,
                    'is_on': dispositivo.is_on,
                    'warning': 'Senza autenticazione'
                }
                print(f"⚠️  Connesso senza autenticazione a {dispositivo.alias}")
                return True
            except Exception as e2:
                print(f"❌ Anche connessione senza auth fallita: {e2}")
                return False
    
    async def controlla_dispositivo(self, ip):
        """Controlla un dispositivo specifico"""
        if ip not in self.dispositivi or not self.dispositivi[ip]['device']:
            print("❌ Dispositivo non disponibile")
            return
        
        dispositivo = self.dispositivi[ip]['device']
        
        while True:
            try:
                await dispositivo.update()
                stato = "🔌 ACCESA" if dispositivo.is_on else "⚡ SPENTA"
                warning = self.dispositivi[ip].get('warning', '')
                
                print("\n" + "="*50)
                print(f"🎛️  CONTROLLO: {dispositivo.alias}")
                print("="*50)
                print(f"IP: {ip}")
                print(f"Stato: {stato}")
                print(f"Modello: {dispositivo.model}")
                if warning:
                    print(f"⚠️  {warning}")
                
                print("\n1. 🔌 Accendi")
                print("2. ⚡ Spegni")
                print("3. 🔄 Aggiorna stato")
                print("4. 📊 Info dettagliate")
                print("5. ↩️  Torna indietro")
                
                scelta = input("\nScegli (1-5): ").strip()
                
                if scelta == "1":
                    await dispositivo.turn_on()
                    print("✅ Dispositivo acceso")
                elif scelta == "2":
                    await dispositivo.turn_off()
                    print("✅ Dispositivo spento")
                elif scelta == "3":
                    print("✅ Stato aggiornato")
                elif scelta == "4":
                    await self.mostra_info_dettagliate(dispositivo)
                elif scelta == "5":
                    break
                else:
                    print("❌ Scelta non valida")
                    
            except Exception as e:
                print(f"❌ Errore durante il controllo: {e}")
                break
    
    async def mostra_info_dettagliate(self, dispositivo):
        """Mostra informazioni dettagliate del dispositivo"""
        try:
            await dispositivo.update()
            print("\n📊 INFORMAZIONI DETTAGLIATE:")
            print(f"   Nome: {dispositivo.alias}")
            print(f"   Modello: {dispositivo.model}")
            print(f"   Hardware: {dispositivo.hw_info}")
            print(f"   Firmware: {dispositivo.sw_info}")
            print(f"   MAC: {dispositivo.mac}")
            if hasattr(dispositivo, 'rssi'):
                print(f"   RSSI: {dispositivo.rssi}")
            
            # Informazioni consumo energetico
            if hasattr(dispositivo, 'emeter_realtime'):
                try:
                    consumo = dispositivo.emeter_realtime
                    if consumo:
                        print("   ⚡ CONSUMO ENERGETICO:")
                        if 'power' in consumo:
                            print(f"     Potenza: {consumo['power']} W")
                        if 'voltage' in consumo:
                            print(f"     Voltaggio: {consumo['voltage']} V")
                        if 'current' in consumo:
                            print(f"     Corrente: {consumo['current']} A")
                except:
                    print("   ⚡ Info consumo: Non disponibili")
                        
        except Exception as e:
            print(f"❌ Errore nel recupero informazioni: {e}")

async def main():
    print("=== CONTROLLO DISPOSITIVI TAPO ===")
    print("   (Utilizza le stesse credenziali dell'app Tapo)\n")
    
    # Richiedi credenziali
    username = input("Email account Tapo: ").strip()
    password = getpass.getpass("Password account Tapo: ")
    
    controller = TapoController(username=username, password=password)
    
    # Scelta modalità connessione
    print("\nModalità connessione:")
    print("1. 🔍 Scansione automatica rete")
    print("2. 🔌 IP specifico")
    
    scelta = input("Scegli (1-2): ").strip()
    
    if scelta == "1":
        # Scansione automatica
        if not await controller.scopri_prese_con_credenziali():
            print("❌ Nessun dispositivo raggiungibile")
            return
    elif scelta == "2":
        # IP specifico
        ip = input("Inserisci IP del dispositivo: ").strip()
        if not await controller.connetti_dispositivo_singolo(ip):
            return
    else:
        print("❌ Scelta non valida")
        return
    
    # Se abbiamo dispositivi, mostra menu di selezione
    if controller.dispositivi:
        print(f"\n✅ Dispositivi disponibili: {len(controller.dispositivi)}")
        
        dispositivi_validi = [ip for ip, info in controller.dispositivi.items() if info['device']]
        
        if dispositivi_validi:
            print("\nSeleziona un dispositivo:")
            for i, ip in enumerate(dispositivi_validi, 1):
                info = controller.dispositivi[ip]
                stato = 'ACCESA' if info['is_on'] else 'SPENTA'
                warning = f" - ⚠️ {info['warning']}" if 'warning' in info else ''
                print(f"{i}. {info['alias']} ({ip}) - {stato}{warning}")
            
            try:
                scelta_idx = int(input("\nNumero dispositivo: ")) - 1
                if 0 <= scelta_idx < len(dispositivi_validi):
                    ip_selezionato = dispositivi_validi[scelta_idx]
                    await controller.controlla_dispositivo(ip_selezionato)
                else:
                    print("❌ Selezione non valida")
            except ValueError:
                print("❌ Inserisci un numero valido")
        else:
            print("❌ Nessun dispositivo autenticato correttamente")
            print("   Verifica email e password dell'app Tapo")
    else:
        print("❌ Nessun dispositivo disponibile")

if __name__ == "__main__":
    asyncio.run(main())