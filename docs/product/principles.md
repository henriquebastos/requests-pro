# Product Principles

Product behavior principles for this project. The "product" is the framework itself plus the recipe it teaches; the "users" are developers and coding agents building API clients. Drafted by the Driver during Ariad adoption (2026-06-12) from the demo's docstring, the README, and the Navigator's stated design philosophy — *(confirm)*.

## Principles

### Endpoints stay trivial

Every API quirk — error envelopes, auth schemes, token renewal, JSON dialects, base URLs, timeouts — is handled exactly once, in the lowest applicable layer (Response → Session → Auth → TokenStore). By the time work reaches `Client`/SubClients, an endpoint is one readable line. If a SubClient method grows logic, a lower layer is missing a hook.

### Transparent infrastructure

Auth renewal, 401 recovery, JSON encoding/decoding, and audit happen without per-call ceremony. A consumer who reads only a SubClient must be able to trust that the machinery underneath did the right thing. Corollary: the machinery must never *break* the request it serves (an audit failure or observability concern must not turn a successful call into an error).

### Separation of concerns everywhere

One class, one reason to change. The integration layer (client + webhook verification) speaks the vendor's protocol; the service layer translates to the domain; webhook handlers stay thin and business-focused. The framework ships the integration layer and documents the boundary.

### Composable over configurable

Capabilities arrive as small cooperating pieces (session mixins, adapter decorators, callable stores) composed explicitly in a factory — not as a god-object with flags. New cross-cutting concerns (retry, rate limiting) should follow the adapter-decorator seam proven by `Audit`.

### The repository is a recipe

Agent-legibility is a product feature. Docs, demo, and tests must teach the pattern well enough that a coding agent pointed at an API spec plus this repo generates a correct client without human coaching. The demo is the recipe's exhibit and must stay canonical; tests double as usage examples.

### The framework absorbs structure, integrations keep idiosyncrasy

When the same shape recurs across clients (error taxonomy, HMAC webhook verification, response builders for tests), it becomes a framework capability with hooks. What is genuinely vendor-specific (a particular payload wrapper, a vendor's link format) stays in the integration subclass. A workaround that a concrete client has to hand-roll is a roadmap signal, not a permanent resident.

### Don't break consumers

`requests-pro` 1.0.0 is published. Extension points are subclassing hooks; consumers never fork or monkey-patch. Breaking the public surface requires a deliberate, versioned decision — including when the async flavor lands: sync consumers must not notice.

## Questions to Answer

- When sync and async flavors exist, is API symmetry (identical names, mirrored modules) a hard promise or a soft goal?
- Is Python 3.10 support a real promise (D-003 currently breaks it) or should the floor move?
