# Voting platform rules, threat model and MVP boundaries

- Issue: #40 (parent roadmap #13)
- Status: **APPROVED by the repository owner (19fn)** on PR #72: the decision
  document, the IdP choice, and the retention and SLO defaults below (MVP).
  Open items in section 8 (B2, B4) still need an owner answer before the
  issues they block.
- Version: 1.0

Rule IDs (`R-xx`) are referenced by downstream tests. The last section maps
each to the issue that must test it.

## 1. Audience and stakes (R-01)

- Private organizational elections (clubs, companies, associations, internal
  boards). One deployment, one operator organization, many elections.
- Not suitable for, and makes no claim of certification for, statutory or
  public elections, or any election where legal validity depends on
  certification, observers or verifiable-voting guarantees.
- Stakes: a disputed result is an organizational/reputational problem, not a
  legal one. Integrity and one-person-one-ballot matter more than anonymity
  strength.

## 2. Election lifecycle

### States (R-02)

`draft` -> `scheduled` -> `open` -> `closed` -> `published` -> `archived`;
`cancelled` is reachable from `draft`, `scheduled`, `open` and `closed`.

| Transition | Allowed by | Notes |
|---|---|---|
| draft -> scheduled/open | manager | needs a valid published ballot version, frozen roster policy, privacy and results policy |
| scheduled -> open | system at `opens_at`, or manager | server checks time on every cast; a late scheduler never extends the window |
| open -> closed | system at `closes_at`, or manager with reason | |
| closed -> published | manager after tally reconciliation (see R-13) | creates an immutable result version |
| any non-archived -> cancelled | manager with confirmation and reason | cancelled elections never show a certified/final result |
| published/cancelled -> archived | manager | read-only |

Every transition is atomic, checked against the current state under a lock or
conditional update, and audited. Illegal transitions are rejected.

### Time (R-03)

- All instants stored and compared in UTC. Local timezone is display only and
  always shown explicitly.
- Voting window is `[opens_at, closes_at)`: open-inclusive, close-exclusive.
  The authoritative clock is the database/server UTC time at the moment the
  ballot transaction commits its state check; client time is never trusted.
- Close and cancel are serialized against in-flight casts: a ballot is
  accepted only if the election is open inside the same transaction.

### Eligibility (R-04)

- Eligibility is a per-election roster bound to the stable identity
  (issuer + subject), not to email.
- Roster is editable until the election opens. At opening it is frozen and its
  size is stored as the denominator.
- After opening, managers may only **revoke** eligibility (before the voter
  has cast). Adding voters after opening is not allowed in the MVP; an
  election needing that is cancelled and recreated.
- A ballot already accepted is never deleted or invalidated by later
  revocation or account deactivation; the count stays in the frozen result.
  Revocation reduces nothing retroactively. The frozen denominator is not
  changed by revocation, and the tally reports the number of revocations.

### Ballots (R-05)

- Exactly one final ballot per eligible voter per election, enforced by a
  database constraint on an election-scoped entitlement, not by cookies, IP
  or process-local locks.
- **No vote changes** and no revoting in the MVP.
- Accepted ballots are immutable. No deletion by any role.

### Cancel and reopen (R-06)

- Cancel is terminal. No reopen of any election that has had a ballot cast.
- A `scheduled` election may return to `draft`. A `closed` election with zero
  ballots may be reopened only by a manager with a recorded reason and a new
  closing time; otherwise create a new election.
- Cancelled elections keep their ballots sealed and never publish a winner.

## 3. Ballot rules

### Question types (R-07)

- Supported: **single-choice** and **bounded multiple-choice** (explicit
  `min` and `max` selections, `1 <= min <= max <= number of options`, where
  `min = 0` is only allowed on optional questions).
- Deferred, needing separate approval: ranked, weighted, delegated, write-in,
  cumulative voting, candidate image upload.
- Ballot definitions are versioned and immutable once the election opens.
  Duplicate or empty options are rejected. Content is plain text, escaped.

### Required, optional and abstention (R-08)

- Required question: voter must select within `[min, max]`.
- Optional question: voter may leave it unanswered.
- Explicit abstention is a distinct, per-election configurable option
  ("Abstain") counted separately from unanswered. Default: off for
  single-choice, no abstention shown. A fully blank ballot is allowed only when
  all questions are optional or abstention is enabled.

