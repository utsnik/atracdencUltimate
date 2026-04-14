# Backup and Documentation Recovery Plan

This plan addresses the need to secure the "lost" conversation data and normalize the project documentation to reflect our current Phase 9/10 status.

## User Review Required

> [!IMPORTANT]
> **Backup Location**: I will consolidate the brain files into `atracdenc/backups/brain_recovery/` within the project directory. This ensures they are tracked in your workspace and not just hidden in the system app data.

## Proposed Changes

### Recovery & Backup
1. **Source Brain Consolidation**: Copy artifacts and logs from the previous "crashed" session (`1c0b098d`) into the project workspace for permanent storage.
2. **Current Brain Backup**: Snapshot the current session's artifacts to the same backup directory.

### Project Documentation
1. **[NEW/UPDATE] [atrac3_lp2_parity_log.md](file:///c:/Users/Igland/Antigravity/Ghidra/atracdenc/atrac3_lp2_parity_log.md)**: 
    - Port the Phase 1-5 history from the previous session.
    - Add NEW entries for Phase 6-8 (QMF Delay, Unit 0 Sync, forensic sweeps).
    - Document Phase 9 (Subband Mapping `{0,1,3,2}`) and the Phase 10 Tonal target.
2. **[UPDATE] [handoff.md](file:///c:/Users/Igland/Antigravity/Ghidra/atracdenc/handoff.md)**: Synchronize the phase numbering to match our true progress.

## Open Questions

- **Git Tracking**: Should these backups be committed to git, or kept locally in the `backups/` folder? (I will assume local for now to avoid bloating the repo unless you specify otherwise).

## Verification Plan

### Automated Verification
- Verify the existence of the backup files in the project directory.
- Check the syntax and link integrity of the newly updated `atrac3_lp2_parity_log.md`.

### Manual Verification
- Review the updated roadmap to ensure it matches your expectations for the project's current state.
