import socket
import base64
import threading
import json
import time
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes

# --- AES CONFIGURATION ---
AES_KEY = b'my_super_secret_key_1234567890!!' # 32 bytes
AES_BLOCK_SIZE = 16

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
    except (ValueError, KeyError, TypeError) as e:
        print(f"\n[CLIENT] Decryption error: {e}")
        return None

def encrypt_data(data_bytes):
    padded_data = pad(data_bytes, AES.block_size)
    iv = get_random_bytes(AES_BLOCK_SIZE)
    cipher = AES.new(AES_KEY, AES.MODE_CBC, iv)
    encrypted_data = cipher.encrypt(padded_data)
    final_data = base64.b64encode(iv + encrypted_data)
    return final_data

# --- CLIENT LOGIC ---

def receive_handler(sock):
    while True:
        try:
            data_b64 = sock.recv(1024)
            if not data_b64:
                print("\n[CLIENT] Server disconnected.")
                break

            print(f"\n[CLIENT] Received (Encrypted): {data_b64.decode('utf-8')[:60]}...")
            # 1. Decrypt the incoming data
            decrypted_json = decrypt_data(data_b64)
            if decrypted_json:
                
                # 2. Parse the JSON status
                status_dict = json.loads(decrypted_json.decode('utf-8'))
                
                # 3. Print the status (This simulates HMI updating)
                print(f"\n--- [CLIENT] STATUS UPDATE RECEIVED ---")
                print(f"  SYSTEM_ON: {status_dict.get('SYSTEM_ON')}")
                print(f"  Overload:  {status_dict.get('Overload')}")
                print(f"  PUMP1:     {status_dict.get('PUMP1')}")
                print(f"  PUMP2:     {status_dict.get('PUMP2')}")
                print(f"  VALVE:     {status_dict.get('VALVE')}")
                print(f"  TURBINE:   {status_dict.get('TURBINE')}")
                print(f"  GENERATOR: {status_dict.get('GENERATOR')}")
                print(f"  Current:   {status_dict.get('Current')}")
                print(f"---------------------------------------------")
        
        except (ConnectionResetError, BrokenPipeError):
            print("\n[CLIENT] Lost connection to Server.")
            break
        except Exception as e:
            print(f"\n[CLIENT] Error receiving data: {e}")
            break
    sock.close()

HOST = '127.0.0.1'
PORT = 5000

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.connect((HOST, PORT))
    print(f"--- [HMI SIMULATION CLIENT] ---")
    print(f"Connected to Server at {HOST}:{PORT}.")

    # Start the receive handler thread
    receive_thread = threading.Thread(target=receive_handler, args=(s,), daemon=True)
    receive_thread.start()

    # Main thread for sending commands
    while True:
        cmd_input = input("\n[CLIENT] Enter command (START, STOP, or quit): ")

        if cmd_input.lower() == 'quit':
            break

        if cmd_input.upper() == 'START' or cmd_input.upper() == 'STOP':
            command_dict = {"command": cmd_input.upper()}
            command_json = json.dumps(command_dict)

            print(f"[CLIENT] Sending (Plaintext): {command_json}")

            encrypted_cmd = encrypt_data(command_json.encode('utf-8'))

            print(f"[CLIENT] Sending (Encrypted): {encrypted_cmd.decode('utf-8')[:60]}...")

            s.sendall(encrypted_cmd)
        else:
            print("[CLIENT] Invalid command. Please type START or STOP.")


except (EOFError, KeyboardInterrupt, ConnectionRefusedError):
    print("\n[CLIENT] Connection failed or shut down.")

finally:
    s.close()
    print("[CLIENT] Connection closed.")