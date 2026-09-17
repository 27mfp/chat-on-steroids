# Skills

Type `/` at the beginning of the composer to open the compact Commands and Skills menu.
Selecting a Skill adds a removable chip without sending a message. There is no separate sidebar
entry, library dialog or Skills action in the attachment menu.

The small **+** at the bottom of the slash menu inserts
`Please add the following skills to my COS skills:` into the composer. Add the desired Skill
content or references and send the request to ChatGPT when ready. The button itself neither
sends a message nor changes files.

Leading `/id` and `/prompt id` commands also select Skills. Multiple leading selections preserve their
order and are deduplicated. Slash text inside the task or a code example stays literal. The chips
are a presentation of those authored commands in the existing draft. Switching chats preserves each
draft's text, attachments and selections; removing a chip removes that selection only.

## Add Skills through chat

Ask ChatGPT to create Markdown instructions in the personal library, exposed to Core as `/skills`.
Normal filesystem permissions apply. Skill documents use `.md`; a package uses `SKILL.md` and
may contain supporting resources. Existing discovered packages remain readable. There are no
file/package import, remove, refresh or open-directory buttons in the composer.

Skill documents retain the limits of 128,000 UTF-8 bytes and 96,000 UTF-16 characters.
The managed library supports 64 Skills. Reading a Skill does not execute its scripts.

## Project and shared discovery

Discovery includes repository `.agents/skills`, the selected project's `.codex/skills`, user
`~/.agents/skills`, `$CODEX_HOME/skills` (normally `~/.codex/skills`), its `.system` directory and the
platform's Codex administration directory. External locations must already be inside the app's
approved roots with file reading enabled. Discovering a Skill never grants access to another
folder or changes the task's working directory.

Each discovered Skill has a stable command derived from its canonical path. Adding another package
with the same display name does not retarget an existing selection. Discovery is bounded, avoids
linked child folders, and does not index example Skills inside a package's own reference material.
Reopening the slash menu reloads the scoped catalog; scan errors remain visible in the menu.

Optional `agents/openai.yaml` supplies display metadata and implicit-use policy. For example:

```yaml
interface:
  display_name: Review this project
  short_description: Read, change, verify.
policy: { allow_implicit_invocation: false }
```

Both inline and block YAML policy have the same meaning. Invalid policy does not enable implicit
invocation. Explicit selection remains available. Tool dependencies in metadata are descriptive;
they do not register tools or enable plugins.

Approved admin, Codex-home and scoped project `config.toml` files can layer `[skills]` settings:
`include_instructions`, `max_context_tokens`, `[skills.bundled].enabled` and `[[skills.config]]`
entries with one `name` or `path` selector plus `enabled`. Later scoped rules take precedence.

## Delivery

Opening prompts include a bounded Skill index. Explicit selections load the instruction bodies
using the existing input preparation boundary. Core instructions and the authored task remain
complete; oversized selections share the current prompt budget and retain exact paths for reading
the remainder. Explicit follow-ups add selected Skill instructions without repeating setup.

The outbox freezes the prepared delivery text. A later edit to an installed Skill cannot silently
change an already-prepared retry. Missing or moved selections fail visibly and must be reselected
or removed from the draft.

The package/discovery and authored-chip implementation incorporate
[@igorbelchior86's #260](https://github.com/totec448-spec/chat-on-steroids/pull/260).
