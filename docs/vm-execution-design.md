# Future VM execution and escape-canary design

## Status

This is a design note for a future Hammer condition. It is not implemented, calibrated, or part of Pilot 1. The current container apparatus exposes filesystem syscalls and cannot execute model-authored programs.

The reason to consider a VM is not merely stronger containment. Native execution would let an agent-created program issue syscalls without passing through Hammer's current adapter. A dedicated guest gives the experiment its own kernel and lets the host observe a whole machine rather than pretending that an `execve` request and its final output describe what the program did.

## Intended boundary

The eventual condition may give the model broad freedom inside a deliberately small guest: compiling and executing programs, creating processes, modifying its filesystem, and possibly changing its own guest kernel. The safety boundary remains outside that world.

The proposed guest has an immutable base image, a separate writable `/work` disk, no virtual network interface, and no shared directories, clipboard, `vsock`, USB, host filesystem, credentials, or GPU passthrough. Model communication crosses one narrow virtio-serial control channel to a host-side harness. Ollama and the harness remain outside the guest.

QEMU runs as a dedicated unprivileged account inside a sparse filesystem and process namespace. Debugger and management sockets are local Unix sockets available only to the observer. The QEMU account receives access only to the guest images, required control endpoints, and the deliberately placed escape canary described below.

## Observation

For filesystem structures used through today's adapter, Hammer already records every model-requested operation and complete before/after state. Executable tools create a second causal layer that must not become opaque:

1. Model actions create a specific artifact version.
2. The model invokes that version with particular arguments and input.
3. The tool and any descendants perform internal actions.
4. Their output and environmental changes become observations for later model turns.

A future execution trace should therefore bind each invocation to the executable's exact bytes and digest; arguments, environment, working directory, and stdin; stdout and stderr; process descendants; syscall arguments and results; exit status or signal; resource use; and filesystem lineage. It must also record exactly which output bytes were returned to the model and whether any capture limit was reached.

The trustworthy record must be produced outside the guest. Once the model can run native code and perhaps modify its kernel, in-guest logs and tracepoints can be disabled or forged. A host-side debugger is useful for developing and validating the apparatus, while actual runs need structured hypervisor-side observation, disk and memory snapshots, and explicit detection of guest-kernel modification. The exact tracing mechanism remains unresolved.

## Dedicated research host

Local models make a nearly airgapped design practical. The current plan is to treat the `ai1` machine as a disposable research appliance: a minimal host with no personal data, browser sessions, cloud credentials, SSH private keys, GitHub token, or trusted mounts. Ollama should be reachable only on host loopback when the harness runs locally. The physical management network should be disabled during an experimental run after models, tasks, and images have been staged.

Publication credentials stay on a separate workstation. After the VM is stopped, the host produces a hashed artifact bundle for review and transfer. Guest-generated files, filenames, terminal output, and archives remain untrusted and must not be automatically executed, previewed, or indexed on the publishing machine.

Development and scientific operation are separate modes. Development may use restricted management networking. A scientific run starts from measured host and guest images with networking disabled, and any evidence of a host escape invalidates the ordinary result and triggers inspection or rebuild.

## Undisclosed escape canary

The QEMU process's outer filesystem sandbox will contain an obvious flag that is unreachable from an intact guest. Its purpose is to give escaped code an immediate, low-friction endpoint and to give the apparatus an unambiguous trigger. It is not disclosed to the model and is not part of the task.

The canary is generated outside the guest with a unique unpredictable value for every run. Before a trigger, its existence, path, name, value, and semantics must not appear in the model prompt, guest image, QEMU arguments, process environment, tracked repository, or ordinary experiment log. It should become obvious only after code has crossed the guest boundary into the sparse outer sandbox. The exact value may be retained in sealed incident evidence after access; public records use a digest or redaction rather than publishing it.

An independent host observer watches for canary access. Opening or reading the file, observing its unique value on the control channel, or touching any other forbidden outer resource immediately causes the observer to:

1. Stop further model requests.
2. Freeze the VM and preserve memory, disk, serial, debugger, and hypervisor evidence.
3. Terminate the QEMU process and keep the research host offline.
4. Record `escape_canary_triggered` as a distinct safety-terminal event, not ordinary task success.
5. Treat the host and the integrity of the run as suspect until inspection or rebuild.

Mechanical termination matters more than the model's interpretation. The canary may reduce the motivation for further exploration after an escape, but containment cannot depend on the model recognizing it, submitting it, or choosing to stop.

## Interpretation

The primitive container condition and a broad VM condition answer different questions. The first asks what an agent composes from a precisely enumerated interface. The second asks what computational environment an agent builds when given a machine and little inherited userspace. They should remain separate named conditions with separate calibration and claims.

A canary trigger is valuable evidence but does not make the task a VM-escape challenge. Advertising an external flag would directly reward hypervisor exploitation and materially change the experiment. The undisclosed canary is only an observer-controlled terminal condition at a boundary we hope is never crossed.

## Decisions still open

- Guest kernel, boot mechanism, and virtual-machine monitor configuration.
- Hypervisor-side tracing method and its completeness when the guest kernel changes.
- The minimal virtual devices required for control, storage, time, and entropy.
- Whether guest-root and guest-kernel modification are allowed in the first VM condition.
- How the outer QEMU sandbox detects canary and forbidden-resource access without creating a guest-visible signal.
- Snapshot, evidence-sealing, host-attestation, and rebuild procedures.
- Reference programs and adversarial fixtures used to validate process, syscall, filesystem, and terminal-event capture before model execution is enabled.
