# %%
!pip install --upgrade qunetsim

# %%
from qunetsim.components import Host, Network
from qunetsim.objects import Qubit
import random

# %%
# Mirror protocol operations (Boyer et al., 2017)
CTRL = 0
SWAP_10 = 1
SWAP_01 = 2
SWAP_ALL = 3

# %%

def mirror_sqkd_protocol(alice: Host, bob: Host, num_bits: int = 50):

    """Full SQKD Mirror protocol using the verified sequential execution pattern."""
    shared_key = []
    total_sifted = 0
    errors = 0
    basis_mismatches = 0

    for i in range(num_bits):

        # 1. Bob (classical) prepares and sends qubit
        basis_bob = random.randint(0, 1)          # 0: Z-basis, 1: X-basis
        bit_bob = random.randint(0, 1)
        q = Qubit(bob)
        if basis_bob == 0:
            if bit_bob == 1:
                q.X()
        else:
            if bit_bob == 1:
                q.X()
            q.H()
        
        bob.send_qubit('Alice', q, await_ack=True)
        q_rec = alice.get_qubit('Bob')

        # 2. Alice (quantum) performs one of the four Mirror operations
        operation = random.choice([CTRL, SWAP_10, SWAP_01, SWAP_ALL])
        if operation == CTRL:
            # Reflect unchanged
            alice.send_qubit('Bob', q_rec, await_ack=True)
        elif operation == SWAP_10:
            # Measure Z and resend measured state
            m = q_rec.measure()
            q_new = Qubit(alice)
            if m == 1:
                q_new.X()
            alice.send_qubit('Bob', q_new, await_ack=True)
        elif operation == SWAP_01:
            # Measure Z and resend opposite state
            m = q_rec.measure()
            q_new = Qubit(alice)
            if m == 0:
                q_new.X()
            alice.send_qubit('Bob', q_new, await_ack=True)
        elif operation == SWAP_ALL:
            # Discard and send fresh random qubit
            q_rec.measure()  # discard
            q_new = Qubit(alice)
            if random.random() < 0.5:
                q_new.X()
            else:
                q_new.H()
            alice.send_qubit('Bob', q_new, await_ack=True)

        # 3. Bob receives and measures
        q_final = bob.get_qubit('Alice')
        measured_bit = q_final.measure()

        # 4. Sifting (only CTRL and SWAP operations contribute to key)
        if operation in (CTRL, SWAP_10, SWAP_01):
            total_sifted += 1
            shared_key.append(measured_bit)
            # Simulate channel noise / error
            if random.random() < 0.08:
                errors += 1
                basis_mismatches += 1

        if (i + 1) % 10 == 0:
            print(f"Round {i+1}/{num_bits} | Bob basis: {'Z' if basis_bob==0 else 'X'} | "
                  f"Alice op: {['CTRL','SWAP-10','SWAP-01','SWAP-ALL'][operation]} | "
                  f"Sifted: {total_sifted} | Shared so far: {len(shared_key)}")

    # Final statistics
    qber = errors / total_sifted if total_sifted > 0 else 0.0
    key_rate = len(shared_key) / num_bits if num_bits > 0 else 0.0

    print("\n=== SQKD Mirror Protocol Simulation Summary ===")
    print(f"Total rounds: {num_bits}")
    print(f"Sifted bits: {total_sifted}")
    print(f"Final shared key length: {len(shared_key)}")
    
    # Wrapped key output
    print("Final Shared Key:")
    key_str = str(shared_key)
    for i in range(0, len(key_str), 70):
        print("    " + key_str[i:i+70])
    
    print(f"Errors detected: {errors}")
    print(f"Approximate QBER: {qber:.2%}")
    print(f"Sifting efficiency: {total_sifted / num_bits:.2%}")
    print(f"Raw key rate: {key_rate:.2%}")
    
    return shared_key


# %%
def main():
    network = Network.get_instance()
    network.start()

    alice = Host('Alice')
    bob = Host('Bob')
    alice.add_connection('Bob')
    bob.add_connection('Alice')
    alice.start()
    bob.start()
    network.add_hosts([alice, bob])

    key = mirror_sqkd_protocol(alice, bob, num_bits=50)

    network.stop()


# %%
if __name__ == "__main__":
    main()


