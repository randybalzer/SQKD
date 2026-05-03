from qunetsim.components import Host, Network
from qunetsim.objects import Qubit
import numpy as np

# 1. Setup Simulation
network = Network.get_instance()
nodes = ['Alice', 'Bob']
network.start(nodes)
network.delay = 0.0

alice = Host('Alice')
bob = Host('Bob')
alice.add_connection('Bob')
bob.add_connection('Alice')
alice.start()
bob.start()
network.add_host(alice)
network.add_host(bob)

# 2. SQKD Protocol Implementation
def sqkd_protocol(alice, bob, num_bits=10):
    shared_key = []
    for _ in range(num_bits):
        # Alice prepares |0>, |1>, |+>, or |->
        basis = np.random.randint(2) # 0 for Z, 1 for X
        bit = np.random.randint(2)
        
        q = Qubit(alice)
        if basis == 0:
            if bit == 1: q.X() # Z basis
        else:
            if bit == 1: q.X() # X basis
            q.H()
        
        # Send to Bob
        alice.send_qubit('Bob', q, await_ack=True)
        q_rec = bob.get_qubit('Alice')
        
        # Bob's operations (CTRL or SIFT)
        operation = np.random.randint(2) # 0 for CTRL, 1 for SIFT
        if operation == 0:
            # CTRL: Reflect back
            bob.send_qubit('Alice', q_rec, await_ack=True)
        else:
            # SIFT: Measure and Resend in Z-basis
            m = q_rec.measure()
            q_new = Qubit(bob)
            if m == 1: q_new.X()
            bob.send_qubit('Alice', q_new, await_ack=True)
            
        q_final = alice.get_qubit('Bob')
        
        # Sifting Phase (Simplified)
        if operation == 1: # Only SIFT bits are used
            # Alice measures in the same basis she prepared
            if basis == 0:
                final_bit = q_final.measure()
            else:
                q_final.H()
                final_bit = q_final.measure()
            shared_key.append(final_bit)
            
    return shared_key

# 3. Execute
key = sqkd_protocol(alice, bob)
print(f"Final Shared Key: {key}")

# Cleanup
network.stop()
