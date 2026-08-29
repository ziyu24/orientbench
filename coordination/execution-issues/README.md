# SERVER execution issues

B or C reviews every abnormal SERVER terminal state and the correctness of its
results. The append-only review receipt binds the prior journal and verified
evidence before SERVER can recover or a correction can be issued. Ordinary
correctable execution errors do not enter this registry and do not notify the
user: the reviewer directly issues the next `rNNN` correction and records
`VERIFIED_CORRECT` after the corrected execution.

This append-only registry is reserved for catastrophic errors that fundamentally
invalidate the scientific route or result chain, or cause unrecoverable external
damage. Such a report binds the `rNNN` instruction and evidence and requires an
immediate user notice.
