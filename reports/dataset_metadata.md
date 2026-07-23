# M1 Dataset Metadata: HPC Job Trace

## Dataset Snapshot

- Source file: `/home/sim/Desktop/Quantum/data/merged_all_jobs.jsonl`
- Records: 210,287
- JSON parse failures: 0
- Distinct fields: 88
- GPU-requesting jobs: 18,883
- CPU-only jobs with explicit zero GPUs: 1,060
- Jobs with start time, runtime, and host allocation: 167,773

## Time Coverage

- `ctime`: 2024-09-01 00:16:32 to 2026-01-31 23:57:06
- `etime`: 2024-09-01 00:16:32 to 2026-01-31 23:57:06
- `mtime`: 2024-09-01 08:54:41 to 2026-01-31 23:59:39
- `qtime`: 2024-09-01 00:16:32 to 2026-01-31 23:57:06
- `stime`: 2024-09-01 00:16:32 to 2026-01-31 23:57:07

## M1 Field-to-QUBO Table

| Field | Present? | Coverage | Use in QUBO? | Why / How |
|---|---|---:|---|---|
| `job_id` | Yes | 100.0% | No | Identifier only. |
| `Job_Name` | Yes | 100.0% | No | Useful for grouping; avoid as optimization variable. |
| `Job_Owner` | Yes | 100.0% | No | Fair-share/user grouping if needed. |
| `euser` | Yes | 100.0% | No | Fair-share/user grouping if needed. |
| `egroup` | Yes | 100.0% | No | Group fair-share if needed. |
| `queue` | Yes | 100.0% | Maybe | Partition/eligibility or queue-class penalties. |
| `job_state` | Yes | 100.0% | Maybe | Filter completed/running/queued records. |
| `Priority` | Yes | 100.0% | Maybe | Priority objective weight, but values may be uninformative if mostly zero. |
| `qtime` | Yes | 100.0% | Yes | Submit/queue time; supports release-time and wait-time terms. |
| `stime` | Yes | 80.5% | Yes | Observed start time; supports replay windows and conflict detection. |
| `etime` | Yes | 100.0% | Yes | Eligibility time; close to submit time in PBS traces. |
| `mtime` | Yes | 100.0% | Yes | Last modified/end proxy for finished jobs. |
| `resources_used.walltime` | Yes | 98.2% | Yes | Observed runtime cost. |
| `Resource_List.walltime` | Yes | 100.0% | Yes | Requested walltime/deadline bound. |
| `Resource_List.ncpus` | Yes | 100.0% | Yes | CPU capacity constraint. |
| `Resource_List.ngpus` | Yes | 9.5% | Maybe | GPU capacity/eligibility constraint. |
| `Resource_List.nodect` | Yes | 100.0% | Yes | Node capacity constraint. |
| `Resource_List.mpiprocs` | Yes | 69.6% | Yes | MPI/process capacity term. |
| `resources_used.mem` | Yes | 98.2% | Yes | Observed memory demand; useful if requested memory is sparse. |
| `Resource_List.mem` | Yes | 9.7% | Maybe | Requested memory capacity constraint when present. |
| `exec_host` | Yes | 98.2% | Yes | Observed allocation; use for overlap/conflict mining. |
| `exec_vnode` | Yes | 98.2% | Yes | Observed vnode resources; use for allocation and GPU/node constraints. |
| `Resource_List.select` | Yes | 100.0% | Yes | Parseable resource request; fills missing CPU/GPU/node fields. |
| `schedselect` | Yes | 100.0% | Yes | Expanded resource request; useful fallback for resources. |
| `Exit_status` | Yes | 98.2% | Maybe | Filter failed jobs or penalize risky classes. |
| `project` | Yes | 100.0% | No | Project/fair-share grouping if useful. |

## Numeric / Duration Profile

| Metric | Count | Missing | Min | P50 | P90 | P95 | Max | Mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| requested_ncpus | 210,287 | 0 | 0 | 128 | 640 | 1,024 | 8,192 | 279.70118932696744 |
| requested_ngpus | 19,943 | 190,344 | 0 | 1 | 4 | 4 | 116 | 1.7583613297899012 |
| requested_nodes | 210,287 | 0 | 1 | 1 | 5 | 8 | 256 | 2.7926120016929246 |
| requested_mpiprocs | 146,273 | 64,014 | 1 | 128 | 640 | 640 | 12,000 | 292.3048546211536 |
| used_ncpus | 206,401 | 3,886 | 0 | 128 | 640 | 1,024 | 8,192 | 279.4126385046584 |
| used_mem_gib | 206,401 | 3,886 | 0 | 7.426784515380859 | 53.48704147338867 | 85.70064544677734 | 33,819.627098083496 | 26.015065197071344 |
| used_vmem_gib | 206,401 | 3,886 | 0 | 59.69104766845703 | 1,217.7516441345215 | 1,275.2299346923828 | 262,499.22270584106 | 491.7726643239377 |
| requested_walltime_seconds | 210,278 | 9 | 00:00:00 | 2d 00:00:00 | 3d 00:00:00 | 3d 00:00:00 | 3d 12:00:00 | 1d 13:43:21 |
| used_walltime_seconds | 206,401 | 3,886 | 00:00:00 | 00:16:07 | 23:15:04 | 2d 00:00:29 | 3d 12:01:18 | 06:03:05 |
| wait_seconds | 169,337 | 40,950 | 00:00:00 | 00:00:00 | 01:46:55 | 05:34:51 | 8d 07:05:36 | 01:12:00 |
| turnaround_seconds | 210,287 | 0 | -1d 18:51:40 | 00:18:40 | 1d 02:05:17 | 2d 00:01:09 | 56d 21:30:14 | 07:03:53 |
| priority | 210,287 | 0 | 0 | 0 | 0 | 0 | 1,000 | 0.01484162121291378 |
| cpupercent | 206,402 | 3,885 | 0 | 1,593 | 12,862 | 13,089 | 7,627,343 | 6,212.942510246994 |