### Quorum and denominator (R-09)

- Quorum, if set, is a percentage of the **frozen eligible roster** that must
  have submitted a ballot (a ballot counts as participation even if all
  answers are abstentions).
- Percentages per option are reported against the number of ballots for the
  question and also the number of selections; multiple-choice percentages need
  not sum to 100%.
- Quorum not met: result is marked "quorum not met" and no winner is declared.

### Ties (R-10)

- The system never breaks ties by database order or rounding. A tie for the
  winning place is reported as a tie; resolution is outside the system and is
  recorded by a manager as a note on the published result.
- No votes: reported as "no votes", no winner.

### Results visibility (R-11)

- Policy per election, frozen before open: `hidden_until_published`
  (default) or `live_totals` (opt-in, managers only may enable; disabled for
  secret elections with fewer than a configured minimum electorate).
- Turnout visibility is separate from choice totals. Voters see only their
  own participation status.
- Publication requires an authorized role, a closed and reconciled tally and a
  recorded reason. Corrections are new immutable versions, never overwrites.

## 4. Identity, access and privacy modes

### Concepts (R-12)

| Concept | Meaning | Stored where |
|---|---|---|
| Authentication | who the user is (IdP-verified issuer+subject) | identity store |
| Eligibility | permission to vote in a given election | roster |
| Participation | fact that a voter has cast a ballot | participation record |
| Ballot contents | the selections | ballot store |

In identified mode, participation and contents may be linked by managers'
policy only as stated in the matrix. In secret mode they must not be linkable
(see section 6).

### Access matrix (R-13)

C = create/manage, R = read, - = none, own = only own record.

| Capability | Voter | Election manager (assigned elections) | Auditor (assigned) | Operator |
|---|---|---|---|---|
| Cast own ballot | yes | only if also eligible | no | no |
| Own participation status | own | own | own | own |
| Ballot definition | R | C (draft only) | R | - |
| Roster | - | C (before open, revoke after) | R | - |
| Participation list (who voted) | - | R | R | - |
| Choices by voter, identified mode | - | R only if election privacy policy is `identified` | R same rule | no app-level access; DB access is residual risk |
| Choices by voter, secret mode | - | never | never | never (by design, see residual risk) |
| Aggregate results before publication | - | R | R | - |
| Aggregate results after publication | R | R | R | - |
| State transitions, publish | - | C | - | - |
| Role grants | - | - | - | first admin provisioning and break-glass, audited |
| Audit log | - | R (own elections) | R | R operational only |
| System config, backups | - | - | - | C |

Deny by default. No role is granted automatically by signup or email domain.
Role changes are election-scoped and audited. The last manager of an election
cannot be removed. Operators cannot cast or modify ballots through the app.

## 5. Threat model (R-14)

