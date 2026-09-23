ARG BASE_IMAGE=precommit_hook:failure-history-56fd0c1
FROM ${BASE_IMAGE}
COPY upstream/agent-interp-envs/environments/precommit_hook/agent.py /opt/agent.py
COPY pilot /opt/pilot
COPY research/scripts/validate_state_equivalence.py /opt/research/scripts/validate_state_equivalence.py
RUN chmod -R go-rwx /opt/pilot /opt/research /opt/agent.py
