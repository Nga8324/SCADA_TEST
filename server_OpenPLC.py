import socket
import base64
import threading
import json
import time
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes

# --- AES CONFIGURATION ---
AES_KEY = b'my_super_secret_key_1234567890!!' # 32 bytes (AES-256)
AES_BLOCK_SIZE = 16                           # AES block size in bytes

# --- ENCRYPTION/DECRYPTION FUNCTIONS ---
def decrypt_data(encrypted_data_b64):
    try:
        encrypted_data = base64.b64decode(encrypted_data_b64)
        iv = encrypted_data[:AES_BLOCK_SIZE]
        ciphertext = encrypted_data[AES_BLOCK_SIZE:]
        cipher = AES.new(AES_KEY, AES.MODE_CBC, iv) 
        decrypted_padded = cipher.decrypt(ciphertext)
        decrypted_data = unpad(decrypted_padded, AES.block_size)
        return decrypted_data
    except Exception as e:
        print(f"\n[SERVER] Decryption error: {e}")
        return None

def encrypt_data(data_bytes):
    padded_data = pad(data_bytes, AES.block_size)
    iv = get_random_bytes(AES_BLOCK_SIZE) 
    cipher = AES.new(AES_KEY, AES.MODE_CBC, iv)
    encrypted_data = cipher.encrypt(padded_data)
    final_data = base64.b64encode(iv + encrypted_data)
    return final_data

# --- SERVER LOGIC ---

# Dictionary to hold all PLC variables
plc_state = {
    "START": False, 
    "PUMP1": False, 
    "PUMP2": False, 
    "VALVE": False, 
    "TURBINE": False,
    "GENERATOR": False, 
    "SYSTEM_ON": False, 
    "Overload": False, 
    "Current": 0
}

# Dictionary to simulate TON timer 'Q' (output) and 'ET' (elapsed time)
plc_timers = {
    "tPump1": {"Q": False, "ET": 0, "PT": 2}, "tPump2": {"Q": False, "ET": 0, "PT": 3},
    "tValve": {"Q": False, "ET": 0, "PT": 2}, "tTurbine": {"Q": False, "ET": 0, "PT": 3},
    "tCurrentUp": {"Q": False, "ET": 0, "PT": 1}, "tCurrentDown": {"Q": False, "ET": 0, "PT": 1}
}

def simulate_ton(timer_name, IN):
    timer = plc_timers[timer_name]
    if IN:
        timer["ET"] += 1
        if timer["ET"] >= timer["PT"]:
            timer["Q"] = True
    else:
        timer["Q"] = False
        timer["ET"] = 0

