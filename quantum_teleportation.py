
import numpy as np

from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.quantum_info import Statevector, state_fidelity
from qiskit_aer import AerSimulator


def create_teleportation_circuit(alpha=0.6, beta=0.8):
    """
    Qubit order:
    q[0] = Q: message qubit
    q[1] = M: Alice's entangled qubit
    q[2] = Y: Bob's entangled qubit
    """

    # Validate the input state
    norm = np.sqrt(abs(alpha) ** 2 + abs(beta) ** 2)

    if not np.isclose(norm, 1.0):
        raise ValueError(
            "alpha and beta must satisfy |alpha|² + |beta|² = 1"
        )

    q = QuantumRegister(3, "q")
    c = ClassicalRegister(2, "c")
    qc = QuantumCircuit(q, c)

    # 1. Prepare the message qubit
    qc.initialize([alpha, beta], q[0])
    qc.barrier(label="Message")

    # 2. Prepare the shared Bell pair between Alice and Bob
    qc.h(q[1])
    qc.cx(q[1], q[2])
    qc.barrier(label="Entanglement")

    # 3. Alice performs the Bell-basis measurement circuit
    qc.cx(q[0], q[1])
    qc.h(q[0])
    qc.barrier(label="Bell measurement")

    # 4. Measure Alice's qubits
    qc.measure(q[0], c[0])
    qc.measure(q[1], c[1])

    # 5. Bob applies conditional corrections
    with qc.if_test((c[1], 1)):
        qc.x(q[2])

    with qc.if_test((c[0], 1)):
        qc.z(q[2])

    return qc


def run_teleportation(alpha=0.6, beta=0.8, shots=2048):
    """Run the teleportation circuit on a local simulator."""

    qc = create_teleportation_circuit(alpha, beta)

    simulator = AerSimulator()
    result = simulator.run(qc, shots=shots).result()
    counts = result.get_counts()

    return qc, counts


if __name__ == "__main__":
    alpha = 0.6
    beta = 0.8

    circuit, counts = run_teleportation(alpha, beta)

    print("Quantum Teleportation")
    print("---------------------")
    print("Input state: 0.6|0> + 0.8|1>")
    print("\nMeasurement counts:")
    print(counts)

    print("\nCircuit:")
    print(circuit.draw(output="text"))
