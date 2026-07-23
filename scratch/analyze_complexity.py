import json
from pathlib import Path
import sys
sys.path.append("src")
import qubo_builder
from qubo_builder import job_view, node_view, zero_matrix, add_to_q, node_cost_proxy, gpu_compatibility_penalty, build_variable_map as build_variable_map_new
from qaoa_cudaq_solver import upper_triangle_terms

# Re-implement old QUBO builder logic for comparison
def build_variable_map_old(jobs, nodes):
    variables = {}
    index_map = {}
    idx = 0
    for i, job in enumerate(jobs):
        for j, node in enumerate(nodes):
            name = f"x({i},{j})_{job['job_id']}_{node['node_id']}"
            variables[name] = {
                "index": idx,
                "i": i,
                "j": j,
                "job_id": job['job_id'],
                "node_id": node['node_id'],
            }
            index_map[(i, j)] = idx
            idx += 1
    return variables, index_map

def build_qubo_old(jobs_input, nodes_input, alpha_assign=10.0, alpha_capacity=10.0, alpha_gpu_compat=10.0, objective_scale=0.1):
    jobs = [job_view(job) for job in jobs_input]
    nodes = [node_view(node) for node in nodes_input]
    variables, index_map = build_variable_map_old(jobs, nodes)
    q_size = len(variables)
    Q = zero_matrix(q_size)

    # A. Objective + gpu compat
    for i, job in enumerate(jobs):
        for j, node in enumerate(nodes):
            idx = index_map[(i, j)]
            add_to_q(Q, idx, idx, objective_scale * node_cost_proxy(job, node))
            if alpha_gpu_compat and gpu_compatibility_penalty(job, node) > 0:
                add_to_q(Q, idx, idx, alpha_gpu_compat)

    # B. Assignment uniqueness
    for i, _job in enumerate(jobs):
        for j, _node in enumerate(nodes):
            idx = index_map[(i, j)]
            add_to_q(Q, idx, idx, -alpha_assign)
        for j in range(len(nodes)):
            for k in range(j + 1, len(nodes)):
                idx_j = index_map[(i, j)]
                idx_k = index_map[(i, k)]
                add_to_q(Q, idx_j, idx_k, 2.0 * alpha_assign)

    # C. Capacity penalties
    for j, node in enumerate(nodes):
        cap_cpu = node["cpu_capacity"]
        cap_gpu = node["gpu_capacity"]
        for i, job in enumerate(jobs):
            idx_i_j = index_map[(i, j)]
            cpu_demand = job["cpu_req"]
            gpu_demand = job["gpu_req"]
            add_to_q(Q, idx_i_j, idx_i_j, alpha_capacity * (cpu_demand * cpu_demand - 2.0 * cap_cpu * cpu_demand))
            add_to_q(Q, idx_i_j, idx_i_j, alpha_capacity * (gpu_demand * gpu_demand - 2.0 * cap_gpu * gpu_demand))
            for k in range(i + 1, len(jobs)):
                idx_k_j = index_map[(k, j)]
                cpu_demand_k = jobs[k]["cpu_req"]
                gpu_demand_k = jobs[k]["gpu_req"]
                add_to_q(Q, idx_i_j, idx_k_j, 2.0 * alpha_capacity * cpu_demand * cpu_demand_k)
                add_to_q(Q, idx_i_j, idx_k_j, 2.0 * alpha_capacity * gpu_demand * gpu_demand_k)

    return Q

def build_qubo_new(jobs_input, nodes_input, alpha_assign=10.0, alpha_capacity=10.0, alpha_gpu_compat=10.0, objective_scale=0.1):
    # This uses the current (reformed) build_qubo function
    res = qubo_builder.build_qubo(jobs_input, nodes_input, alpha_assign, alpha_capacity, alpha_gpu_compat, objective_scale)
    return res["Q"]

def count_non_zero(Q):
    count = 0
    for r in range(len(Q)):
        for c in range(r, len(Q)): # Upper triangle entries
            if Q[r][c] != 0.0:
                count += 1
    return count

def count_hamiltonian_terms(Q):
    linear, quadratic, _ = upper_triangle_terms(Q)
    return len(linear) + len(quadratic)

def get_stats(jobs, nodes, old=True):
    if old:
        Q = build_qubo_old(jobs, nodes)
        variables, _ = build_variable_map_old(jobs, nodes)
    else:
        Q = build_qubo_new(jobs, nodes)
        variables, _ = build_variable_map_new([job_view(j) for j in jobs], [node_view(n) for n in nodes])
    
    return {
        "variables": len(variables),
        "non_zero": count_non_zero(Q),
        "hamiltonian_terms": count_hamiltonian_terms(Q),
        "qubits": len(variables)
    }

# Toy instances
from brute_force_mapping_solver import make_example_2x2, make_example_3x2
from validate_qaoa import make_example_4x3

toy_instances = {
    "2x2": make_example_2x2(),
    "3x2": make_example_3x2(),
    "4x3": make_example_4x3()
}

print("=== TOY INSTANCES ===")
for name, payload in toy_instances.items():
    jobs = payload["jobs"]
    nodes = payload["nodes"]
    old_stats = get_stats(jobs, nodes, old=True)
    new_stats = get_stats(jobs, nodes, old=False)
    
    var_red = (1 - new_stats["variables"]/old_stats["variables"])*100
    entry_red = (1 - new_stats["non_zero"]/old_stats["non_zero"])*100
    ham_red = (1 - new_stats["hamiltonian_terms"]/old_stats["hamiltonian_terms"])*100
    
    print(f"\nInstance {name}:")
    print(f"  OLD: vars={old_stats['variables']}, non_zero_Q={old_stats['non_zero']}, ham_terms={old_stats['hamiltonian_terms']}, qubits={old_stats['qubits']}")
    print(f"  NEW: vars={new_stats['variables']}, non_zero_Q={new_stats['non_zero']}, ham_terms={new_stats['hamiltonian_terms']}, qubits={new_stats['qubits']}")
    print(f"  RED: var_red={var_red:.2f}%, Q_entry_red={entry_red:.2f}%, ham_red={ham_red:.2f}%")

# Real trace benchmark windows
reduced_dir = Path("data/windows/quantum_windows_reduced")
buckets = ["small", "medium", "large"]

print("\n=== REPRESENTATIVE REAL WINDOWS ===")
for b in buckets:
    p = reduced_dir / f"{b}.json"
    if not p.exists():
        continue
    data = json.loads(p.read_text(encoding="utf-8"))
    w = data["windows"][0]
    label = w.get("label")
    jobs = w.get("jobs", [])
    nodes = w.get("candidate_nodes", [])
    
    old_stats = get_stats(jobs, nodes, old=True)
    new_stats = get_stats(jobs, nodes, old=False)
    
    var_red = (1 - new_stats["variables"]/old_stats["variables"])*100
    entry_red = (1 - new_stats["non_zero"]/old_stats["non_zero"])*100
    ham_red = (1 - new_stats["hamiltonian_terms"]/old_stats["hamiltonian_terms"])*100
    
    print(f"\nBucket {b.upper()} (window {label}):")
    print(f"  OLD: vars={old_stats['variables']}, non_zero_Q={old_stats['non_zero']}, ham_terms={old_stats['hamiltonian_terms']}")
    print(f"  NEW: vars={new_stats['variables']}, non_zero_Q={new_stats['non_zero']}, ham_terms={new_stats['hamiltonian_terms']}")
    print(f"  RED: var_red={var_red:.2f}%, Q_entry_red={entry_red:.2f}%, ham_red={ham_red:.2f}%")