| Threat | Mitigation in scope | Residual risk |
|---|---|---|
| Replay of a ballot request | CSRF token, single-use entitlement, idempotency key scoped to entitlement | none beyond idempotency design |
| Concurrent requests (double submit, close vs cast) | DB unique constraint + transaction; state check inside same transaction; MySQL deadlock retry | retry latency under load |
| Cross-election access (IDOR) | all queries scoped by election id; roles election-scoped; tests per endpoint | implementation bugs, covered by tests |
| Malicious administrator (manager) | roster changes before open only; frozen definition; audited reasons; managers cannot edit ballots or see secret choices | manager can add ineligible voters before open; detectable via audit and roster review |
| Database or log access (DBA, operator, backup thief) | separated tables, no choices or ballot identifiers in logs, encrypted backups | a DBA in identified mode sees choices; in any mode can alter data. Tamper-evidence reduces but does not remove this |
| Timing correlation (who voted when) | no per-ballot timestamps in secret mode, coarse or no ordering IDs | small electorates, privileged log/binlog access can still correlate |
| Coercion and vote selling | none; no receipt-freeness | Explicitly unsupported |
| Availability (DoS, outage during window) | rate limits, health checks, targets in section 7 | no multi-region HA; election window not auto-extended |
| Compromised client devices | server-side validation only | malware can change what the voter submits; not mitigated |
| Compromised IdP | restrict issuers; audit | an IdP compromise can impersonate eligible voters |
| Compromised application/operator code | audit and external checkpoints | no end-to-end verifiability (see #67) |

Supported privacy guarantees: other voters and managers cannot see an
individual's choices in secret mode; identified mode makes no privacy
promise beyond access control. The system does **not** protect against a
fully malicious operator/DBA, collusion of components, coercion, or compromised
clients.

## 6. Privacy modes that may ship (R-15)

| Mode | May ship in MVP? | Condition |
|---|---|---|
| Identified (voter linked to ballot, visible to authorized roles) | Yes | privacy mode frozen at creation, shown to voters before voting |
| "Confidential" (identity kept apart from ballot, participation recorded, no choice-to-voter access via app roles) | Yes, but must be labeled "not anonymous" | no UI or docs claim anonymity |
| Anonymous / secret ballot with unlinkability | **Disabled** | stays disabled behind a deployment flag until #53 review and sign-off and #54 pass; no voter foreign key in the ballot table |

Mode cannot change after opening. Wording shown to voters must match the real
guarantee.

## 7. Operational decisions

### Identity provider (R-16)

- MVP: external OIDC provider, Authorization Code flow with PKCE; no custom
  password store. Identity key is `issuer + sub`. Issuers allowlisted by
  configuration. Local/demo login exists only in explicit dev mode, never in
  production.
- MFA, account recovery and deactivation are the **IdP's and the organization's
  responsibility**. Privileged roles (manager, auditor, operator) require
  MFA asserted by the IdP (`amr`/`acr`) or an approved step-up; the
  application documents but does not implement recovery.

### Deployment assumptions (R-17)

- Single container image behind a TLS-terminating reverse proxy, one MySQL 8.4
  instance with backups, multiple app workers. Time via NTP-synced hosts.
- Operators are trusted for availability, not for ballot secrecy beyond the
  guarantees above.

### Retention (R-18)

| Data | Retention |
|---|---|
| Ballots and final tallies | kept for the organization's records period, default 3 years after archive, then deleted |
| Roster and participation | same as ballots |
| Identity records | while the account is active; anonymized on deactivation if no election references it, otherwise kept minimally |
| Audit events | same as ballots, minimum 3 years |
| Application logs | 30 days, no ballot choices or tokens |
| Backups | 35 days, encrypted |

Values are the owner-approved MVP defaults; changes need a new approval. No claim of legal
compliance (GDPR etc.) is made without separate review.

### Targets (R-19)

| Metric | Target |
|---|---|
| Availability during a voting window | 99.5% measured per election window |
| Cast latency | p95 under 1 s, p99 under 3 s at 200 concurrent voters |
| Capacity | 5,000 eligible voters per election, 50 concurrent elections |
| RPO | 15 minutes (accepted ballots), RTO 4 hours |
| Backup restore | rehearsed before first production election |

## 8. Unresolved decisions (blockers)

Each open item needs an owner answer before the named issue starts:

1. B1 (blocks #44): RESOLVED. Microsoft Entra ID is the production IdP
   (OIDC). The tenant ID is deployment configuration.
2. B2 (blocks #47, #55): quorum on/off defaults and tie resolution process.
3. B3 (blocks #63): RESOLVED. Retention periods in section 7 approved as MVP
   defaults. Legal review is still required before any compliance claim.
4. B4 (blocks #53/#54): whether secret-ballot mode is needed at all for MVP.
   Anonymous mode stays disabled meanwhile.
5. B5 (blocks #62): RESOLVED. Targets in section 7 (R-19) approved as MVP
   defaults.

## 9. Rule-to-test map (R-20)

| Rule | Downstream issue / acceptance test |
|---|---|
| R-01, R-15 | #63 privacy notice, #54 UI wording tests |
| R-02, R-03, R-06 | #47 state machine, clock-boundary and concurrency tests |
| R-04 | #46 roster freeze, revoke-after-cast tests |
| R-05 | #51 duplicate/concurrent/idempotency tests |
| R-07, R-08 | #48 validation tests, #51 payload validation |
| R-09, R-10 | #55 tally, quorum and tie tests |
| R-11 | #56 visibility tests across routes |
| R-12, R-13 | #45 permission matrix tests, #46 participation tests |
| R-14 | #43, #51, #53, #58 abuse-case tests |
| R-16 | #44 OIDC tests |
| R-17, R-19 | #61 alerts, #62 restore rehearsal |
| R-18 | #63 retention job tests |