## Key Categorical Distributions

### Queues

- `workq`: 173,184
- `gpu`: 37,031
- `defective_test`: 64
- `iworkq`: 5
- `mistralq`: 3

### Job States

- `F`: 210,287

### Users

- `vhazra`: 30,817
- `neetu`: 19,354
- `mudixitk`: 10,417
- `sureshch`: 9,817
- `janesh`: 7,832
- `yarasi`: 6,963
- `rsnlab`: 5,386
- `tej`: 4,781
- `sahilk`: 4,647
- `indrajit`: 3,945
- `saikatc`: 3,880
- `kvanka`: 3,880
- `sailaja`: 3,796
- `aprakash`: 3,484
- `nayana`: 3,316
- `kavita`: 3,043
- `rituraj`: 2,832
- `bganguly`: 2,792
- `supriya`: 2,627
- `shikhar`: 2,617

### Projects

- `_pbs_project_default`: 210,213
- `urgent`: 74

### Source Files

- `final_full_job_data.txt`: 210,287
- `qstat_output.txt`: 144,949
- `full_job_details.txt`: 65,338

### Allocated Nodes

- `r04gn06`: 3,338
- `r04gn01`: 3,225
- `r04gn03`: 3,126
- `r05gn04`: 3,099
- `r04gn02`: 3,090
- `r05gn06`: 3,061
- `r05gn03`: 3,004
- `r05gn02`: 2,988
- `r05gn01`: 2,947
- `r04gn05`: 2,917
- `r05gn05`: 2,763
- `r04gn04`: 2,639
- `r06cn37`: 677
- `r11cn28`: 673
- `r12cn05`: 664
- `r13cn14`: 663
- `r03cn24`: 658
- `r08cn08`: 642
- `r11cn07`: 626
- `r13cn20`: 608

## Initial QUBO-Relevant Interpretation

- Strong constraint candidates: CPU count, GPU count, node count, requested walltime, observed runtime, and observed allocation host/vnode.
- Objective candidates: minimize waiting time, minimize turnaround, penalize long runtimes, and optionally reward priority or queue class.
- Filtering candidates: finished jobs with valid `qtime`, `stime`, `resources_used.walltime`, and `exec_host`/`exec_vnode` are the cleanest replay substrate.
- Memory is useful if requested memory exists; otherwise observed memory can support analysis but is weaker as a scheduling constraint because it is known after execution.
- Priority should be inspected before use; if it is mostly zero, it will not provide a meaningful QUBO weight without an inferred priority scheme.
- Some rare field names look like shell/environment fragments from the merge process; treat them as data-quality artifacts, not scheduling features.
- `mtime - qtime` can be negative for a small number of records, so observed runtime from `resources_used.walltime` is safer than deriving runtime from timestamps.

## Example Same-Node Overlap Windows

- Node `r05gn05`: `100057.champ1` at 2025-01-12 23:25:33 overlaps 100006.champ1 (00:00:01)
- Node `r05gn05`: `100235.champ1` at 2025-01-13 12:07:16 overlaps 100217.champ1 (00:14:59)
- Node `r05gn01`: `100334.champ1` at 2025-01-13 14:33:09 overlaps 100301.champ1 (00:15:25)
- Node `r05gn06`: `100409.champ1` at 2025-01-13 17:30:12 overlaps 100370.champ1 (01:03:03)
- Node `r05gn01`: `100509.champ1` at 2025-01-13 21:31:03 overlaps 100301.champ1 (00:13:45)
- Node `r05gn05`: `100511.champ1` at 2025-01-13 21:57:03 overlaps 100217.champ1 (00:11:40)
- Node `r05gn06`: `100516.champ1` at 2025-01-13 22:14:19 overlaps 100370.champ1 (00:13:10)
- Node `r09cn23`: `100529.champ1` at 2025-01-14 01:12:27 overlaps 100451.champ1 (00:15:34)
- Node `r05gn01`: `100541.champ1` at 2025-01-14 01:38:28 overlaps 100301.champ1 (1d 02:57:15)
- Node `r05gn01`: `100543.champ1` at 2025-01-14 01:40:05 overlaps 100301.champ1 (01:14:48), 100541.champ1 (01:14:48)

## All Fields