def plc_logic_thread(connection): # 
    global plc_state, plc_timers
    
    # Biến để lưu trạng thái của vòng lặp trước đó
    old_state = {} 

    while True:
        try:
            # --- 1. Run ST Logic (Giống hệt code ST của bạn) ---
            
            # (Toàn bộ logic IF/ELSE của bạn giữ nguyên ở đây)
            if plc_state['Current'] > 300: plc_state['Overload'] = True
            elif plc_state['Current'] < 250: plc_state['Overload'] = False
            
            if plc_state['START'] and not plc_state['Overload']:
                plc_state['SYSTEM_ON'] = True
                simulate_ton("tPump1", IN=True)
                if plc_timers["tPump1"]["Q"]: plc_state['PUMP1'] = True
                simulate_ton("tPump2", IN=plc_state['PUMP1'])
                if plc_timers["tPump2"]["Q"]: plc_state['PUMP2'] = True
                simulate_ton("tValve", IN=plc_state['PUMP2'])
                if plc_timers["tValve"]["Q"]: plc_state['VALVE'] = True
                simulate_ton("tTurbine", IN=plc_state['VALVE'])
                if plc_timers["tTurbine"]["Q"]: plc_state['TURBINE'] = True
                if plc_state['TURBINE']: plc_state['GENERATOR'] = True
                simulate_ton("tCurrentUp", IN=plc_state['GENERATOR'])
                if plc_timers["tCurrentUp"]["Q"]:
                    if plc_state['Current'] < 320: plc_state['Current'] += 10
                    simulate_ton("tCurrentUp", IN=False)
            else:
                plc_state['SYSTEM_ON'] = False
                plc_state['PUMP1'] = False
                plc_state['PUMP2'] = False
                plc_state['VALVE'] = False
                plc_state['TURBINE'] = False
                plc_state['GENERATOR'] = False
                simulate_ton("tPump1", IN=False)
                simulate_ton("tPump2", IN=False)
                simulate_ton("tValve", IN=False)
                simulate_ton("tTurbine", IN=False)
                simulate_ton("tCurrentUp", IN=False)
                simulate_ton("tCurrentDown", IN=True)
                if plc_timers["tCurrentDown"]["Q"] and plc_state['Current'] > 0:
                    plc_state['Current'] -= 10
                    if plc_state['Current'] < 0: plc_state['Current'] = 0
                    simulate_ton("tCurrentDown", IN=False)
            
            # --- 2. Gửi Trạng thái (CHỈ KHI CÓ THAY ĐỔI) ---
            if plc_state != old_state:
                status_json = json.dumps(plc_state)
                
                print(f"\n[SERVER LOGIC] State Changed! Sending (Plaintext): {status_json}")
                
                encrypted_status = encrypt_data(status_json.encode('utf-8'))
                
                print(f"[SERVER LOGIC] Sending (Encrypted): {encrypted_status.decode('utf-8')[:60]}...")
                
                connection.sendall(encrypted_status)
                
                # Cập nhật old_state
                old_state = plc_state.copy()

            # Wait for the next scan cycle
            time.sleep(1) # 1 second scan cycle
            
        except (BrokenPipeError, ConnectionResetError):
            print("[SERVER LOGIC] Client connection lost. Stopping logic thread.")
            break
        except Exception as e:
            print(f"[SERVER LOGIC] Error in logic thread: {e}")
            break

def receive_handler(connection):
    """Handles commands from the HMI (Client)."""
    global plc_state
    
    while True:
        try:
            data_b64 = connection.recv(1024)
            if not data_b64:
                print("\n[SERVER HMI] Client disconnected.")
                break
            
            print(f"\n[SERVER HMI] Received (Encrypted): {data_b64.decode('utf-8')[:60]}...")
            
            decrypted_json = decrypt_data(data_b64)
            if decrypted_json:
                command_dict = json.loads(decrypted_json.decode('utf-8'))
                command = command_dict.get('command')
                
                print(f"[SERVER HMI] Received (Decrypted): {command}")
                
                if command == 'START':
                    plc_state['START'] = True
                elif command == 'STOP':
                    plc_state['START'] = False
        
        except Exception as e:
            print(f"\n[SERVER HMI] Receive error: {e}")
            break
    connection.close()

# --- 4. Main Server Execution ---
HOST = '127.0.0.1'
PORT = 5000 
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen()
print(f"--- [PLC SIMULATION SERVER (ST Logic)] ---")
print(f"Listening on {HOST}:{PORT}...")
conn, addr = s.accept()
print(f"Connected by {addr}. Ready to receive commands.")

# Start the PLC logic simulation thread
plc_thread = threading.Thread(target=plc_logic_thread, args=(conn,), daemon=True)
plc_thread.start()

# Start the HMI command handler thread
receive_thread = threading.Thread(target=receive_handler, args=(conn,), daemon=True)
receive_thread.start()

# Main thread now accepts keyboard input (Local Control)
try:
    while True:
        cmd_input = input("\n[SERVER LOCAL] Enter local command (START, STOP, or quit): ")
        if cmd_input.lower() == 'quit': break
            
        if cmd_input.upper() == 'START':
            plc_state['START'] = True
            print("[SERVER LOCAL] Local START command issued.")
        elif cmd_input.upper() == 'STOP':
            plc_state['START'] = False
            print("[SERVER LOCAL] Local STOP command issued.")
        
except (KeyboardInterrupt, EOFError, BrokenPipeError):
    print("\n[SERVER] Shutting down.")
finally:
    conn.close()
    s.close()
    print("[SERVER] Connection closed.")