| Field | Present Count | Types | Examples |
|---|---:|---|---|
| `" -a \"${_mlv}\"` | 25,532 | str:25532 | `\"${_mlv#[0-9]}\" ]; then if [ -n \"`eval \'echo ${ \'$_mlv\'+x}\'`\" ]; then _mlre=\"${_mlre:-}${_mlv}_modquar=\'`eval \' echo ${\'$_mlv\'}\'`\' \"; fi; _mlrv=`<br>`\"${_mlv#[0-9]}\" ]; then if [ -n \"`eval \'echo ${ \'$_mlv\'+x}\'`\" ]; then _mlre=\"${_mlre:-}${_mlv}_modquar=\'`eval \' echo ${\'$_mlv\'}\'`\' \"; fi; _mlrv=`<br>`\"${_mlv#[0-9]}\" ]; then if [ -n \"`eval \'echo ${ \'$_mlv\'+x}\'`\" ]; then _mlre=\"${_mlre:-}${_mlv}_modquar=\'`eval \' echo ${\'$_mlv\'}\'`\' \"; fi; _mlrv=`<br>`\"${_mlv#[0-9]}\" ]; then if [ -n \"`eval \'echo ${ \'$_mlv\'+x}\'`\" ]; then _mlre=\"${_mlre:-}${_mlv}_modquar=\'`eval \' echo ${\'$_mlv\'}\'`\' \"; fi; _mlrv=`<br>`\"${_mlv#[0-9]}\" ]; then if [ -n \"`eval \'echo ${ \'$_mlv\'+x}\'`\" ]; then _mlre=\"${_mlre:-}${_mlv}_modquar=\'`eval \' echo ${\'$_mlv\'}\'`\' \"; fi; _mlrv=` |
| `; if [ \"$_sp_arg\"` | 1,711 | str:1711 | `\"-h\" ] || [ \"$_sp_arg\" = \"--help\" ]; then command spack cd -h; else LOC=\"$(SPACK_COLOR=\"${SPACK_COLOR:-always} \" spack location $_sp_arg \"$@\")\"; if `<br>`\"-h\" ] || [ \"$_sp_arg\" = \"--help\" ]; then command spack cd -h; else LOC=\"$(SPACK_COLOR=\"${SPACK_COLOR:-always} \" spack location $_sp_arg \"$@\")\"; if `<br>`\"-h\" ] || [ \"$_sp_arg\" = \"--help\" ]; then command spack cd -h; else LOC=\"$(SPACK_COLOR=\"${SPACK_COLOR:-always} \" spack location $_sp_arg \"$@\")\"; if `<br>`\"-h\" ] || [ \"$_sp_arg\" = \"--help\" ]; then command spack cd -h; else LOC=\"$(SPACK_COLOR=\"${SPACK_COLOR:-always} \" spack location $_sp_arg \"$@\")\"; if `<br>`\"-h\" ] || [ \"$_sp_arg\" = \"--help\" ]; then command spack cd -h; else LOC=\"$(SPACK_COLOR=\"${SPACK_COLOR:-always} \" spack location $_sp_arg \"$@\")\"; if ` |
| `BASH_FUNC_scl%%=() {  if [ \"$1\"` | 136 | str:136 | `\"load\" -o \"$1\" = \"unload\" ]; then eval \"module $@\"; else /usr/bin/scl \"$@\"; fi }, BASH_FUNC_ml%%=() { module ml \"$@\" },_=/opt/pbs/bin/qsub, PBS_O_QU`<br>`\"load\" -o \"$1\" = \"unload\" ]; then eval \"module $@\"; else /usr/bin/scl \"$@\"; fi }, BASH_FUNC_ml%%=() { module ml \"$@\" },_=/opt/pbs/bin/qsub, PBS_O_QU`<br>`\"load\" -o \"$1\" = \"unload\" ]; then eval \"module $@\"; else /usr/bin/scl \"$@\"; fi }, BASH_FUNC_ml%%=() { module ml \"$@\" },_=/opt/pbs/bin/qsub, PBS_O_QU`<br>`\"load\" -o \"$1\" = \"unload\" ]; then eval \"module $@\"; else /usr/bin/scl \"$@\"; fi }, BASH_FUNC_ml%%=() { module ml \"$@\" },_=/opt/pbs/bin/qsub, PBS_O_QU`<br>`\"load\" -o \"$1\" = \"unload\" ]; then eval \"module $@\"; else /usr/bin/scl \"$@\"; fi }, BASH_FUNC_ml%%=() { module ml \"$@\" },_=/opt/pbs/bin/qsub, PBS_O_QU` |
| `Checkpoint` | 210,175 | str:210175 | `u` |
| `Error_Path` | 210,287 | str:210287 | `champ2.cm.cluster:/scratch/amitl/Eyegaze/MPII_CODES/Training/E fficientNet_B4/B4.e100000`<br>`champ2.cm.cluster:/scratch/amitl/Eyegaze/MPII_CODES/Training/E fficientNet_B7/B7.e100001`<br>`champ2.cm.cluster:/scratch/amitl/Eyegaze/MPII_CODES/Training/E fficientNet_v2_l/v2_l.e100002`<br>`champ2.cm.cluster:/scratch/amitl/Eyegaze/MPII_CODES/Testing/Ef ficientNet_v2_s/v2_s.e100003`<br>`champ2.cm.cluster:/scratch/nidhi/lokesh/ds/npt.e100004` |
| `Execution_Time` | 1 | str:1 | `Sun Nov 30 10:00:00 2025` |
| `Exit_status` | 206,455 | str:206455 | `0`<br>`143`<br>`271`<br>`255`<br>`1` |
| `Hold_Types` | 210,175 | str:210175 | `n`<br>`s`<br>`u` |
| `ION:-0}\"` | 4 | str:4 | `\'1\' ]; then swname=\'main\'; if [ -e /cm/local/apps/envi ronment-modules/4.5.3//libexec/modulecmd.tcl ]; then swfound=0; unset MODULES_USE_COMPAT_VERSION; fi;`<br>`\'1\' ]; then swname=\'main\'; if [ -e /cm/local/apps/envi ronment-modules/4.5.3//libexec/modulecmd.tcl ]; then swfound=0; unset MODULES_USE_COMPAT_VERSION; fi;`<br>`\'1\' ]; then swname=\'main\'; if [ -e /cm/local/apps/envi ronment-modules/4.5.3//libexec/modulecmd.tcl ]; then swfound=0; unset MODULES_USE_COMPAT_VERSION; fi;`<br>`\'1\' ]; then swname=\'main\'; if [ -e /cm/local/apps/envi ronment-modules/4.5.3//libexec/modulecmd.tcl ]; then swfound=0; unset MODULES_USE_COMPAT_VERSION; fi;` |
| `Job_Name` | 210,287 | str:210287 | `B4`<br>`B7`<br>`v2_l`<br>`v2_s`<br>`npt` |
| `Job_Owner` | 210,287 | str:210287 | `amitl@champ2.cm.cluster`<br>`nidhi@champ2.cm.cluster`<br>`saikatc@champ2.cm.cluster`<br>`bganguly@champ2.cm.cluster`<br>`vhazra@champ1.cm.cluster` |
| `Join_Path` | 210,287 | str:210287 | `n`<br>`oe` |
| `Keep_Files` | 210,287 | str:210287 | `oed`<br>`doe` |
| `Mail_Points` | 210,287 | str:210287 | `a`<br>`abe` |
| `Mail_Users` | 1,545 | str:1545 | `rakhi1777rakhi@gmail.com`<br>`mithun@csir4pi.in`<br>`gaurav.csir4pi@gmail.com`<br>`mithun.4pi@gmail.com`<br>`rathna@csir4pi.in` |
| `Output_Path` | 210,287 | str:210287 | `champ2.cm.cluster:/scratch/amitl/Eyegaze/MPII_CODES/Training/ EfficientNet_B4/B4.o100000`<br>`champ2.cm.cluster:/scratch/amitl/Eyegaze/MPII_CODES/Training/ EfficientNet_B7/B7.o100001`<br>`champ2.cm.cluster:/scratch/amitl/Eyegaze/MPII_CODES/Training/ EfficientNet_v2_l/v2_l.o100002`<br>`champ2.cm.cluster:/scratch/amitl/Eyegaze/MPII_CODES/Testing/E fficientNet_v2_s/v2_s.o100003`<br>`champ2.cm.cluster:/scratch/nidhi/lokesh/ds/npt.o100004` |
| `PAT_VERSION:-0}\"` | 25,538 | str:25538 | `\'1\' ]; then typeset swname=\'main\'; if [ -e /cm /local/apps/environment-modules/4.5.3//libexec/modulecmd.tcl ]; then t ypeset swfound=0; unset MODULES_USE_CO`<br>`\'1\' ]; then typeset swname=\'main\'; if [ -e /cm /local/apps/environment-modules/4.5.3//libexec/modulecmd.tcl ]; then t ypeset swfound=0; unset MODULES_USE_CO`<br>`\'1\' ]; then typeset swname=\'main\'; if [ -e /cm /local/apps/environment-modules/4.5.3//libexec/modulecmd.tcl ]; then t ypeset swfound=0; unset MODULES_USE_CO`<br>`\'1\' ]; then typeset swname=\'main\'; if [ -e /cm /local/apps/environment-modules/4.5.3//libexec/modulecmd.tcl ]; then t ypeset swfound=0; unset MODULES_USE_CO`<br>`\'1\' ]; then typeset swname=\'main\'; if [ -e /cm /local/apps/environment-modules/4.5.3//libexec/modulecmd.tcl ]; then t ypeset swfound=0; unset MODULES_USE_CO` |
| `Priority` | 210,287 | str:210287 | `0`<br>`1000`<br>`10`<br>`11`<br>`50` |
| `Rerunable` | 210,287 | str:210287 | `True`<br>`False` |
| `Resource_List.arch` | 5 | str:5 | `linux` |
| `Resource_List.mem` | 20,360 | str:20360 | `10gb`<br>`80gb`<br>`400gb`<br>`5kb`<br>`524288000kb` |
| `Resource_List.mpiprocs` | 146,273 | str:146273 | `128`<br>`1280`<br>`32`<br>`1`<br>`256` |
| `Resource_List.ncpus` | 210,287 | str:210287 | `1`<br>`1280`<br>`4`<br>`96`<br>`32` |
| `Resource_List.ndesktops` | 5 | str:5 | `1` |
| `Resource_List.ngpus` | 19,943 | str:19943 | `1`<br>`4`<br>`3`<br>`16`<br>`8` |
| `Resource_List.nodect` | 210,287 | str:210287 | `1`<br>`10`<br>`4`<br>`2`<br>`8` |
| `Resource_List.nodes` | 4,021 | str:4021 | `1:ppn=1`<br>`1:ppn=126`<br>`1:ppn=52`<br>`1:ppn=40`<br>`1:ppn=4` |
| `Resource_List.place` | 210,287 | str:210287 | `scatter:excl`<br>`free`<br>`pack`<br>`scatter`<br>`scatter:shared` |
| `Resource_List.select` | 210,287 | str:210287 | `1:ngpus=1:mpiprocs=128`<br>`10:ncpus=128:mpiprocs=128`<br>`4:ncpus=1`<br>`4:ncpus=24`<br>`2:ncpus=16:mpiprocs=16` |
| `Resource_List.walltime` | 210,278 | str:210278 | `60:00:00`<br>`48:00:00`<br>`72:00:00`<br>`12:00:00`<br>`00:30:00` |
| `SHELL_DEBUG:-0}\"` | 25,532 | str:25532 | `\'1\' ]; then case \"$-\" in *v*x*) set +vx; _m lshdbg=\'vx\' ;; *v*) set +v; _mlshdbg=\'v\' ;; *x*) set +x; _mlshd bg=\'x\' ;; *) _mlshdbg=\'\' ;; esac; fi; un`<br>`\'1\' ]; then case \"$-\" in *v*x*) set +vx; _m lshdbg=\'vx\' ;; *v*) set +v; _mlshdbg=\'v\' ;; *x*) set +x; _mlshd bg=\'x\' ;; *) _mlshdbg=\'\' ;; esac; fi; un`<br>`\'1\' ]; then case \"$-\" in *v*x*) set +vx; _m lshdbg=\'vx\' ;; *v*) set +v; _mlshdbg=\'v\' ;; *x*) set +x; _mlshd bg=\'x\' ;; *) _mlshdbg=\'\' ;; esac; fi; un`<br>`\'1\' ]; then case \"$-\" in *v*x*) set +vx; _m lshdbg=\'vx\' ;; *v*) set +v; _mlshdbg=\'v\' ;; *x*) set +x; _mlshd bg=\'x\' ;; *) _mlshdbg=\'\' ;; esac; fi; un`<br>`\'1\' ]; then case \"$-\" in *v*x*) set +vx; _m lshdbg=\'vx\' ;; *v*) set +v; _mlshdbg=\'v\' ;; *x*) set +x; _mlshd bg=\'x\' ;; *) _mlshdbg=\'\' ;; esac; fi; un` |
| `Shell_Path_List` | 40,930 | str:40930 | `/bin/bash`<br>`/bin/csh`<br>`/bin/sh`<br>`/bin/tcsh` |
| `Stageout_status` | 145,708 | str:145708 | `1`<br>`0` |
| `Submit_Host` | 210,287 | str:210287 | `champ2.cm.cluster`<br>`champ1.cm.cluster`<br>`r05gn04.cm.cluster`<br>`r13cn10.cm.cluster`<br>`r04gn02.cm.cluster` |
| `Submit_arguments` | 209,841 | str:209841 | `mpii_efficientnet_b4.bash`<br>`mpii_efficientnet_b7.bash`<br>`mpii_efficientnet_v2_l.bash`<br>`v2_s.bash`<br>`npt.pbs` |
| `User_List` | 22 | str:22 | `bmurugan`<br>`yarasi`<br>`mudixitk`<br>`sumank`<br>`muralinio` |
| `Variable_List` | 210,287 | str:210287 | `PBS_O_HOME=/home/amitl,PBS_O_LANG=en_US.UTF-8, PBS_O_LOGNAME=amitl, PBS_O_PATH=/scratch/amitl/Eyegaze/envP/bin:/scratch/amitl/Eyegaze/venv /bin:/home/amitl/loca`<br>`PBS_O_HOME=/home/amitl,PBS_O_LANG=en_US.UTF-8, PBS_O_LOGNAME=amitl, PBS_O_PATH=/scratch/amitl/Eyegaze/envP/bin:/scratch/amitl/Eyegaze/venv /bin:/home/amitl/loca`<br>`PBS_O_HOME=/home/amitl,PBS_O_LANG=en_US.UTF-8, PBS_O_LOGNAME=amitl, PBS_O_PATH=/scratch/amitl/Eyegaze/envP/bin:/scratch/amitl/Eyegaze/venv /bin:/home/amitl/loca`<br>`PBS_O_HOME=/home/amitl,PBS_O_LANG=en_US.UTF-8, PBS_O_LOGNAME=amitl, PBS_O_PATH=/scratch/amitl/Eyegaze/envP/bin:/scratch/amitl/Eyegaze/venv /bin:/home/amitl/loca`<br>`PBS_O_HOME=/home/nidhi,PBS_O_LANG=en_US.UTF-8, PBS_O_LOGNAME=nidhi, PBS_O_PATH=/cm/local/apps/environment-modules/4.5.3//bin:/usr/local/bi n:/usr/bin:/usr/local` |
| `\"${_mlv}\"` | 84 | str:84 | `\"${_mlv#[0-9]}\" ]; then if [ -n \"`eval \'echo ${\'$_m lv\'+x}\'`\" ]; then _mlre=\"${_mlre:-}${_mlv}_modquar=\'`eval \'echo ${\'$_mlv\'}\'`\' \"; fi; _mlrv=\`<br>`\"${_mlv#[0-9]}\" ]; then if [ -n \"`eval \'echo ${\'$_m lv\'+x}\'`\" ]; then _mlre=\"${_mlre:-}${_mlv}_modquar=\'`eval \'echo ${\'$_mlv\'}\'`\' \"; fi; _mlrv=\`<br>`\"${_mlv#[0-9]}\" ]; then if [ -n \"`eval \'echo ${\'$_m lv\'+x}\'`\" ]; then _mlre=\"${_mlre:-}${_mlv}_modquar=\'`eval \'echo ${\'$_mlv\'}\'`\' \"; fi; _mlrv=\`<br>`\"${_mlv#[0-9]}\" ]; then if [ -n \"`eval \'echo ${\'$_m lv\'+x}\'`\" ]; then _mlre=\"${_mlre:-}${_mlv}_modquar=\'`eval \'echo ${\'$_mlv\'}\'`\' \"; fi; _mlrv=\`<br>`\"${_mlv#[0-9]}\" ]; then if [ -n \"`eval \'echo ${\'$_m lv\'+x}\'`\" ]; then _mlre=\"${_mlre:-}${_mlv}_modquar=\'`eval \'echo ${\'$_mlv\'}\'`\' \"; fi; _mlrv=\` |
| `] || [ \"$_sp_arg\"` | 1,711 | str:1711 | `\"--help\" ]; then command spack env -h; else case $_sp_arg in activate) _a=\" $@\"; if [ \"${_a#* --sh}\" != \"$_ a\" ] || [ \"${_a#* --csh}\" != \"$_a\" ] || `<br>`\"--help\" ]; then command spack env -h; else case $_sp_arg in activate) _a=\" $@\"; if [ \"${_a#* --sh}\" != \"$_ a\" ] || [ \"${_a#* --csh}\" != \"$_a\" ] || `<br>`\"--help\" ]; then command spack env -h; else case $_sp_arg in activate) _a=\" $@\"; if [ \"${_a#* --sh}\" != \"$_ a\" ] || [ \"${_a#* --csh}\" != \"$_a\" ] || `<br>`\"--help\" ]; then command spack env -h; else case $_sp_arg in activate) _a=\" $@\"; if [ \"${_a#* --sh}\" != \"$_ a\" ] || [ \"${_a#* --csh}\" != \"$_a\" ] || `<br>`\"--help\" ]; then command spack env -h; else case $_sp_arg in activate) _a=\" $@\"; if [ \"${_a#* --sh}\" != \"$_ a\" ] || [ \"${_a#* --csh}\" != \"$_a\" ] || ` |
| `_DEBUG:-0}\"` | 84 | str:84 | `\'1\' ]; then case \"$-\" in *v*x*) set +vx; _mlshdb g=\'vx\' ;; *v*) set +v; _mlshdbg=\'v\' ;; *x*) set +x; _mlshdbg=\' x\' ;; *) _mlshdbg=\'\' ;; esac; fi; un`<br>`\'1\' ]; then case \"$-\" in *v*x*) set +vx; _mlshdb g=\'vx\' ;; *v*) set +v; _mlshdbg=\'v\' ;; *x*) set +x; _mlshdbg=\' x\' ;; *) _mlshdbg=\'\' ;; esac; fi; un`<br>`\'1\' ]; then case \"$-\" in *v*x*) set +vx; _mlshdb g=\'vx\' ;; *v*) set +v; _mlshdbg=\'v\' ;; *x*) set +x; _mlshdbg=\' x\' ;; *) _mlshdbg=\'\' ;; esac; fi; un`<br>`\'1\' ]; then case \"$-\" in *v*x*) set +vx; _mlshdb g=\'vx\' ;; *v*) set +v; _mlshdbg=\'v\' ;; *x*) set +x; _mlshdbg=\' x\' ;; *) _mlshdbg=\'\' ;; esac; fi; un`<br>`\'1\' ]; then case \"$-\" in *v*x*) set +vx; _mlshdb g=\'vx\' ;; *v*) set +v; _mlshdbg=\'v\' ;; *x*) set +x; _mlshdbg=\' x\' ;; *) _mlshdbg=\'\' ;; esac; fi; un` |
| `_sp_arg=\"$1\"; shift; fi; if [ \"$_sp_arg\"` | 1,711 | str:1711 | `\"-h\"` |
| `argument_list` | 1 | str:1 | `<jsdl-hpcpa:Argument>-np</jsdl-hpcpa:Argument><jsdl-hpcpa:A rgument>128</jsdl-hpcpa:Argument><jsdl-hpcpa:Argument>./wrf.exe</jsdl-h pcpa:Argument>` |
| `array` | 19 | str:19 | `True` |
| `array_id` | 112 | str:112 | `230396[].champ1`<br>`230397[].champ1`<br>`230399[].champ1`<br>`230400[].champ1`<br>`230407[].champ1` |
| `array_index` | 112 | str:112 | `1`<br>`2`<br>`3`<br>`4`<br>`5` |
| `array_indices_remaining` | 19 | str:19 | `-` |
| `array_indices_submitted` | 19 | str:19 | `1-5`<br>`1-15`<br>`1-2`<br>`3-10`<br>`11-12` |
| `array_state_count` | 19 | str:19 | `Queued:0 Running:0 Exiting:0 Expired:0` |
| `comment` | 210,219 | str:210219 | `Job run at Sun Jan 12 at 17:31 on (r04gn02:ngpus=1:ncpus=1) and f inished`<br>`Job run at Sun Jan 12 at 17:40 on (r05gn03:ngpus=1:ncpus=1) and f inished`<br>`Job run at Sun Jan 12 at 17:40 on (r04gn01:ngpus=1:ncpus=1) and f inished`<br>`Job run at Sun Jan 12 at 17:44 on (r05gn04:ngpus=1:ncpus=1) and f inished`<br>`Job run at Sun Jan 12 at 17:52 on (r09cn10:ncpus=128)+(r12cn35:nc pus=128)+(r13cn35:ncpus=128)+(r13cn36:ncpus=128)+(r08cn05:ncpus=128)+(r 08cn11:ncpus=128)+(r11` |
| `ctime` | 210,287 | str:210287 | `Sun Jan 12 17:31:30 2025`<br>`Sun Jan 12 17:40:22 2025`<br>`Sun Jan 12 17:40:50 2025`<br>`Sun Jan 12 17:44:22 2025`<br>`Sun Jan 12 17:52:11 2025` |
| `depend` | 187 | str:187 | `beforeok:143900.champ1@champ1`<br>`beforeok:143901.champ1@champ1`<br>`afterok:143900.champ1@champ1`<br>`beforeok:143908.champ1@champ1`<br>`beforeok:143909.champ1@champ1` |
| `egroup` | 210,287 | str:210287 | `csio`<br>`igib`<br>`ccmb`<br>`csmcri`<br>`csir4pi` |
| `estimated.exec_vnode` | 1,094 | str:1094 | `(r11cn10:ncpus=16)+(r11cn36:ncpus=16)`<br>`(r11cn10:ncpus=128)`<br>`(r11cn10:ncpus=16)`<br>`(r11cn10:ncpus=55)`<br>`(r05gn02:ncpus=128:ngpus=4)` |
| `estimated.start_time` | 1,094 | str:1094 | `Tue Jan 14 15:23:12 2025`<br>`Wed Jan 15 12:57:47 2025`<br>`Fri Jan 17 11:33:40 2025`<br>`Fri Jan 17 20:27:09 2025`<br>`Sat Jan 18 15:23:31 2025` |
| `etime` | 210,215 | str:210215 | `Sun Jan 12 17:31:30 2025`<br>`Sun Jan 12 17:40:22 2025`<br>`Sun Jan 12 17:40:50 2025`<br>`Sun Jan 12 17:44:22 2025`<br>`Sun Jan 12 17:52:11 2025` |
| `euser` | 210,287 | str:210287 | `amitl`<br>`nidhi`<br>`saikatc`<br>`bganguly`<br>`vhazra` |
| `exec_host` | 206,420 | str:206420 | `r04gn02/0`<br>`r05gn03/0`<br>`r04gn01/0`<br>`r05gn04/0`<br>`r09cn10/0*128+r12cn35/0*128+r13cn35/0*128+r13cn36/0*128+r08cn05 /0*128+r08cn11/0*128+r11cn06/0*128+r11cn28/0*128+r12cn13/0*128+r01cn34/ 0*128` |
| `exec_vnode` | 206,420 | str:206420 | `(r04gn02:ngpus=1:ncpus=1)`<br>`(r05gn03:ngpus=1:ncpus=1)`<br>`(r04gn01:ngpus=1:ncpus=1)`<br>`(r05gn04:ngpus=1:ncpus=1)`<br>`(r09cn10:ncpus=128)+(r12cn35:ncpus=128)+(r13cn35:ncpus=128)+(r 13cn36:ncpus=128)+(r08cn05:ncpus=128)+(r08cn11:ncpus=128)+(r11cn06:ncpu s=128)+(r11cn28:ncpus=128` |
| `executable` | 2 | str:2 | `<jsdl-hpcpa:Executable>./wrf.exe</jsdl-hpcpa:Executable>`<br>`<jsdl-hpcpa:Executable>mpirun</jsdl-hpcpa:Executable>` |
| `forward_x11_cookie` | 245 | str:245 | `MIT-MAGIC-COOKIE-1:30169054841049fd3e1dfed43814c4c3:0`<br>`MIT-MAGIC-COOKIE-1:a3e78facc6edcd205db47b44f2d01028:0`<br>`MIT-MAGIC-COOKIE-1:f55b68060d3e70f761cd4552aa4ca554:0`<br>`MIT-MAGIC-COOKIE-1:16c04129c03a009d5e1c88060aa2d30f:0`<br>`MIT-MAGIC-COOKIE-1:8f35b473a9594000d23a6bf78a4c47f7:0` |
| `forward_x11_port` | 245 | str:245 | `True` |
| `hashname` | 206,442 | str:206442 | `100000.champ1`<br>`100001.champ1`<br>`100002.champ1`<br>`100003.champ1`<br>`100004.champ1` |
| `history_timestamp` | 210,287 | str:210287 | `1736690372`<br>`1736683904`<br>`1736683973`<br>`1736684185`<br>`1736744618` |
| `if [ \"${_mlv}\"` | 25,542 | str:25542 | `\"${_mlv##*[!A-Za-z0-9_]}\`<br>`\"${_mlv##*[!A-Za-z0-9_]}\" -a` |
| `interactive` | 6,137 | str:6137 | `True` |
| `job_id` | 210,287 | str:210287 | `100000.champ1`<br>`100001.champ1`<br>`100002.champ1`<br>`100003.champ1`<br>`100004.champ1` |
| `job_state` | 210,287 | str:210287 | `F` |
| `jobdir` | 206,396 | str:206396 | `/home/amitl`<br>`/home/nidhi`<br>`/home/saikatc`<br>`/home/bganguly`<br>`/home/vhazra` |
| `mtime` | 210,287 | str:210287 | `Sun Jan 12 19:29:32 2025`<br>`Sun Jan 12 17:41:44 2025`<br>`Sun Jan 12 17:42:53 2025`<br>`Sun Jan 12 17:46:25 2025`<br>`Mon Jan 13 10:33:38 2025` |
| `project` | 210,287 | str:210287 | `_pbs_project_default`<br>`urgent` |
| `qtime` | 210,287 | str:210287 | `Sun Jan 12 17:31:30 2025`<br>`Sun Jan 12 17:40:22 2025`<br>`Sun Jan 12 17:40:50 2025`<br>`Sun Jan 12 17:44:22 2025`<br>`Sun Jan 12 17:52:11 2025` |
| `queue` | 210,287 | str:210287 | `gpu`<br>`workq`<br>`defective_test`<br>`mistralq`<br>`iworkq` |
| `queue_rank` | 210,287 | str:210287 | `1736683290866`<br>`1736683822677`<br>`1736683850862`<br>`1736684062478`<br>`1736684531403` |
| `queue_type` | 210,287 | str:210287 | `E` |
| `resources_used.cpupercent` | 206,402 | str:206402 | `126`<br>`74`<br>`71`<br>`73`<br>`13293` |
| `resources_used.cput` | 206,402 | str:206402 | `02:30:10`<br>`00:00:26`<br>`00:00:32`<br>`00:01:03`<br>`2129:22:18` |
| `resources_used.mem` | 206,401 | str:206401 | `19914852kb`<br>`394804kb`<br>`12586124kb`<br>`3465276kb`<br>`27761364kb` |
| `resources_used.ncpus` | 206,401 | str:206401 | `1`<br>`1280`<br>`4`<br>`96`<br>`32` |
| `resources_used.vmem` | 206,401 | str:206401 | `461200608kb`<br>`2735108kb`<br>`142983604kb`<br>`35745116kb`<br>`1219150956kb` |
| `resources_used.walltime` | 206,401 | str:206401 | `01:57:58`<br>`00:01:19`<br>`00:02:00`<br>`00:02:01`<br>`16:41:24` |
| `run_count` | 206,442 | str:206442 | `1`<br>`2`<br>`21`<br>`6933`<br>`28` |
| `run_version` | 206,439 | str:206439 | `1`<br>`2`<br>`21`<br>`6933`<br>`28` |
| `schedselect` | 210,287 | str:210287 | `1:ngpus=1:mpiprocs=128:ncpus=1`<br>`10:ncpus=128:mpiprocs=128`<br>`4:ncpus=1`<br>`4:ncpus=24`<br>`2:ncpus=16:mpiprocs=16` |
| `server` | 210,287 | str:210287 | `champ1` |
| `session_id` | 206,017 | str:206017 | `1164651`<br>`2300250`<br>`2303021`<br>`3572274`<br>`1767953` |
| `source_files` | 210,287 | list:210287 | `["final_full_job_data.txt", "qstat_output.txt"]`<br>`["final_full_job_data.txt", "full_job_details.txt"]` |
| `stime` | 169,337 | str:169337 | `Sun Jan 12 17:31:31 2025`<br>`Sun Jan 12 17:40:22 2025`<br>`Sun Jan 12 17:40:51 2025`<br>`Sun Jan 12 17:44:22 2025`<br>`Sun Jan 12 18:25:33 2025` |
| `substate` | 210,287 | str:210287 | `92`<br>`91`<br>`93` |
